"""
OpenAI API client with LangChain integration for the Personal Learning Agent.

This module provides a comprehensive AI client that integrates OpenAI's API
with LangChain for text processing, embeddings, and chat functionality.
"""

import os
import time
from typing import Optional, List, Dict, Any, Union, Generator
from dataclasses import dataclass
import logging

import openai
from langchain_openai import OpenAI, ChatOpenAI, OpenAIEmbeddings
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_core.callbacks.base import BaseCallbackHandler
from langchain_core.callbacks.manager import CallbackManager
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate
# Note: Chains and memory functionality will be implemented in future iterations
# from langchain_community.chains import LLMChain, ConversationChain
# from langchain_community.memory import ConversationBufferMemory

from .config import get_config, validate_environment

# Configure logging
logger = logging.getLogger(__name__)


@dataclass
class AIResponse:
    """Response from AI client with metadata."""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    response_time: Optional[float] = None
    error: Optional[str] = None


@dataclass
class EmbeddingResponse:
    """Response from embedding generation."""
    embeddings: List[List[float]]
    model: str
    usage: Optional[Dict[str, int]] = None
    response_time: Optional[float] = None
    error: Optional[str] = None


class AICallbackHandler(BaseCallbackHandler):
    """Custom callback handler for AI operations."""
    
    def __init__(self):
        self.tokens_used = 0
        self.start_time = None
        self.end_time = None
    
    def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """Called when LLM starts."""
        self.start_time = time.time()
        logger.debug("LLM started")
    
    def on_llm_end(self, response: Any, **kwargs) -> None:
        """Called when LLM ends."""
        self.end_time = time.time()
        if hasattr(response, 'llm_output') and response.llm_output:
            if 'token_usage' in response.llm_output:
                self.tokens_used = response.llm_output['token_usage'].get('total_tokens', 0)
        logger.debug(f"LLM ended. Tokens used: {self.tokens_used}")
    
    def on_llm_error(self, error: Union[Exception, KeyboardInterrupt], **kwargs) -> None:
        """Called when LLM encounters an error."""
        logger.error(f"LLM error: {error}")


class AIClient:
    """
    OpenAI API client with LangChain integration.
    
    Provides methods for text generation, embeddings, and chat functionality
    with proper error handling, retry logic, and configuration management.
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize AI client.
        
        Args:
            config_manager: Configuration manager instance. If None, uses global config.
        """
        self.config = config_manager or get_config()
        self.settings = self.config.get_settings()
        self.openai_config = self.config.get_openai_config()
        self.langchain_config = self.config.get_langchain_config()
        
        # Initialize OpenAI client
        self._setup_openai_client()
        
        # Initialize LangChain components
        self._setup_langchain_components()
        
        # Initialize callback handler
        self.callback_handler = AICallbackHandler()
        self.callback_manager = CallbackManager([self.callback_handler])
        
        logger.info("AI Client initialized successfully")
    
    def _setup_openai_client(self) -> None:
        """Setup OpenAI client with configuration."""
        try:
            # Set OpenAI API key
            openai.api_key = self.openai_config['api_key']
            
            # Set OpenAI configuration
            openai.api_base = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
            openai.api_type = os.getenv("OPENAI_API_TYPE", "open_ai")
            openai.api_version = os.getenv("OPENAI_API_VERSION", "2023-05-15")
            
            logger.info("OpenAI client configured successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup OpenAI client: {e}")
            raise
    
    def _setup_langchain_components(self) -> None:
        """Setup LangChain components with configuration."""
        try:
            # Initialize LLM
            self.llm = OpenAI(
                openai_api_key=self.openai_config['api_key'],
                model_name=self.openai_config['model'],
                temperature=self.openai_config['temperature'],
                max_tokens=self.openai_config['max_tokens'],
                request_timeout=self.openai_config['timeout'],
                verbose=self.langchain_config['verbose']
            )
            
            # Initialize Chat Model
            self.chat_model = ChatOpenAI(
                openai_api_key=self.openai_config['api_key'],
                model_name=self.openai_config['model'],
                temperature=self.openai_config['temperature'],
                max_tokens=self.openai_config['max_tokens'],
                request_timeout=self.openai_config['timeout'],
                verbose=self.langchain_config['verbose']
            )
            
            # Initialize Embeddings
            self.embeddings = OpenAIEmbeddings(
                openai_api_key=self.openai_config['api_key'],
                model="text-embedding-ada-002",
                request_timeout=self.openai_config['timeout']
            )
            
            # Note: Memory and conversation chains will be implemented in future iterations
            # For now, we'll use simple chat functionality without persistent memory
            self.memory = None
            self.conversation_chain = None
            
            logger.info("LangChain components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to setup LangChain components: {e}")
            raise
    
    def generate_text(
        self, 
        prompt: str, 
        system_message: Optional[str] = None,
        max_retries: int = 3,
        **kwargs
    ) -> AIResponse:
        """
        Generate text using OpenAI API.
        
        Args:
            prompt: Input prompt for text generation
            system_message: Optional system message for context
            max_retries: Maximum number of retry attempts
            **kwargs: Additional parameters for the LLM
            
        Returns:
            AIResponse: Generated text response with metadata
        """
        start_time = time.time()
        
        try:
            # Prepare messages
            messages = []
            if system_message:
                messages.append(SystemMessage(content=system_message))
            messages.append(HumanMessage(content=prompt))
            
            # Generate response with retry logic
            for attempt in range(max_retries):
                try:
                    response = self.chat_model.invoke(messages)
                    
                    response_time = time.time() - start_time
                    
                    return AIResponse(
                        content=response.content,
                        model=self.openai_config['model'],
                        usage=getattr(response, 'usage', None),
                        finish_reason=getattr(response, 'finish_reason', None),
                        response_time=response_time
                    )
                    
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
            
        except Exception as e:
            logger.error(f"Text generation failed: {e}")
            return AIResponse(
                content="",
                model=self.openai_config['model'],
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    def generate_embeddings(
        self, 
        texts: Union[str, List[str]], 
        max_retries: int = 3
    ) -> EmbeddingResponse:
        """
        Generate embeddings for text(s).
        
        Args:
            texts: Text or list of texts to embed
            max_retries: Maximum number of retry attempts
            
        Returns:
            EmbeddingResponse: Embeddings with metadata
        """
        start_time = time.time()
        
        try:
            # Ensure texts is a list
            if isinstance(texts, str):
                texts = [texts]
            
            # Generate embeddings with retry logic
            for attempt in range(max_retries):
                try:
                    embeddings = self.embeddings.embed_documents(texts)
                    
                    response_time = time.time() - start_time
                    
                    return EmbeddingResponse(
                        embeddings=embeddings,
                        model="text-embedding-ada-002",
                        response_time=response_time
                    )
                    
                except Exception as e:
                    if attempt == max_retries - 1:
                        raise
                    logger.warning(f"Embedding attempt {attempt + 1} failed: {e}. Retrying...")
                    time.sleep(2 ** attempt)  # Exponential backoff
            
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            return EmbeddingResponse(
                embeddings=[],
                model="text-embedding-ada-002",
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    def chat(
        self, 
        message: str, 
        conversation_id: Optional[str] = None,
        system_message: Optional[str] = None,
        **kwargs
    ) -> AIResponse:
        """
        Chat with the AI model using simple message passing.
        
        Args:
            message: User message
            conversation_id: Optional conversation ID for context (not used in current implementation)
            system_message: Optional system message for context
            **kwargs: Additional parameters
            
        Returns:
            AIResponse: Chat response with metadata
        """
        start_time = time.time()
        
        try:
            # Use the generate_text method with system message for chat functionality
            response = self.generate_text(message, system_message=system_message)
            
            return response
            
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return AIResponse(
                content="",
                model=self.openai_config['model'],
                response_time=time.time() - start_time,
                error=str(e)
            )
    
    def create_prompt_template(
        self, 
        template: str, 
        input_variables: List[str]
    ) -> PromptTemplate:
        """
        Create a prompt template for consistent prompting.
        
        Args:
            template: Prompt template string
            input_variables: List of input variable names
            
        Returns:
            PromptTemplate: LangChain prompt template
        """
        return PromptTemplate(
            input_variables=input_variables,
            template=template
        )
    
    def create_chain(
        self, 
        prompt_template: PromptTemplate, 
        **kwargs
    ) -> None:
        """
        Create a LangChain chain with the given prompt template.
        
        Note: This functionality will be implemented in future iterations.
        
        Args:
            prompt_template: Prompt template to use
            **kwargs: Additional parameters for the chain
            
        Returns:
            None: Currently not implemented
        """
        logger.warning("Chain creation not implemented in current version")
        return None
    
    def clear_memory(self) -> None:
        """Clear conversation memory."""
        # Note: Memory functionality not implemented in current version
        logger.info("Memory clearing not implemented in current version")
    
    def get_memory_summary(self) -> Dict[str, Any]:
        """
        Get summary of conversation memory.
        
        Returns:
            dict: Memory summary (currently empty as memory is not implemented)
        """
        return {
            'total_messages': 0,
            'user_messages': 0,
            'ai_messages': 0,
            'system_messages': 0,
            'recent_messages': []
        }
    
    def test_connection(self) -> bool:
        """
        Test AI client connection and functionality.
        
        Returns:
            bool: True if connection test passes, False otherwise
        """
        try:
            # Test with a simple prompt
            response = self.generate_text("Hello, this is a test message.")
            
            if response.error:
                logger.error(f"AI client test failed: {response.error}")
                return False
            
            logger.info("AI client connection test passed")
            return True
            
        except Exception as e:
            logger.error(f"AI client test failed: {e}")
            return False
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """
        Get usage statistics from the callback handler.
        
        Returns:
            dict: Usage statistics including tokens used and response times
        """
        return {
            'tokens_used': self.callback_handler.tokens_used,
            'start_time': self.callback_handler.start_time,
            'end_time': self.callback_handler.end_time,
            'response_time': (
                self.callback_handler.end_time - self.callback_handler.start_time
                if self.callback_handler.start_time and self.callback_handler.end_time
                else None
            )
        }


# Global AI client instance
_ai_client: Optional[AIClient] = None


def get_ai_client() -> AIClient:
    """
    Get the global AI client instance.
    
    Returns:
        AIClient: Global AI client instance
    """
    global _ai_client
    if _ai_client is None:
        _ai_client = AIClient()
    return _ai_client


def initialize_ai_client(config_manager=None) -> AIClient:
    """
    Initialize the global AI client.
    
    Args:
        config_manager: Configuration manager instance
        
    Returns:
        AIClient: Initialized AI client instance
    """
    global _ai_client
    _ai_client = AIClient(config_manager)
    return _ai_client


def reset_ai_client() -> None:
    """Reset the global AI client instance (useful for testing)."""
    global _ai_client
    _ai_client = None


def validate_ai_setup() -> bool:
    """
    Validate AI client setup and configuration.
    
    Returns:
        bool: True if setup is valid, False otherwise
    """
    try:
        # Validate environment
        if not validate_environment():
            return False
        
        # Test AI client
        client = get_ai_client()
        return client.test_connection()
        
    except Exception as e:
        logger.error(f"AI setup validation failed: {e}")
        return False
