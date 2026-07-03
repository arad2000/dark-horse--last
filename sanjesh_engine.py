"""
Sanjesh Engine v9.3 – Updated for v5.3.1 data
- Added "intl" to COURSE_TYPE_MULTIPLIER
"""
import logging
from typing import Dict, List, Optional, Tuple, Any

logger = logging.getLogger("sanjesh_engine")

# ====================== Constants ======================
ADMISSION_DISPLAY_THRESHOLD = 50
PROBABILITY_MAX = 99.0
PROBABILITY_HIGH = 85.0
PROBABILITY_MEDIUM = 70.0
PROBABILITY_LOW = 50.0
RANK_RATIO_HIGH = 0.85
RANK_RATIO_MEDIUM = 1.0
RANK_RATIO_LOW = 1.15
SCORE_EXCELLENT = 1.10
SCORE_GOOD = 1.0
SCORE_ACCEPTABLE = 0.90
ISARGARAN_70_RULE = 0.70
ISARGARAN_85_RULE = 0.85

GPA_IMPACT_BY_YEAR = {
    1402: {"konkur": 0.60, "gpa": 0.40},
    1403: {"konkur": 0.50, "gpa": 0.50},
    1404: {"konkur": 0.40, "gpa": 0.60},
    1405: {"konkur": 0.40, "gpa": 0.60},
}

HISTORICAL_WEIGHTS = {"1404": 0.50, "1403": 0.30, "1402": 0.15, "1401": 0.05}

COURSE_TYPE_MULTIPLIER = {
    "roozaneh": 1.00,
    "shabaneh": 1.15,
    "nobat_dovom": 1.15,
    "intl": 1.00,            # جدید: کات‌آف از قبل در تولید افزایش یافته
    "pardis": 1.40,
    "majazi": 1.50,
    "azad": 1.60,
    "payam_noor": 2.00,
    "gheir_entefaei": 1.70,
    "mazad": 1.80,
}

SAVABEGH_QUOTA_BOOST = {
    "isargaran_25": 1.30, "shahid": 1.30, "isargaran_5": 1.15,
    "zone_3": 1.10, "zone_2": 1.00, "zone_1": 0.95,
}

DEFAULT_QUOTA = "zone_2"
METHOD_KONKUR = ("با آزمون", "konkur", "farhangian", "shahed", "boursie")
METHOD_SAVABEGH = ("سوابق تحصیلی", "savabegh")
MAJOR_GROUP_TO_DIPLOMAS = {
    "ریاضی-فیزیک": ["ریاضی", "فنی"],
    "علوم تجربی": ["تجربی"],
    "علوم انسانی": ["انسانی", "علوم و معارف"],
    "هنر و معماری": ["هنر", "ریاضی", "تجربی", "انسانی"],
    "زبان‌های خارجی": ["انسانی", "علوم و معارف", "تجربی", "ریاضی"],
}

POLES = {
    "قطب ۱": {"تهران", "البرز", "قم", "قزوین", "سمنان", "مرکزی"},
    "قطب ۲": {"اصفهان", "یزد", "چهارمحال و بختیاری"},
    "قطب ۳": {"فارس", "بوشهر", "هرمزگان", "کهگیلویه و بویراحمد"},
    "قطب ۴": {"خراسان رضوی", "خراسان شمالی", "خراسان جنوبی", "سیستان و بلوچستان", "کرمان"},
    "قطب ۵": {"آذربایجان شرقی", "آذربایجان غربی", "اردبیل", "زنجان", "گیلان",
              "مازندران", "گلستان", "کردستان", "کرمانشاه", "ایلام", "لرستان", "همدان"},
}

ZONES_MAP = {
    "ناحیه ۱": {"تهران", "البرز", "قم", "قزوین", "سمنان"},
    "ناحیه ۲": {"اصفهان", "یزد"},
    "ناحیه ۳": {"فارس", "بوشهر", "هرمزگان"},
    "ناحیه ۴": {"آذربایجان شرقی", "آذربایجان غربی", "اردبیل", "زنجان"},
    "ناحیه ۵": {"گیلان", "مازندران", "گلستان"},
    "ناحیه ۶": {"خراسان رضوی", "خراسان شمالی", "خراسان جنوبی"},
    "ناحیه ۷": {"کرمان", "سیستان و بلوچستان"},
    "ناحیه ۸": {"کردستان", "کرمانشاه", "ایلام", "لرستان", "همدان", "چهارمحال و بختیاری",
                "کهگیلویه و بویراحمد", "مرکزی", "خوزستان"},
}

DISCLAIMER = (
    "⚠️ این نتایج بر اساس تخمین‌های آماری و داده‌های موجود است و جایگزین "
    "مشاوره تخصصی با داده‌های رسمی سازمان سنجش نیست. برای تصمیم‌گیری نهایی "
    "حتماً با مشاوران مجرب و داده‌های به‌روز سنجش مشورت کنید."
)

# ====================== Major ID Mapping ======================
MAJOR_ID_MAPPING = {
    "1": "medicine", "2": "dentistry", "3": "pharmacy", "4": "veterinary",
    "5": "nursing", "6": "midwifery", "7": "emergency_medicine",
    "8": "operating_room", "9": "anesthesiology", "10": "physiotherapy",
    "11": "occupational_therapy", "12": "speech_therapy", "13": "audiology",
    "14": "optometry", "15": "nutrition_science", "16": "laboratory_science",
    "17": "radiology", "18": "radiotherapy", "19": "medical_biotechnology",
    "20": "public_health", "21": "environmental_health", "22": "occupational_health",
    "23": "health_management", "24": "health_economics", "25": "health_information",
    "26": "medical_library", "27": "medical_physics", "28": "medical_engineering",
    "29": "clinical_psychology", "30": "medical_genetics_research",
    "31": "medical_microbiology", "32": "medical_immunology",
    "33": "medical_genetics", "34": "medical_education",
    "35": "forensic_medicine", "36": "health_education",
    "37": "gerontology", "38": "sports_medicine",
    "39": "traditional_medicine", "40": "rehabilitation",
    "41": "electrical_engineering", "42": "computer_engineering",
    "43": "it_engineering", "44": "software_engineering",
    "45": "computer_science", "46": "mechanical_engineering",
    "47": "aerospace_engineering", "48": "marine_engineering",
    "49": "naval_architecture", "50": "agricultural_machinery",
    "51": "food_industry_machinery", "52": "railway_engineering",
    "53": "civil_engineering", "54": "surveying_engineering",
    "55": "urban_planning", "56": "water_engineering",
    "57": "geomatics", "58": "chemical_engineering",
    "59": "petroleum_engineering", "60": "gas_engineering",
    "61": "polymer_engineering", "62": "materials_engineering",
    "63": "metallurgy_engineering", "64": "industrial_engineering",
    "65": "logistics_engineering", "66": "biomedical_engineering",
    "67": "biomechanics", "68": "textile_engineering",
    "69": "mining_engineering", "70": "geological_engineering",
    "71": "nuclear_engineering", "72": "energy_engineering",
    "73": "architecture", "74": "landscape_architecture",
    "75": "interior_design", "76": "urban_design",
    "77": "construction_management", "78": "environmental_engineering",
    "79": "mining_exploration", "80": "petroleum_exploration",
    "81": "mathematics", "82": "statistics", "83": "data_science",
    "84": "physics", "85": "applied_physics", "86": "chemistry",
    "87": "applied_chemistry", "88": "biology", "89": "microbiology",
    "90": "biochemistry", "91": "genetics", "92": "cell_biology",
    "93": "plant_biology", "94": "animal_biology", "95": "ecology",
    "96": "geology", "97": "geophysics", "98": "astronomy",
    "99": "nanotechnology", "100": "cognitive_science",
    "101": "law", "102": "political_science", "103": "international_relations",
    "104": "islamic_law", "105": "islamic_theology", "106": "psychology",
    "107": "counseling", "108": "education", "109": "primary_education",
    "110": "special_education", "111": "educational_technology",
    "112": "curriculum_planning", "113": "educational_management",
    "114": "economics", "115": "theoretical_economics", "116": "business_administration",
    "117": "public_administration", "118": "industrial_management",
    "119": "financial_management", "120": "insurance_management",
    "121": "customs_management", "122": "tourism_management",
    "123": "hotel_management", "124": "cultural_management",
    "125": "sports_management", "126": "media_management",
    "127": "journalism", "128": "sociology", "129": "anthropology",
    "130": "social_work", "131": "philosophy", "132": "accounting",
    "133": "banking", "134": "history", "135": "geography",
    "136": "painting_theory", "137": "industrial_design",
    "138": "carpet_design", "139": "fabric_design",
    "140": "graphic_design", "141": "visual_communication",
    "142": "painting", "143": "sculpture", "144": "photography",
    "145": "animation",
    "146": "english_translation", "147": "english_teaching",
    "148": "french_language", "149": "german_language",
    "150": "linguistics",
}

MAJOR_ID_REVERSE_MAPPING = {v: k for k, v in MAJOR_ID_MAPPING.items()}


def resolve_major_id(major_id: str, programs_database: List[Dict]) -> List[str]:
    possible_ids = [major_id]
    if major_id in MAJOR_ID_MAPPING:
        possible_ids.append(MAJOR_ID_MAPPING[major_id])
    if major_id in MAJOR_ID_REVERSE_MAPPING:
        possible_ids.append(MAJOR_ID_REVERSE_MAPPING[major_id])
    for prog in programs_database[:20]:
        prog_major = prog.get("major_id", "")
        if prog_major in possible_ids:
            return [prog_major]
    return possible_ids


def get_pole_of_province(province: str) -> Optional[str]:
    for pole, provinces in POLES.items():
        if province in provinces:
            return pole
    return None


def get_zone_of_province(province: str) -> Optional[str]:
    for zone, provinces in ZONES_MAP.items():
        if province in provinces:
            return zone
    return None


def gender_compatibility_check(user_gender: str, program_gender_policy: str) -> bool:
    if not program_gender_policy or program_gender_policy == "مختلط":
        return True
    return user_gender == program_gender_policy


def validate_user_input(user: Dict) -> List[str]:
    warnings = []
    rank = user.get("rank")
    if rank is not None and (not isinstance(rank, (int, float)) or rank < 0):
        warnings.append("⚠️ رتبه نامعتبر – برای مسیر بدون آزمون رتبه نباید وارد شود")
    final_gpa = user.get("final_gpa", 0)
    if final_gpa is not None and (final_gpa < 0 or final_gpa > 20):
        warnings.append("⚠️ معدل خارج از بازه ۰-۲۰")
    gpa = user.get("gpa", 0)
    if gpa is not None and (gpa < 0 or gpa > 20):
        warnings.append("⚠️ معدل کل خارج از بازه ۰-۲۰")
    traz = user.get("traz", 0)
    if traz is not None and traz < 0:
        warnings.append("⚠️ تراز منفی")
    age = user.get("age")
    if age is not None and (age < 10 or age > 80):
        warnings.append("⚠️ سن نامعتبر")
    return warnings


def check_basic_eligibility(user: Dict, program: Dict) -> Tuple[bool, List[str]]:
    warnings = []
    is_eligible = True
    user_gender = user.get("gender", "")
    uni = program.get("university", {})
    gender_policy = uni.get("gender_policy", "مختلط")
    if not gender_compatibility_check(user_gender, gender_policy):
        return False, [f"این رشته فقط برای {gender_policy} است"]
    spec_req = program.get("special_requirements", {})
    min_gpa = spec_req.get("min_gpa_required", 0)
    if min_gpa > 0:
        user_gpa = user.get("final_gpa", 0)
        if user_gpa < min_gpa:
            warnings.append(f"معدل شما ({user_gpa}) کمتر از حد نصاب ({min_gpa}) است")
            is_eligible = False
    admission_info = program.get("admission_info", {})
    special_cond = admission_info.get("special_conditions", {})
    max_age = special_cond.get("max_age")
    user_age = user.get("age")
    if max_age and user_age and user_age > max_age:
        warnings.append(f"⚠️ سن شما ({user_age}) بیشتر از حد مجاز ({max_age}) است")
    if special_cond.get("has_interview"):
        warnings.append("⚠️ این رشته نیاز به مصاحبه دارد")
    if special_cond.get("has_practical_exam"):
        warnings.append("⚠️ این رشته نیاز به آزمون عملی دارد")
    if spec_req.get("has_service_commitment"):
        years = spec_req.get("service_years", 4)
        warnings.append(f"⚠️ تعهد خدمت {years * 2} سال در مناطق محروم")
    return is_eligible, warnings


def validate_diploma_match(user_diploma_type: str, program: Dict) -> Tuple[bool, Optional[str]]:
    admission_info = program.get("admission_info", {})
    is_floating = admission_info.get("is_floating", False)
    if is_floating:
        return True, None
    diploma_req = admission_info.get("diploma_requirements", {})
    accepts_types = diploma_req.get("accepts_diploma_types", [])
    if accepts_types:
        if user_diploma_type in accepts_types:
            return True, None
        types_str = ", ".join(accepts_types)
        return False, f"❌ این رشته فقط از دیپلم‌های {types_str} می‌پذیرد"
    major_group = program.get("major_group", "")
    if major_group in MAJOR_GROUP_TO_DIPLOMAS:
        accepted = MAJOR_GROUP_TO_DIPLOMAS[major_group]
        if user_diploma_type in accepted:
            return True, None
        return False, f"❌ این رشته فقط از دیپلم‌های {', '.join(accepted)} می‌پذیرد"
    return True, None


def resolve_user_quota(user: Dict) -> Tuple[str, List[str]]:
    warnings = []
    quota = user.get("quota")
    if quota:
        return quota, warnings
    return DEFAULT_QUOTA, ["⚠️ سهمیه مشخص نیست، منطقه ۲ فرض شد"]


def extract_cutoff_from_structure(cutoff_structure: Any, target_year: str = "1404") -> Dict[str, Any]:
    if not isinstance(cutoff_structure, dict):
        return {}
    if "1401" in cutoff_structure or "1402" in cutoff_structure or "1403" in cutoff_structure or "1404" in cutoff_structure:
        year_cutoff = cutoff_structure.get(target_year, {})
        if isinstance(year_cutoff, dict):
            return year_cutoff
        return {}
    return cutoff_structure


def calculate_effective_cutoff(
    cutoffs: Dict[str, Any],
    user_quota: str,
    program: Dict[str, Any],
    user: Dict[str, Any]
) -> Tuple[float, List[str]]:
    warnings = []
    admission_info = program.get("admission_info", {})
    course_type = admission_info.get("course_type", "roozaneh")
    user_province = user.get("province", "")
    uni = program.get("university", {})
    university_province = uni.get("province", "")
    bomi_type = admission_info.get("bomi_type", "keshvari")

    is_bomi = False
    if bomi_type == "keshvari":
        is_bomi = True
        warnings.append("✓ پذیرش کشوری - رقابت در کل ظرفیت")
    elif bomi_type == "ghotbi":
        user_pole = get_pole_of_province(user_province)
        uni_pole = get_pole_of_province(university_province)
        if user_pole and uni_pole and user_pole == uni_pole:
            is_bomi = True
            warnings.append(f"✓ شما بومی ({bomi_type}) هستید - در 80% ظرفیت رقابت می‌کنید")
        else:
            warnings.append("⚠️ شما غیربومی هستید - فقط در 20% ظرفیت رقابت می‌کنید")
    elif bomi_type == "ostani":
        if user_province == university_province:
            is_bomi = True
            warnings.append(f"✓ شما بومی ({bomi_type}) هستید - در 80% ظرفیت رقابت می‌کنید")
        else:
            warnings.append("⚠️ شما غیربومی هستید - فقط در 20% ظرفیت رقابت می‌کنید")
    elif bomi_type == "nahiei":
        user_zone = get_zone_of_province(user_province)
        uni_zone = get_zone_of_province(university_province)
        if user_zone and uni_zone and user_zone == uni_zone:
            is_bomi = True
            warnings.append(f"✓ شما بومی ({bomi_type}) هستید - در 80% ظرفیت رقابت می‌کنید")
        else:
            warnings.append("⚠️ شما غیربومی هستید - فقط در 20% ظرفیت رقابت می‌کنید")

    if is_bomi:
        raw_cutoffs = program.get("cutoffs_bomi", program.get("cutoffs_historical", {}))
    else:
        raw_cutoffs = program.get("cutoffs_non_bomi", program.get("cutoffs_historical", {}))

    cutoff_dict = extract_cutoff_from_structure(raw_cutoffs, "1404")
    if not cutoff_dict:
        historical = program.get("cutoffs_historical", {})
        cutoff_dict = extract_cutoff_from_structure(historical, "1404")
    if not cutoff_dict:
        return 0, ["❌ داده cutoff برای این رشته موجود نیست"]

    cutoff = 0
    if user_quota in ("isargaran_25", "shahid"):
        free_cutoff = cutoff_dict.get("zone_2", cutoff_dict.get("zone_1", 0))
        if free_cutoff > 0:
            cutoff = free_cutoff / ISARGARAN_70_RULE
            warnings.append("✓ قانون ۷۰٪ ایثارگران اعمال شد")
        else:
            cutoff = cutoff_dict.get(user_quota, 0)
    elif user_quota == "isargaran_5":
        free_cutoff = cutoff_dict.get("zone_2", cutoff_dict.get("zone_1", 0))
        if free_cutoff > 0:
            cutoff = free_cutoff / ISARGARAN_85_RULE
            warnings.append("✓ قانون ۸۵٪ ایثارگران اعمال شد")
        else:
            cutoff = cutoff_dict.get(user_quota, 0)
    else:
        cutoff = cutoff_dict.get(user_quota, 0)

    if cutoff == 0:
        return 0, [f"❌ این رشته سهمیه {user_quota} را نمی‌پذیرد"]

    multiplier = COURSE_TYPE_MULTIPLIER.get(course_type, 1.0)
    cutoff *= multiplier
    return cutoff, warnings


def apply_gpa_impact(user: Dict[str, Any], program: Dict[str, Any]) -> float:
    try:
        user_rank = user.get("rank", 99999)
        user_gpa = user.get("final_gpa", 17.0)
        BASE_GPA = 17.0
        gpa_delta = user_gpa - BASE_GPA
        mgp_factor = 1.0 - (gpa_delta * 0.04)
        mgp_factor = max(0.70, min(1.30, mgp_factor))
        effective_rank = user_rank * mgp_factor
        effective_rank = max(1, min(300000, effective_rank))
        return effective_rank
    except Exception as e:
        logger.error(f"Error in apply_gpa_impact: {e}")
        return user.get("rank", 99999)


def calculate_weighted_historical_cutoffs(cutoffs_historical: Dict) -> Dict:
    cutoffs = {}
    quota_keys = ["zone_1", "zone_2", "zone_3", "isargaran_25", "isargaran_5", "shahid"]
    for key in quota_keys:
        weighted_sum = 0.0
        total_weight = 0.0
        for year, weight in HISTORICAL_WEIGHTS.items():
            if year in cutoffs_historical:
                year_data = extract_cutoff_from_structure(cutoffs_historical, year)
                if key in year_data:
                    weighted_sum += year_data[key] * weight
                    total_weight += weight
        if total_weight > 0:
            cutoffs[key] = int(weighted_sum / total_weight)
    return cutoffs


def calculate_advanced_exam_probability(user: Dict, program: Dict) -> Tuple[float, List[str], str]:
    all_warnings = []
    user_rank = user.get("rank")
    if user_rank is None or not isinstance(user_rank, (int, float)):
        return 0.0, ["⚠️ برای پذیرش با آزمون، رتبه معتبر الزامی است"], "رتبه وارد نشده است"

    validation_warnings = validate_user_input(user)
    all_warnings.extend(validation_warnings)

    is_eligible, basic_warnings = check_basic_eligibility(user, program)
    all_warnings.extend(basic_warnings)
    if not is_eligible:
        return 0.0, all_warnings, "عدم احراز شرایط اولیه"

    diploma_type = user.get("diploma_type", "ریاضی")
    is_valid, diploma_error = validate_diploma_match(diploma_type, program)
    if not is_valid:
        all_warnings.append(diploma_error)
        return 0.0, all_warnings, "عدم تطابق دیپلم"

    user_quota, quota_warnings = resolve_user_quota(user)
    all_warnings.extend(quota_warnings)

    cutoffs_pred = program.get("cutoffs_predicted_1405", {})
    cutoffs_hist = program.get("cutoffs_historical", {})
    cutoffs_old = program.get("cutoffs_konkur", {})
    if cutoffs_pred:
        cutoffs = extract_cutoff_from_structure(cutoffs_pred, "1405")
    elif cutoffs_hist:
        cutoffs = calculate_weighted_historical_cutoffs(cutoffs_hist)
    else:
        cutoffs = extract_cutoff_from_structure(cutoffs_old, "1404")

    cutoff, cutoff_warnings = calculate_effective_cutoff(cutoffs, user_quota, program, user)
    all_warnings.extend(cutoff_warnings)
    if cutoff == 0:
        return 0.0, all_warnings, "کات‌آف موجود نیست"

    effective_rank = apply_gpa_impact(user, program)
    rank_ratio = effective_rank / cutoff

    if rank_ratio <= RANK_RATIO_HIGH:
        probability = PROBABILITY_MAX
        basis = "رتبه شما بسیار بهتر از آخرین رتبه قبولی است"
    elif rank_ratio <= RANK_RATIO_MEDIUM:
        probability = PROBABILITY_MAX - ((rank_ratio - RANK_RATIO_HIGH) * 260)
        basis = "رتبه شما بهتر از آخرین رتبه قبولی است"
    elif rank_ratio <= RANK_RATIO_LOW:
        probability = 60.0 - ((rank_ratio - RANK_RATIO_MEDIUM) * 400)
        basis = "رتبه شما نزدیک به آخرین رتبه قبولی است"
    else:
        probability = 0.0
        basis = "رتبه شما بدتر از آخرین رتبه قبولی است"

    admission_info = program.get("admission_info", {})
    special_cond = admission_info.get("special_conditions", {})
    if special_cond.get("has_interview"):
        probability *= 0.90
    if special_cond.get("has_practical_exam"):
        probability *= 0.85

    probability = max(0.0, min(PROBABILITY_MAX, probability))
    return round(probability, 1), all_warnings, basis


def calculate_savabegh_probability(user: Dict, program: Dict) -> Tuple[float, List[str], str]:
    all_warnings = []
    validation_warnings = validate_user_input(user)
    all_warnings.extend(validation_warnings)

    is_eligible, basic_warnings = check_basic_eligibility(user, program)
    all_warnings.extend(basic_warnings)
    if not is_eligible:
        return 0.0, all_warnings, "عدم احراز شرایط اولیه"

    diploma_type = user.get("diploma_type", "ریاضی")
    is_valid, diploma_error = validate_diploma_match(diploma_type, program)
    if not is_valid:
        all_warnings.append(diploma_error)
        return 0.0, all_warnings, "عدم تطابق دیپلم"

    cutoffs = program.get("cutoffs_savabegh", {})
    min_gpa = cutoffs.get("minimum_gpa", 0)
    min_traz = cutoffs.get("minimum_traz", 0)

    user_gpa = user.get("gpa", 0)
    user_traz = user.get("traz", 0)

    score = 0.0
    gpa_ok = False
    traz_ok = False

    if min_gpa > 0:
        gpa_ratio = user_gpa / min_gpa
        if gpa_ratio >= SCORE_EXCELLENT:
            score += 60
            gpa_ok = True
        elif gpa_ratio >= SCORE_GOOD:
            score += 45
            gpa_ok = True
        elif gpa_ratio >= SCORE_ACCEPTABLE:
            score += 25
            gpa_ok = True
        else:
            all_warnings.append(f"معدل شما ({user_gpa}) کمتر از حد نصاب ({min_gpa}) است")

    if min_traz > 0:
        traz_ratio = user_traz / min_traz
        if traz_ratio >= SCORE_EXCELLENT:
            score += 40
            traz_ok = True
        elif traz_ratio >= SCORE_GOOD:
            score += 30
            traz_ok = True
        elif traz_ratio >= SCORE_ACCEPTABLE:
            score += 15
            traz_ok = True

    if gpa_ok and traz_ok:
        basis = "معدل و تراز شما بالاتر از حد نصاب است"
    elif gpa_ok:
        basis = "معدل شما بالاتر از حد نصاب است"
    elif traz_ok:
        basis = "تراز شما بالاتر از حد نصاب است"
    else:
        basis = "معدل و تراز شما در مرز حد نصاب قرار دارند"

    admission_info = program.get("admission_info", {})
    course_type = admission_info.get("course_type", "")
    user_province = user.get("province", "")
    uni = program.get("university", {})
    university_province = uni.get("province", "")
    bomi_type = admission_info.get("bomi_type", "keshvari")

    if bomi_type == "ostani" and user_province != university_province:
        if course_type == "payam_noor":
            score *= 0.95
            all_warnings.append("⚠️ پیام نور اولویت کمی با بومی دارد")
        else:
            score *= 0.70
            all_warnings.append("⚠️ در سوابق، اولویت با بومی است")

    user_quota, quota_warnings = resolve_user_quota(user)
    all_warnings.extend(quota_warnings)
    quota_boost = SAVABEGH_QUOTA_BOOST.get(user_quota, 1.0)
    if quota_boost != 1.0:
        score *= quota_boost
        all_warnings.append(f"✓ سهمیه {user_quota} در سوابق تحصیلی اعمال شد")

    probability = min(PROBABILITY_MAX, max(0.0, score))
    return round(probability, 1), all_warnings, basis


def get_probability_level(probability: float, basis_override: str = None) -> Dict[str, str]:
    if probability >= PROBABILITY_HIGH:
        level = "بسیار بالا"
        color = "green"
        description = "قبولی تقریباً قطعی"
        default_basis = "رتبه شما بسیار بهتر از آخرین رتبه قبولی است"
    elif probability >= PROBABILITY_MEDIUM:
        level = "بالا"
        color = "yellow"
        description = "احتمال قبولی زیاد"
        default_basis = "رتبه شما بهتر از آخرین رتبه قبولی است"
    elif probability >= PROBABILITY_LOW:
        level = "متوسط"
        color = "orange"
        description = "شانس متوسط"
        default_basis = "رتبه شما نزدیک به آخرین رتبه قبولی است"
    else:
        level = "پایین"
        color = "red"
        description = "فقط با تکمیل ظرفیت"
        default_basis = "رتبه شما بدتر از آخرین رتبه قبولی است"

    return {
        "level": level,
        "color": color,
        "description": description,
        "basis": basis_override if basis_override else default_basis,
    }


def get_tuition_range(financial_cost: int) -> str:
    if financial_cost == 0:
        return "بدون شهریه"
    elif financial_cost <= 3_000_000:
        return "تا ۳ میلیون تومان در ترم"
    elif financial_cost <= 6_000_000:
        return "۳ تا ۶ میلیون تومان در ترم"
    elif financial_cost <= 10_000_000:
        return "۶ تا ۱۰ میلیون تومان در ترم"
    elif financial_cost <= 15_000_000:
        return "۱۰ تا ۱۵ میلیون تومان در ترم"
    elif financial_cost <= 20_000_000:
        return "۱۵ تا ۲۰ میلیون تومان در ترم"
    else:
        return "بیش از ۲۰ میلیون تومان در ترم"


def get_eligible_universities(
    programs_database: List[Dict],
    major_id: str,
    user: Dict
) -> Tuple[List[Dict], List[str]]:
    eligible = []
    all_rejection_reasons = []

    user_quota, quota_warnings = resolve_user_quota(user)
    user_gender = user.get("gender", "")
    possible_major_ids = resolve_major_id(major_id, programs_database)

    for program in programs_database:
        prog_major = program.get("major_id", "")
        if prog_major not in possible_major_ids:
            continue

        uni = program.get("university", {})
        gender_policy = uni.get("gender_policy", "مختلط")
        if not gender_compatibility_check(user_gender, gender_policy):
            continue

        admission_info = program.get("admission_info", {})
        method = admission_info.get("method", "konkur")
        probability = 0.0
        warnings = []
        basis = ""

        if method in METHOD_KONKUR:
            probability, warnings, basis = calculate_advanced_exam_probability(user, program)
        elif method in METHOD_SAVABEGH:
            probability, warnings, basis = calculate_savabegh_probability(user, program)

        if probability < ADMISSION_DISPLAY_THRESHOLD:
            for w in warnings:
                if not w.startswith("✓") and w not in all_rejection_reasons:
                    all_rejection_reasons.append(w)
            continue

        level_info = get_probability_level(probability, basis)
        financial = program.get("financial", {})
        tuition = financial.get("tuition_per_term", 0)

        eligible.append({
            "program_id": program.get("program_id"),
            "university_name": uni.get("name", ""),
            "province": uni.get("province", ""),
            "university_prestige_level": uni.get("prestige_level", 2),
            "course_type": admission_info.get("course_type", "roozaneh"),
            "admission_method": method,
            "probability": probability,
            "probability_label": level_info["level"],
            "probability_color": level_info["color"],
            "probability_description": level_info["description"],
            "probability_basis": level_info["basis"],
            "quota_used": user_quota,
            "bomi_type": admission_info.get("bomi_type", "keshvari"),
            "tuition_range": get_tuition_range(tuition),
            "warnings": warnings,
        })

    eligible.sort(key=lambda x: x["probability"], reverse=True)
    return eligible, all_rejection_reasons


def calculate_admission_for_major(
    programs_database: List[Dict],
    majors_database: Dict,
    major_id: str,
    user: Dict
) -> Dict:
    major_data = majors_database.get(major_id)
    if not major_data:
        return {"error": f"رشته {major_id} یافت نشد"}

    eligible, rejection_reasons = get_eligible_universities(programs_database, major_id, user)
    user_quota, _ = resolve_user_quota(user)
    status = "دانشگاه‌های در دسترس" if eligible else "دانشگاهی با شانس قابل توجه یافت نشد"

    free_count = 0
    paid_count = 0
    high_count = 0
    medium_count = 0
    for uni in eligible:
        if uni["tuition_range"] == "بدون شهریه":
            free_count += 1
        else:
            paid_count += 1
        prob = uni["probability"]
        if prob >= PROBABILITY_HIGH:
            high_count += 1
        elif PROBABILITY_LOW <= prob < PROBABILITY_HIGH:
            medium_count += 1

    return {
        "major_info": {
            "major_id": major_id,
            "major_name_fa": major_data.get("name_fa", ""),
        },
        "user_context": {
            "quota_used": user_quota,
            "province": user.get("province", ""),
            "rank": user.get("rank"),
            "final_gpa": user.get("final_gpa", 0),
            "diploma_type": user.get("diploma_type", ""),
            "age": user.get("age"),
        },
        "admission_possibilities": {
            "status": status,
            "basis": "بر اساس رتبه، سهمیه، بومی‌گزینی، جنسیت، معدل",
            "universities": eligible,
            "rejection_reasons": rejection_reasons,
        },
        "summary": {
            "total_universities_found": len(eligible),
            "free_education_count": free_count,
            "paid_education_count": paid_count,
            "high_probability_count": high_count,
            "medium_probability_count": medium_count,
        },
        "rules_applied": [
            "تأثیر قطعی ۶۰٪ معدل (۱۴۰۴+)",
            "قانون ۷۰٪ ایثارگران ۲۵٪",
            "قانون ۸۵٪ ایثارگران ۵٪",
            "بومی‌گزینی (کشوری/قطبی/ناحیه‌ای/استانی)",
            "تطابق دیپلم با رشته (کنکور و سوابق)",
            "تأثیر سهمیه در پذیرش سوابق تحصیلی",
            "میانگین وزن‌دار ۴ سال (۱۴۰۱-۱۴۰۴)",
            "MGP Factor (اصلاح رتبه موثر)",
        ],
        "disclaimer": DISCLAIMER,
    }


def calculate_all_majors_admission(
    programs_database: List[Dict],
    majors_database: Dict,
    user: Dict,
    admission_type: str = "both"
) -> Dict:
    all_results = []
    for major_id in majors_database.keys():
        major_data = majors_database.get(major_id)
        if not major_data:
            continue
        possible_major_ids = resolve_major_id(major_id, programs_database)
        filtered_programs = []
        for program in programs_database:
            prog_major = program.get("major_id", "")
            if prog_major not in possible_major_ids:
                continue
            method = program.get("admission_info", {}).get("method", "konkur")
            if admission_type == "exam" and method not in METHOD_KONKUR:
                continue
            if admission_type == "savabegh" and method not in METHOD_SAVABEGH:
                continue
            filtered_programs.append(program)
        if not filtered_programs:
            continue
        result = calculate_admission_for_major(filtered_programs, majors_database, major_id, user)
        if "error" in result:
            continue
        possibilities = result.get("admission_possibilities", {})
        universities = possibilities.get("universities", [])
        if not universities:
            continue
        top_universities = universities[:3]
        max_probability = max(u["probability"] for u in universities)
        top_list = [{
            "university_name": u["university_name"],
            "province": u["province"],
            "probability": u["probability"],
            "probability_label": u["probability_label"],
            "course_type": u["course_type"],
            "admission_method": u["admission_method"],
            "tuition_range": u["tuition_range"],
            "warnings": u["warnings"],
        } for u in top_universities]
        all_results.append({
            "major_id": major_id,
            "major_name_fa": major_data.get("name_fa", ""),
            "major_group": major_data.get("group", ""),
            "total_universities": len(universities),
            "max_probability": max_probability,
            "top_universities": top_list,
        })
    all_results.sort(key=lambda x: x["max_probability"], reverse=True)
    high_count = sum(1 for r in all_results if r["max_probability"] >= PROBABILITY_HIGH)
    medium_count = sum(1 for r in all_results if PROBABILITY_LOW <= r["max_probability"] < PROBABILITY_HIGH)
    user_quota, _ = resolve_user_quota(user)
    return {
        "user_context": {
            "quota_used": user_quota,
            "province": user.get("province", ""),
            "rank": user.get("rank", 0),
            "final_gpa": user.get("final_gpa", 0),
            "diploma_type": user.get("diploma_type", ""),
            "age": user.get("age"),
            "admission_type": admission_type,
        },
        "total_matches": len(all_results),
        "high_probability_majors": high_count,
        "medium_probability_majors": medium_count,
        "recommendations": all_results,
        "basis": "بر اساس رتبه، سهمیه، بومی‌گزینی، جنسیت، معدل، تطابق دیپلم",
        "rules_applied": [
            "تأثیر قطعی ۶۰٪ معدل (۱۴۰۴+)",
            "قانون ۷۰٪ ایثارگران ۲۵٪",
            "قانون ۸۵٪ ایثارگران ۵٪",
            "بومی‌گزینی (کشوری/قطبی/ناحیه‌ای/استانی)",
            "تطابق دیپلم با رشته (کنکور و سوابق)",
            "تأثیر سهمیه در پذیرش سوابق تحصیلی",
            "میانگین وزن‌دار ۴ سال (۱۴۰۱-۱۴۰۴)",
            "MGP Factor (اصلاح رتبه موثر)",
        ],
        "disclaimer": DISCLAIMER,
    }
