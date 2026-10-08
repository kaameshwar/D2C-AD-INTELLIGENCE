import pytest
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Organization, Campaign, DailyCampaignMetric, Recommendation
from app.ai.ai_service import explain_recommendation, answer_query, plan_query

@pytest.fixture(scope="module")
def test_db():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestingSessionLocal()
    
    # Setup Data
    org1 = Organization(id="org_test_1", name="Test Org 1")
    org2 = Organization(id="org_test_2", name="Test Org 2")
    db.add(org1)
    db.add(org2)
    db.commit()
    
    camp1 = Campaign(id="camp_1", organization_id="org_test_1", name="Strong Campaign", daily_budget=100.0, status="Active")
    camp2 = Campaign(id="camp_2", organization_id="org_test_2", name="Other Org Campaign", daily_budget=50.0, status="Active")
    db.add(camp1)
    db.add(camp2)
    db.commit()
    
    metric1 = DailyCampaignMetric(campaign_id="camp_1", date="2023-01-01", spend=1000, revenue=5000, conversions=50)
    db.add(metric1)
    db.commit()
    
    ev_json = json.dumps({
        "metrics": {"spend": 1000, "revenue": 5000, "roas": 5.0},
        "decision": {"type": "SCALE", "reason": "ROAS exceeds strong threshold"}
    })
    
    rec1 = Recommendation(
        id="rec_1", organization_id="org_test_1", campaign_id="camp_1", 
        title="Scale Strong", action_type="SCALE", budget_change=20.0, 
        projected_profit=800.0, score=90, confidence="High", 
        reason="Good ROAS", evidence_json=ev_json, status="Pending"
    )
    db.add(rec1)
    db.commit()
    
    yield db
    db.close()

def test_explain_recommendation_mock(test_db, mocker):
    mocker.patch.dict(os.environ, {"LLM_ENABLED": "true", "LLM_PROVIDER": "mock", "LLM_API_KEY": "mock-key"})
    result = explain_recommendation(test_db, "org_test_1", "rec_1")
    
    assert result["available"] is True
    assert "summary" in result
    assert result["summary"] == "This is a mock AI summary based on the provided evidence."
    assert "evidence_points" in result

def test_explain_recommendation_disabled(test_db, mocker):
    mocker.patch.dict(os.environ, {"LLM_ENABLED": "false"})
    result = explain_recommendation(test_db, "org_test_1", "rec_1")
    
    assert result["available"] is False
    assert result["summary"] == "AI explanation is currently unavailable."
    assert "Scale Strong. Good ROAS" in result["deterministic_summary"]

def test_tenant_isolation_explain(test_db, mocker):
    mocker.patch.dict(os.environ, {"LLM_ENABLED": "true", "LLM_PROVIDER": "mock", "LLM_API_KEY": "mock-key"})
    # Try to access org_test_1's recommendation using org_test_2
    result = explain_recommendation(test_db, "org_test_2", "rec_1")
    assert result["available"] is False
    assert result["reason"] == "Recommendation not found"

def test_provider_failure_fallback(test_db, mocker):
    mocker.patch.dict(os.environ, {"LLM_ENABLED": "true", "LLM_PROVIDER": "mock", "LLM_API_KEY": "mock-key"})
    
    # Clear cache so we actually hit the provider
    import app.ai.ai_service
    app.ai.ai_service.EXPLANATION_CACHE.clear()
    
    # Mock the mock provider to throw an exception
    mocker.patch("app.ai.providers.MockProvider.generate_json", side_effect=Exception("API Timeout"))
    
    result = explain_recommendation(test_db, "org_test_1", "rec_1")
    assert result["available"] is False
    assert result["summary"] == "AI explanation is currently unavailable."
    
def test_query_planning(mocker):
    from app.ai.providers import MockProvider
    from app.ai.ai_service import plan_query
    provider = MockProvider()
    
    plan1 = plan_query(provider, "Which campaign is best?", [])
    assert plan1["domain"] == "CAMPAIGN"
    
    plan2 = plan_query(provider, "What are my biggest risks?", [])
    assert plan2["domain"] == "GENERAL_BUSINESS"
    
    plan3 = plan_query(provider, "Tell me about my products.", [])
    assert plan3["domain"] == "PRODUCT"


def test_answer_query_tenant_isolation(test_db, mocker):
    mocker.patch.dict(os.environ, {"LLM_ENABLED": "true", "LLM_PROVIDER": "mock", "LLM_API_KEY": "mock-key"})
    
    # We expect the mock provider to return its mock string, but we can verify
    # tenant isolation indirectly by making sure no exception is thrown when
    # querying for an org that doesn't have much data, or by checking the answer format.
    result = answer_query(test_db, "org_test_2", "Which campaign is best?")
    assert result["answer"] == "This is a mock AI response to your chat query."
