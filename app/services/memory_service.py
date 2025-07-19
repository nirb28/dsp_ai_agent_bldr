import json
import logging
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from app.config import MemoryType, settings
from app.models.agent_models import MemoryEntry

logger = logging.getLogger(__name__)

class MemoryService:
    """Service for managing agent memory"""
    
    def __init__(self):
        self.memory_stores: Dict[str, List[MemoryEntry]] = {}
        self._load_memory_stores()
    
    def _load_memory_stores(self):
        """Load memory stores from storage"""
        memory_file = Path(settings.STORAGE_PATH) / "agent_memories.json"
        
        try:
            if memory_file.exists():
                with open(memory_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for agent_name, memories_data in data.items():
                    memories = []
                    for memory_data in memories_data:
                        # Convert timestamp string back to datetime
                        if memory_data.get('timestamp'):
                            memory_data['timestamp'] = datetime.fromisoformat(memory_data['timestamp'])
                        
                        memory = MemoryEntry(**memory_data)
                        memories.append(memory)
                    
                    self.memory_stores[agent_name] = memories
                    
                logger.info(f"Loaded memory for {len(self.memory_stores)} agents")
            else:
                logger.info("No existing memory stores found")
                
        except Exception as e:
            logger.error(f"Error loading memory stores: {str(e)}")
    
    def _save_memory_stores(self):
        """Save memory stores to storage"""
        try:
            memory_file = Path(settings.STORAGE_PATH) / "agent_memories.json"
            memory_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert memory stores to dict for JSON serialization
            data = {}
            for agent_name, memories in self.memory_stores.items():
                memories_data = []
                for memory in memories:
                    memory_dict = memory.dict()
                    # Convert datetime to string
                    if memory_dict.get('timestamp'):
                        memory_dict['timestamp'] = memory_dict['timestamp'].isoformat()
                    memories_data.append(memory_dict)
                
                data[agent_name] = memories_data
            
            with open(memory_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info("Saved agent memories")
            
        except Exception as e:
            logger.error(f"Error saving memory stores: {str(e)}")
    
    async def store_conversation(self, agent_name: str, messages: List[Dict[str, str]]):
        """Store conversation messages in agent memory"""
        try:
            if agent_name not in self.memory_stores:
                self.memory_stores[agent_name] = []
            
            # Store each message as a memory entry
            for message in messages:
                memory_id = str(uuid.uuid4())
                memory = MemoryEntry(
                    id=memory_id,
                    agent_name=agent_name,
                    content=message.get("content", ""),
                    role=message.get("role", "user"),
                    metadata=message.get("metadata", {})
                )
                
                self.memory_stores[agent_name].append(memory)
            
            # Apply memory limits based on agent configuration
            await self._apply_memory_limits(agent_name)
            
            self._save_memory_stores()
            
        except Exception as e:
            logger.error(f"Error storing conversation for {agent_name}: {str(e)}")
    
    async def get_memory_context(self, agent_name: str, current_messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Get relevant memory context for agent execution"""
        try:
            from app.services.agent_service import AgentService
            
            # Get agent configuration to determine memory type
            agent_service = AgentService()
            config = agent_service.get_configuration(agent_name)
            
            if not config or config.memory.type == MemoryType.NONE:
                return current_messages
            
            if agent_name not in self.memory_stores:
                return current_messages
            
            memories = self.memory_stores[agent_name]
            
            if config.memory.type == MemoryType.BUFFER:
                # Return recent memories within token limit
                context_messages = []
                total_tokens = 0
                max_tokens = config.memory.max_tokens
                
                # Add current messages first
                for msg in current_messages:
                    msg_tokens = len(msg.get("content", "").split()) * 1.3  # Rough token estimation
                    if total_tokens + msg_tokens <= max_tokens:
                        context_messages.append(msg)
                        total_tokens += msg_tokens
                    else:
                        break
                
                # Add recent memories
                for memory in reversed(memories[-20:]):  # Last 20 memories
                    memory_tokens = len(memory.content.split()) * 1.3
                    if total_tokens + memory_tokens <= max_tokens:
                        context_messages.insert(-len(current_messages), {
                            "role": memory.role,
                            "content": memory.content,
                            "metadata": memory.metadata
                        })
                        total_tokens += memory_tokens
                    else:
                        break
                
                return context_messages
            
            elif config.memory.type == MemoryType.SUMMARY:
                # Create a summary of past conversations
                summary = await self._create_memory_summary(agent_name, memories)
                
                # Add summary as system message
                context_messages = [{
                    "role": "system",
                    "content": f"Previous conversation summary: {summary}"
                }]
                context_messages.extend(current_messages)
                
                return context_messages
            
            elif config.memory.type == MemoryType.VECTOR:
                # For vector memory, we'd implement similarity search
                # For now, fall back to buffer memory
                return await self.get_memory_context(agent_name, current_messages)
            
            else:
                return current_messages
                
        except Exception as e:
            logger.error(f"Error getting memory context for {agent_name}: {str(e)}")
            return current_messages
    
    async def _create_memory_summary(self, agent_name: str, memories: List[MemoryEntry]) -> str:
        """Create a summary of conversation memories"""
        try:
            # Simple summarization - in a real implementation, you'd use an LLM
            recent_memories = memories[-10:]  # Last 10 memories
            
            summary_parts = []
            for memory in recent_memories:
                if memory.role == "user":
                    summary_parts.append(f"User asked: {memory.content[:100]}")
                elif memory.role == "assistant":
                    summary_parts.append(f"Assistant responded: {memory.content[:100]}")
            
            return " | ".join(summary_parts)
            
        except Exception as e:
            logger.error(f"Error creating memory summary: {str(e)}")
            return "No summary available"
    
    async def _apply_memory_limits(self, agent_name: str):
        """Apply memory limits based on agent configuration"""
        try:
            from app.services.agent_service import AgentService
            
            agent_service = AgentService()
            config = agent_service.get_configuration(agent_name)
            
            if not config or agent_name not in self.memory_stores:
                return
            
            memories = self.memory_stores[agent_name]
            max_tokens = config.memory.max_tokens
            
            # Calculate total tokens
            total_tokens = sum(len(memory.content.split()) * 1.3 for memory in memories)
            
            # Remove oldest memories if over limit
            while total_tokens > max_tokens and len(memories) > 1:
                removed_memory = memories.pop(0)
                total_tokens -= len(removed_memory.content.split()) * 1.3
            
        except Exception as e:
            logger.error(f"Error applying memory limits: {str(e)}")
    
    async def query_memory(self, agent_name: str, query: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
        """Query agent memory"""
        try:
            if agent_name not in self.memory_stores:
                return []
            
            memories = self.memory_stores[agent_name]
            
            if not query:
                # Return recent memories
                recent_memories = memories[-limit:]
            else:
                # Simple text search - in a real implementation, you'd use vector search
                matching_memories = []
                query_lower = query.lower()
                
                for memory in memories:
                    if query_lower in memory.content.lower():
                        matching_memories.append(memory)
                
                recent_memories = matching_memories[-limit:]
            
            # Convert to dict format
            result = []
            for memory in recent_memories:
                result.append({
                    "id": memory.id,
                    "content": memory.content,
                    "role": memory.role,
                    "timestamp": memory.timestamp.isoformat(),
                    "metadata": memory.metadata
                })
            
            return result
            
        except Exception as e:
            logger.error(f"Error querying memory for {agent_name}: {str(e)}")
            return []
    
    async def clear_memory(self, agent_name: str) -> bool:
        """Clear all memory for an agent"""
        try:
            if agent_name in self.memory_stores:
                self.memory_stores[agent_name] = []
                self._save_memory_stores()
                logger.info(f"Cleared memory for agent: {agent_name}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error clearing memory for {agent_name}: {str(e)}")
            return False
    
    def get_memory_stats(self, agent_name: str) -> Dict[str, Any]:
        """Get memory statistics for an agent"""
        try:
            if agent_name not in self.memory_stores:
                return {"total_memories": 0, "total_tokens": 0}
            
            memories = self.memory_stores[agent_name]
            total_memories = len(memories)
            total_tokens = sum(len(memory.content.split()) * 1.3 for memory in memories)
            
            return {
                "total_memories": total_memories,
                "total_tokens": int(total_tokens),
                "oldest_memory": memories[0].timestamp.isoformat() if memories else None,
                "newest_memory": memories[-1].timestamp.isoformat() if memories else None
            }
            
        except Exception as e:
            logger.error(f"Error getting memory stats for {agent_name}: {str(e)}")
            return {"total_memories": 0, "total_tokens": 0}
