# SupportTicket
Tiny full-stack app: paste a support ticket → get {category, urgency, rationale}.

## Acceptance Criteria
- POST /api/triage returns valid JSON {category, urgency, rationale}
- Minimal JS page calls the API and renders the result
- No database, in-memory only

## Run
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn app:app --reload
# open http://127.0.0.1:8000
