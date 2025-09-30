# Gaia — Goddess-Guided Mentorship
# First Place at GirlHacks '25, hosted by Women in Computer Science (WiCS) @ NJIT.


Gaia pairs women on campus with Greek goddess mentors who deliver grounded, citation-backed guidance. Students describe what they need and Gaia matches intent to a persona. Athena for academics, Aphrodite for well-being, Artemis for professional help like jobs and research, Tyche for scholarships and returns actionable next steps with live campus-specific links.

## Highlights

- **Chat-first experience** with goddess avatars, persona tone, and resource citation chips
- **Auth0-secured** login, JWT forwarded to FastAPI for every chat request
- **Rules-first match engine** with configurable personas and optional embedding tie-breaker
- **Intent classification** with keyword heuristics ready for Gemini refinement
- **Azure AI Search integration** plus offline JSON corpus fallback for reliable retrieval
- **MongoDB persistence** of user profiles, intents, and full chat history

## Architecture Overview

| Layer      | Stack & Purpose |
|------------|-----------------|
| Frontend   | React + Vite + Tailwind. Auth0 React SDK for authentication. Chat interface pulls history, posts messages, and renders citations with graceful error states. |
| Backend    | FastAPI with Auth0 JWT guard, Gemini client, SearchService, and MongoDB via Motor. Chat endpoint orchestrates intent prediction, goddess matching, retrieval, and persona prompt building. |
| Data       | Azure AI Search (hybrid keyword/vector). Fallback corpus lives under `data-ingestion/njit_resources.json`. MongoDB Atlas collections: `users`, `chat_histories`. |
| LLM        | Google Gemini (text). Generates persona responses; future hooks ready for intent refinement. |

## Project Layout

```
GirlHacks25/
├── backend/            # FastAPI app and domain services
├── frontend/           # React + Vite SPA
├── data-ingestion/     # Scrapers and Azure Search indexing utilities
├── deployment/         # Azure deployment manifests
└── docs/               # Extended documentation
```

## Getting Started

### 1. Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate   # use source venv/bin/activate on macOS/Linux
pip install -r requirements.txt
cp .env .env.local       # commit-safe copy; edit with your secrets
```

Populate `.env.local` with:

```
AUTH0_DOMAIN=...            # your Auth0 tenant (e.g., dev-xxxx.us.auth0.com)
AUTH0_AUDIENCE=...          # API audience configured in Auth0
MONGODB_URL=...             # MongoDB Atlas connection string
GEMINI_API_KEY=...          # Google Generative AI key
AZURE_SEARCH_ENDPOINT=...   # Azure Cognitive Search endpoint
AZURE_SEARCH_API_KEY=...
AZURE_SEARCH_INDEX_NAME=gaia-resources
CORS_ORIGINS=http://localhost:5173
```

Run the API locally:

```bash
uvicorn main:app --reload --port 8000
```

### 2. Frontend

```bash
cd frontend
npm install
cp .env .env.local
```

Edit `frontend/.env.local`:

```
VITE_AUTH0_DOMAIN=dev-xxx.us.auth0.com
VITE_AUTH0_CLIENT_ID=...
VITE_AUTH0_AUDIENCE=https://gaia.njit/api
VITE_AUTH0_CALLBACK_URL=http://localhost:5173
VITE_API_BASE_URL=http://localhost:8000
VITE_LAST_INDEXED=2025-09-27T09:00:00-04:00
```

Start the SPA:

```bash
npm run dev -- --open
```

### 3. Optional: Data Ingestion

```bash
cd data-ingestion
python setup_index.py           # provisions Azure index
python scrape_njit_resources.py # refreshes fallback corpus / pushes to search
```

## Key API Endpoints

- `GET /api/config/personas` — public persona metadata (id, display name, tagline)
- `GET /api/user` — Auth0-protected user profile create/update
- `POST /api/chat` — main chat endpoint. Body `{ "message": "..." }`
- `GET /api/chat/history` — returns logged messages with citations
- `POST /api/match` — optional quiz mapping, returns `MatchResult`

Chat responses include:

```json
{
  "message": "Athena-style reply",
  "goddess": "athena",
  "intent": "academics",
  "citations": [
    { "id": "resource-1", "title": "NJIT Advising", "url": "https://..." }
  ],
  "timestamp": "2025-09-27T16:28:09Z",
  "trace": { "intent": {...}, "match": {...} }
}
```

## Safety & Demo Guardrails

- Never fabricate events or jobs; all claims must tie to retrieved citations.
- Default to campus wellness contacts for sensitive health or safety conversations.
- No medical, legal, or financial advice beyond official NJIT resources.

## Development Notes

- Frontend build: `npm run build`
- Backend lint/tests: add `pytest` or `ruff` as needed (not bundled yet).
- Configure Auth0 rules to restrict login to `@njit.edu` addresses for demo.
- When deploying, set CORS to the production SPA origin.

## License

MIT License — see [`LICENSE`](LICENSE).
