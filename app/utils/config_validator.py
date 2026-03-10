# app/utils/config_validator.py
from app.utils.config import get_settings
import logging
import os
import sys

logger = logging.getLogger(__name__)

class ConfigValidator:
    """Validate application configuration on startup"""
    
    @staticmethod
    def validate_environment_variables():
        """Validate required environment variables are set"""
        settings = get_settings()
        
        # Check for required environment variables
        required_vars = []
        
        if settings.enable_auth and not settings.api_key:
            required_vars.append("API_KEY")
        
        if settings.rate_limit_enabled and not settings.rate_limit_redis_url:
            required_vars.append("RATE_LIMIT_REDIS_URL")
        
        if settings.audit_log_enabled and not settings.audit_log_file:
            required_vars.append("AUDIT_LOG_FILE")
        
        if required_vars:
            error_msg = f"Missing required environment variables: {', '.join(required_vars)}"
            logger.error(error_msg)
            if settings.environment == "production":
                raise ValueError(error_msg)
            else:
                logger.warning(f"Development mode: {error_msg}")
    
    @staticmethod
    def validate_file_paths():
        """Validate file paths and create directories if needed"""
        settings = get_settings()
        
        # Validate audit log file path
        if settings.audit_log_enabled and settings.audit_log_file:
            log_dir = os.path.dirname(settings.audit_log_file)
            if log_dir and not os.path.exists(log_dir):
                try:
                    os.makedirs(log_dir, exist_ok=True)
                    logger.info(f"Created audit log directory: {log_dir}")
                except Exception as e:
                    logger.error(f"Failed to create audit log directory {log_dir}: {e}")
                    if settings.environment == "production":
                        raise
    
    @staticmethod
    def validate_security_settings():
        """Validate security-related settings"""
        settings = get_settings()
        
        # Warn if auth is disabled in production
        if settings.environment == "production" and not settings.enable_auth:
            logger.warning("Authentication is disabled in production environment - this is not recommended")
        
        # Warn if CORS allows all origins in production
        if settings.environment == "production" and settings.allowed_origins == ["*"]:
            logger.warning("CORS allows all origins in production environment - this is not recommended")
        
        # Validate rate limiting settings
        if settings.rate_limit_enabled:
            if settings.rate_limit_requests_per_minute <= 0:
                logger.error("Rate limit requests per minute must be greater than 0")
                if settings.environment == "production":
                    raise ValueError("Invalid rate limiting configuration")
    
    @staticmethod
    def validate():
        """Run all configuration validations"""
        logger.info("Validating application configuration...")
        
        try:
            ConfigValidator.validate_environment_variables()
            ConfigValidator.validate_file_paths()
            ConfigValidator.validate_security_settings()
            
            logger.info("Configuration validation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            return False

def validate_config_on_startup():
    """Validate configuration when the application starts"""
    if not ConfigValidator.validate():
        if get_settings().environment == "production":
            logger.critical("Configuration validation failed in production - shutting down")
            sys.exit(1)
        else:
            logger.warning("Configuration validation failed in development - continuing with warnings")