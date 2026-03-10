"""
Groq API service for handling LLM interactions
"""
import os
import time
import logging
from typing import Dict, Any, AsyncGenerator
from groq import AsyncGroq
from config import settings

logger = logging.getLogger(__name__)

class GroqService:
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY or os.getenv('GROQ_API_KEY')
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in settings or environment variables")
        
        # Use AsyncGroq for proper async support  
        self.client = AsyncGroq(api_key=self.api_key)
        self.model = settings.GROQ_MODEL
        logger.info("Groq async client initialized successfully")
    
    async def check_connection(self) -> bool:
        """Check if the Groq service is available"""
        try:
            response = await self.client.chat.completions.create(
                messages=[{"role": "user", "content": "Test"}],
                model=self.model,
                max_tokens=5
            )
            logger.info("Groq connection test successful")
            return True
        except Exception as e:
            logger.error(f"Groq connection test failed: {e}")
            return False

    async def generate_response(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = None
    ) -> str:
        """Generate a response from the LLM"""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        start_time = time.time()

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature or settings.GROQ_TEMPERATURE,
                max_tokens=settings.GROQ_MAX_TOKENS
            )

            end_time = time.time()
            duration = end_time - start_time

            # Log token usage
            usage = response.usage
            prompt_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0
            total_tokens = usage.total_tokens if usage else 0

            if total_tokens > 0:
                tokens_per_sec = output_tokens / duration if duration > 0 else 0
                print(f"Token Usage: {prompt_tokens} input + {output_tokens} output = {total_tokens} total")
                print(f"Speed: {tokens_per_sec:.1f} tokens/sec | Duration: {duration:.1f}s\n")
            else:
                print(f"Generation took {duration:.1f}s (token stats not available)\n")

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Error generating response with Groq: {e}")
            raise

    async def generate_streaming_response(
        self,
        prompt: str,
        system_prompt: str = None,
        temperature: float = None
    ) -> AsyncGenerator[str, None]:
        """Generate a streaming response from the LLM"""
        messages = []

        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})

        messages.append({"role": "user", "content": prompt})

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                stream=True,
                temperature=temperature or settings.GROQ_TEMPERATURE,
                max_tokens=settings.GROQ_MAX_TOKENS
            )

            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            logger.error(f"Error in streaming response: {e}")
            # Fallback to non-streaming
            response = await self.generate_response(prompt, system_prompt, temperature)
            yield response