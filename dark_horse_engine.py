"""
Dark Horse Engine v12.0 (Final Production-Ready)
موتور کشف فردیت - نسخه نهایی

فرمول امتیازدهی:
  Total = 0.60 × M + 0.20 × S + 0.20 × V

M Score (میکروموتیوها):
  نسبت موتیوهای مشترک کاربر و رشته به کل موتیوهای رشته.

S Score (راهبردهای شخصی):
  میانگین وزن‌های strategy_weights بر اساس پاسخ‌های ۲۵ سؤال.

V Score (ارزش‌های بنیادین):
  میانگین وزن‌های value_weights بر اساس پاسخ‌های ۱۵ دوگانه.

ویژگی‌های نسخه ۱۲:
  - پشتیبانی از لیست و دیکشنری برای micro_motive_codes
  - رفع باگ پاسخ‌های خالی (S و V)
  - تولید Evidence (دلایل تناسب) و Warnings (پرچم‌های زرد)
  - فیلتر حداقل ۳۰٪ برای نمایش رشته‌ها
  - معماری شیءگرا، بدون متغیر global
  - پیوند به موتور سنجش (next_step)
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger("darkhorse_engine")


class DarkHorseEngine:
    """
    موتور اصلی کشف فردیت.
    داده‌ها یک‌بار هنگام نمونه‌سازی بارگذاری می‌شوند.
    """

    def __init__(
        self,
        motives_path: str = "micro_motives.json",
        majors_path: str = "majors_database.json"
    ):
        self.motives_map: Dict[str, str] = {}
        self.majors_db: Dict[str, Dict] = {}
        self._load_data(motives_path, majors_path)

    # ========================================================================
    # ۱. بارگذاری داده‌ها
    # ========================================================================
    def _load_data(self, motives_path: str, majors_path: str) -> None:
        """لود کردن فایل‌های JSON در حافظه."""
        # میکروموتیوها
        try:
            self.motives_map = self._load_json(
                motives_path, key_field="code", value_field="description_fa"
            )
            logger.info(f"✅ {len(self.motives_map)} میکروموتیو بارگذاری شد.")
        except Exception as e:
            logger.error(f"خطا در بارگذاری میکروموتیوها: {e}")
            self.motives_map = {}

        # دیتابیس رشته‌ها
        try:
            self.majors_db = self._load_json(majors_path, key_field="id")
            logger.info(f"✅ {len(self.majors_db)} رشته بارگذاری شد.")
        except Exception as e:
            logger.error(f"خطا در بارگذاری رشته‌ها: {e}")
            self.majors_db = {}

    def _load_json(
        self,
        path: str,
        key_field: Optional[str] = None,
        value_field: Optional[str] = None
    ) -> Dict:
        """لود کردن فایل JSON و تبدیل به دیکشنری در صورت نیاز."""
        if not Path(path).exists():
            raise FileNotFoundError(f"فایل {path} یافت نشد.")

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if key_field and isinstance(data, list):
            if value_field:
                return {
                    item[key_field]: item.get(value_field, "")
                    for item in data if key_field in item
                }
            return {
                item[key_field]: item
                for item in data if key_field in item
            }
        return data

    # ========================================================================
    # ۲. محاسبه M Score (فرمول ساده و شفاف)
    # ========================================================================
    def _compute_m_score(
        self,
        user_motives: List[str],
        major_data: Dict
    ) -> Tuple[float, List[Dict]]:
        """
        محاسبه نمره میکروموتیوها با فرمول ساده:
        M = تعداد موتیوهای مشترک / تعداد کل موتیوهای رشته
        """
        if not user_motives:
            return 0.0, []

        # دریافت کدهای موتیو
        raw_codes = major_data.get("micro_motive_codes", [])

        # تبدیل به مجموعه (پشتیبانی از لیست و دیکشنری)
        if isinstance(raw_codes, dict):
            major_set = set(raw_codes.keys())
        elif isinstance(raw_codes, list):
            major_set = # حالت لیستی
            major_set = {c.strip().lower() for c in raw_codes}
        else:
            return 0.0, []

        if not major_set:
            return 0.0, []

        user_set = {m.strip().lower() for m in user_motives if m and m.strip()}
        matched = user_set & major_set

        if not matched:
            return 0.0, []

        # فرمول ساده
        score = len(matched) / len(major_set)

        # جزئیات برای Evidence
        matched_details = [
            {"code": code, "description": self.motives_map.get(code, "")}
            for code in user_motives
            if code.strip().lower() in matched
        ]

        return min(1.0, score), matched_details

    # ========================================================================
    # ۳. محاسبه S Score
    # ========================================================================
    def _compute_s_score(
        self,
        strategy_answers: List[int],
        strategy_weights: List[List[float]]
    ) -> Tuple[float, List[str]]:
        """محاسبه نمره راهبردهای شخصی با میانگین وزن‌ها."""
        if not strategy_weights or not strategy_answers:
            return 0.0, []

        total_weight = 0.0
        valid = 0

        for i, row in enumerate(strategy_weights):
            if i >= len(strategy_answers):
                continue
            idx = strategy_answers[i]
            if idx < 0 or idx >= len(row):
                continue  # پاسخ نامعتبر
            total_weight += row[idx]
            valid += 1

        score = min(1.0, total_weight / 25.0) if valid > 0 else 0.0
        return score, []

    # ========================================================================
    # ۴. محاسبه V Score
    # ========================================================================
    def _compute_v_score(
        self,
        value_choices: List[str],
        value_weights: Dict[str, float]
    ) -> Tuple[float, List[str]]:
        """محاسبه نمره ارزش‌های بنیادین با میانگین وزن‌ها."""
        if not value_choices or not value_weights:
            return 0.0, []

        total = 0.0
        valid = 0

        for v in value_choices:
            weight = value_weights.get(v.strip(), 0.0)
            total += weight
            valid += 1

        score = min(1.0, total / valid) if valid > 0 else 0.0
        return score, []

    # ========================================================================
    # ۵. ساختن Evidence و Warnings
    # ========================================================================
    def _build_evidence(
        self,
        m_evidence: List[Dict],
        s_score: float,
        v_score: float
    ) -> Dict:
        """تولید دلایل تناسب و پرچم‌های هشدار."""
        evidence: Dict = {
            "micro_motives_matched": m_evidence
        }

        warnings = []
        if s_score < 0.4:
            warnings.append(
                "راهبردهای شخصی شما (سبک یادگیری و حل مسئله) با الگوی رایج "
                "در این رشته تفاوت‌هایی دارد. این یک مانع نیست؛ با آگاهی "
                "می‌توانید مسیر شخصی خود را بسازید."
            )
        if v_score < 0.4:
            warnings.append(
                "برخی ارزش‌های بنیادین شما با اولویت‌های این رشته فاصله دارد. "
                "ممکن است این مسیر برایتان چالش‌برانگیز باشد."
            )

        if warnings:
            evidence["warnings"] = warnings

        return evidence

    # ========================================================================
    # ۶. سطح تناسب
    # ========================================================================
    @staticmethod
    def _get_fit_level(score: float) -> str:
        if score >= 80:
            return "همخوانی بسیار بالا"
        elif score >= 60:
            return "همخوانی بالا"
        elif score >= 40:
            return "همخوانی متوسط"
        else:
            return "همخوانی پایین"

    # ========================================================================
    # ۷. متد اصلی: کشف فردیت
    # ========================================================================
    def discover_individuality(
        self,
        user_motives: List[str],
        sjt_answers: Dict[str, str],
        conjoint_choices: Dict[str, str],
    ) -> Dict:
        """
        متد اصلی کشف رشته‌های متناسب با فردیت کاربر.

        Args:
            user_motives: لیست کدهای میکروموتیو انتخاب‌شده توسط کاربر
            sjt_answers: دیکشنری پاسخ‌های S (کلید: sjt_1 تا sjt_25، مقدار: A-E)
            conjoint_choices: دیکشنری پاسخ‌های V (کلید: conj_1 تا conj_15، مقدار: A/B)

        Returns:
            دیکشنری شامل لیست رشته‌های کشف‌شده با نمره و Evidence
        """
        # ------------------------------------------------------------------
        # ۱. تبدیل پاسخ‌های S (با رفع باگ پاسخ خالی)
        # ------------------------------------------------------------------
        strategy_answers: List[int] = []
        for i in range(1, 26):  # ۲۵ سؤال
            key = f"sjt_{i}"
            answer = (sjt_answers or {}).get(key, "").strip().upper()
            if len(answer) == 1 and 'A' <= answer <= 'E':
                strategy_answers.append(ord(answer) - ord('A'))
            else:
                strategy_answers.append(-1)  # پاسخ نامعتبر

        # ------------------------------------------------------------------
        # ۲. تبدیل پاسخ‌های V
        # ------------------------------------------------------------------
        value_choices: List[str] = []
        for i in range(1, 16):  # ۱۵ سؤال
            key = f"conj_{i}"
            answer = (conjoint_choices or {}).get(key, "").strip().upper()
            if answer in ('A', 'B'):
                value_choices.append(f"Q{i}{answer}")
            else:
                value_choices.append("")  # پاسخ نامعتبر

        # ------------------------------------------------------------------
        # ۳. محاسبه برای همه رشته‌ها
        # ------------------------------------------------------------------
        discovered: List[Dict] = []

        for major_id, major_data in self.majors_db.items():
            try:
                # لایه ۱: میکروموتیوها
                m_score, m_evidence = self._compute_m_score(
                    user_motives or [], major_data
                )

                # لایه ۲: راهبردها
                s_score, _ = self._compute_s_score(
                    strategy_answers,
                    major_data.get("strategy_weights", [])
                )

                # لایه ۳: ارزش‌ها
                v_score, _ = self._compute_v_score(
                    value_choices,
                    major_data.get("value_weights", {})
                )

                # فرمول نهایی
                total = (0.60 * m_score) + (0.20 * s_score) + (0.20 * v_score)
                final_score = round(total * 100, 1)

                # فیلتر حداقل ۳۰٪
                if final_score < 30.0:
                    continue

                # ساختن Evidence و Warnings
                evidence = self._build_evidence(m_evidence, s_score, v_score)

                discovered.append({
                    "major_id": int(major_id),
                    "major_name_fa": major_data.get("name", ""),
                    "realm_fa": major_data.get("group", ""),
                    "individuality_fit": {
                        "score": final_score,
                        "level": self._get_fit_level(final_score),
                        "prestige_level": major_data.get("prestige_level", 2),
                        "raw_components": {
                            "m_score": round(m_score * 100, 1),
                            "s_score": round(s_score * 100, 1),
                            "v_score": round(v_score * 100, 1),
                        },
                        "evidence": evidence,
                    },
                })
            except Exception as e:
                logger.error(f"خطا در تحلیل رشته {major_id}: {e}")
                continue

        # ------------------------------------------------------------------
        # ۴. مرتب‌سازی نزولی
        # ------------------------------------------------------------------
        discovered.sort(
            key=lambda x: x["individuality_fit"]["score"],
            reverse=True
        )

        # ------------------------------------------------------------------
        # ۵. آمار
        # ------------------------------------------------------------------
        high = sum(1 for m in discovered if m["individuality_fit"]["score"] >= 80)
        med = sum(1 for m in discovered if 60 <= m["individuality_fit"]["score"] < 80)
        low = sum(1 for m in discovered if m["individuality_fit"]["score"] < 60)

        return {
            "discovered_majors": discovered,
            "summary": {
                "total_majors_analyzed": len(self.majors_db),
                "total_matches": len(discovered),
                "high_compatibility": high,
                "medium_compatibility": med,
                "low_compatibility": low,
            },
            "method": {
                "principle": (
                    "کشف فردیت بر اساس ریزانگیزه‌ها، "
                    "۲۵ سوال استراتژی، ۱۵ سوال ارزشی"
                ),
                "scoring": "Total = 0.60×M + 0.20×S + 0.20×V (سند اجرایی)",
                "filter": "نمایش رشته‌ها با Total ≥ 30%",
                "policy_decision": "تصمیم نهایی با داوطلب است",
                "version": "12.0 Final",
            },
            "next_step": (
                "برای مشاهده شانس قبولی دانشگاه‌ها، "
                "اطلاعات سنجش خود را وارد کنید"
            ),
        }
