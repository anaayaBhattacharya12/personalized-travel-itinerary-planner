# Personalized Travel Itinerary Planner
Skill Wallet Capstone Project 4

## Run locally
```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Features
- Demo mode with no API key
- Optional Gemini or Groq enhancement through session-only API key input
- Destination recommendation based on vibe, budget, interests and season-friendly built-in city profiles
- Day-by-day locality clustering to reduce backtracking
- Itemized local/USD/INR cost estimates and cumulative tracker
- Single-slot activity swaps without regenerating the rest of the plan
- Local JSON trip persistence with history
- One-click offline PDF export with emergency/departure checklist
- No external database required

## Streamlit Community Cloud
Upload `app.py` and `requirements.txt` to a GitHub repository and deploy the repository as a Streamlit app. Demo mode works without secrets.

For production API use, prefer Streamlit Secrets instead of entering a key in the UI. The UI key is intentionally session-only in this capstone implementation.
