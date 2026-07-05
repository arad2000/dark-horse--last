"""
Dark Horse API v10.5 – Integrated with DarkHorseEngine v14.3
+ Branch Discovery for 9th Grade (هدایت تحصیلی)
+ Uses school_branches.json
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
from pydantic import BaseModel, Field, field_validator
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
try:
    from dark_horse_engine import DarkHorseEngine
    logger.info("✅ DarkHorseEngine imported successfully.")
except ImportError as e:
    logger.critical(f"❌ DarkHorseEngine import failed: {e}")
    DarkHorseEngine = None

try:
    import sanjesh_engine
    calculate_admission_for_major = getattr(sanjesh_engine, 'calculate_admission_for_major', None)
    calculate_all_majors_admission = getattr(sanjesh_engine, 'calculate_all_majors_admission', None)
    if calculate_admission_for_major and calculate_all_majors_admission:
        logger.info("✅ Sanjesh engine imported successfully.")
    else:
        raise ImportError("Functions not found inside sanjesh_engine")
except ImportError as e:
    logger.warning(f"⚠️  Sanjesh engine not available ({e}) – endpoints will return 503")
    calculate_admission_for_major = None
    calculate_all_majors_admission = None


# ---------------------------------------------------------------------------
# Data loaders
# ---------------------------------------------------------------------------
def _load_json_file(filename: str) -> Optional[Dict | List]:
    """Load a JSON file from data/ or project root."""
    base = Path(__file__).parent
    for candidate in (base / "data" / filename, base / filename):
        if candidate.exists():
            try:
                with open(candidate, "r", encoding="utf-8") as fh:
                    logger.info(f"✅ Loaded {filename}")
                    return json.load(fh)
            except Exception as e:
                logger.error(f"❌ Error reading {filename}: {e}")
    logger.warning(f"❌ File not found: {filename}")
    return None


def _load_programs() -> List:
    data = _load_json_file("programs.json")
    if not data:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        if "programs" in data:
            return data["programs"]
        all_progs = []
        for v in data.values():
            if isinstance(v, list):
                all_progs.extend(v)
            elif isinstance(v, dict):
                all_progs.append(v)
        return all_progs
    return []


def _load_universities() -> Dict:
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
    logger.info("🚀 Starting Dark Horse API v10.5 ...")

    # --- Dark Horse Engine (رشته‌های دانشگاهی) ---
    if DarkHorseEngine is not None:
        try:
            app.state.darkhorse = DarkHorseEngine(
                motives_path=os.path.join("data", "micro_motives.json"),
                majors_path=os.path.join("data", "majors_database.json"),
            )
            logger.info("✅ DarkHorseEngine (رشته‌ها) آماده است.")
        except Exception as e:
            logger.error(f"❌ DarkHorseEngine init failed: {e}")
            app.state.darkhorse = None

        # --- Branch Engine (شاخه‌های دبیرستان) ---
        try:
            app.state.branch_engine = DarkHorseEngine(
                motives_path=os.path.join("data", "micro_motives.json"),
                majors_path=os.path.join("data", "school_branches.json"),
            )
            logger.info("✅ BranchEngine (شاخه‌های دبیرستان) آماده است.")
        except Exception as e:
            logger.error(f"❌ BranchEngine init failed: {e}")
            app.state.branch_engine = None
    else:
        app.state.darkhorse = None
        app.state.branch_engine = None

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
    version="10.5",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)


# ---------------------------------------------------------------------------
# Pydantic Models
# ---------------------------------------------------------------------------
class EducationHistory(BaseModel):
    grade_10_city: Optional[str] = None
    grade_11_city: Optional[str] = None
    grade_12_city: Optional[str] = None


class UserProfile(BaseModel):
    gender: str
    province: str
    rank: Optional[int] = Field(default=99999)
    quota: Optional[str] = Field(default="منطقه ۲")
    gpa: Optional[float] = Field(default=0.0)
    final_gpa: Optional[float] = Field(default=0.0)
    traz: Optional[float] = Field(default=0.0)
    diploma_type: str = Field(default="تجربی")
    age: Optional[int] = Field(default=18)
    education_history: Optional[EducationHistory] = None

    @field_validator('rank')
    @classmethod
    def rank_valid(cls, v):
        if v is not None and (v < 1 or v > 300_000):
            raise ValueError('رتبه باید بین ۱ تا ۳۰۰۰۰۰ باشد')
        return v

    @field_validator('gpa', 'final_gpa')
    @classmethod
    def gpa_valid(cls, v):
        if v is not None and (v < 0 or v > 20):
            raise ValueError('معدل باید بین ۰ تا ۲۰ باشد')
        return v


class DarkHorseDiscoverRequest(BaseModel):
    micro_motives: List[str] = Field(default_factory=list)
    sjt_answers: Optional[Dict[str, str]] = Field(default_factory=dict)
    conjoint_choices: Optional[Dict[str, str]] = Field(default_factory=dict)


class SanjeshCalculateRequest(BaseModel):
    major_id: str
    user_profile: UserProfile


class SanjeshDiscoverAllRequest(BaseModel):
    user_profile: UserProfile
    admission_type: str = Field(default="both")


class FeedbackRequest(BaseModel):
    session_id: str = ""
    timestamp: str = ""
    likedCodes: int = 0
    strategyAnswers: int = 0
    valueAnswers: int = 0
    feedback: Dict = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _get_darkhorse(request: Request):
    engine = getattr(request.app.state, 'darkhorse', None)
    if engine is None:
        raise HTTPException(503, detail="موتور اسب سیاه در دسترس نیست")
    return engine


def _get_branch_engine(request: Request):
    engine = getattr(request.app.state, 'branch_engine', None)
    if engine is None:
        raise HTTPException(503, detail="موتور هدایت تحصیلی در دسترس نیست")
    return engine


# ---------------------------------------------------------------------------
# Root & Health
# ---------------------------------------------------------------------------
@app.get("/")
async def root():
    return {"name": "Dark Horse API", "version": "10.5", "status": "online"}


@app.get("/api/health")
async def health_check(request: Request):
    dh_ok = getattr(request.app.state, 'darkhorse', None) is not None
    br_ok = getattr(request.app.state, 'branch_engine', None) is not None
    sj_ok = calculate_admission_for_major is not None

    engine_version = "unknown"
    if dh_ok:
        try:
            dummy = request.app.state.darkhorse.discover_individuality([], {}, {})
            engine_version = dummy.get("method", {}).get("version", "unknown")
        except Exception:
            pass

    return {
        "ok": dh_ok,
        "engines": {
            "darkhorse": dh_ok,
            "branch_engine": br_ok,
            "sanjesh": sj_ok,
        },
        "data_loaded": {
            "programs": len(getattr(request.app.state, 'programs_db', [])),
            "universities": len(getattr(request.app.state, 'universities_db', {})),
        },
        "engine_version": engine_version,
    }


# =========================================================================
# Dark Horse Endpoint (رشته‌های دانشگاهی)
# =========================================================================
@app.post("/api/darkhorse/discover")
async def discover_darkhorse(request: DarkHorseDiscoverRequest, req: Request):
    engine = _get_darkhorse(req)
    try:
        sjt = request.sjt_answers if request.sjt_answers is not None else {}
        conjoint = request.conjoint_choices if request.conjoint_choices is not None else {}
        discovery = await asyncio.to_thread(
            engine.discover_individuality,
            request.micro_motives,
            sjt,
            conjoint,
        )

        recommendations = []
        for item in discovery.get("discovered_majors", []):
            fit = item.get("individuality_fit", {})
            recommendations.append({
                "major_id": item.get("major_id"),
                "major_name_fa": item.get("major_name_fa"),
                "realm_fa": item.get("realm_fa"),
                "fit_score": fit.get("score", 0),
                "fit_level": fit.get("level", ""),
                "prestige_level": fit.get("prestige_level", 2),
                "raw_components": fit.get("raw_components", {}),
                "evidence": fit.get("evidence", {}),
                "personalized_description": fit.get("personalized_description", ""),
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
# Branch Discovery Endpoint (هدایت تحصیلی)
# =========================================================================
@app.post("/api/darkhorse/branch-discovery")
async def branch_discovery(request: DarkHorseDiscoverRequest, req: Request):
    """تحلیل هدایت تحصیلی برای شاخه‌های دبیرستان"""
    engine = _get_branch_engine(req)
    try:
        sjt = request.sjt_answers if request.sjt_answers is not None else {}
        conjoint = request.conjoint_choices if request.conjoint_choices is not None else {}
        discovery = await asyncio.to_thread(
            engine.discover_individuality,
            request.micro_motives,
            sjt,
            conjoint,
        )

        branches = []
        for item in discovery.get("discovered_majors", []):
            fit = item.get("individuality_fit", {})
            branches.append({
                "branch_id": item.get("major_id"),
                "branch_name_fa": item.get("major_name_fa"),
                "group": item.get("realm_fa"),
                "fit_score": fit.get("score", 0),
                "fit_level": fit.get("level", ""),
                "raw_components": fit.get("raw_components", {}),
                "evidence": fit.get("evidence", {}),
                "personalized_description": fit.get("personalized_description", ""),
            })

        branches.sort(key=lambda x: x["fit_score"], reverse=True)
        for i, b in enumerate(branches, 1):
            b["order"] = i

        high = sum(1 for b in branches if b["fit_score"] >= 80)
        med = sum(1 for b in branches if 60 <= b["fit_score"] < 80)

        return {
            "session_id": str(uuid.uuid4()),
            "branch_discovery_result": {
                "total_matches": len(branches),
                "high_fit_branches": high,
                "medium_fit_branches": med,
                "branches": branches,
                "basis": "بر اساس ریزانگیزه‌ها، ۲۵ سوال راهبردی و ۱۵ سوال ارزشی",
                "method": discovery.get("method", {}),
                "summary": discovery.get("summary", {}),
            },
        }

    except HTTPException:
        raise
    except Exception:
        logger.error("Error in /api/darkhorse/branch-discovery", exc_info=True)
        raise HTTPException(500, detail="خطای داخلی سرور")


# =========================================================================
# Sanjesh Endpoints
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
        {},
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
        {},
        user_dict,
        request.admission_type,
    )
    return {
        "session_id": str(uuid.uuid4()),
        "sanjesh_result": result,
    }


# =========================================================================
# Feedback Endpoints
# =========================================================================
@app.post("/api/feedback/submit")
async def submit_feedback(fb: FeedbackRequest, req: Request):
    try:
        feedback_file = os.path.join("data", "feedbacks.json")
        existing = []
        if os.path.exists(feedback_file):
            with open(feedback_file, "r", encoding="utf-8") as f:
                existing = json.load(f)
        existing.append(fb.model_dump())
        with open(feedback_file, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        logger.info(f"✅ Feedback saved (total: {len(existing)})")
        return {"ok": True, "total": len(existing)}
    except Exception as e:
        logger.error(f"Error saving feedback: {e}")
        raise HTTPException(500, detail="خطا در ثبت بازخورد")


@app.get("/api/feedback/all")
async def get_all_feedback(req: Request):
    try:
        feedback_file = os.path.join("data", "feedbacks.json")
        if not os.path.exists(feedback_file):
            return {"feedbacks": [], "total": 0}
        with open(feedback_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        return {"feedbacks": data, "total": len(data)}
    except Exception as e:
        logger.error(f"Error reading feedbacks: {e}")
        raise HTTPException(500, detail="خطا در خواندن بازخوردها")


# ---------------------------------------------------------------------------
# Global exception handler
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    error_id = str(uuid.uuid4())
    logger.error(f"[{error_id}] Unhandled error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "message": "خطای سرور - دوباره تلاش کنید",
            "error_id": error_id,
        },
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=int(os.getenv("PORT", "8000")), reload=False)
