from fastapi import FastAPI, Header, HTTPException
from dotenv import load_dotenv
from datetime import datetime
import httpx
import json
import os

load_dotenv()

FMCSA_API_KEY = os.getenv("FMCSA_API_KEY")
API_KEY = os.getenv("API_KEY")

app = FastAPI()

with open("loads.json") as f:
    loads = json.load(f)


def load_calls():
    if not os.path.exists("calls.json"):
        return []
    with open("calls.json") as f:
        return json.load(f)


def save_calls(calls):
    with open("calls.json", "w") as f:
        json.dump(calls, f, indent=2)


def check_api_key(x_api_key: str = Header(...)):
    if x_api_key != API_KEY:
        raise HTTPException(status_code=401, detail="Unauthorized")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/verify-carrier")
async def verify_carrier(mc_number: str, x_api_key: str = Header(...)):
    check_api_key(x_api_key)

    url = f"https://mobile.fmcsa.dot.gov/qc/services/carriers/docket-number/{mc_number}?webKey={FMCSA_API_KEY}"

    async with httpx.AsyncClient() as client:
        r = await client.get(url, timeout=10)
        data = r.json()

    content = data.get("content", [])
    if not content:
        return {"eligible": False, "reason": "Carrier not found"}

    carrier = content[0].get("carrier", content[0])

    if carrier.get("allowedToOperate") != "Y":
        return {"eligible": False, "reason": "Not authorized to operate"}

    return {
        "eligible": True,
        "carrier_name": carrier.get("legalName", ""),
        "dot_number": carrier.get("dotNumber", ""),
        "equipment_type": "Dry Van",
        "state": carrier.get("phyState", "")
    }


@app.get("/search-loads")
async def search_loads(equipment_type: str, x_api_key: str = Header(...)):
    check_api_key(x_api_key)

    matches = [l for l in loads if l["equipment_type"].lower() == equipment_type.lower()]

    if not matches:
        return {"found": False, "loads": []}

    return {"found": True, "loads": matches[:2]}


@app.post("/save-call")
async def save_call(call_data: dict, x_api_key: str = Header(...)):
    check_api_key(x_api_key)

    call_data["timestamp"] = datetime.utcnow().isoformat()
    calls = load_calls()
    calls.append(call_data)
    save_calls(calls)

    return {"saved": True}


@app.get("/call-stats")
async def call_stats(x_api_key: str = Header(...)):
    check_api_key(x_api_key)

    calls = load_calls()
    total = len(calls)

    if total == 0:
        return {"total_calls": 0}

    outcomes = {}
    sentiments = {}
    rates = []
    loadboard_rates = []

    for call in calls:
        outcome = call.get("call_outcome", "unknown")
        outcomes[outcome] = outcomes.get(outcome, 0) + 1

        sentiment = call.get("sentiment", "unknown")
        sentiments[sentiment] = sentiments.get(sentiment, 0) + 1

        try:
            rates.append(float(call.get("agreed_rate", 0)))
        except:
            pass

        try:
            loadboard_rates.append(float(call.get("loadboard_rate", 0)))
        except:
            pass

    deal_count = outcomes.get("deal_made", 0)
    conversion_rate = round((deal_count / total) * 100, 1) if total > 0 else 0
    avg_rate = round(sum(rates) / len(rates), 0) if rates else 0

    return {
        "total_calls": total,
        "conversion_rate": conversion_rate,
        "avg_agreed_rate": avg_rate,
        "outcomes": outcomes,
        "sentiments": sentiments,
        "recent_calls": calls[-10:][::-1]
    }