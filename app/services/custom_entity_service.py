"""
Custom Entity Recognition Service for domain-specific PII patterns.

This service allows clients to define custom PII patterns and integrates
them with the Presidio anonymization system.
"""

import logging
import re
from typing import List, Dict, Optional, Any, Pattern
from dataclasses import dataclass
from pathlib import Path
import yaml

from app.utils.config import get_config
from app.exceptions import DocumentProcessingError

logger = logging.getLogger(__name__)


@dataclass
class CustomEntity:
    """Represents a custom PII entity pattern."""
    name: str
    pattern: str
    description: str
    confidence: float = 0.8
    context: List[str] = None
    enabled: bool = True


class CustomEntityService:
    """Service for managing custom PII entity patterns."""
    
    def __init__(self):
        """Initialize custom entity service."""
        self.config = get_config()
        self.entities_config_path = self.config.custom_entities.config_path
        self.custom_entities: Dict[str, CustomEntity] = {}
        self.compiled_patterns: Dict[str, Pattern] = {}
        
        # Load custom entities configuration
        self.load_custom_entities()
    
    def load_custom_entities(self) -> None:
        """
        Load custom entity patterns from configuration file.
        
        Raises:
            DocumentProcessingError: If configuration loading fails
        """
        try:
            if not Path(self.entities_config_path).exists():
                logger.info(f"Custom entities config file not found: {self.entities_config_path}")
                return
            
            with open(self.entities_config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            if not config_data or 'entities' not in config_data:
                logger.warning("No custom entities found in configuration")
                return
            
            self.custom_entities = {}
            self.compiled_patterns = {}
            
            for entity_data in config_data['entities']:
                try:
                    entity = CustomEntity(
                        name=entity_data['name'],
                        pattern=entity_data['pattern'],
                        description=entity_data.get('description', ''),
                        confidence=entity_data.get('confidence', 0.8),
                        context=entity_data.get('context', []),
                        enabled=entity_data.get('enabled', True)
                    )
                    
                    if entity.enabled:
                        # Compile regex pattern for performance
                        compiled_pattern = re.compile(entity.pattern, re.IGNORECASE)
                        self.custom_entities[entity.name] = entity
                        self.compiled_patterns[entity.name] = compiled_pattern
                        
                        logger.info(f"Loaded custom entity: {entity.name}")
                        
                except Exception as e:
                    logger.error(f"Failed to load custom entity: {str(e)}")
            
            logger.info(f"Loaded {len(self.custom_entities)} custom entities")
            
        except Exception as e:
            logger.error(f"Failed to load custom entities configuration: {str(e)}")
            raise DocumentProcessingError(f"Custom entities configuration failed: {str(e)}")
    
    def detect_custom_entities(self, text: str) -> List[Dict[str, Any]]:
        """
        Detect custom entities in text.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of detected custom entities
        """
        detected_entities = []
        
        for entity_name, pattern in self.compiled_patterns.items():
            entity = self.custom_entities[entity_name]
            
            # Find all matches
            matches = pattern.finditer(text)
            
            for match in matches:
                # Check context if specified
                if entity.context and not self._check_context(text, match, entity.context):
                    continue
                
                detected_entities.append({
                    'entity_type': entity_name,
                    'text': match.group(),
                    'start': match.start(),
                    'end': match.end(),
                    'confidence': entity.confidence,
                    'description': entity.description
                })
        
        return detected_entities
    
    def detect_custom_entities_batch(self, texts: List[str]) -> List[List[Dict[str, Any]]]:
        """
        Detect custom entities in multiple texts.
        
        Args:
            texts: List of texts to analyze
            
        Returns:
            List of detected entities for each text
        """
        results = []
        
        for i, text in enumerate(texts):
            try:
                entities = self.detect_custom_entities(text)
                results.append(entities)
            except Exception as e:
                logger.error(f"Failed to detect custom entities in text {i}: {str(e)}")
                results.append([])
        
        return results
    
    def validate_custom_pattern(self, pattern: str) -> bool:
        """
        Validate a custom regex pattern.
        
        Args:
            pattern: Regex pattern to validate
            
        Returns:
            True if pattern is valid, False otherwise
        """
        try:
            re.compile(pattern, re.IGNORECASE)
            return True
        except re.error:
            return False
    
    def add_custom_entity(self, entity: CustomEntity) -> bool:
        """
        Add a new custom entity.
        
        Args:
            entity: Custom entity to add
            
        Returns:
            True if added successfully, False otherwise
        """
        try:
            # Validate pattern
            if not self.validate_custom_pattern(entity.pattern):
                logger.error(f"Invalid regex pattern for entity {entity.name}")
                return False
            
            # Compile pattern
            compiled_pattern = re.compile(entity.pattern, re.IGNORECASE)
            
            # Add to collections
            self.custom_entities[entity.name] = entity
            self.compiled_patterns[entity.name] = compiled_pattern
            
            # Save to configuration
            self._save_custom_entities()
            
            logger.info(f"Added custom entity: {entity.name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add custom entity {entity.name}: {str(e)}")
            return False
    
    def remove_custom_entity(self, entity_name: str) -> bool:
        """
        Remove a custom entity.
        
        Args:
            entity_name: Name of entity to remove
            
        Returns:
            True if removed successfully, False otherwise
        """
        try:
            if entity_name in self.custom_entities:
                del self.custom_entities[entity_name]
                del self.compiled_patterns[entity_name]
                
                # Save to configuration
                self._save_custom_entities()
                
                logger.info(f"Removed custom entity: {entity_name}")
                return True
            else:
                logger.warning(f"Custom entity not found: {entity_name}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to remove custom entity {entity_name}: {str(e)}")
            return False
    
    def update_custom_entity(self, entity_name: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing custom entity.
        
        Args:
            entity_name: Name of entity to update
            updates: Dictionary of fields to update
            
        Returns:
            True if updated successfully, False otherwise
        """
        try:
            if entity_name not in self.custom_entities:
                logger.warning(f"Custom entity not found: {entity_name}")
                return False
            
            entity = self.custom_entities[entity_name]
            
            # Update fields
            for field, value in updates.items():
                if hasattr(entity, field):
                    setattr(entity, field, value)
            
            # Recompile pattern if it changed
            if 'pattern' in updates:
                if not self.validate_custom_pattern(entity.pattern):
                    logger.error(f"Invalid regex pattern for entity {entity_name}")
                    return False
                
                self.compiled_patterns[entity.name] = re.compile(entity.pattern, re.IGNORECASE)
            
            # Save to configuration
            self._save_custom_entities()
            
            logger.info(f"Updated custom entity: {entity_name}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update custom entity {entity_name}: {str(e)}")
            return False
    
    def get_custom_entities(self) -> List[Dict[str, Any]]:
        """
        Get all custom entities.
        
        Returns:
            List of custom entity configurations
        """
        entities_list = []
        
        for entity in self.custom_entities.values():
            entities_list.append({
                'name': entity.name,
                'pattern': entity.pattern,
                'description': entity.description,
                'confidence': entity.confidence,
                'context': entity.context,
                'enabled': entity.enabled
            })
        
        return entities_list
    
    def get_entity_by_name(self, entity_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a custom entity by name.
        
        Args:
            entity_name: Name of entity to retrieve
            
        Returns:
            Entity configuration or None if not found
        """
        if entity_name in self.custom_entities:
            entity = self.custom_entities[entity_name]
            return {
                'name': entity.name,
                'pattern': entity.pattern,
                'description': entity.description,
                'confidence': entity.confidence,
                'context': entity.context,
                'enabled': entity.enabled
            }
        return None
    
    def _check_context(self, text: str, match: re.Match, context_keywords: List[str]) -> bool:
        """
        Check if entity match has relevant context keywords.
        
        Args:
            text: Full text
            match: Regex match object
            context_keywords: List of context keywords to check
            
        Returns:
            True if context is relevant, False otherwise
        """
        # Get text around the match
        start = max(0, match.start() - 50)
        end = min(len(text), match.end() + 50)
        context_text = text[start:end].lower()
        
        # Check if any context keyword is present
        for keyword in context_keywords:
            if keyword.lower() in context_text:
                return True
        
        return False
    
    def _save_custom_entities(self) -> None:
        """
        Save custom entities to configuration file.
        
        Raises:
            DocumentProcessingError: If saving fails
        """
        try:
            # Ensure directory exists
            Path(self.entities_config_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Prepare data for saving
            config_data = {
                'entities': []
            }
            
            for entity in self.custom_entities.values():
                config_data['entities'].append({
                    'name': entity.name,
                    'pattern': entity.pattern,
                    'description': entity.description,
                    'confidence': entity.confidence,
                    'context': entity.context,
                    'enabled': entity.enabled
                })
            
            # Save to file
            with open(self.entities_config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"Saved custom entities to {self.entities_config_path}")
            
        except Exception as e:
            logger.error(f"Failed to save custom entities: {str(e)}")
            raise DocumentProcessingError(f"Failed to save custom entities: {str(e)}")
    
    def reset_custom_entities(self) -> None:
        """
        Reset custom entities to default configuration.
        """
        try:
            self.custom_entities = {}
            self.compiled_patterns = {}
            
            # Remove config file if it exists
            if Path(self.entities_config_path).exists():
                Path(self.entities_config_path).unlink()
            
            logger.info("Reset custom entities to default")
            
        except Exception as e:
            logger.error(f"Failed to reset custom entities: {str(e)}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about custom entities.
        
        Returns:
            Dictionary with custom entity statistics
        """
        return {
            'total_entities': len(self.custom_entities),
            'enabled_entities': len([e for e in self.custom_entities.values() if e.enabled]),
            'disabled_entities': len([e for e in self.custom_entities.values() if not e.enabled]),
            'entity_names': list(self.custom_entities.keys())
        }