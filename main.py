import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
from math import radians, sin, cos, sqrt, atan2
from datetime import date

from database import db, create_document, get_documents
from schemas import Place, Itinerary, DayPlan

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "AI Route Itinerary Creator API"}

@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"

    return response

# ----------------------- Utility functions -----------------------

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return R * c

# Simple nearest-neighbor route ordering

def order_by_proximity(points: List[dict]) -> List[dict]:
    if not points:
        return []
    remaining = points.copy()
    ordered = [remaining.pop(0)]
    while remaining:
        last = ordered[-1]
        last_lat, last_lon = last["latitude"], last["longitude"]
        idx, best = 0, None
        for i, p in enumerate(remaining):
            dist = haversine_km(last_lat, last_lon, p["latitude"], p["longitude"])
            if best is None or dist < best:
                best = dist
                idx = i
        ordered.append(remaining.pop(idx))
    return ordered

# ----------------------- Request models -----------------------

class SavePlaceRequest(BaseModel):
    user_id: str
    name: str
    latitude: float
    longitude: float
    category: Optional[str] = None
    notes: Optional[str] = None

class GenerateRequest(BaseModel):
    user_id: str = Field(..., description="User/session id to fetch saved places")
    days: int = Field(1, ge=1, le=14)
    start_date: Optional[date] = None
    title: Optional[str] = None

# ----------------------- Endpoints -----------------------

@app.post("/api/places")
async def save_place(payload: SavePlaceRequest):
    place = Place(**payload.model_dump())
    place_id = create_document("place", place)
    return {"id": place_id}

@app.get("/api/places")
async def list_places(user_id: str):
    docs = get_documents("place", {"user_id": user_id})
    for d in docs:
        d["_id"] = str(d["_id"])  # stringify for JSON
    return docs

@app.post("/api/itineraries/generate")
async def generate_itinerary(req: GenerateRequest):
    # Load saved places for user
    places = get_documents("place", {"user_id": req.user_id})
    if not places:
        raise HTTPException(status_code=400, detail="No saved places found for this user")

    # Greedy order by proximity starting from first saved place
    place_points = [
        {
            "_id": str(p.get("_id")),
            "name": p["name"],
            "latitude": p["latitude"],
            "longitude": p["longitude"],
            "category": p.get("category"),
        }
        for p in places
    ]

    ordered = order_by_proximity(place_points)

    # Split into days as evenly as possible
    per_day = max(1, len(ordered) // req.days + (1 if len(ordered) % req.days else 0))
    days: List[DayPlan] = []
    total_distance = 0.0

    for i in range(req.days):
        day_places = ordered[i*per_day : (i+1)*per_day]
        if not day_places and i >= 1:
            break
        # distance within the day
        for j in range(1, len(day_places)):
            total_distance += haversine_km(
                day_places[j-1]["latitude"], day_places[j-1]["longitude"],
                day_places[j]["latitude"], day_places[j]["longitude"],
            )
        days.append(DayPlan(day=i+1, place_ids=[p["_id"] for p in day_places]))

    itinerary = Itinerary(
        user_id=req.user_id,
        title=req.title or "Smart Itinerary",
        start_date=req.start_date,
        days=days,
        total_distance_km=round(total_distance, 2)
    )

    itinerary_id = create_document("itinerary", itinerary)
    return {"id": itinerary_id, "itinerary": itinerary.model_dump()}

@app.get("/api/itineraries")
async def list_itineraries(user_id: str):
    docs = get_documents("itinerary", {"user_id": user_id})
    for d in docs:
        d["_id"] = str(d["_id"])  # stringify
    return docs

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
