# Support Ticket Triage

A tiny full-stack web app that instantly categorizes and prioritizes support tickets using deterministic heuristics.

## Features

- **Instant Triage**: Paste any support ticket text and get immediate classification
- **Smart Categorization**: Automatically detects billing, bug, feature, or other issues
- **Priority Assessment**: Determines urgency (low, medium, high) based on content analysis
- **Clear Rationale**: Provides human-readable explanations for each classification
- **Beautiful UI**: Modern, responsive interface with smooth animations
- **Example Tickets**: Click-to-try sample tickets for testing

## How It Works

The app uses keyword-based heuristics to analyze ticket content:

- **Category Detection**: Counts relevant keywords to determine if it's billing, bug, feature, or other
- **Urgency Assessment**: Evaluates impact keywords and category-specific rules
- **Rationale Generation**: Creates human-readable explanations for classifications

## API Endpoint

```
POST /api/triage
Content-Type: application/json

{
  "text": "Your support ticket text here"
}

Response:
{
  "category": "billing|bug|feature|other",
  "urgency": "low|medium|high", 
  "rationale": "Human-readable explanation"
}
```

## Example Results

- **"I was charged twice after updating my card"** → `billing`, `high` urgency
- **"The app keeps crashing when I try to upload photos"** → `bug`, `high` urgency  
- **"It would be great if you could add dark mode"** → `feature`, `low` urgency

## Run Locally

```bash
# Setup virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start the server
uvicorn app:app --reload

# Open http://127.0.0.1:8000 in your browser
```

## Tech Stack

- **Backend**: FastAPI with Pydantic models
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Styling**: Modern CSS with gradients, animations, and responsive design
- **No Database**: All processing done in-memory with deterministic rules
