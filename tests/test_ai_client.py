"""
Unit tests for the AI client module.

This module tests the OpenAI API client with LangChain integration,
including configuration management, text generation, embeddings, and chat functionality.
"""

import pytest
import os
import time
from unittest.mock import Mock, patch, MagicMock
from typing import List, Dict, Any

# Import the modules to test
from backend.core.config import ConfigManager, Settings, get_config, validate_environment
from backend.core.ai_client import (
    AIClient, AIResponse, EmbeddingResponse, AICallbackHandler,
    get_ai_client, initialize_ai_client, reset_ai_client, validate_ai_setup
)


class TestConfigManager:
    """Test configuration management functionality."""
    
    def test_config_manager_singleton(self):
        """Test that ConfigManager follows singleton pattern."""
        config1 = ConfigManager()
        config2 = ConfigManager()
        assert config1 is config2
    
    def test_get_settings(self):
        """Test getting settings from config manager."""
        config = ConfigManager()
        settings = config.get_settings()
        assert isinstance(settings, Settings)
    
    def test_get_openai_config(self):
        """Test getting OpenAI configuration."""
        config = ConfigManager()
        openai_config = config.get_openai_config()
        
        assert 'api_key' in openai_config
        assert 'model' in openai_config
        assert 'temperature' in openai_config
        assert 'max_tokens' in openai_config
        assert 'timeout' in openai_config
    
    def test_get_database_config(self):
        """Test getting database configuration."""
        config = ConfigManager()
        db_config = config.get_database_config()
        
        assert 'database_path' in db_config
        assert 'chroma_path' in db_config
    
    def test_get_langchain_config(self):
        """Test getting LangChain configuration."""
        config = ConfigManager()
        langchain_config = config.get_langchain_config()
        
        assert 'verbose' in langchain_config
        assert 'tracing' in langchain_config
    
    def test_is_debug_mode(self):
        """Test debug mode detection."""
        config = ConfigManager()
        debug_mode = config.is_debug_mode()
        assert isinstance(debug_mode, bool)
    
    def test_get_log_level(self):
        """Test log level retrieval."""
        config = ConfigManager()
        log_level = config.get_log_level()
        assert log_level in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']


class TestSettings:
    """Test Settings class validation and configuration."""
    
    def test_settings_validation_temperature(self):
        """Test temperature validation."""
        # Valid temperature
        settings = Settings(openai_api_key="test-key", openai_temperature=0.5)
        assert settings.openai_temperature == 0.5
        
        # Invalid temperature (too high)
        with pytest.raises(ValueError, match="Temperature must be between 0 and 2"):
            Settings(openai_api_key="test-key", openai_temperature=3.0)
        
        # Invalid temperature (negative)
        with pytest.raises(ValueError, match="Temperature must be between 0 and 2"):
            Settings(openai_api_key="test-key", openai_temperature=-0.1)
    
    def test_settings_validation_max_tokens(self):
        """Test max tokens validation."""
        # Valid max tokens
        settings = Settings(openai_api_key="test-key", openai_max_tokens=1000)
        assert settings.openai_max_tokens == 1000
        
        # Invalid max tokens (zero)
        with pytest.raises(ValueError, match="Max tokens must be positive"):
            Settings(openai_api_key="test-key", openai_max_tokens=0)
        
        # Invalid max tokens (negative)
        with pytest.raises(ValueError, match="Max tokens must be positive"):
            Settings(openai_api_key="test-key", openai_max_tokens=-100)
    
    def test_settings_validation_log_level(self):
        """Test log level validation."""
        # Valid log levels
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        for level in valid_levels:
            settings = Settings(openai_api_key="test-key", log_level=level)
            assert settings.log_level == level
        
        # Invalid log level
        with pytest.raises(ValueError, match="Log level must be one of"):
            Settings(openai_api_key="test-key", log_level="INVALID")
    
    def test_settings_validation_api_port(self):
        """Test API port validation."""
        # Valid ports
        valid_ports = [1, 8000, 65535]
        for port in valid_ports:
            settings = Settings(openai_api_key="test-key", api_port=port)
            assert settings.api_port == port
        
        # Invalid ports
        invalid_ports = [0, 65536, -1]
        for port in invalid_ports:
            with pytest.raises(ValueError, match="API port must be between 1 and 65535"):
                Settings(openai_api_key="test-key", api_port=port)


class TestAICallbackHandler:
    """Test AI callback handler functionality."""
    
    def test_callback_handler_initialization(self):
        """Test callback handler initialization."""
        handler = AICallbackHandler()
        assert handler.tokens_used == 0
        assert handler.start_time is None
        assert handler.end_time is None
    
    def test_callback_handler_llm_start(self):
        """Test LLM start callback."""
        handler = AICallbackHandler()
        handler.on_llm_start({}, ["test prompt"])
        
        assert handler.start_time is not None
        assert isinstance(handler.start_time, float)
    
    def test_callback_handler_llm_end(self):
        """Test LLM end callback."""
        handler = AICallbackHandler()
        handler.start_time = time.time()
        
        # Mock response with token usage
        mock_response = Mock()
        mock_response.llm_output = {'token_usage': {'total_tokens': 150}}
        
        handler.on_llm_end(mock_response)
        
        assert handler.end_time is not None
        assert handler.tokens_used == 150
    
    def test_callback_handler_llm_error(self):
        """Test LLM error callback."""
        handler = AICallbackHandler()
        
        # Should not raise exception
        handler.on_llm_error(Exception("Test error"))


class TestAIClient:
    """Test AI client functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Create a mock configuration for testing."""
        mock_config = Mock()
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-api-key"
        mock_settings.openai_model = "gpt-3.5-turbo"
        mock_settings.openai_temperature = 0.7
        mock_settings.openai_max_tokens = 2000
        mock_settings.openai_timeout = 30
        mock_settings.langchain_verbose = False
        mock_settings.langchain_tracing = False
        
        mock_config.get_settings.return_value = mock_settings
        mock_config.get_openai_config.return_value = {
            'api_key': 'test-api-key',
            'model': 'gpt-3.5-turbo',
            'temperature': 0.7,
            'max_tokens': 2000,
            'timeout': 30
        }
        mock_config.get_langchain_config.return_value = {
            'verbose': False,
            'tracing': False
        }
        
        return mock_config
    
    @patch('backend.core.ai_client.openai')
    @patch('backend.core.ai_client.OpenAI')
    @patch('backend.core.ai_client.ChatOpenAI')
    @patch('backend.core.ai_client.OpenAIEmbeddings')
    def test_ai_client_initialization(self, mock_embeddings, mock_chat, mock_llm, mock_openai, mock_config):
        """Test AI client initialization."""
        client = AIClient(mock_config)
        
        # Verify OpenAI client setup
        mock_openai.api_key = "test-api-key"
        
        # Verify LangChain components were initialized
        mock_llm.assert_called_once()
        mock_chat.assert_called_once()
        mock_embeddings.assert_called_once()
        
        # Verify client attributes
        assert client.config is mock_config
        assert client.llm is not None
        assert client.chat_model is not None
        assert client.embeddings is not None
        assert client.memory is not None
        assert client.conversation_chain is not None
    
    @patch('backend.core.ai_client.openai')
    @patch('backend.core.ai_client.OpenAI')
    @patch('backend.core.ai_client.ChatOpenAI')
    @patch('backend.core.ai_client.OpenAIEmbeddings')
    def test_generate_text_success(self, mock_embeddings, mock_chat, mock_llm, mock_openai, mock_config):
        """Test successful text generation."""
        # Mock chat model response
        mock_response = Mock()
        mock_response.content = "Generated text response"
        mock_response.usage = {'total_tokens': 100}
        mock_response.finish_reason = 'stop'
        
        mock_chat_instance = Mock()
        mock_chat_instance.return_value = mock_response
        mock_chat.return_value = mock_chat_instance
        
        client = AIClient(mock_config)
        response = client.generate_text("Test prompt")
        
        assert isinstance(response, AIResponse)
        assert response.content == "Generated text response"
        assert response.model == "gpt-3.5-turbo"
        assert response.usage == {'total_tokens': 100}
        assert response.finish_reason == 'stop'
        assert response.error is None
        assert response.response_time is not None
    
    @patch('backend.core.ai_client.openai')
    @patch('backend.core.ai_client.OpenAI')
    @patch('backend.core.ai_client.ChatOpenAI')
    @patch('backend.core.ai_client.OpenAIEmbeddings')
    def test_generate_text_with_system_message(self, mock_embeddings, mock_chat, mock_llm, mock_openai, mock_config):
        """Test text generation with system message."""
        # Mock chat model response
        mock_response = Mock()
        mock_response.content = "Generated text response"
        
        mock_chat_instance = Mock()
        mock_chat_instance.return_value = mock_response
        mock_chat.return_value = mock_chat_instance
        
        client = AIClient(mock_config)
        response = client.generate_text("Test prompt", system_message="You are a helpful assistant")
        
        assert isinstance(response, AIResponse)
        assert response.content == "Generated text response"
        assert response.error is None
    
    @patch('backend.core.ai_client.openai')
    @patch('backend.core.ai_client.OpenAI')
    @patch('backend.core.ai_client.ChatOpenAI')
    @patch('backend.core.ai_client.OpenAIEmbeddings')
    def test_generate_text_error(self, mock_embeddings, mock_chat, mock_llm, mock_openai, mock_config):
        """Test text generation with error."""
        # Mock chat model to raise exception
        mock_chat_instance = Mock()
        mock_chat_instance.side_effect = Exception("API Error")
        mock_chat.return_value = mock_chat_instance
        
        client = AIClient(mock_config)
        response = client.generate_text("Test prompt")
        
        assert isinstance(response, AIResponse)
        assert response.content == ""
        assert response.error == "API Error"
        assert response.response_time is not None
    
    @patch('backend.core.ai_client.openai')
    @patch('backend.core.ai_client.OpenAI')
    @patch('backend.core.ai_client.ChatOpenAI')
    @patch('backend.core.ai_client.OpenAIEmbeddings')
    def test_generate_embeddings_success(self, mock_embeddings, mock_chat, mock_llm, mock_openai, mock_config):
        """Test successful embedding generation."""
        # Mock embeddings response
        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_documents.return_value = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]
        mock_embeddings.return_value = mock_embeddings_instance
        
        client = AIClient(mock_config)
        response = client.generate_embeddings(["text1", "text2"])
        
        assert isinstance(response, EmbeddingResponse)
        assert len(response.embeddings) == 2
        assert response.embeddings[0] == [0.1, 0.2, 0.3]
        assert response.embeddings[1] == [0.4, 0.5, 0.6]
        assert response.model == "text-embedding-ada-002"
        assert response.error is None
        assert response.response_time is not None
    
    @patch('backend.core.ai_client.openai')
    @patch('backend.core.ai_client.OpenAI')
    @patch('backend.core.ai_client.ChatOpenAI')
    @patch('backend.core.ai_client.OpenAIEmbeddings')
    def test_generate_embeddings_single_text(self, mock_embeddings, mock_chat, mock_llm, mock_openai, mock_config):
        """Test embedding generation with single text."""
        # Mock embeddings response
        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_documents.return_value = [[0.1, 0.2, 0.3]]
        mock_embeddings.return_value = mock_embeddings_instance
        
        client = AIClient(mock_config)
        response = client.generate_embeddings("single text")
        
        assert isinstance(response, EmbeddingResponse)
        assert len(response.embeddings) == 1
        assert response.embeddings[0] == [0.1, 0.2, 0.3]
    
    @patch('backend.core.ai_client.openai')
    @patch('backend.core.ai_client.OpenAI')
    @patch('backend.core.ai_client.ChatOpenAI')
    @patch('backend.core.ai_client.OpenAIEmbeddings')
    def test_generate_embeddings_error(self, mock_embeddings, mock_chat, mock_llm, mock_openai, mock_config):
        """Test embedding generation with error."""
        # Mock embeddings to raise exception
        mock_embeddings_instance = Mock()
        mock_embeddings_instance.embed_documents.side_effect = Exception("Embedding Error")
        mock_embeddings.return_value = mock_embeddings_instance
        
        client = AIClient(mock_config)
        response = client.generate_embeddings(["text1"])
        
        assert isinstance(response, EmbeddingResponse)
        assert response.embeddings == []
        assert response.error == "Embedding Error"
        assert response.response_time is not None
    
    @patch('backend.core.ai_client.openai')
    @patch('backend.core.ai_client.OpenAI')
    @patch('backend.core.ai_client.ChatOpenAI')
    @patch('backend.core.ai_client.OpenAIEmbeddings')
    def test_chat_success(self, mock_embeddings, mock_chat, mock_llm, mock_openai, mock_config):
        """Test successful chat functionality."""
        # Mock conversation chain response
        mock_chain = Mock()
        mock_chain.predict.return_value = "Chat response"
        
        client = AIClient(mock_config)
        client.conversation_chain = mock_chain
        
        response = client.chat("Hello, how are you?")
        
        assert isinstance(response, AIResponse)
        assert response.content == "Chat response"
        assert response.model == "gpt-3.5-turbo"
        assert response.error is None
        assert response.response_time is not None
    
    @patch('backend.core.ai_client.openai')
    @patch('backend.core.ai_client.OpenAI')
    @patch('backend.core.ai_client.ChatOpenAI')
    @patch('backend.core.ai_client.OpenAIEmbeddings')
    def test_chat_with_system_message(self, mock_embeddings, mock_chat, mock_llm, mock_openai, mock_config):
        """Test chat with system message."""
        # Mock conversation chain response
        mock_chain = Mock()
        mock_chain.predict.return_value = "Chat response"
        
        client = AIClient(mock_config)
        client.conversation_chain = mock_chain
        
        response = client.chat("Hello", system_message="You are a helpful assistant")
        
        assert isinstance(response, AIResponse)
        assert response.content == "Chat response"
        assert response.error is None
    
    @patch('backend.core.ai_client.openai')
    @patch('backend.core.ai_client.OpenAI')
    @patch('backend.core.ai_client.ChatOpenAI')
    @patch('backend.core.ai_client.OpenAIEmbeddings')
    def test_chat_error(self, mock_embeddings, mock_chat, mock_llm, mock_openai, mock_config):
        """Test chat with error."""
        # Mock conversation chain to raise exception
        mock_chain = Mock()
        mock_chain.predict.side_effect = Exception("Chat Error")
        
        client = AIClient(mock_config)
        client.conversation_chain = mock_chain
        
        response = client.chat("Hello")
        
        assert isinstance(response, AIResponse)
        assert response.content == ""
        assert response.error == "Chat Error"
        assert response.response_time is not None
    
    @patch('backend.core.ai_client.openai')
    @patch('backend.core.ai_client.OpenAI')
    @patch('backend.core.ai_client.ChatOpenAI')
    @patch('backend.core.ai_client.OpenAIEmbeddings')
    def test_create_prompt_template(self, mock_embeddings, mock_chat, mock_llm, mock_openai, mock_config):
        """Test prompt template creation."""
        client = AIClient(mock_config)
        
        template = client.create_prompt_template(
            "Hello {name}, you are {role}",
            ["name", "role"]
        )
        
        assert template is not None
        assert template.input_variables == ["name", "role"]
        assert template.template == "Hello {name}, you are {role}"
    
    @patch('backend.core.ai_client.openai')
    @patch('backend.core.ai_client.OpenAI')
    @patch('backend.core.ai_client.ChatOpenAI')
    @patch('backend.core.ai_client.OpenAIEmbeddings')
    def test_create_chain(self, mock_embeddings, mock_chat, mock_llm, mock_openai, mock_config):
        """Test chain creation."""
        client = AIClient(mock_config)
        
        template = client.create_prompt_template("Test {input}", ["input"])
        chain = client.create_chain(template)
        
        assert chain is not None
        assert chain.llm is client.llm
        assert chain.prompt is template
    
    @patch('backend.core.ai_client.openai')
    @patch('backend.core.ai_client.OpenAI')
    @patch('backend.core.ai_client.ChatOpenAI')
    @patch('backend.core.ai_client.OpenAIEmbeddings')
    def test_clear_memory(self, mock_embeddings, mock_chat, mock_llm, mock_openai, mock_config):
        """Test memory clearing."""
        client = AIClient(mock_config)
        
        # Add some messages to memory
        client.memory.chat_memory.add_user_message("Hello")
        client.memory.chat_memory.add_ai_message("Hi there")
        
        # Clear memory
        client.clear_memory()
        
        # Verify memory is cleared
        memory_vars = client.memory.load_memory_variables({})
        assert len(memory_vars.get('chat_history', [])) == 0
    
    @patch('backend.core.ai_client.openai')
    @patch('backend.core.ai_client.OpenAI')
    @patch('backend.core.ai_client.ChatOpenAI')
    @patch('backend.core.ai_client.OpenAIEmbeddings')
    def test_get_memory_summary(self, mock_embeddings, mock_chat, mock_llm, mock_openai, mock_config):
        """Test memory summary retrieval."""
        client = AIClient(mock_config)
        
        # Add some messages to memory
        client.memory.chat_memory.add_user_message("Hello")
        client.memory.chat_memory.add_ai_message("Hi there")
        client.memory.chat_memory.add_system_message("System message")
        
        summary = client.get_memory_summary()
        
        assert summary['total_messages'] == 3
        assert summary['user_messages'] == 1
        assert summary['ai_messages'] == 1
        assert summary['system_messages'] == 1
        assert len(summary['recent_messages']) == 3
    
    @patch('backend.core.ai_client.openai')
    @patch('backend.core.ai_client.OpenAI')
    @patch('backend.core.ai_client.ChatOpenAI')
    @patch('backend.core.ai_client.OpenAIEmbeddings')
    def test_test_connection_success(self, mock_embeddings, mock_chat, mock_llm, mock_openai, mock_config):
        """Test successful connection test."""
        # Mock successful text generation
        mock_response = Mock()
        mock_response.content = "Test response"
        
        mock_chat_instance = Mock()
        mock_chat_instance.return_value = mock_response
        mock_chat.return_value = mock_chat_instance
        
        client = AIClient(mock_config)
        result = client.test_connection()
        
        assert result is True
    
    @patch('backend.core.ai_client.openai')
    @patch('backend.core.ai_client.OpenAI')
    @patch('backend.core.ai_client.ChatOpenAI')
    @patch('backend.core.ai_client.OpenAIEmbeddings')
    def test_test_connection_failure(self, mock_embeddings, mock_chat, mock_llm, mock_openai, mock_config):
        """Test failed connection test."""
        # Mock failed text generation
        mock_chat_instance = Mock()
        mock_chat_instance.side_effect = Exception("Connection failed")
        mock_chat.return_value = mock_chat_instance
        
        client = AIClient(mock_config)
        result = client.test_connection()
        
        assert result is False
    
    @patch('backend.core.ai_client.openai')
    @patch('backend.core.ai_client.OpenAI')
    @patch('backend.core.ai_client.ChatOpenAI')
    @patch('backend.core.ai_client.OpenAIEmbeddings')
    def test_get_usage_stats(self, mock_embeddings, mock_chat, mock_llm, mock_openai, mock_config):
        """Test usage statistics retrieval."""
        client = AIClient(mock_config)
        
        # Set some mock values
        client.callback_handler.tokens_used = 150
        client.callback_handler.start_time = 1000.0
        client.callback_handler.end_time = 1005.0
        
        stats = client.get_usage_stats()
        
        assert stats['tokens_used'] == 150
        assert stats['start_time'] == 1000.0
        assert stats['end_time'] == 1005.0
        assert stats['response_time'] == 5.0


class TestGlobalFunctions:
    """Test global AI client functions."""
    
    def test_get_ai_client_singleton(self):
        """Test that get_ai_client returns singleton instance."""
        reset_ai_client()  # Reset to ensure clean state
        
        client1 = get_ai_client()
        client2 = get_ai_client()
        
        assert client1 is client2
    
    def test_initialize_ai_client(self):
        """Test AI client initialization."""
        reset_ai_client()  # Reset to ensure clean state
        
        mock_config = Mock()
        client = initialize_ai_client(mock_config)
        
        assert client is not None
        assert client.config is mock_config
    
    def test_reset_ai_client(self):
        """Test AI client reset."""
        # Initialize client
        client1 = get_ai_client()
        
        # Reset client
        reset_ai_client()
        
        # Get new client
        client2 = get_ai_client()
        
        assert client1 is not client2
    
    @patch('backend.core.ai_client.validate_environment')
    @patch('backend.core.ai_client.get_ai_client')
    def test_validate_ai_setup_success(self, mock_get_client, mock_validate_env):
        """Test successful AI setup validation."""
        mock_validate_env.return_value = True
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_get_client.return_value = mock_client
        
        result = validate_ai_setup()
        
        assert result is True
        mock_validate_env.assert_called_once()
        mock_client.test_connection.assert_called_once()
    
    @patch('backend.core.ai_client.validate_environment')
    def test_validate_ai_setup_env_failure(self, mock_validate_env):
        """Test AI setup validation with environment failure."""
        mock_validate_env.return_value = False
        
        result = validate_ai_setup()
        
        assert result is False
        mock_validate_env.assert_called_once()
    
    @patch('backend.core.ai_client.validate_environment')
    @patch('backend.core.ai_client.get_ai_client')
    def test_validate_ai_setup_connection_failure(self, mock_get_client, mock_validate_env):
        """Test AI setup validation with connection failure."""
        mock_validate_env.return_value = True
        mock_client = Mock()
        mock_client.test_connection.return_value = False
        mock_get_client.return_value = mock_client
        
        result = validate_ai_setup()
        
        assert result is False
        mock_validate_env.assert_called_once()
        mock_client.test_connection.assert_called_once()


class TestEnvironmentValidation:
    """Test environment validation functionality."""
    
    @patch('backend.core.config.get_settings')
    def test_validate_environment_success(self, mock_get_settings):
        """Test successful environment validation."""
        mock_settings = Mock()
        mock_settings.openai_api_key = "test-key"
        mock_get_settings.return_value = mock_settings
        
        result = validate_environment()
        
        assert result is True
    
    @patch('backend.core.config.get_settings')
    def test_validate_environment_missing_key(self, mock_get_settings):
        """Test environment validation with missing API key."""
        mock_settings = Mock()
        mock_settings.openai_api_key = None
        mock_get_settings.return_value = mock_settings
        
        result = validate_environment()
        
        assert result is False
    
    @patch('backend.core.config.get_settings')
    def test_validate_environment_exception(self, mock_get_settings):
        """Test environment validation with exception."""
        mock_get_settings.side_effect = Exception("Config error")
        
        result = validate_environment()
        
        assert result is False


if __name__ == "__main__":
    pytest.main([__file__])
