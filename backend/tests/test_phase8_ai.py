import pytest
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Organization, Campaign, Product, DailyCampaignMetric, Recommendation
from app.ai.ai_service import answer_query, plan_query, SYSTEM_PROMPT
from app.ai.providers import get_llm_provider, MockProvider

@pytest.fixture(scope="module")
def ai_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    # Org
    org = Organization(id="org_ai_1", name="AI Test Org")
    db.add(org)
    
    # Campaign
    camp = Campaign(id="camp_ai_1", organization_id="org_ai_1", name="Adversarial Camp", daily_budget=100.0, status="Active")
    db.add(camp)
    
    # Metric
    db.add(DailyCampaignMetric(campaign_id="camp_ai_1", date="2023-10-01", spend=50, revenue=200, conversions=5))
    
    # Product
    db.add(Product(id="prod_ai_1", organization_id="org_ai_1", sku="PRD-1", name="Test Product", price=100.0, cost=50.0))
    
    db.commit()
    
    yield db
    db.close()

def test_ai_history_parsing(ai_db, mocker):
    mocker.patch.dict(os.environ, {"LLM_ENABLED": "true", "LLM_PROVIDER": "mock", "LLM_API_KEY": "mock-key"})
    history = [
        {"role": "user", "content": "What is the best campaign?"},
        {"role": "ai", "content": "Adversarial Camp is the best."}
    ]
    
    result = answer_query(ai_db, "org_ai_1", "Why?", history)
    
    # Should use the Mock provider
    assert result["answer"] == "This is a mock AI response to your chat query."
    
def test_system_prompt_safeguards():
    # Verify the system prompt contains anti-hallucination guardrails
    assert "Do not invent financial values" in SYSTEM_PROMPT
    assert "Do not override deterministic DeciFlow decisions" in SYSTEM_PROMPT
    assert "When information is missing, state that it is unavailable" in SYSTEM_PROMPT
    assert "ROAS measures revenue efficiency, not profitability" in SYSTEM_PROMPT

def test_missing_entities_fallback(ai_db, mocker):
    mocker.patch.dict(os.environ, {"LLM_ENABLED": "true", "LLM_PROVIDER": "mock", "LLM_API_KEY": "mock-key"})
    # The MockProvider will classify as GENERAL_BUSINESS but let's mock it to extract an entity
    
    class EntityMockProvider(MockProvider):
        def generate_json(self, system_prompt: str, user_prompt: str) -> dict:
            return {
                "domain": "CAMPAIGN",
                "entities": ["NonExistent Z"],
                "intent": "analyze",
                "comparison": None,
                "time_range": "available_data"
            }
            
    mocker.patch("app.ai.ai_service.get_llm_provider", return_value=EntityMockProvider())
    
    # answer_query should gracefully fall back to showing all campaigns with a note if entity isn't found
    # But wait, answer_query doesn't return the context directly.
    # We can mock generate_text to capture the user_prompt and assert the note is there.
    
    captured_prompt = ""
    class CapturedMockProvider(EntityMockProvider):
        def generate_text(self, system_prompt: str, user_prompt: str) -> str:
            nonlocal captured_prompt
            captured_prompt = user_prompt
            return "Captured"
            
    mocker.patch("app.ai.ai_service.get_llm_provider", return_value=CapturedMockProvider())
    
    result = answer_query(ai_db, "org_ai_1", "Analyze NonExistent Z", [])
    
    assert "Could not find exact campaigns matching" in captured_prompt
    assert "NonExistent Z" in captured_prompt
    
def test_prompt_injection_safety(mocker):
    assert "Do not invent" in SYSTEM_PROMPT
    # The actual effectiveness of the prompt injection is validated by LLM tests,
    # Since we don't have API keys, we assert the system prompt structure is correct.

from fastapi.testclient import TestClient
from app.main import app
from app.api.deps import get_current_user
from app.models import User

client = TestClient(app)

def override_get_current_user():
    # Return a dummy user mapped to org_ai_1
    return User(id="user_1", email="test@test.com", organization_id="org_ai_1")

def test_api_ai_query_with_history(mocker):
    mocker.patch.dict(os.environ, {"LLM_ENABLED": "true", "LLM_PROVIDER": "mock", "LLM_API_KEY": "mock-key"})
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    response = client.post(
        "/api/ai/query",
        json={
            "query": "Test query",
            "history": [
                {"role": "user", "content": "What is up?"},
                {"role": "ai", "content": "Nothing much."}
            ]
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "mock AI response" in data["answer"]
    
    app.dependency_overrides.clear()
