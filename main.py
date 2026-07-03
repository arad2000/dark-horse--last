"""
Dark Horse API v10.1 - Integrated with DarkHorseEngine v12.0
موتور کشف فردیت (جدید) + موتور سنجش (حفظ شده)
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

# Logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("darkhorse_api_v10")

# Import Engines
try:
    from sanjesh_engine import (
        calculate_admission_for_major,
        calculate_all_majors_admission,
    )
except ImportError as e:
    logger.error(f"Sanjesh import error: {e}")
    calculate_admission_for_major = None
    calculate_all_majors_admission = None

# Import New DarkHorseEngine
try:
    from dark_horse_engine import DarkHorseEngine
except ImportError as e:
    logger.error(f"DarkHorseEngine import error: {e}")
    DarkHorseEngine = None


# =========================================================================
# Lifespan: Startup and Shutdown
# =========================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """راه‌اندازی و خاموش‌سازی سرویس"""
    logger.info("Starting Dark Horse API v10.0...")
    
    # ایجاد وهله از موتور اسب سیاه
    if DarkHorseEngine is not None:
        try:
            app.state.darkhorse = DarkHorseEngine(
                motives_path=os.path.join("data", "micro_motives.json"),
                majors_path=os.path.join("data", "majors_database.json"),
            )
            logger.info("✅ DarkHorseEngine v12.0 initialized")
        except Exception as e:
            logger.error(f"Failed to init DarkHorseEngine: {e}")
            app.state.darkhorse = None
    else:
        app.state.darkhorse = None
    
    # بارگذاری دیتابیس سنجش (برنامه‌ها و دانشگاه‌ها)
    app.state.programs_db = _load_programs()
    app.state.universities_db = _load_universities()
    
    logger.info("Dark Horse API v10.0 started successfully")
    yield
    logger.info("Shutting down...")


def _load_programs() -> List:
    """بارگذاری فایل برنامه‌ها"""
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
    """بارگذاری فایل دانشگاه‌ها"""
    data = _load_json_file("universities_top50.json")
    if not data:
        return {}
    if isinstance(data, list):
        return {u.get("university_id", ""): u for u in data if u.get("university_id")}
    return data


def _load_json_file(filename: str) -> Optional[Dict]:
    """لود کردن یک فایل JSON از پوشه data/ یا ریشه"""
    try:
        base_path = Path(__file__).parent
        for path in [base_path / "data" / filename, base_path / filename]:
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    logger.info(f"✅ Loaded {filename}")
                    return json.load(f)
        logger.warning(f"❌ File not found: {filename}")
        return None
    except Exception as e:
        logger.error(f"Error loading {filename}: {e}")
        return None


# =========================================================================
# FastAPI App
# =========================================================================

app = FastAPI(
    title="Dark Horse API",
    description="موتور کشف فردیت و انتخاب رشته هوشمند",
    version="10.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================================
# Pydantic Models
# =========================================================================

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
        if v is not None and (v < 1 or v > 300000):
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


# =========================================================================
# Helper Functions
# =========================================================================

def get_darkhorse_engine(request: Request):
    """بازگرداندن وهله موتور اسب سیاه"""
    engine = getattr(request.app.state, 'darkhorse', None)
    if engine is None:
        raise HTTPException(status_code=503, detail="موتور اسب سیاه در دسترس نیست")
    return engine


def get_programs_db(request: Request):
    return getattr(request.app.state, 'programs_db', [])


def get_universities_db(request: Request):
    return getattr(request.app.state, 'universities_db', {})


# =========================================================================
# Endpoints
# =========================================================================

@app.get("/")
async def root():
    return {"name": "Dark Horse API", "version": "10.0", "status": "online"}


@app.get("/api/health")
async def health_check(request: Request):
    dh_ok = getattr(request.app.state, 'darkhorse', None) is not None
    sj_ok = calculate_admission_for_major is not None
    data_ok = len(get_programs_db(request)) > 0

    return {
        "ok": dh_ok and sj_ok and data_ok,
        "engines": {
            "darkhorse": dh_ok,
            "sanjesh": sj_ok,
        },
        "data_loaded": {
            "programs": len(get_programs_db(request)),
            "universities": len(get_universities_db(request)),
        },
        "engine_version": "12.0 Final",
    }


# ═══════════════════════════════════════════════════════════════════════
# ENDPOINT اصلی: کشف رشته‌های متناسب با فردیت
# ═══════════════════════════════════════════════════════════════════════

@app.post("/api/darkhorse/discover")
async def discover_darkhorse(request: DarkHorseDiscoverRequest, req: Request):
    """کشف رشته‌های متناسب با فردیت کاربر"""
    engine = get_darkhorse_engine(req)

    try:
        # فراخوانی موتور جدید (در thread جداگانه)
        discovery = await asyncio.to_thread(
            engine.discover_individuality,
            request.micro_motives,
            request.sjt_answers or {},
            request.conjoint_choices or {},
        )

        # پردازش خروجی برای فرانت‌اند
        recommendations = []
        for item in discovery.get("discovered_majors", []):
            fit_data = item.get("individuality_fit", {})
            score = fit_data.get("score", 0)

            if score < 30:
                continue

            recommendations.append({
                "major_id": item.get("major_id"),
                "major_name_fa": item.get("major_name_fa"),
                "realm_fa": item.get("realm_fa"),
                "fit_score": score,
                "fit_level": fit_data.get("level", ""),
                "prestige_level": fit_data.get("prestige_level", 2),
                "raw_components": fit_data.get("raw_components", {}),
                "evidence": fit_data.get("evidence", {}),
            })

        # مرتب‌سازی نهایی
        recommendations.sort(key=lambda x: x["fit_score"], reverse=True)
        for i, rec in enumerate(recommendations, 1):
            rec["order"] = i

        high_fit = sum(1 for r in recommendations if r["fit_score"] >= 80)
        medium_fit = sum(1 for r in recommendations if 60 <= r["fit_score"] < 80)

        return {
            "session_id": str(uuid.uuid4()),
            "discovery_result": {
                "total_matches": len(recommendations),
                "high_fit_majors": high_fit,
                "medium_fit_majors": medium_fit,
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
        logger.error("Error in darkhorse discover", exc_info=True)
        raise HTTPException(status_code=500, detail="خطا در پردازش درخواست")


# ═══════════════════════════════════════════════════════════════════════
# ENDPOINT های سنجش (بدون تغییر)
# ═══════════════════════════════════════════════════════════════════════

@app.post("/api/sanjesh/calculate")
async def calculate_admission(request: SanjeshCalculateRequest, req: Request):
    if calculate_admission_for_major is None:
        raise HTTPException(status_code=503)

    try:
        programs_db = get_programs_db(req)
        if not programs_db:
            raise HTTPException(status_code=500)

        user_dict = request.user_profile.model_dump()
        result = await asyncio.to_thread(
            calculate_admission_for_major,
            programs_db,
            {},
            request.major_id,
            user_dict,
        )

        if "error" in result:
            raise HTTPException(status_code=400, detail=result.get("error"))

        return {
            "session_id": str(uuid.uuid4()),
            "admission_result": result,
        }

    except HTTPException:
        raise
    except Exception:
        logger.error("Error in calculate_admission", exc_info=True)
        raise HTTPException(status_code=500)


@app.post("/api/sanjesh/discover-all")
async def discover_all_majors(request: SanjeshDiscoverAllRequest, req: Request):
    if calculate_all_majors_admission is None:
        raise HTTPException(status_code=503)

    try:
        programs_db = get_programs_db(req)
        if not programs_db:
            raise HTTPException(status_code=500)

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

    except Exception:
        logger.error("Error in discover-all", exc_info=True)
        raise HTTPException(status_code=500)


# =========================================================================
# Global Exception Handler
# =========================================================================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "خطای سرور - دوباره تلاش کنید"},
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)
