"""
Azure OpenAI client wrapper
"""

import openai
import json
import logging
import re
from fastapi import HTTPException
from config.settings import AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, API_VERSION, MODEL_NAME

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AzureOpenAIClient:
    def __init__(self):
        self.model = MODEL_NAME
        # Using newer SDK approach
        self.client = openai.AzureOpenAI(
            api_key=AZURE_OPENAI_API_KEY,
            api_version=API_VERSION,
            azure_endpoint=AZURE_OPENAI_ENDPOINT
        )
        self.token_usage = {
            "total_prompt_tokens": 0,
            "total_completion_tokens": 0,
            "total_tokens": 0
        }
    
    def generate_chat_completion(self, messages, max_tokens=1000, temperature=0.8, structured_output=False):
        """Generate chat completion using Azure OpenAI
        
        Args:
            messages: List of message dictionaries (role, content)
            max_tokens: Maximum tokens in the response
            temperature: Temperature for generation (higher = more creative)
            structured_output: Whether to request structured JSON output
        
        Returns:
            The content of the message from the model's response
        """
        try:
            # If structured output is requested, add appropriate configuration
            if structured_output:
                # Check if API version supports response_format (newer versions)
                try:
                    # If response_format is supported, use it
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        response_format={"type": "json_object"}
                    )
                except Exception as e:
                    # If not, fall back to regular completion but add system message
                    if not any("ONLY raw JSON" in msg.get("content", "") for msg in messages if msg.get("role") == "system"):
                        # Add JSON instruction if not already present
                        messages.insert(0, {
                            "role": "system", 
                            "content": "You must respond with ONLY valid JSON with no markdown formatting, explanations, or code blocks."
                        })
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        max_tokens=max_tokens,
                        temperature=temperature
                    )
            else:
                # Regular text completion
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
            
            # Track token usage if available
            if hasattr(response, 'usage'):
                self.token_usage["total_prompt_tokens"] += response.usage.prompt_tokens
                self.token_usage["total_completion_tokens"] += response.usage.completion_tokens
                self.token_usage["total_tokens"] += response.usage.total_tokens
            
            content = response.choices[0].message.content.strip()
    
            return content
        
        except Exception as e:
            logger.error(f"Azure OpenAI API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Azure OpenAI API error: {str(e)}")
    
    def get_token_usage(self):
        """Return the current token usage statistics"""
        return self.token_usage