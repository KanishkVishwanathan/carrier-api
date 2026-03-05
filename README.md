# carrier-api

This is the backend API for an inbound carrier sales automation I built on HappyRobot. The idea is simple: carriers call in, the AI agent verifies them against FMCSA, finds them a load, negotiates the rate, and transfers to a sales rep if they agree.

Built for the HappyRobot FDE Technical Challenge.

## What it does

Verifies carriers in real time using the FMCSA API, serves available loads from a JSON file based on equipment type, saves call data after each conversation, and exposes metrics for a custom operations dashboard.

## Tech

Python and FastAPI for the API, deployed on Railway, containerized with Docker. HappyRobot calls this API mid-conversation using webhook tool nodes.

## Endpoints

| Method | Endpoint | What it does |
|--------|----------|-------------|
| GET | `/health` | Check if the server is up |
| GET | `/verify-carrier` | Verify a carrier by MC number via FMCSA |
| GET | `/search-loads` | Find loads by equipment type |
| POST | `/save-call` | Save call data when a conversation ends |
| GET | `/call-stats` | Get metrics for the dashboard |

Every endpoint requires an `x-api-key` header. Returns 401 if it's missing or wrong.

## Running locally

Clone the repo and set up a virtual environment:

```bash
git clone https://github.com/KanishkVishwanathan/carrier-api.git
cd carrier-api
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file with your keys:

```
FMCSA_API_KEY=your_fmcsa_key
API_KEY=your_chosen_api_key
```

Start the server:

```bash
uvicorn main:app --reload
```

Go to `http://127.0.0.1:8000/docs` to see and test all the endpoints interactively.

## Running with Docker

```bash
docker build -t carrier-api .
docker run -p 8080:8080 -e FMCSA_API_KEY=your_key -e API_KEY=your_api_key carrier-api
```

## Deployment

Live at `https://carrier-api-production-bde1.up.railway.app`

To reproduce it yourself:
1. Fork this repo
2. Create a new project on railway.app and connect your fork
3. Add environment variables in the Variables tab: `FMCSA_API_KEY`, `API_KEY`, `PORT=8080`
4. Set the start command to `uvicorn main:app --host 0.0.0.0 --port 8080`
5. Generate a public domain under Settings > Networking

Railway auto-deploys every time you push to master.

## Security

API key authentication on every endpoint, keys stored as environment variables, HTTPS enforced by Railway, `.env` excluded from git.

## File structure

```
carrier-api/
├── main.py           
├── loads.json        
├── calls.json        
├── requirements.txt  
├── Dockerfile        
└── .env              
```