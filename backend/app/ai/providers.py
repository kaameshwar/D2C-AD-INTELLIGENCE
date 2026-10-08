import os
from abc import ABC, abstractmethod
import json

class LLMProvider(ABC):
    @abstractmethod
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        pass
        
    @abstractmethod
    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        pass

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=api_key)
            self.model = model
        except ImportError:
            raise RuntimeError("openai package not installed")

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = response.choices[0].message.content
        return json.loads(content)
        
    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content

class MockProvider(LLMProvider):
    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        return {
            "summary": "This is a mock AI summary based on the provided evidence.",
            "why_it_matters": "Mock explanation of business impact.",
            "recommended_action": "Mock recommended action reflecting the deterministic evidence.",
            "risk": "Ensure data sufficiency before proceeding.",
            "evidence_points": ["Mock evidence point 1"]
        }

    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        return "This is a mock AI response to your chat query."

class GroqProvider(LLMProvider):
    def __init__(self, api_key: str, model: str):
        try:
            from openai import OpenAI
            self.client = OpenAI(
                api_key=api_key,
                base_url="https://api.groq.com/openai/v1"
            )
            self.model = model
        except ImportError:
            raise RuntimeError("openai package not installed")

    def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        content = response.choices[0].message.content
        return json.loads(content)
        
    def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
        )
        return response.choices[0].message.content

def get_llm_provider() -> LLMProvider:
    enabled = os.environ.get("LLM_ENABLED", "false").lower() == "true"
    if not enabled:
        return None
        
    provider_name = os.environ.get("LLM_PROVIDER", "openai").lower()
    api_key = os.environ.get("LLM_API_KEY")
    
    if not api_key:
        return None
        
    if provider_name == "openai":
        return OpenAIProvider(
            api_key=api_key, 
            model=os.environ.get("LLM_MODEL", "gpt-4-turbo-preview")
        )
    elif provider_name == "groq":
        return GroqProvider(
            api_key=api_key,
            model=os.environ.get("LLM_MODEL", "llama3-70b-8192")
        )
    elif provider_name == "mock":
        return MockProvider()
        
    return None
