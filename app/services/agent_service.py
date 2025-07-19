import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from app.config import AgentConfig, settings, process_env_vars_in_model
from app.models.agent_models import AgentMetrics

logger = logging.getLogger(__name__)

class AgentService:
    """Service for managing agent configurations"""
    
    def __init__(self):
        self.configurations: Dict[str, AgentConfig] = {}
        self.metrics: Dict[str, AgentMetrics] = {}
        self._load_configurations()
        self._load_metrics()
    
    def _load_configurations(self):
        """Load agent configurations from storage"""
        config_file = Path(settings.STORAGE_PATH) / settings.AGENT_CONFIGS_FILE
        
        try:
            if config_file.exists():
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for agent_name, config_data in data.items():
                    try:
                        config = AgentConfig(**config_data)
                        # Process environment variables
                        config = process_env_vars_in_model(config)
                        self.configurations[agent_name] = config
                    except Exception as e:
                        logger.error(f"Error loading configuration '{agent_name}': {str(e)}")
                        continue
                        
                logger.info(f"Loaded {len(self.configurations)} agent configurations")
            else:
                logger.info("No existing configurations found, starting with empty set")
                # Create default configuration
                self._create_default_configuration()
                
        except Exception as e:
            logger.error(f"Error loading configurations: {str(e)}")
            self._create_default_configuration()
    
    def _create_default_configuration(self):
        """Create a default agent configuration"""
        from app.config import LLMConfig, ToolConfig, MemoryConfig, AgentType, ToolType, MemoryType
        
        default_config = AgentConfig(
            name="default",
            description="Default conversational agent with basic tools",
            agent_type=AgentType.REACT,
            llm=LLMConfig(),
            system_prompt="You are a helpful AI assistant. Use the available tools to help the user with their requests.",
            tools=[
                ToolConfig(
                    name="calculator",
                    type=ToolType.CALCULATOR,
                    description="Perform mathematical calculations",
                    enabled=True
                )
            ],
            memory=MemoryConfig(type=MemoryType.BUFFER)
        )
        
        self.configurations["default"] = default_config
        self._save_configurations()
    
    def _save_configurations(self):
        """Save configurations to storage"""
        try:
            config_file = Path(settings.STORAGE_PATH) / settings.AGENT_CONFIGS_FILE
            config_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert configurations to dict for JSON serialization
            data = {}
            for agent_name, config in self.configurations.items():
                data[agent_name] = config.dict()
            
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info("Saved agent configurations")
            
        except Exception as e:
            logger.error(f"Error saving configurations: {str(e)}")
    
    def _load_metrics(self):
        """Load agent metrics from storage"""
        metrics_file = Path(settings.STORAGE_PATH) / "agent_metrics.json"
        
        try:
            if metrics_file.exists():
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for agent_name, metrics_data in data.items():
                    try:
                        # Convert datetime strings back to datetime objects
                        if metrics_data.get('last_execution'):
                            metrics_data['last_execution'] = datetime.fromisoformat(metrics_data['last_execution'])
                        if metrics_data.get('created_at'):
                            metrics_data['created_at'] = datetime.fromisoformat(metrics_data['created_at'])
                        if metrics_data.get('updated_at'):
                            metrics_data['updated_at'] = datetime.fromisoformat(metrics_data['updated_at'])
                            
                        self.metrics[agent_name] = AgentMetrics(**metrics_data)
                    except Exception as e:
                        logger.error(f"Error loading metrics for '{agent_name}': {str(e)}")
                        continue
                        
                logger.info(f"Loaded metrics for {len(self.metrics)} agents")
            else:
                logger.info("No existing metrics found")
                
        except Exception as e:
            logger.error(f"Error loading metrics: {str(e)}")
    
    def _save_metrics(self):
        """Save agent metrics to storage"""
        try:
            metrics_file = Path(settings.STORAGE_PATH) / "agent_metrics.json"
            metrics_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert metrics to dict for JSON serialization
            data = {}
            for agent_name, metrics in self.metrics.items():
                metrics_dict = metrics.dict()
                # Convert datetime objects to strings
                if metrics_dict.get('last_execution'):
                    metrics_dict['last_execution'] = metrics_dict['last_execution'].isoformat()
                if metrics_dict.get('created_at'):
                    metrics_dict['created_at'] = metrics_dict['created_at'].isoformat()
                if metrics_dict.get('updated_at'):
                    metrics_dict['updated_at'] = metrics_dict['updated_at'].isoformat()
                    
                data[agent_name] = metrics_dict
            
            with open(metrics_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            logger.info("Saved agent metrics")
            
        except Exception as e:
            logger.error(f"Error saving metrics: {str(e)}")
    
    def add_configuration(self, agent_name: str, config: AgentConfig) -> bool:
        """Add or update an agent configuration"""
        try:
            # Process environment variables
            config = process_env_vars_in_model(config)
            
            # Update the name in config to match the key
            config.name = agent_name
            
            self.configurations[agent_name] = config
            self._save_configurations()
            
            # Initialize metrics if not exists
            if agent_name not in self.metrics:
                self.metrics[agent_name] = AgentMetrics(agent_name=agent_name)
                self._save_metrics()
            
            logger.info(f"Added/updated agent configuration: {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error adding configuration '{agent_name}': {str(e)}")
            return False
    
    def get_configuration(self, agent_name: str) -> Optional[AgentConfig]:
        """Get an agent configuration"""
        return self.configurations.get(agent_name)
    
    def get_configuration_names(self) -> List[str]:
        """Get list of all agent configuration names"""
        return list(self.configurations.keys())
    
    def get_configurations(self) -> List[Dict[str, Any]]:
        """Get information about all configurations"""
        configurations = []
        
        for agent_name, config in self.configurations.items():
            metrics = self.metrics.get(agent_name)
            
            config_info = {
                "name": agent_name,
                "description": config.description,
                "agent_type": config.agent_type.value,
                "llm_provider": config.llm.provider.value,
                "llm_model": config.llm.model,
                "tools_count": len(config.tools),
                "memory_type": config.memory.type.value,
                "created_at": metrics.created_at.isoformat() if metrics else None,
                "updated_at": metrics.updated_at.isoformat() if metrics else None,
                "total_executions": metrics.total_executions if metrics else 0,
                "success_rate": (
                    metrics.successful_executions / metrics.total_executions * 100
                    if metrics and metrics.total_executions > 0 else 0
                )
            }
            configurations.append(config_info)
        
        return configurations
    
    def delete_configuration(self, agent_name: str) -> bool:
        """Delete an agent configuration"""
        try:
            if agent_name not in self.configurations:
                logger.warning(f"Configuration '{agent_name}' not found")
                return False
            
            # Don't allow deletion of default configuration
            if agent_name == "default":
                logger.warning("Cannot delete default configuration")
                return False
            
            # Remove configuration
            del self.configurations[agent_name]
            
            # Remove metrics
            if agent_name in self.metrics:
                del self.metrics[agent_name]
            
            self._save_configurations()
            self._save_metrics()
            
            logger.info(f"Deleted agent configuration: {agent_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting configuration '{agent_name}': {str(e)}")
            return False
    
    def duplicate_configuration(self, source_name: str, target_name: str) -> bool:
        """Duplicate an agent configuration"""
        try:
            if source_name not in self.configurations:
                logger.error(f"Source configuration '{source_name}' not found")
                return False
            
            if target_name in self.configurations:
                logger.error(f"Target configuration '{target_name}' already exists")
                return False
            
            # Create a copy of the source configuration
            source_config = self.configurations[source_name]
            target_config = AgentConfig(**source_config.dict())
            target_config.name = target_name
            target_config.description = f"Copy of {source_config.description}"
            
            self.configurations[target_name] = target_config
            self._save_configurations()
            
            # Initialize metrics for the new configuration
            self.metrics[target_name] = AgentMetrics(agent_name=target_name)
            self._save_metrics()
            
            logger.info(f"Duplicated configuration '{source_name}' to '{target_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Error duplicating configuration: {str(e)}")
            return False
    
    def reload_configurations(self) -> bool:
        """Reload configurations from file"""
        try:
            # Clear existing configurations
            self.configurations = {}
            self.metrics = {}
            
            # Reload from files
            self._load_configurations()
            self._load_metrics()
            
            logger.info(f"Reloaded configurations. Found {len(self.configurations)} configurations.")
            return True
            
        except Exception as e:
            logger.error(f"Error reloading configurations: {str(e)}")
            return False
    
    def update_metrics(self, agent_name: str, execution_time: float, success: bool, iterations: int, tool_calls: int):
        """Update agent metrics after execution"""
        try:
            if agent_name not in self.metrics:
                self.metrics[agent_name] = AgentMetrics(agent_name=agent_name)
            
            metrics = self.metrics[agent_name]
            metrics.total_executions += 1
            
            if success:
                metrics.successful_executions += 1
            else:
                metrics.failed_executions += 1
            
            # Update averages
            total_time = metrics.average_execution_time * (metrics.total_executions - 1) + execution_time
            metrics.average_execution_time = total_time / metrics.total_executions
            
            total_iterations = metrics.average_iterations * (metrics.total_executions - 1) + iterations
            metrics.average_iterations = total_iterations / metrics.total_executions
            
            metrics.total_tool_calls += tool_calls
            metrics.last_execution = datetime.now()
            metrics.updated_at = datetime.now()
            
            self._save_metrics()
            
        except Exception as e:
            logger.error(f"Error updating metrics for '{agent_name}': {str(e)}")
    
    def get_metrics(self, agent_name: str) -> Optional[AgentMetrics]:
        """Get metrics for an agent"""
        return self.metrics.get(agent_name)
