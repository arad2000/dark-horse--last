"""
Dark Horse API v10.2 – Dual Engine Integration
موتور کشف فردیت (اسب سیاه v12) + موتور سنجش (Sanjesh)
"""

import json
import logging
import os
import uuid
from pathlib import Path
from typing import Dict, List, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, validator
import asyncio

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("darkhorse_api_v10")

# ---------------------------------------------------------------------------
# Engine imports
# ---------------------------------------------------------------------------
# 1. Dark Horse Engine (v12)
try:
    from dark_horse_engine import DarkHorseEngine
    logger.info("✅ DarkHorseEngine imported")
except ImportError as e:
    logger.critical(f"❌ DarkHorseEngine import failed: {e}")
    DarkHorseEngine = None

# 2. Sanjesh Engine
try:
    from sanjesh_engine import (
        calculate_admission_for_major,
        calculate_all_majors_admission,
    )
    logger.info("✅ Sanjesh engine imported")
except ImportError as e:
    logger.warning(f"⚠️  Sanjesh engine not available ({e}) – endpoints will return 503")
    calculate_admission_for_major = None
    calculate_all_majors_admission = None


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------
def _load_json_file(filename: str) -> Optional[Dict | List]:
    """Load a JSON file from data/ or project root."""
    try:
        base = Path(__file__).parent
        for candidate in (base / "data" / filename, base / filename):
            if candidate.exists():
                with open(candidate, "r", encoding="utf-8") as fh:
                    logger.info(f"✅ Loaded {filename}")
                    return json.load(fh)
        logger.warning(f"❌ File not found: {filename}")
    except Exception as e:
        logger.error(f"Error loading {filename}: {e}")
    return None


def _load_programs() -> List:
    """Load programs.json (list of programs)."""
    data = _load_json_file("programs.json")
    if not data:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "programs" in data:
            return data["programs"]
        # flatten dict of dicts
        all_progs = []
        for v in data.values():
            if isinstance(v, list):
                all_progs.extend(v)
            elif isinstance(v, dict):
                all_progs.append(v)
        return all_progs
    return []


def _load_universities() -> Dict:
    """Load universities_top50.json (university_id → university)."""
    data = _load_json_file("universities_top50.json")
    if not data:
        return {}
    if isinstance(data, list):
        return {str(u.get("university_id", "")): u for u in data if u.get("university_id")}
    return data


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting Dark Horse API v10.2 ...")

    # --- Dark Horse Engine ---
    if DarkHorseEngine is not None:
        try:
            app.state.darkhorse = DarkHorseEngine(
                motives_path=os.path.join("data", "micro_motives.json"),
                majors_path=os.path.join("data", "majors_database.json"),
            )
            logger.info("✅ DarkHorseEngine ready")
        except Exception as e:
            logger.error(f"❌ DarkHorseEngine init failed: {e}")
            app.state.darkhorse = None
    else:
        app.state.darkhorse = None

    # --- Sanjesh data ---
    app.state.programs_db = _load_programs()
    app.state.universities_db = _load_universities()
    logger.info(
        f"📦 Programs: {len(app.state.programs_db)}, "
        f"Universities: {len(app.state.universities_db)}"
    )

    yield
    logger.info("🛑 Shutting down ...")


# ---------------------------------------------------------------------------
# FastAPI application
# ---------------------------------------------------------------------------
app = FastAPI(
    title="Dark Horse API",
    description="موتور کشف فردیت و انتخاب رشته هوشمند",
    version="10.2",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Pydantic models (unchanged from original)
# ---------------------------------------------------------------------------
class EducationHistory(BaseModel):
    grade_10_city: Optional[str] = None
    grade_11_city: Optional[str] = None
    grade_12_city: Optional[str] = None


class UserProfile(BaseModel):
    gender: str = Field(...)
    province: str = Field(...)
    rank: Optional[int] = Field(99999)
    quota: Optional[str] = Field(None)
    gpa: Optional[float] = Field(0)
    final_gpa: Optional[float] = Field(0)
    traz: Optional[float] = Field(0)
    diploma_type: str = Field("ریاضی")
    age: Optional[int] = Field(None)
    education_history: Optional[EducationHistory] = None

    @validator('rank')
    def rank_valid(cls, v):
        if v is not None and (v < 1 or v > 300_000):
            raise ValueError('رتبه باید بین ۱ تا ۳۰۰۰۰۰ باشد')
        return v

    @validator('gpa', 'final_gpa')
    def gpa_valid(cls, v):
        if v is not None and (v < 0 or v > 20):
            raise ValueError('معدل باید بین ۰ تا ۲۰ باشد')
        return v


class DarkHorseDiscoverRequest(BaseModel):
    micro_motives: List[str] = Field(default=[])
    sjt_answers: Optional[Dict[str, str]] = Field(default=None)
    conjoint_choices: Optional[Dict[str, str]] = Field(default=None)
    reality: Optional[Dict] = Field(default=None)


class SanjeshCalculateRequest(BaseModel):
    major_id: str
    user_profile: UserProfile


class SanjeshDiscoverAllRequest(BaseModel):
    user_profile: UserProfile
    admission_type: str = Field("both")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_darkhorse(request: Request):
    engine = getattr(request.app.state, 'darkhorse', None)
    if engine is None:
        raise HTTPException(503, detail="موتور اسب سیاه در دسترس نیست")
    return engine


# ---------------------------------------------------------------------------
# Root & Health
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {"name": "Dark Horse API", "version": "10.2", "status": "online"}


@app.get("/api/health")
async def health_check(request: Request):
    dh_ok = getattr(request.app.state, 'darkhorse', None) is not None
    sj_ok = calculate_admission_for_major is not None
    return {
        "ok": dh_ok,  # overall OK only if darkhorse is up (sanjesh may be absent)
        "engines": {
            "darkhorse": dh_ok,
            "sanjesh": sj_ok,
        },
        "data_loaded": {
            "programs": len(getattr(request.app.state, 'programs_db', [])),
            "universities": len(getattr(request.app.state, 'universities_db', {})),
        },
        "engine_version": "12.0 Final",
    }


# =========================================================================
# Dark Horse Endpoint
# =========================================================================
@app.post("/api/darkhorse/discover")
async def discover_darkhorse(request: DarkHorseDiscoverRequest, req: Request):
    engine = _get_darkhorse(req)

    try:
        discovery = await asyncio.to_thread(
            engine.discover_individuality,
            request.micro_motives,
            request.sjt_answers or {},
            request.conjoint_choices or {},
        )

        recommendations = []
        for item in discovery.get("discovered_majors", []):
            fit = item.get("individuality_fit", {})
            score = fit.get("score", 0)
            if score < 30:
                continue
            recommendations.append({
                "major_id": item.get("major_id"),
                "major_name_fa": item.get("major_name_fa"),
                "realm_fa": item.get("realm_fa"),
                "fit_score": score,
                "fit_level": fit.get("level", ""),
                "prestige_level": fit.get("prestige_level", 2),
                "raw_components": fit.get("raw_components", {}),
                "evidence": fit.get("evidence", {}),
            })

        recommendations.sort(key=lambda x: x["fit_score"], reverse=True)
        for i, rec in enumerate(recommendations, 1):
            rec["order"] = i

        high = sum(1 for r in recommendations if r["fit_score"] >= 80)
        med = sum(1 for r in recommendations if 60 <= r["fit_score"] < 80)

        return {
            "session_id": str(uuid.uuid4()),
            "discovery_result": {
                "total_matches": len(recommendations),
                "high_fit_majors": high,
                "medium_fit_majors": med,
                "recommendations": recommendations,
                "basis": "بر اساس ریزانگیزه‌ها، ۲۵ سوال راهبردی و ۱۵ سوال ارزشی",
                "method": discovery.get("method", {}),
                "summary": discovery.get("summary", {}),
                "next_step": discovery.get("next_step", "اطلاعات سنجش خود را وارد کنید"),
            },
        }

    except HTTPException:
        raise
    except Exception:
        logger.error("Error in /api/darkhorse/discover", exc_info=True)
        raise HTTPException(500, detail="خطای داخلی سرور")


# =========================================================================
# Sanjesh Endpoints (return 503 if engine not loaded)
# =========================================================================
@app.post("/api/sanjesh/calculate")
async def calculate_admission(request: SanjeshCalculateRequest, req: Request):
    if calculate_admission_for_major is None:
        raise HTTPException(503, detail="موتور سنجش در دسترس نیست")
    programs_db = getattr(req.app.state, 'programs_db', [])
    if not programs_db:
        raise HTTPException(500, detail="داده‌های سنجش بارگذاری نشده‌اند")

    user_dict = request.user_profile.model_dump()
    result = await asyncio.to_thread(
        calculate_admission_for_major,
        programs_db,
        {},                                     # majors_db not needed here
        request.major_id,
        user_dict,
    )
    if "error" in result:
        raise HTTPException(400, detail=result["error"])

    return {
        "session_id": str(uuid.uuid4()),
        "admission_result": result,
    }


@app.post("/api/sanjesh/discover-all")
async def discover_all_majors(request: SanjeshDiscoverAllRequest, req: Request):
    if calculate_all_majors_admission is None:
        raise HTTPException(503, detail="موتور سنجش در دسترس نیست")
    programs_db = getattr(req.app.state, 'programs_db', [])
    if not programs_db:
        raise HTTPException(500, detail="داده‌های سنجش بارگذاری نشده‌اند")

    user_dict = request.user_profile.model_dump()
    result = await asyncio.to_thread(
        calculate_all_majors_admission,
        programs_db,
        {},                                     # majors_db not needed
        user_dict,
        request.admission_type,
    )
    return {
        "session_id": str(uuid.uuid4()),
        "sanjesh_result": result,
    }


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "خطای سرور - دوباره تلاش کنید"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
