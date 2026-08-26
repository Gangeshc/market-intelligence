# Angel One Live Feed — Market Intelligence

This is the live-feed backend connector for the Market Intelligence PWA.

## Current architecture
Android/Browser → local/hosted web UI → FastAPI backend → Angel One SmartAPI WebSocket → price ticks → anomaly engine.

Angel One SmartAPI supports live market-data WebSocket streaming. The official Python SDK includes SmartWebSocketV2.

## Before running
1. Create/enable SmartAPI access in Angel One.
2. Put your credentials in `.env` based on `.env.example`.
3. Register the required static IP if Angel One requires it for your account/API configuration.
4. Fill `TOKENS` in `main.py` with the NSE instrument tokens you want to scan.
5. Install Python dependencies and run:
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   uvicorn main:app --host 127.0.0.1 --port 8000

## Security
Never put API keys, passwords, TOTP secrets or access tokens in the browser or commit `.env` to GitHub.

## Important
This connector does NOT place trades. The anomaly score is a starter heuristic and must be historically validated before use with real money.

News/announcement matching is intentionally a separate layer. It should use an authorized announcement/news source rather than relying on unofficial scraping.
