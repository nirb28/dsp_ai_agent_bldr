import asyncio
import logging
import time
import uuid
from typing import Dict, List, Any, Optional, AsyncGenerator
from datetime import datetime

from langchain_groq import ChatGroq
from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, AIMessage, SystemMessage
from langgraph.prebuilt import create_react_agent
from langgraph.graph import StateGraph, END

from app.config import AgentConfig, LLMProvider, AgentType
from app.models.agent_models import AgentExecution, ToolCall, AgentState
from app.services.tool_service import ToolService
from app.services.memory_service import MemoryService

logger = logging.getLogger(__name__)

class ExecutionService:
    """Service for executing agents using LangGraph"""
    
    def __init__(self, tool_service: ToolService, memory_service: MemoryService):
        self.tool_service = tool_service
        self.memory_service = memory_service
        self.active_executions: Dict[str, AgentExecution] = {}
    
    def _create_llm(self, config: AgentConfig):
        """Create LLM instance based on configuration"""
        llm_config = config.llm
        
        if llm_config.provider == LLMProvider.GROQ:
            return ChatGroq(
                model=llm_config.model,
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens,
                top_p=llm_config.top_p,
                groq_api_key=llm_config.api_key
            )
        elif llm_config.provider == LLMProvider.OPENAI:
            return ChatOpenAI(
                model=llm_config.model,
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens,
                top_p=llm_config.top_p,
                openai_api_key=llm_config.api_key
            )
        elif llm_config.provider == LLMProvider.OPENAI_COMPATIBLE:
            return ChatOpenAI(
                model=llm_config.model,
                temperature=llm_config.temperature,
                max_tokens=llm_config.max_tokens,
                top_p=llm_config.top_p,
                openai_api_key=llm_config.api_key or "dummy",
                openai_api_base=llm_config.server_url
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {llm_config.provider}")
    
    def _create_agent_graph(self, config: AgentConfig):
        """Create agent graph based on configuration"""
        llm = self._create_llm(config)
        tools = self.tool_service.get_tools_for_agent(config.name)
        
        if config.agent_type == AgentType.REACT:
            # Use LangGraph's built-in ReAct agent
            return create_react_agent(llm, tools)
        
        elif config.agent_type == AgentType.CONVERSATIONAL:
            # Create a simple conversational agent
            return self._create_conversational_agent(llm, tools, config)
        
        elif config.agent_type == AgentType.TOOL_CALLING:
            # Create a tool-focused agent
            return self._create_tool_calling_agent(llm, tools, config)
        
        elif config.agent_type == AgentType.PLANNING:
            # Create a planning agent
            return self._create_planning_agent(llm, tools, config)
        
        else:
            # Default to ReAct
            return create_react_agent(llm, tools)
    
    def _create_conversational_agent(self, llm, tools, config: AgentConfig):
        """Create a simple conversational agent"""
        def agent_node(state: AgentState):
            messages = state["messages"]
            
            # Add system message if not present
            if not messages or (isinstance(messages[0], dict) and messages[0].get("role") != "system"):
                system_msg = {"role": "system", "content": config.system_prompt}
                messages = [system_msg] + messages
            
            # Convert to LangChain message format
            lc_messages = []
            for msg in messages:
                # Handle if message is already a LangChain message object
                if isinstance(msg, SystemMessage):
                    lc_messages.append(msg)
                elif isinstance(msg, HumanMessage):
                    lc_messages.append(msg)
                elif isinstance(msg, AIMessage):
                    lc_messages.append(msg)
                # Handle dictionary format messages
                elif isinstance(msg, dict):
                    if msg.get("role") == "system":
                        lc_messages.append(SystemMessage(content=msg["content"]))
                    elif msg.get("role") == "user":
                        lc_messages.append(HumanMessage(content=msg["content"]))
                    elif msg.get("role") == "assistant":
                        lc_messages.append(AIMessage(content=msg["content"]))
            
            # Get response from LLM
            response = llm.invoke(lc_messages)
            
            # Add response to messages
            messages.append({"role": "assistant", "content": response.content})
            
            return {"messages": messages, "is_complete": True}
        
        # Create simple graph
        workflow = StateGraph(AgentState)
        workflow.add_node("agent", agent_node)
        workflow.set_entry_point("agent")
        workflow.add_edge("agent", END)
        
        return workflow.compile()
    
    def _create_tool_calling_agent(self, llm, tools, config: AgentConfig):
        """Create a tool-focused agent"""
        # For now, use ReAct as it's good for tool calling
        return create_react_agent(llm, tools)
    
    def _create_planning_agent(self, llm, tools, config: AgentConfig):
        """Create a planning agent"""
        # For now, use ReAct as base - can be extended later
        return create_react_agent(llm, tools)
    
    async def execute_agent(
        self, 
        agent_name: str, 
        config: AgentConfig, 
        messages: List[Dict[str, str]], 
        context: Optional[Dict[str, Any]] = None
    ) -> AgentExecution:
        """Execute an agent with the given messages"""
        
        execution_id = str(uuid.uuid4())
        execution = AgentExecution(
            agent_name=agent_name,
            execution_id=execution_id,
            status="running"
        )
        
        self.active_executions[execution_id] = execution
        
        try:
            start_time = time.time()
            
            # Load memory context
            memory_context = await self.memory_service.get_memory_context(agent_name, messages)
            
            # Create agent graph
            agent_graph = self._create_agent_graph(config)
            
            # Prepare initial state
            if config.agent_type == AgentType.CONVERSATIONAL:
                state = {
                    "messages": messages,
                    "context": context or {},
                    "iteration": 0,
                    "max_iterations": config.max_iterations,
                    "is_complete": False
                }
            else:
                # For ReAct and other agents, use the standard format
                state = {
                    "messages": messages,
                    "context": context or {}
                }
            
            # Execute agent
            result = await asyncio.get_event_loop().run_in_executor(
                None, agent_graph.invoke, state
            )
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Extract final response
            if "messages" in result and result["messages"]:
                last_message = result["messages"][-1]
                # Handle both dict and AIMessage formats
                if isinstance(last_message, dict):
                    final_response = last_message.get("content", "No response")
                elif hasattr(last_message, "content"):
                    # Handle LangChain message objects (AIMessage, etc.)
                    final_response = last_message.content
                else:
                    final_response = str(last_message)
            else:
                # Handle result output
                if isinstance(result, dict):
                    final_response = str(result.get("output", "No response"))
                else:
                    final_response = str(result)
            
            # Update execution
            execution.end_time = datetime.now()
            execution.status = "completed"
            execution.final_response = final_response
            execution.iterations = result.get("iteration", 1)
            
            # Store in memory
            await self.memory_service.store_conversation(agent_name, messages + [
                {"role": "assistant", "content": final_response}
            ])
            
            logger.info(f"Agent {agent_name} executed successfully in {execution_time:.2f}s")
            
        except asyncio.TimeoutError:
            execution.status = "timeout"
            execution.error = f"Execution timed out after {config.timeout} seconds"
            execution.end_time = datetime.now()
            logger.error(f"Agent {agent_name} execution timed out")
            
        except Exception as e:
            execution.status = "failed"
            execution.error = str(e)
            execution.end_time = datetime.now()
            logger.error(f"Agent {agent_name} execution failed: {str(e)}")
        
        finally:
            # Remove from active executions
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
        
        return execution
    
    async def execute_agent_stream(
        self, 
        agent_name: str, 
        config: AgentConfig, 
        messages: List[Dict[str, str]], 
        context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute an agent with streaming response"""
        
        execution_id = str(uuid.uuid4())
        execution = AgentExecution(
            agent_name=agent_name,
            execution_id=execution_id,
            status="running"
        )
        
        self.active_executions[execution_id] = execution
        
        try:
            # Load memory context
            memory_context = await self.memory_service.get_memory_context(agent_name, messages)
            
            # Create agent graph
            agent_graph = self._create_agent_graph(config)
            
            # For streaming, we'll simulate chunks for now
            # In a real implementation, you'd use the agent's streaming capabilities
            
            yield {
                "chunk": "Starting agent execution...",
                "agent_name": agent_name,
                "is_final": False,
                "metadata": {"execution_id": execution_id}
            }
            
            # Execute agent (non-streaming for now)
            execution = await self.execute_agent(agent_name, config, messages, context)
            
            # Stream the response in chunks
            if execution.final_response:
                words = execution.final_response.split()
                for i, word in enumerate(words):
                    chunk = word + " "
                    is_final = (i == len(words) - 1)
                    
                    yield {
                        "chunk": chunk,
                        "agent_name": agent_name,
                        "is_final": is_final,
                        "metadata": {
                            "execution_id": execution_id,
                            "iterations": execution.iterations,
                            "tool_calls": len(execution.tool_calls)
                        }
                    }
                    
                    # Small delay to simulate streaming
                    await asyncio.sleep(0.1)
            
        except Exception as e:
            yield {
                "chunk": f"Error: {str(e)}",
                "agent_name": agent_name,
                "is_final": True,
                "metadata": {"execution_id": execution_id, "error": str(e)}
            }
        
        finally:
            if execution_id in self.active_executions:
                del self.active_executions[execution_id]
    
    def get_active_executions(self) -> List[AgentExecution]:
        """Get list of currently active executions"""
        return list(self.active_executions.values())
    
    def cancel_execution(self, execution_id: str) -> bool:
        """Cancel an active execution"""
        if execution_id in self.active_executions:
            execution = self.active_executions[execution_id]
            execution.status = "cancelled"
            execution.end_time = datetime.now()
            del self.active_executions[execution_id]
            logger.info(f"Cancelled execution {execution_id}")
            return True
        return False
