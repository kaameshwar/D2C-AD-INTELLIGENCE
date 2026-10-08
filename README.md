# DeciFlow

**"We don't optimize advertising. We optimize the next best business decision."**

DeciFlow is an Autonomous D2C Advertising Intelligence & Profit Optimization Platform built for the DataQuest 3.0 Hackathon. 

## The Problem
Traditional marketing analytics dashboards tell you "what happened." They show ROAS, clicks, and impressions. But a campaign with high ROAS is not necessarily the best business opportunity if the product margin is low or inventory is constrained. There is a disconnect between marketing metrics and core business profitability.

## The Solution: INGEST → DIAGNOSE → DECIDE → EXECUTE → LEARN
DeciFlow bridges the gap by functioning as a complete autonomous optimization engine:
1. **Unifies Data:** Connects Ads, Sales, Inventory, Margins, and Analytics.
2. **Diagnoses & Detects:** AI automatically identifies risks (e.g., creative fatigue) and high-value opportunities.
3. **Optimizes for Profit:** Recommends budget shifts based on an intelligent Opportunity Score (balancing margin, inventory, CVR, and trend).
4. **Simulates & Executes:** Allows marketers to simulate the business impact of a recommendation and execute it seamlessly.
5. **Learns:** Remembers past decisions, comparing expected vs. actual outcomes to continuously improve its model.

## Tech Stack & Architecture
- **Frontend**: Next.js 16, React, TypeScript, Tailwind CSS, shadcn/ui, Recharts.
- **Backend**: Python 3, FastAPI, Pydantic, Uvicorn.
- **Data Engine**: Pandas for analytics and synthetic data generation.
- **AI Abstraction**: Built-in abstraction layer for LLM connectivity with a functional deterministic fallback for guaranteed demo stability.

### Directory Structure
- `/frontend/` - Next.js application containing all UI components and pages.
- `/backend/` - FastAPI backend implementing the intelligence and decision logic.
- `/data/` - Synthetic data generation script and output CSVs simulating a real D2C brand.

## Setup Instructions

### 1. Generate Synthetic Data
```bash
python3 data_generator.py
```
This generates `campaigns.csv`, `products.csv`, `inventory.csv`, etc., with realistic patterns (e.g., declining performance on one campaign, strong margins on another) designed specifically for testing the decision engine.

### 2. Run the Backend (FastAPI)
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt # (or install fastapi uvicorn pydantic pandas)
uvicorn app.main:app --reload --port 8000
```
The API will be available at `http://localhost:8000`.

### 3. Run the Frontend (Next.js)
```bash
cd frontend
npm install
npm run dev
```
The application will be available at `http://localhost:3000`.

## Environment Variables
Create a `.env` file in the root directory:
```env
DATABASE_URL=sqlite:///./deciflow.db
AI_MODE=demo # Set to 'llm' when real API keys are connected
NEXT_PUBLIC_API_URL=http://localhost:8000/api
```

## The Core Demo Flow
To experience the true power of DeciFlow, follow this critical user journey:
1. **Command Center (`/`)**: View high-level business health and spot the "Top Opportunity".
2. **Opportunities (`/ai/opportunities`)**: Review AI-detected opportunities ranked by incremental profit potential, including the evidence and reasoning.
3. **What-If Simulator (`/optimization/simulator`)**: Select the recommended campaign, simulate a budget shift, and view the projected incremental profit and constraint validation.
4. **Action Center (`/actions`)**: Approve the recommended action, moving it from Pending to Approved, and then Execute it.
5. **Learning Center (`/learning`)**: Review past executed decisions and see how the AI's expected profit matched the actual real-world outcome.

## Future Roadmap
- True integration with Meta Ads, Google Ads, and Shopify APIs.
- Full LLM agentic workflow for automated causal analysis.
- Advanced predictive forecasting using deep learning models.
- Expanded portfolio allocation optimizer.
