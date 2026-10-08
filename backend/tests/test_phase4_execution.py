import pytest
import json
from sqlalchemy.orm import Session
from app.models import Organization, Campaign, Recommendation, Action, DecisionMemory, DailyCampaignMetric
from app.decision_engine.execution import DemoExecutionAdapter
from app.decision_engine.learning import evaluate_outcomes, apply_calibration
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.db import Base
from datetime import datetime, timedelta

# Setup test DB
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    org1 = Organization(id="ORG-1", name="Test Org 1")
    db.add(org1)
    db.commit()
    yield db
    db.close()
    Base.metadata.drop_all(bind=engine)

def test_demo_execution_adapter(db_session: Session):
    # Setup
    camp = Campaign(id="CAMP-1", organization_id="ORG-1", daily_budget=100.0)
    rec = Recommendation(id="REC-1", organization_id="ORG-1", campaign_id="CAMP-1", budget_change=20.0, action_type="SCALE", status="APPROVED")
    db_session.add(camp)
    db_session.add(rec)
    db_session.commit()
    
    adapter = DemoExecutionAdapter(db_session)
    res = adapter.execute(rec, user_id="user123")
    
    assert res["status"] == "success"
    
    # Check campaign updated
    db_session.refresh(camp)
    assert camp.daily_budget == 120.0
    
    # Check action created
    action = db_session.query(Action).filter_by(recommendation_id="REC-1").first()
    assert action is not None
    assert action.execution_mode == "Demo"
    assert "120.0" in action.execution_details_json
    
    # Check recommendation state
    db_session.refresh(rec)
    assert rec.status == "MONITORING"
    
    # Duplicate prevention
    res2 = adapter.execute(rec, user_id="user123")
    assert res2["status"] == "error"

def test_evaluate_outcomes_and_learning(db_session: Session):
    # Setup executed rec
    camp = Campaign(id="CAMP-2", organization_id="ORG-1", daily_budget=100.0)
    rec = Recommendation(
        id="REC-2", organization_id="ORG-1", campaign_id="CAMP-2", 
        budget_change=20.0, action_type="SCALE", projected_profit=100.0, 
        status="MONITORING"
    )
    action = Action(id="ACT-1", organization_id="ORG-1", recommendation_id="REC-2", created_at=datetime.utcnow() - timedelta(days=2))
    
    db_session.add(camp)
    db_session.add(rec)
    db_session.add(action)
    db_session.commit()
    
    # Simulate new data arriving after execution (Actual Profit = 150)
    metric = DailyCampaignMetric(
        campaign_id="CAMP-2", 
        date=datetime.utcnow().strftime("%Y-%m-%d"), 
        spend=50.0, revenue=200.0 # profit = 150
    )
    db_session.add(metric)
    db_session.commit()
    
    # Run evaluation
    evaluate_outcomes(db_session, "ORG-1")
    
    db_session.refresh(rec)
    assert rec.status == "EVALUATED"
    assert rec.actual_profit == 150.0
    assert rec.variance == 50.0
    assert rec.outcome_status == "OUTPERFORMED_EXPECTATION"
    
    # Check memory
    memory = db_session.query(DecisionMemory).filter_by(recommendation_id="REC-2").first()
    assert memory is not None
    assert memory.actual_profit == 150.0
    
    # Check learning
    calib = apply_calibration(db_session, "ORG-1", "SCALE", 100.0)
    # bias = 50. factor = 1.0 + (50 / 100) = 1.5
    assert calib["factor"] == 1.5
    assert calib["calibrated_profit"] == 150.0
    assert calib["label"] == "CALIBRATED PROJECTION"
