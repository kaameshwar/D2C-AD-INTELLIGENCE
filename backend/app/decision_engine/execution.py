import json
import uuid
from datetime import datetime
from sqlalchemy.orm import Session
from app.models import Recommendation, Action, Campaign

class DemoExecutionAdapter:
    def __init__(self, db: Session):
        self.db = db
        
    def execute(self, recommendation: Recommendation, user_id: str, payload: dict = None) -> dict:
        # Check idempotency
        existing_action = self.db.query(Action).filter(Action.recommendation_id == recommendation.id).first()
        if existing_action:
            return {"status": "error", "message": "Already executed."}
            
        # Demo adapter just manipulates the DB record to simulate execution
        campaign = self.db.query(Campaign).filter(Campaign.id == recommendation.campaign_id).first()
        if not campaign:
            return {"status": "error", "message": "Campaign not found"}
            
        old_budget = campaign.daily_budget
        new_budget = old_budget + recommendation.budget_change
        
        # Apply change
        campaign.daily_budget = new_budget
        
        execution_details = {
            "platform": "Demo",
            "old_budget": old_budget,
            "new_budget": new_budget,
            "timestamp": datetime.utcnow().isoformat(),
            "status": "SUCCESS"
        }
        
        if payload:
            execution_details.update(payload)
        
        # Create action record
        action = Action(
            organization_id=recommendation.organization_id,
            recommendation_id=recommendation.id,
            user_id=user_id,
            execution_mode="Demo",
            execution_result="SUCCESS",
            execution_details_json=json.dumps(execution_details)
        )
        self.db.add(action)
        
        # Update recommendation status
        recommendation.status = "EXECUTED"
        self.db.commit()
        
        # Transition to monitoring immediately in demo mode
        recommendation.status = "MONITORING"
        self.db.commit()
        
        return {"status": "success", "action_id": action.id}

def get_adapter(db: Session, platform: str):
    # Abstract factory for future platforms (Meta, Google)
    if platform == "Demo" or True: # Force demo for hackathon
        return DemoExecutionAdapter(db)
