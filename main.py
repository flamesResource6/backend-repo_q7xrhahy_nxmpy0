import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from database import create_document, get_documents, db
from schemas import (
    GlucoseReading,
    Meal,
    MedicationLog,
    Activity,
    Reminder,
    InsightsWindow,
)

app = FastAPI(title="Diabetes Health Management API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "Diabetes Health Management API is running"}


@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, "name") else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:  # pragma: no cover
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
    except Exception as e:  # pragma: no cover
        response["database"] = f"❌ Error: {str(e)[:50]}"
    return response


# Helpers

def _collection_name(model_cls: Any) -> str:
    return model_cls.__name__.lower()


def _to_dict(doc: Dict[str, Any]) -> Dict[str, Any]:
    d = dict(doc)
    if d.get("_id") is not None:
        d["_id"] = str(d["_id"])  # stringify ObjectId
    return d


# Generic list helper

def _list_recent(collection: str, limit: int = 20, since: Optional[datetime] = None):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")
    filt: Dict[str, Any] = {}
    if since is not None:
        filt["timestamp"] = {"$gte": since}
    items = (
        db[collection]
        .find(filt)
        .sort("timestamp", -1)
        .limit(limit)
    )
    return [_to_dict(x) for x in items]


# Glucose endpoints
@app.post("/api/glucose")
def create_glucose(reading: GlucoseReading):
    try:
        new_id = create_document(_collection_name(GlucoseReading), reading)
        return {"inserted_id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/glucose")
def list_glucose(limit: int = Query(50, ge=1, le=500), days: Optional[int] = Query(None, ge=1, le=90)):
    since = None
    if days is not None:
        since = datetime.now(timezone.utc) - timedelta(days=days)
    try:
        items = _list_recent(_collection_name(GlucoseReading), limit=limit, since=since)
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Meals
@app.post("/api/meals")
def create_meal(meal: Meal):
    try:
        new_id = create_document(_collection_name(Meal), meal)
        return {"inserted_id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/meals")
def list_meals(limit: int = Query(50, ge=1, le=500), days: Optional[int] = Query(None, ge=1, le=90)):
    since = None
    if days is not None:
        since = datetime.now(timezone.utc) - timedelta(days=days)
    try:
        items = _list_recent(_collection_name(Meal), limit=limit, since=since)
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Medications
@app.post("/api/medications")
def create_med(med: MedicationLog):
    try:
        new_id = create_document(_collection_name(MedicationLog), med)
        return {"inserted_id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/medications")
def list_meds(limit: int = Query(50, ge=1, le=500), days: Optional[int] = Query(None, ge=1, le=90)):
    since = None
    if days is not None:
        since = datetime.now(timezone.utc) - timedelta(days=days)
    try:
        items = _list_recent(_collection_name(MedicationLog), limit=limit, since=since)
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Activities
@app.post("/api/activities")
def create_activity(act: Activity):
    try:
        new_id = create_document(_collection_name(Activity), act)
        return {"inserted_id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/activities")
def list_activities(limit: int = Query(50, ge=1, le=500), days: Optional[int] = Query(None, ge=1, le=90)):
    since = None
    if days is not None:
        since = datetime.now(timezone.utc) - timedelta(days=days)
    try:
        items = _list_recent(_collection_name(Activity), limit=limit, since=since)
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Reminders (simple storage)
@app.post("/api/reminders")
def create_reminder(rem: Reminder):
    try:
        new_id = create_document(_collection_name(Reminder), rem)
        return {"inserted_id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/reminders")
def list_reminders(limit: int = Query(50, ge=1, le=500)):
    try:
        items = _list_recent(_collection_name(Reminder), limit=limit)
        return {"items": items}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Insights & summary
class SummaryResponse(BaseModel):
    days: int
    count_readings: int
    avg_mgdl: Optional[float] = None
    min_mgdl: Optional[float] = None
    max_mgdl: Optional[float] = None
    time_in_range_pct: Optional[float] = None  # 70-180 mg/dL
    recent_readings: List[Dict[str, Any]]


@app.get("/api/summary", response_model=SummaryResponse)
def get_summary(window: InsightsWindow = InsightsWindow()):
    if db is None:
        raise HTTPException(status_code=500, detail="Database not configured")

    since = datetime.now(timezone.utc) - timedelta(days=window.days)
    readings = _list_recent(_collection_name(GlucoseReading), limit=1000, since=since)

    count = len(readings)
    avg = None
    mn = None
    mx = None
    tir = None
    if count > 0:
        values = [float(r.get("value_mgdl", 0)) for r in readings]
        avg = sum(values) / count
        mn = min(values)
        mx = max(values)
        in_range = [v for v in values if 70 <= v <= 180]
        tir = round(len(in_range) / count * 100, 1)

    return SummaryResponse(
        days=window.days,
        count_readings=count,
        avg_mgdl=round(avg, 1) if avg is not None else None,
        min_mgdl=mn,
        max_mgdl=mx,
        time_in_range_pct=tir,
        recent_readings=readings[:10],
    )


# Basic schema exposure for tooling
@app.get("/schema")
def get_schema_definitions():
    return {
        "collections": [
            _collection_name(GlucoseReading),
            _collection_name(Meal),
            _collection_name(MedicationLog),
            _collection_name(Activity),
            _collection_name(Reminder),
        ],
        "notes": "Each class in schemas.py maps to a collection with automatic created_at/updated_at.",
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
