# Vani GTM Pulse — Four-Agent Assignment Demo

This project adapts the GTM Pulse dashboard into a Vani-specific GTM workflow.

## Four agents
1. **Demand Sensing Agent** — searches for public signals potentially relevant to communication coaching, sales enablement, customer experience, workforce growth, and learning/development.
2. **Customer Profiling Agent** — computes an explainable heuristic ICP score and documents the score breakdown.
3. **Outbound Strategy Agent** — creates a Vani-specific, evidence-aware outreach draft and follow-up suggestions.
4. **Managing Agent** — validates the pipeline result, records missing verification, and routes the draft for human review.

## Important limitations
- Search results are research candidates, not confirmed buying intent. Re-open and verify the source before relying on it.
- A score is a heuristic, not a validated prediction of purchase likelihood.
- Contact/persona verification, CRM duplicate checks, and email suppression checks require connected systems and are not claimed as completed here.
- **No email is sent automatically.** Outreach is draft-only and requires human approval.
- The default prospect is a fictional example. Enter a real target account and verify all facts before presenting account-specific results.

## Requirements
- Python 3.10+
- Node.js 18+
- Context.dev API key for live public web research (optional; pipeline still runs with supplied hypotheses if unavailable)

## Configure the API key
Create `backend/.env` using `backend/.env.example` as a template:

```env
CONTEXT_DEV_API_KEY=put_your_own_key_here
```

Never submit or share `.env`. If a real API key was included in an earlier shared ZIP, revoke/rotate it.

## Run backend (Windows CMD)
```bat
cd backend
py -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt
uvicorn app.main:app --reload
```
API: http://127.0.0.1:8000 · API docs: http://127.0.0.1:8000/docs

## Run frontend (second terminal)
```bat
cd frontend
npm install
npm run dev
```
Open http://127.0.0.1:5173

## Run backend tests
From the project root:
```bat
cd backend
python -m unittest discover -s tests -v
```

## Outputs
- Dashboard displays agent logs, prospect profile, fit score, signals, and an outreach draft.
- API `POST /api/pipeline/run` returns the output of all four agents.
- Existing lead database and analytics endpoints are preserved.

## Suggested demo steps
1. Start the backend and frontend.
2. Enter a real prospect company and a relevant buyer role.
3. Run the pipeline and open the Demand Sensing research candidates.
4. Verify at least one source URL and correct any unsupported claims.
5. Review the ICP score breakdown.
6. Inspect the outreach draft.
7. Show the Managing Agent's pending-human-review decision and explain why no message is sent.
"# Vani-GTM-Pulse-AI-Powered-Multi-Agent-Go-to-Market-Automation-System" 
