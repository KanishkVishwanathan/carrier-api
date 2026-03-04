from fastapi import FastAPI, Header, HTTPException
from dotenv import load_dotenv
import httpx
import json
import os

load_dotenv()

FMCSA_API_KEY = os.getenv("FMCSA_API_KEY")
API_KEY = os.getenv("API_KEY")

app = FastAPI()

with open("loads.json") as f:
    loads = json.load(f)


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