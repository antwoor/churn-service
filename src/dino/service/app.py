import time
import uuid
from contextlib import asynccontextmanager

import joblib
import pandas as pd
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

from dino import db
from dino.config import settings


class Features(BaseModel):
    model_config = {"extra": "forbid"}

    dino_type: str = Field(min_length=1, description="Тип динозавра, например large theropod или sauropod")
    length_m: float | None = Field(default=None, gt=0, le=50, description="Длина в метрах; в исходных данных бывает пропуск")
    period: str = Field(min_length=1, description="Геологический период, например Late Cretaceous")
    lived_in: str | None = Field(default=None, description="Регион находки; в данных бывает пропуск")


class Prediction(BaseModel):
    score: float
    carnivorous: bool
    model_version: str
    request_id: str
    latency_ms: float


@asynccontextmanager
async def lifespan(app: FastAPI):
    bundle = joblib.load(settings.model_path)
    app.state.pipeline = bundle["pipeline"]
    app.state.meta = bundle["metadata"]
    app.state.version = bundle["metadata"]["model_version"]

    db.init()
    yield
    app.state.pipeline = None


app = FastAPI(title="dino-service", version="1.0", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "model_version": getattr(app.state, "version", "unknown")}


@app.get("/ready")
def ready():
    if getattr(app.state, "pipeline", None) is None:
        raise HTTPException(status_code=503, detail="Model not loaded")

    return {"status": "ready"}


@app.post("/v1/predict")
def predict(x: Features, bg: BackgroundTasks) -> Prediction:
    t0 = time.perf_counter()
    request_id = str(uuid.uuid4())
    payload = x.model_dump()
    frame = pd.DataFrame([payload]).reindex(columns=app.state.meta["features"])

    score = float(app.state.pipeline.predict_proba(frame)[0, 1])

    latency_ms = round((time.perf_counter() - t0) * 1000, 2)
    status_code = 200

    bg.add_task(db.save_prediction, request_id, payload, score, app.state.version, latency_ms, status_code)

    carnivorous = score >= app.state.meta["threshold"]

    return Prediction(
        score=score,
        carnivorous=carnivorous,
        model_version=app.state.version,
        request_id=request_id,
        latency_ms=latency_ms,
    )
