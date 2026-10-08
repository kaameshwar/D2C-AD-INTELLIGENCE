from fastapi import APIRouter, HTTPException, Depends, File, UploadFile
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from pydantic import BaseModel
import pandas as pd
import io
from app.services import data_service, analytics_service, import_service
from app.decision_engine import engine
from app.simulation import simulator
from app.ai import ai_service
from app.db import get_db
from app.models import User, Campaign, DailyCampaignMetric, Recommendation
from app.api.deps import get_current_user

router = APIRouter()

class SimulationRequest(BaseModel):
    campaign_id: str
    proposed_budget: float

class ActionRequest(BaseModel):
    action: str
    budget_change: float

class Message(BaseModel):
    role: str
    content: str

class AIQueryRequest(BaseModel):
    query: str
    history: List[Message] = []

@router.get("/health")
def health_check():
    return {"status": "healthy"}

@router.get("/overview")
def get_overview(days: int = 7, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return analytics_service.get_dashboard_overview(db, current_user.organization_id, days)

@router.get("/campaigns")
def get_campaigns(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return data_service.get_all_campaigns(db, current_user.organization_id)

@router.get("/campaigns/{id}")
def get_campaign(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    campaign = data_service.get_campaign_by_id(db, current_user.organization_id, id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@router.get("/products")
def get_products(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return analytics_service.get_product_profitability(db, current_user.organization_id)

@router.get("/creatives")
def get_creatives(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return data_service.get_all_creatives(db, current_user.organization_id)

@router.get("/channels")
def get_channels(days: int = 7, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return analytics_service.get_channel_performance(db, current_user.organization_id, days)

@router.get("/diagnostics")
def get_diagnostics(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return engine.get_diagnostics(db, current_user.organization_id)

@router.get("/opportunities")
def get_opportunities(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return engine.get_opportunities(db, current_user.organization_id)

@router.get("/recommendations")
def get_recommendations(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return engine.get_recommendations(db, current_user.organization_id)

@router.post("/simulations")
def run_simulation(req: SimulationRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # Validate campaign ownership
    camp = db.query(Campaign).filter(Campaign.id == req.campaign_id).first()
    if not camp or camp.organization_id != current_user.organization_id:
        raise HTTPException(status_code=403, detail="Unauthorized access to campaign")
        
    return simulator.simulate_budget_change(db, current_user.organization_id, req.campaign_id, req.proposed_budget)

@router.post("/recommendations/{id}/explain")
def explain_recommendation(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return ai_service.explain_recommendation(db, current_user.organization_id, id)

@router.get("/recommendations/{id}")
def get_recommendation_by_id(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models import Recommendation, Campaign
    rec = db.query(Recommendation).filter(
        Recommendation.id == id, 
        Recommendation.organization_id == current_user.organization_id
    ).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Recommendation not found")
        
    camp = db.query(Campaign).filter(Campaign.id == rec.campaign_id).first()
    import json
    
    current_spend = camp.daily_budget if camp else 0
    if rec.evidence_json:
        try:
            evidence = json.loads(rec.evidence_json) if isinstance(rec.evidence_json, str) else rec.evidence_json
            if "metrics" in evidence and "spend" in evidence["metrics"]:
                current_spend = float(evidence["metrics"]["spend"])
        except Exception:
            pass
            
    return {
        "id": rec.id,
        "title": rec.title,
        "action_type": rec.action_type,
        "recommended_action": f"{'Increase' if rec.budget_change > 0 else 'Decrease'} spend by ₹{abs(rec.budget_change)}",
        "campaign_id": rec.campaign_id,
        "campaign_name": camp.name if camp else rec.campaign_id,
        "current_budget": current_spend,
        "projected_profit": rec.projected_profit,
        "budget_change": rec.budget_change
    }

@router.post("/recommendations/{id}/approve")
def approve_recommendation(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rec = db.query(Recommendation).filter(Recommendation.id == id).first()
    if not rec or rec.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return engine.approve_recommendation(db, id, current_user.organization_id)

@router.post("/recommendations/{id}/execute")
def execute_recommendation(id: str, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    rec = db.query(Recommendation).filter(Recommendation.id == id).first()
    if not rec or rec.organization_id != current_user.organization_id:
        raise HTTPException(status_code=404, detail="Recommendation not found")
    return engine.execute_recommendation(db, id, current_user.organization_id, current_user.id)

@router.get("/ai/status")
def get_ai_status():
    import os
    enabled = os.environ.get("LLM_ENABLED", "false").lower() == "true"
    provider = os.environ.get("LLM_PROVIDER", "openai").lower()
    api_key = os.environ.get("LLM_API_KEY")
    return {
        "enabled": enabled,
        "provider": provider,
        "configured": bool(api_key and len(api_key) > 0)
    }

@router.post("/ai/query")
def ask_ai(req: AIQueryRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    history_dicts = [{"role": m.role, "content": m.content} for m in req.history]
    return ai_service.answer_query(db, current_user.organization_id, req.query, history_dicts)

class OrgCreateRequest(BaseModel):
    name: str

@router.post("/organizations")
def create_organization(req: OrgCreateRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models import Organization
    org = Organization(name=req.name)
    db.add(org)
    db.commit()
    db.refresh(org)
    return {"id": org.id, "name": org.name}

@router.post("/upload/campaigns")
def upload_campaigns(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contents = file.file.read()
    res = import_service.import_campaigns(db, current_user.organization_id, contents)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@router.post("/products/import")
def upload_products(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contents = file.file.read()
    res = import_service.import_products(db, current_user.organization_id, contents)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@router.post("/orders/import")
def upload_orders(file: UploadFile = File(...), db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    contents = file.file.read()
    res = import_service.import_orders(db, current_user.organization_id, contents)
    if not res["success"]:
        raise HTTPException(status_code=400, detail=res["error"])
    return res

@router.get("/customers")
def get_customers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return analytics_service.get_customer_analytics(db, current_user.organization_id)

@router.get("/orders")
def get_orders(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return data_service.get_all_orders(db, current_user.organization_id)

@router.get("/reports")
def get_reports(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return []

@router.get("/journey")
def get_journey(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return analytics_service.get_customer_journey(db, current_user.organization_id)

class ScenarioRequest(BaseModel):
    current_spend: float
    current_roas: float
    current_margin_pct: float
    proposed_budget_change_pct: float

@router.post("/intelligence/simulate")
def simulate_scenario(req: ScenarioRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    try:
        from app.decision_engine import intelligence
        return intelligence.simulate_scenario(
            req.current_spend,
            req.current_roas,
            req.current_margin_pct,
            req.proposed_budget_change_pct
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from app.decision_engine.execution import get_adapter
from app.decision_engine.learning import evaluate_outcomes

class ExecutePayload(BaseModel):
    expected_revenue: float
    expected_contribution_profit: float
    expected_incremental_profit: float
    expected_roas: float
    previous_budget: float
    approved_budget: float

@router.post("/recommendations/{id}/execute")
def execute_recommendation_endpoint(id: str, payload: ExecutePayload, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models import Recommendation
    rec = db.query(Recommendation).filter(Recommendation.id == id, Recommendation.organization_id == current_user.organization_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail="Not found")
        
    adapter = get_adapter(db, "Demo")
    result = adapter.execute(rec, current_user.id, payload.dict())
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
        
    return result

@router.post("/intelligence/demo_sync")
def trigger_demo_sync(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # 1. Evaluate outcomes for anything in MONITORING
    evaluate_outcomes(db, current_user.organization_id)
    return {"status": "success", "message": "Demo continuous sync completed. Outcomes evaluated."}

@router.get("/intelligence/learning")
def get_decision_memory(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    from app.models import DecisionMemory, Recommendation
    memories = db.query(DecisionMemory).filter(DecisionMemory.organization_id == current_user.organization_id).order_by(DecisionMemory.evaluated_at.desc()).all()
    results = []
    for m in memories:
        rec = db.query(Recommendation).filter(Recommendation.id == m.recommendation_id).first()
        results.append({
            "id": m.id,
            "action": rec.title if rec else "Unknown",
            "expected": m.expected_profit,
            "actual": m.actual_profit,
            "variance": m.variance,
            "result": m.outcome_classification,
            "date": m.evaluated_at.isoformat() if m.evaluated_at else None
        })
    return results
