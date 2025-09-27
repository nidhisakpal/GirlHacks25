# Gaia — Goddess-Guided Mentorship

A women-focused mentorship web app for NJIT students. Students describe what they need; Gaia matches them to a Greek goddess persona and delivers grounded guidance with live links to NJIT events, jobs, and resources.

## Features

- **Goddess Personas**: Athena (academics), Aphrodite (well-being), Hera (career)
- **Smart Matching**: Rules-based keyword mapping with embeddings tie-breaker
- **Intent Classification**: AI-powered understanding of user needs
- **Resource Retrieval**: Azure AI Search integration for NJIT resources
- **Chat Interface**: Goddess-voiced responses with citation chips
- **Auth0 Integration**: Secure authentication for NJIT students

## Tech Stack

### Frontend
- React + Vite + Tailwind CSS
- Auth0 React SDK
- Chat-first UI with goddess avatars

### Backend
- FastAPI (Python)
- Auth0 JWT validation
- Gemini AI for persona responses and classification
- Azure AI Search for resource retrieval
- MongoDB Atlas for data storage

### Data Sources
- Highlander Hub events
- Handshake job listings
- ScholarshipUniverse summaries
- NJIT support pages (tutoring, wellness, advising)

## Project Structure

```
gaia-mentorship/
├── frontend/                 # React + Vite + Tailwind
├── backend/                  # FastAPI application
├── data-ingestion/           # Web scraping and indexing
├── deployment/               # Azure deployment configs
├── docs/                     # Documentation
└── scripts/                  # Utility scripts
```

## Quick Start

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd gaia-mentorship
   ```

2. **Backend setup**:
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # or `venv\Scripts\activate` on Windows
   pip install -r requirements.txt
   cp .env.example .env
   # Configure your .env file with API keys
   ```

3. **Frontend setup**:
   ```bash
   cd frontend
   npm install
   cp .env.example .env.local
   # Configure your .env.local file
   ```

4. **Data ingestion**:
   ```bash
   cd data-ingestion
   python setup_index.py
   python scrape_njit_resources.py
   ```

5. **Run development servers**:
   ```bash
   # Terminal 1 - Backend
   cd backend && uvicorn main:app --reload

   # Terminal 2 - Frontend
   cd frontend && npm run dev
   ```

## Environment Variables

See `.env.example` files in each directory for required configuration.

## Deployment

- **Frontend**: Azure Static Web Apps
- **Backend**: Azure App Service
- **Search**: Azure AI Search (managed)
- **Database**: MongoDB Atlas

## Safety & Guardrails

- Never fabricate events; all answers cite retrieved items
- Sensitive topics redirect to official campus resources
- No medical or legal advice provided
- All responses grounded in real NJIT resources

## Contributing

This is a hackathon project for GirlHacks25 at NJIT. See `docs/CONTRIBUTING.md` for guidelines.

## License

MIT License - see `LICENSE` file for details.