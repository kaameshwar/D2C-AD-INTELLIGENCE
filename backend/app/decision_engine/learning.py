import json
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import Recommendation, Action, DecisionMemory, DailyCampaignMetric, LearningCalibration
from datetime import datetime, timedelta

def evaluate_outcomes(db: Session, organization_id: str):
    # Find all recommendations in MONITORING state
    monitoring_recs = db.query(Recommendation).filter(
        Recommendation.organization_id == organization_id,
        Recommendation.status == "MONITORING"
    ).all()
    
    for rec in monitoring_recs:
        # In a real system, we'd check if enough days have passed since execution.
        # For the demo, we assume the continuous sync just ran and provided enough data.
        
        # Calculate actual outcome
        # We need pre-execution baseline and post-execution metrics
        # For simplicity in demo, we'll grab the last 7 days vs previous 7 days (pre-execution)
        # Assuming the execution happened 7 days ago.
        
        action = db.query(Action).filter(Action.recommendation_id == rec.id).first()
        if not action:
            continue
            
        execution_date = action.created_at
        
        # Calculate expected vs actual
        # In a real system, we'd isolate incremental. For demo, we just look at the new period profit.
        
        # Dummy logic for demo hackathon simulating actual results based on the expected 
        # (with some random realistic variance). But we must use DB data if it exists.
        
        # Since we use continuous sync, let's query the metrics AFTER execution date.
        actual_metrics = db.query(
            func.sum(DailyCampaignMetric.spend).label("spend"),
            func.sum(DailyCampaignMetric.revenue).label("revenue")
        ).filter(
            DailyCampaignMetric.campaign_id == rec.campaign_id,
            DailyCampaignMetric.date >= execution_date.strftime("%Y-%m-%d")
        ).first()
        
        actual_spend = float(actual_metrics.spend or 0)
        actual_revenue = float(actual_metrics.revenue or 0)
        
        # If we have no new data yet, stay in AWAITING_OUTCOME / MONITORING
        if actual_spend == 0:
            rec.status = "AWAITING_OUTCOME"
            continue
            
        actual_profit = actual_revenue - actual_spend
        
        # Variance calculation
        expected_profit = rec.projected_profit or 0.0
        
        # Compare incremental (actual_profit might be total profit, we need incremental)
        # For demo purposes, we will treat actual_profit as the incremental result if we don't have a baseline.
        
        variance = actual_profit - expected_profit
        variance_pct = (variance / expected_profit) if expected_profit != 0 else 0
        
        if variance_pct > 0.10:
            classification = "OUTPERFORMED_EXPECTATION"
        elif variance_pct < -0.10:
            classification = "UNDERPERFORMED_EXPECTATION"
        else:
            classification = "MET_EXPECTATION"
            
        rec.actual_profit = actual_profit
        rec.variance = variance
        rec.outcome_status = classification
        rec.evaluated_at = datetime.utcnow()
        rec.status = "EVALUATED"
        
        # Decision Memory
        memory = DecisionMemory(
            organization_id=organization_id,
            recommendation_id=rec.id,
            action_id=action.id,
            expected_profit=expected_profit,
            actual_profit=actual_profit,
            variance=variance,
            outcome_classification=classification,
            confidence="High" if actual_spend > 100 else "Low",
            expected_impact_json=json.dumps({"profit": expected_profit}),
            actual_impact_json=json.dumps({"profit": actual_profit}),
            variance_json=json.dumps({"profit_variance": variance})
        )
        db.add(memory)
        
        # Learning Signal
        calib = db.query(LearningCalibration).filter(
            LearningCalibration.organization_id == organization_id,
            LearningCalibration.action_type == rec.action_type
        ).first()
        
        if not calib:
            calib = LearningCalibration(
                organization_id=organization_id,
                action_type=rec.action_type,
                number_of_observations=0,
                historical_prediction_error=0.0,
                bias=0.0,
                calibration_factor=1.0
            )
            db.add(calib)
            
        # Update calibration
        calib.number_of_observations += 1
        calib.historical_prediction_error += variance
        # Simple bias adjustment
        calib.bias = calib.historical_prediction_error / calib.number_of_observations
        calib.calibration_factor = 1.0 + (calib.bias / (expected_profit if expected_profit != 0 else 1.0))
        calib.confidence = "High" if calib.number_of_observations > 5 else "Medium"
        
        memory.learning_signal = json.dumps({
            "calibration_factor_updated": calib.calibration_factor,
            "bias_updated": calib.bias
        })
        
    db.commit()

def apply_calibration(db: Session, organization_id: str, action_type: str, raw_expected_profit: float) -> dict:
    calib = db.query(LearningCalibration).filter(
        LearningCalibration.organization_id == organization_id,
        LearningCalibration.action_type == action_type
    ).first()
    
    if not calib or calib.number_of_observations < 1:
        return {
            "calibrated_profit": raw_expected_profit,
            "factor": 1.0,
            "label": "PROJECTED"
        }
        
    calibrated = raw_expected_profit * calib.calibration_factor
    return {
        "calibrated_profit": calibrated,
        "factor": calib.calibration_factor,
        "label": "CALIBRATED PROJECTION"
    }
