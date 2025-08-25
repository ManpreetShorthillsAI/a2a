## Weather Agent (Google ADK)

Minimal single-agent, single-tool example using Google ADK.

### Setup

1. Python 3.10+
2. Install deps:

```
pip install -r requirements.txt
```

3. Create `.env` in repository root:

```
GOOGLE_GENAI_USE_VERTEXAI=False
GOOGLE_API_KEY=YOUR_GOOGLE_API_KEY
```

Get the key from Google AI Studio.

### Run

- Dev UI:

```
adk web
```

Open `http://localhost:8000`, select `weather_agent`, and ask e.g. "Weather in London?".

- CLI:

```
adk run weather_agent
```

### Notes

- Tool `get_weather` calls `wttr.in` (no extra API key) for a concise summary.
- For production, swap in a proper weather API and add error handling/rate limits as needed.

