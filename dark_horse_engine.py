"""
Dark Horse Engine v12.2 (Production-Ready, All Bugfixes Applied)
موتور کشف فردیت - نسخه نهایی

رفع باگ‌های بحرانی:
  1. S Score: تقسیم بر valid به‌جای 25
  2. V Score: skip پاسخ‌های خالی
  3. docstring _get_fit_level
  4. بازگرداندن highlights برای S و V
  5. مستندسازی prestige_level
  6. امن‌سازی int(major_id)
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional

logger = logging.getLogger("darkhorse_engine")


class DarkHorseEngine:
    def __init__(
        self,
        motives_path: str = "micro_motives.json",
        majors_path: str = "majors_database.json"
    ):
        self.motives_map: Dict[str, str] = {}
        self.majors_db: Dict[str, Dict] = {}
        self._load_data(motives_path, majors_path)

    # ============================================================
    # بارگذاری داده‌ها
    # ============================================================
    def _load_data(self, motives_path: str, majors_path: str) -> None:
        try:
            self.motives_map = self._load_json(
                motives_path, key_field="code", value_field="description_fa"
            )
            logger.info(f"✅ {len(self.motives_map)} میکروموتیو بارگذاری شد.")
        except Exception as e:
            logger.error(f"خطا در بارگذاری میکروموتیوها: {e}")
            self.motives_map = {}

        try:
            self.majors_db = self._load_json(majors_path, key_field="id")
            logger.info(f"✅ {len(self.majors_db)} رشته بارگذاری شد.")
        except Exception as e:
            logger.error(f"خطا در بارگذاری رشته‌ها: {e}")
            self.majors_db = {}

    def _load_json(self, path: str, key_field: Optional[str] = None,
                   value_field: Optional[str] = None) -> Dict:
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
            return {item[key_field]: item for item in data if key_field in item}
        return data

    # ============================================================
    # M Score
    # ============================================================
    def _compute_m_score(
        self, user_motives: List[str], major_data: Dict
    ) -> Tuple[float, List[Dict]]:
        if not user_motives:
            return 0.0, []

        raw_codes = major_data.get("micro_motive_codes", [])
        if isinstance(raw_codes, dict):
            major_set = {str(c).strip().lower() for c in raw_codes.keys()}
        elif isinstance(raw_codes, list):
            major_set = {str(c).strip().lower() for c in raw_codes}
        else:
            return 0.0, []

        if not major_set:
            return 0.0, []

        user_set = {str(m).strip().lower() for m in user_motives if m and str(m).strip()}
        matched = user_set & major_set
        if not matched:
            return 0.0, []

        score = len(matched) / len(major_set)

        matched_details = []
        for code in user_motives:
            code_lower = str(code).strip().lower()
            if code_lower in matched:
                desc = self.motives_map.get(code, "") or self.motives_map.get(code.upper(), "")
                matched_details.append({"code": code, "description": desc})

        return min(1.0, score), matched_details

    # ============================================================
    # S Score (باگ تقسیم بر 25 رفع شده)
    # ============================================================
    def _compute_s_score(
        self, strategy_answers: List[int], strategy_weights: List[List[float]]
    ) -> Tuple[float, List[str]]:
        if not strategy_weights or not strategy_answers:
            return 0.0, []

        total_weight = 0.0
        valid = 0
        highlights = []

        for i, row in enumerate(strategy_weights):
            if i >= len(strategy_answers):
                continue
            idx = strategy_answers[i]
            if idx < 0 or idx >= len(row):
                continue
            total_weight += row[idx]
            valid += 1
            if row[idx] > 0.7:
                highlights.append(f"بُعد {i+1}: هم‌خوانی بالا")

        # ✅ اصلاح: تقسیم بر valid به‌جای 25
        score = min(1.0, total_weight / valid) if valid > 0 else 0.0
        return score, highlights

    # ============================================================
    # V Score (باگ پاسخ خالی رفع شده)
    # ============================================================
    def _compute_v_score(
        self, value_choices: List[str], value_weights: Dict[str, float]
    ) -> Tuple[float, List[str]]:
        if not value_choices or not value_weights:
            return 0.0, []

        total = 0.0
        valid = 0
        highlights = []

        for v in value_choices:
            # ✅ اصلاح: skip پاسخ خالی
            if not v or not v.strip():
                continue
            weight = value_weights.get(v.strip(), 0.0)
            total += weight
            valid += 1
            if weight > 0.7:
                highlights.append(f"ارزش {v}: هم‌راستایی قوی")

        score = min(1.0, total / valid) if valid > 0 else 0.0
        return score, highlights

    # ============================================================
    # Evidence & Warnings
    # ============================================================
    def _build_evidence(
        self, m_evidence: List[Dict],
        s_score: float, s_highlights: List[str],
        v_score: float, v_highlights: List[str]
    ) -> Dict:
        evidence: Dict = {
            "micro_motives_matched": m_evidence
        }
        if s_highlights:
            evidence["strategy_highlights"] = s_highlights
        if v_highlights:
            evidence["value_alignment"] = v_highlights

        warnings = []
        if s_score < 0.4:
            warnings.append(
                "راهبردهای شخصی شما (سبک یادگیری و حل مسئله) با الگوی رایج "
                "در این رشته تفاوت‌هایی دارد."
            )
        if v_score < 0.4:
            warnings.append(
                "برخی ارزش‌های بنیادین شما با اولویت‌های این رشته فاصله دارد."
            )
        if warnings:
            evidence["warnings"] = warnings

        return evidence

    # ============================================================
    # سطح تناسب (ورودی: درصد)
    # ============================================================
    @staticmethod
    def _get_fit_level(score: float) -> str:
        """
        تشخیص سطح همخوانی.

        Args:
            score: نمره نهایی به درصد (0 تا 100)
        """
        if score >= 80:
            return "همخوانی بسیار بالا"
        elif score >= 60:
            return "همخوانی بالا"
        elif score >= 40:
            return "همخوانی متوسط"
        else:
            return "همخوانی پایین"

    # ============================================================
    # متد اصلی
    # ============================================================
    def discover_individuality(
        self, user_motives: List[str],
        sjt_answers: Dict[str, str],
        conjoint_choices: Dict[str, str],
    ) -> Dict:
        # --- تبدیل S ---
        strategy_answers: List[int] = []
        for i in range(1, 26):
            key = f"sjt_{i}"
            ans = (sjt_answers or {}).get(key, "").strip().upper()
            if len(ans) == 1 and 'A' <= ans <= 'E':
                strategy_answers.append(ord(ans) - ord('A'))
            else:
                strategy_answers.append(-1)

        # --- تبدیل V ---
        value_choices: List[str] = []
        for i in range(1, 16):
            key = f"conj_{i}"
            ans = (conjoint_choices or {}).get(key, "").strip().upper()
            value_choices.append(f"Q{i}{ans}" if ans in ('A', 'B') else "")

        discovered: List[Dict] = []

        for major_id, major_data in self.majors_db.items():
            try:
                m_score, m_ev = self._compute_m_score(user_motives or [], major_data)
                s_score, s_high = self._compute_s_score(
                    strategy_answers, major_data.get("strategy_weights", [])
                )
                v_score, v_high = self._compute_v_score(
                    value_choices, major_data.get("value_weights", {})
                )

                total = (0.60 * m_score) + (0.20 * s_score) + (0.20 * v_score)
                final_score = round(total * 100, 1)

                if final_score < 30.0:
                    continue

                evidence = self._build_evidence(
                    m_ev, s_score, s_high, v_score, v_high
                )

                # ✅ امن‌سازی major_id
                try:
                    safe_id = int(major_id)
                except (ValueError, TypeError):
                    safe_id = major_id

                discovered.append({
                    "major_id": safe_id,
                    "major_name_fa": major_data.get("name", ""),
                    "realm_fa": major_data.get("group", ""),
                    "individuality_fit": {
                        "score": final_score,
                        "level": self._get_fit_level(final_score),
                        # صرفاً نمایشی - در محاسبات نقشی ندارد
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

        discovered.sort(key=lambda x: x["individuality_fit"]["score"], reverse=True)

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
                "version": "12.2 Final (All Bugfixes)",
            },
            "next_step": (
                "برای مشاهده شانس قبولی دانشگاه‌ها، "
                "اطلاعات سنجش خود را وارد کنید"
            ),
        }
