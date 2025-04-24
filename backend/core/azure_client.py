"""
Azure OpenAI client wrapper
"""

import openai
import logging
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
    
    def generate_chat_completion(self, messages, max_tokens=1000, temperature=0.8):
        """Generate chat completion using Azure OpenAI"""
        try:
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
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Azure OpenAI API error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Azure OpenAI API error: {str(e)}")
    
    def get_token_usage(self):
        """Return the current token usage statistics"""
        return self.token_usage