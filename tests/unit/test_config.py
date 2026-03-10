import pytest
from unittest.mock import patch, Mock
from app.utils.config import Config, ConfigError


class TestConfig:
    """Test cases for Config class"""

    @pytest.fixture
    def sample_env_vars(self):
        """Sample environment variables for testing"""
        return {
            'APP_ENV': 'test',
            'DEBUG': 'true',
            'LOG_LEVEL': 'DEBUG',
            'HOST': 'localhost',
            'PORT': '8000',
            'PRESIDIO_ANALYZER_URL': 'http://localhost:3000',
            'PRESIDIO_ANONYMIZER_URL': 'http://localhost:3001',
            'OPENAI_API_KEY': 'test-api-key',
            'OPENAI_MODEL': 'gpt-4',
            'OPENAI_MAX_TOKENS': '1000',
            'OPENAI_TEMPERATURE': '0.1',
            'PII_MIN_CONFIDENCE': '0.5',
            'PDF_MAX_SIZE_MB': '10',
            'PDF_MAX_PAGES': '50',
            'RATE_LIMIT_REQUESTS': '100',
            'RATE_LIMIT_WINDOW': '60',
            'REDIS_URL': 'redis://localhost:6379/0',
            'ENABLE_AUTH': 'false',
            'API_KEY': 'test-api-key',
            'ENABLE_AUDIT': 'true',
            'ENABLE_CORS': 'true',
            'CORS_ORIGINS': 'http://localhost:3000,http://localhost:8080'
        }

    @pytest.fixture
    def invalid_env_vars(self):
        """Invalid environment variables for testing"""
        return {
            'APP_ENV': 'invalid_env',
            'DEBUG': 'not_a_boolean',
            'LOG_LEVEL': 'INVALID_LEVEL',
            'HOST': '',
            'PORT': 'not_a_number',
            'PRESIDIO_ANALYZER_URL': 'invalid_url',
            'PRESIDIO_ANONYMIZER_URL': 'invalid_url',
            'OPENAI_API_KEY': '',
            'OPENAI_MODEL': 'invalid_model',
            'OPENAI_MAX_TOKENS': 'not_a_number',
            'OPENAI_TEMPERATURE': 'not_a_number',
            'PII_MIN_CONFIDENCE': 'not_a_number',
            'PDF_MAX_SIZE_MB': 'not_a_number',
            'PDF_MAX_PAGES': 'not_a_number',
            'RATE_LIMIT_REQUESTS': 'not_a_number',
            'RATE_LIMIT_WINDOW': 'not_a_number',
            'REDIS_URL': 'invalid_url',
            'ENABLE_AUTH': 'not_a_boolean',
            'API_KEY': '',
            'ENABLE_AUDIT': 'not_a_boolean',
            'ENABLE_CORS': 'not_a_boolean',
            'CORS_ORIGINS': ''
        }

    @patch.dict('os.environ', {
        'APP_ENV': 'test',
        'DEBUG': 'true',
        'LOG_LEVEL': 'DEBUG',
        'HOST': 'localhost',
        'PORT': '8000',
        'PRESIDIO_ANALYZER_URL': 'http://localhost:3000',
        'PRESIDIO_ANONYMIZER_URL': 'http://localhost:3001',
        'OPENAI_API_KEY': 'test-api-key',
        'OPENAI_MODEL': 'gpt-4',
        'OPENAI_MAX_TOKENS': '1000',
        'OPENAI_TEMPERATURE': '0.1',
        'PII_MIN_CONFIDENCE': '0.5',
        'PDF_MAX_SIZE_MB': '10',
        'PDF_MAX_PAGES': '50',
        'RATE_LIMIT_REQUESTS': '100',
        'RATE_LIMIT_WINDOW': '60',
        'REDIS_URL': 'redis://localhost:6379/0',
        'ENABLE_AUTH': 'false',
        'API_KEY': 'test-api-key',
        'ENABLE_AUDIT': 'true',
        'ENABLE_CORS': 'true',
        'CORS_ORIGINS': 'http://localhost:3000,http://localhost:8080'
    })
    def test_config_loading_from_env(self):
        """Test loading configuration from environment variables"""
        config = Config()
        
        # Test basic properties
        assert config.app_env == 'test'
        assert config.debug is True
        assert config.log_level == 'DEBUG'
        assert config.host == 'localhost'
        assert config.port == 8000
        
        # Test Presidio configuration
        assert config.presidio_analyzer_url == 'http://localhost:3000'
        assert config.presidio_anonymizer_url == 'http://localhost:3001'
        assert config.pii_min_confidence == 0.5
        
        # Test OpenAI configuration
        assert config.openai_api_key == 'test-api-key'
        assert config.openai_model == 'gpt-4'
        assert config.openai_max_tokens == 1000
        assert config.openai_temperature == 0.1
        
        # Test PDF configuration
        assert config.pdf_max_size_mb == 10
        assert config.pdf_max_pages == 50
        
        # Test rate limiting configuration
        assert config.rate_limit_requests == 100
        assert config.rate_limit_window == 60
        
        # Test Redis configuration
        assert config.redis_url == 'redis://localhost:6379/0'
        
        # Test security configuration
        assert config.enable_auth is False
        assert config.api_key == 'test-api-key'
        assert config.enable_audit is True
        assert config.enable_cors is True
        assert config.cors_origins == ['http://localhost:3000', 'http://localhost:8080']

    @patch.dict('os.environ', {}, clear=True)
    def test_config_loading_with_defaults(self):
        """Test loading configuration with default values"""
        config = Config()
        
        # Test default values
        assert config.app_env == 'development'
        assert config.debug is False
        assert config.log_level == 'INFO'
        assert config.host == '0.0.0.0'
        assert config.port == 8000
        
        # Test default Presidio configuration
        assert config.presidio_analyzer_url == 'http://localhost:3000'
        assert config.presidio_anonymizer_url == 'http://localhost:3001'
        assert config.pii_min_confidence == 0.5
        
        # Test default OpenAI configuration
        assert config.openai_api_key is None
        assert config.openai_model == 'gpt-4'
        assert config.openai_max_tokens == 1000
        assert config.openai_temperature == 0.1
        
        # Test default PDF configuration
        assert config.pdf_max_size_mb == 10
        assert config.pdf_max_pages == 50
        
        # Test default rate limiting configuration
        assert config.rate_limit_requests == 100
        assert config.rate_limit_window == 60
        
        # Test default Redis configuration
        assert config.redis_url == 'redis://localhost:6379/0'
        
        # Test default security configuration
        assert config.enable_auth is False
        assert config.api_key is None
        assert config.enable_audit is True
        assert config.enable_cors is True
        assert config.cors_origins == ['*']

    @patch.dict('os.environ', {'DEBUG': 'true'})
    def test_debug_property(self):
        """Test debug property conversion"""
        config = Config()
        assert config.debug is True

    @patch.dict('os.environ', {'DEBUG': 'false'})
    def test_debug_property_false(self):
        """Test debug property conversion for false"""
        config = Config()
        assert config.debug is False

    @patch.dict('os.environ', {'DEBUG': '1'})
    def test_debug_property_numeric_true(self):
        """Test debug property conversion for numeric true"""
        config = Config()
        assert config.debug is True

    @patch.dict('os.environ', {'DEBUG': '0'})
    def test_debug_property_numeric_false(self):
        """Test debug property conversion for numeric false"""
        config = Config()
        assert config.debug is False

    @patch.dict('os.environ', {'ENABLE_AUTH': 'true'})
    def test_enable_auth_property(self):
        """Test enable_auth property conversion"""
        config = Config()
        assert config.enable_auth is True

    @patch.dict('os.environ', {'ENABLE_AUDIT': 'false'})
    def test_enable_audit_property(self):
        """Test enable_audit property conversion"""
        config = Config()
        assert config.enable_audit is False

    @patch.dict('os.environ', {'ENABLE_CORS': 'true'})
    def test_enable_cors_property(self):
        """Test enable_cors property conversion"""
        config = Config()
        assert config.enable_cors is True

    @patch.dict('os.environ', {'PORT': '8080'})
    def test_port_property(self):
        """Test port property conversion"""
        config = Config()
        assert config.port == 8080

    @patch.dict('os.environ', {'PDF_MAX_SIZE_MB': '20'})
    def test_pdf_max_size_mb_property(self):
        """Test PDF max size property conversion"""
        config = Config()
        assert config.pdf_max_size_mb == 20

    @patch.dict('os.environ', {'PDF_MAX_PAGES': '100'})
    def test_pdf_max_pages_property(self):
        """Test PDF max pages property conversion"""
        config = Config()
        assert config.pdf_max_pages == 100

    @patch.dict('os.environ', {'OPENAI_MAX_TOKENS': '2000'})
    def test_openai_max_tokens_property(self):
        """Test OpenAI max tokens property conversion"""
        config = Config()
        assert config.openai_max_tokens == 2000

    @patch.dict('os.environ', {'OPENAI_TEMPERATURE': '0.5'})
    def test_openai_temperature_property(self):
        """Test OpenAI temperature property conversion"""
        config = Config()
        assert config.openai_temperature == 0.5

    @patch.dict('os.environ', {'PII_MIN_CONFIDENCE': '0.8'})
    def test_pii_min_confidence_property(self):
        """Test PII minimum confidence property conversion"""
        config = Config()
        assert config.pii_min_confidence == 0.8

    @patch.dict('os.environ', {'RATE_LIMIT_REQUESTS': '200'})
    def test_rate_limit_requests_property(self):
        """Test rate limit requests property conversion"""
        config = Config()
        assert config.rate_limit_requests == 200

    @patch.dict('os.environ', {'RATE_LIMIT_WINDOW': '120'})
    def test_rate_limit_window_property(self):
        """Test rate limit window property conversion"""
        config = Config()
        assert config.rate_limit_window == 120

    @patch.dict('os.environ', {'CORS_ORIGINS': 'http://localhost:3000,http://localhost:8080'})
    def test_cors_origins_property(self):
        """Test CORS origins property conversion"""
        config = Config()
        assert config.cors_origins == ['http://localhost:3000', 'http://localhost:8080']

    @patch.dict('os.environ', {'CORS_ORIGINS': 'http://localhost:3000'})
    def test_cors_origins_single_origin(self):
        """Test CORS origins property with single origin"""
        config = Config()
        assert config.cors_origins == ['http://localhost:3000']

    @patch.dict('os.environ', {'CORS_ORIGINS': ''})
    def test_cors_origins_empty(self):
        """Test CORS origins property with empty string"""
        config = Config()
        assert config.cors_origins == ['*']

    @patch.dict('os.environ', {'CORS_ORIGINS': '*'})
    def test_cors_origins_wildcard(self):
        """Test CORS origins property with wildcard"""
        config = Config()
        assert config.cors_origins == ['*']

    def test_invalid_debug_value(self):
        """Test invalid debug value raises ConfigError"""
        with patch.dict('os.environ', {'DEBUG': 'invalid'}):
            with pytest.raises(ConfigError, match="Invalid value for DEBUG"):
                Config()

    def test_invalid_port_value(self):
        """Test invalid port value raises ConfigError"""
        with patch.dict('os.environ', {'PORT': 'not_a_number'}):
            with pytest.raises(ConfigError, match="Invalid value for PORT"):
                Config()

    def test_invalid_pdf_max_size_mb_value(self):
        """Test invalid PDF max size value raises ConfigError"""
        with patch.dict('os.environ', {'PDF_MAX_SIZE_MB': 'not_a_number'}):
            with pytest.raises(ConfigError, match="Invalid value for PDF_MAX_SIZE_MB"):
                Config()

    def test_invalid_pdf_max_pages_value(self):
        """Test invalid PDF max pages value raises ConfigError"""
        with patch.dict('os.environ', {'PDF_MAX_PAGES': 'not_a_number'}):
            with pytest.raises(ConfigError, match="Invalid value for PDF_MAX_PAGES"):
                Config()

    def test_invalid_openai_max_tokens_value(self):
        """Test invalid OpenAI max tokens value raises ConfigError"""
        with patch.dict('os.environ', {'OPENAI_MAX_TOKENS': 'not_a_number'}):
            with pytest.raises(ConfigError, match="Invalid value for OPENAI_MAX_TOKENS"):
                Config()

    def test_invalid_openai_temperature_value(self):
        """Test invalid OpenAI temperature value raises ConfigError"""
        with patch.dict('os.environ', {'OPENAI_TEMPERATURE': 'not_a_number'}):
            with pytest.raises(ConfigError, match="Invalid value for OPENAI_TEMPERATURE"):
                Config()

    def test_invalid_pii_min_confidence_value(self):
        """Test invalid PII minimum confidence value raises ConfigError"""
        with patch.dict('os.environ', {'PII_MIN_CONFIDENCE': 'not_a_number'}):
            with pytest.raises(ConfigError, match="Invalid value for PII_MIN_CONFIDENCE"):
                Config()

    def test_invalid_rate_limit_requests_value(self):
        """Test invalid rate limit requests value raises ConfigError"""
        with patch.dict('os.environ', {'RATE_LIMIT_REQUESTS': 'not_a_number'}):
            with pytest.raises(ConfigError, match="Invalid value for RATE_LIMIT_REQUESTS"):
                Config()

    def test_invalid_rate_limit_window_value(self):
        """Test invalid rate limit window value raises ConfigError"""
        with patch.dict('os.environ', {'RATE_LIMIT_WINDOW': 'not_a_number'}):
            with pytest.raises(ConfigError, match="Invalid value for RATE_LIMIT_WINDOW"):
                Config()

    def test_invalid_log_level_value(self):
        """Test invalid log level value raises ConfigError"""
        with patch.dict('os.environ', {'LOG_LEVEL': 'INVALID_LEVEL'}):
            with pytest.raises(ConfigError, match="Invalid value for LOG_LEVEL"):
                Config()

    def test_invalid_app_env_value(self):
        """Test invalid app environment value raises ConfigError"""
        with patch.dict('os.environ', {'APP_ENV': 'invalid_env'}):
            with pytest.raises(ConfigError, match="Invalid value for APP_ENV"):
                Config()

    def test_missing_required_openai_api_key(self):
        """Test missing required OpenAI API key raises ConfigError"""
        with patch.dict('os.environ', {'OPENAI_API_KEY': ''}):
            with pytest.raises(ConfigError, match="OPENAI_API_KEY is required"):
                Config()

    def test_missing_required_api_key_when_auth_enabled(self):
        """Test missing required API key when auth is enabled raises ConfigError"""
        with patch.dict('os.environ', {'ENABLE_AUTH': 'true', 'API_KEY': ''}):
            with pytest.raises(ConfigError, match="API_KEY is required when ENABLE_AUTH is true"):
                Config()

    def test_invalid_redis_url(self):
        """Test invalid Redis URL raises ConfigError"""
        with patch.dict('os.environ', {'REDIS_URL': 'invalid_url'}):
            with pytest.raises(ConfigError, match="Invalid REDIS_URL"):
                Config()

    def test_invalid_presidio_analyzer_url(self):
        """Test invalid Presidio analyzer URL raises ConfigError"""
        with patch.dict('os.environ', {'PRESIDIO_ANALYZER_URL': 'invalid_url'}):
            with pytest.raises(ConfigError, match="Invalid PRESIDIO_ANALYZER_URL"):
                Config()

    def test_invalid_presidio_anonymizer_url(self):
        """Test invalid Presidio anonymizer URL raises ConfigError"""
        with patch.dict('os.environ', {'PRESIDIO_ANONYMIZER_URL': 'invalid_url'}):
            with pytest.raises(ConfigError, match="Invalid PRESIDIO_ANONYMIZER_URL"):
                Config()

    def test_invalid_openai_model(self):
        """Test invalid OpenAI model raises ConfigError"""
        with patch.dict('os.environ', {'OPENAI_MODEL': 'invalid_model'}):
            with pytest.raises(ConfigError, match="Invalid OPENAI_MODEL"):
                Config()

    def test_get_property_existing(self):
        """Test getting existing configuration property"""
        config = Config()
        value = config.get('DEBUG')
        assert value is False  # Default value

    def test_get_property_nonexistent(self):
        """Test getting non-existent configuration property"""
        config = Config()
        value = config.get('NON_EXISTENT_PROPERTY')
        assert value is None

    def test_get_property_with_default(self):
        """Test getting configuration property with default value"""
        config = Config()
        value = config.get('NON_EXISTENT_PROPERTY', 'default_value')
        assert value == 'default_value'

    def test_get_property_with_env_override(self):
        """Test getting configuration property with environment override"""
        with patch.dict('os.environ', {'DEBUG': 'true'}):
            config = Config()
            value = config.get('DEBUG')
            assert value is True

    def test_is_development_environment(self):
        """Test is_development method"""
        with patch.dict('os.environ', {'APP_ENV': 'development'}):
            config = Config()
            assert config.is_development() is True

    def test_is_production_environment(self):
        """Test is_production method"""
        with patch.dict('os.environ', {'APP_ENV': 'production'}):
            config = Config()
            assert config.is_production() is True

    def test_is_test_environment(self):
        """Test is_test method"""
        with patch.dict('os.environ', {'APP_ENV': 'test'}):
            config = Config()
            assert config.is_test() is True

    def test_is_development_false(self):
        """Test is_development method returns False for non-development environment"""
        with patch.dict('os.environ', {'APP_ENV': 'production'}):
            config = Config()
            assert config.is_development() is False

    def test_is_production_false(self):
        """Test is_production method returns False for non-production environment"""
        with patch.dict('os.environ', {'APP_ENV': 'development'}):
            config = Config()
            assert config.is_production() is False

    def test_is_test_false(self):
        """Test is_test method returns False for non-test environment"""
        with patch.dict('os.environ', {'APP_ENV': 'production'}):
            config = Config()
            assert config.is_test() is False

    def test_config_validation_success(self):
        """Test successful configuration validation"""
        with patch.dict('os.environ', {
            'APP_ENV': 'test',
            'DEBUG': 'true',
            'LOG_LEVEL': 'DEBUG',
            'HOST': 'localhost',
            'PORT': '8000',
            'PRESIDIO_ANALYZER_URL': 'http://localhost:3000',
            'PRESIDIO_ANONYMIZER_URL': 'http://localhost:3001',
            'OPENAI_API_KEY': 'test-api-key',
            'OPENAI_MODEL': 'gpt-4',
            'OPENAI_MAX_TOKENS': '1000',
            'OPENAI_TEMPERATURE': '0.1',
            'PII_MIN_CONFIDENCE': '0.5',
            'PDF_MAX_SIZE_MB': '10',
            'PDF_MAX_PAGES': '50',
            'RATE_LIMIT_REQUESTS': '100',
            'RATE_LIMIT_WINDOW': '60',
            'REDIS_URL': 'redis://localhost:6379/0',
            'ENABLE_AUTH': 'false',
            'API_KEY': 'test-api-key',
            'ENABLE_AUDIT': 'true',
            'ENABLE_CORS': 'true',
            'CORS_ORIGINS': 'http://localhost:3000,http://localhost:8080'
        }):
            config = Config()
            # Should not raise any exceptions
            assert config is not None

    def test_config_validation_failure(self):
        """Test configuration validation failure"""
        with patch.dict('os.environ', {
            'DEBUG': 'invalid',
            'PORT': 'not_a_number',
            'OPENAI_API_KEY': ''
        }):
            with pytest.raises(ConfigError):
                Config()

    def test_config_repr(self):
        """Test configuration string representation"""
        config = Config()
        repr_str = repr(config)
        assert 'Config' in repr_str
        assert 'app_env' in repr_str
        assert 'debug' in repr_str
        assert 'log_level' in repr_str

    def test_config_str(self):
        """Test configuration string representation"""
        config = Config()
        str_str = str(config)
        assert 'Config' in str_str
        assert 'app_env' in str_str
        assert 'debug' in str_str
        assert 'log_level' in str_str