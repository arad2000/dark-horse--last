"""
Dark Horse Engine v14.3 (Final) – Full Personalization with Micro-Alignment Details
============================================================================
- سناریوهای سه‌گانه (M+S+V)
- درج مثال‌های واقعی از ابعاد همسو/ناهمسو (راهبردها و ارزش‌ها)
- حفظ next_step
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

        # نگاشت trait_hint برای ۲۵ سوال راهبرد
        self.trait_map = {
            1: ["تحلیلی", "تجربی", "مشورتی", "شهودی", "عمل‌گرا"],
            2: ["ساختاریافته", "حسی", "مشورتی", "آزمایشی", "بیرونی"],
            3: ["نقدگرا", "فرضیه‌ساز", "مشورتی", "صبور", "شهودی"],
            4: ["ریشه‌یاب", "مشاهده‌گر", "مشورتی", "خلاق", "عمل‌گرا"],
            5: ["مستندات‌محور", "بصری", "پروژه‌محور", "اجتماعی", "اکتشافی"],
            6: ["شنیداری", "پیش‌خوان", "عملی", "گفتگویی", "بازنویس"],
            7: ["آکادمیک", "بصری", "تدریسی", "تمثیلی", "فرمال"],
            8: ["منطقی", "جایگزین", "سلسله‌مراتبی", "همدلانه", "جمعی"],
            9: ["مداخله‌گر", "میانجی", "تسهیل‌گر", "ناظر", "دموکراتیک"],
            10: ["مدیر", "ایده‌پرداز", "مجری", "هماهنگ‌کننده", "مستقل"],
            11: ["ساختارساز", "ماجراجو", "الگویاب", "شفافیت‌خواه", "چابک"],
            12: ["صبور", "شهودی", "سناریوساز", "مشورتی", "انعطاف‌پذیر"],
            13: ["قانون‌یاب", "شبکه‌ساز", "مشاهده‌گر", "عمل‌گرا", "فرهنگ‌خوان"],
            14: ["آرام", "بداهه‌پرداز", "همکاری‌طلب", "واکنش‌سریع", "قیاسی"],
            15: ["قانون‌مدار", "هوشمند", "مذاکره‌گر", "اصلاح‌گر", "برون‌سپار"],
            16: ["وابسته به ساختار", "شخصی‌ساز", "خلاق", "موقعیتی", "شهودی"],
            17: ["پشتکار", "مذاکره‌گر", "اولویت‌بند", "همکاری‌طلب", "کیفیت‌محور"],
            18: ["تطبیق‌پذیر", "فراتر از حد", "نظام‌گرا", "خودمختار", "یادگیرنده"],
            19: ["تحلیلی", "تجربی", "مشورتی", "شهودی", "عمل‌گرا"],
            20: ["اولویت‌بند", "همکاری‌طلب", "سرعت‌گرا", "مذاکره‌گر", "برنامه‌ریز"],
            21: ["خودمختار", "دستورپذیر", "نیمه‌مستقل", "تیمی", "موقعیتی"],
            22: ["آزمایشگاه", "بیمارستان", "طبیعت", "کارگاه", "دفتر"],
            23: ["سکوت-تنهایی", "پس‌زمینه", "فضای باز", "تعاملی", "خانگی"],
            24: ["تعامل اجتماعی", "تنهایی", "فیزیکی", "ساخت‌وکار", "چالش فکری"],
            25: ["فرایندگرا", "نتیجه‌گرا-تأثیر", "پیشرفت‌گرا", "چالش‌گرا", "رشدگرا"]
        }

        # نگاشت قطب‌های ارزشی
        self.value_poles = {
            "Q1A": "انسان‌محور", "Q1B": "سیستم‌محور",
            "Q2A": "میراث مادی", "Q2B": "میراث فکری",
            "Q3A": "تنوع‌طلب", "Q3B": "عمیق‌گرا",
            "Q4A": "مسئولیت فردی", "Q4B": "مسئولیت سیستمی",
            "Q5A": "نظم‌گرا", "Q5B": "خلاق‌گرا",
            "Q6A": "تعامل‌گرا", "Q6B": "تمرکزگرا",
            "Q7A": "مخترع", "Q7B": "مربی",
            "Q8A": "ساختارگرا", "Q8B": "آزادی‌خواه",
            "Q9A": "خدمت‌گرا", "Q9B": "خالق",
            "Q10A": "رهبر", "Q10B": "وفاق‌ساز",
            "Q11A": "داده‌گرا", "Q11B": "انسان‌گرا",
            "Q12A": "خطرپذیر", "Q12B": "ثبات‌گرا",
            "Q13A": "نتیجه‌گرا", "Q13B": "اثرگرا",
            "Q14A": "استقلال‌طلب", "Q14B": "تعلق‌گرا",
            "Q15A": "تسلط‌گرا", "Q15B": "کنجکاوی‌گرا"
        }

    # ======================= بارگذاری داده‌ها =======================
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

    # ======================= محاسبات امتیاز =======================
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

        score = min(1.0, total_weight / valid) if valid > 0 else 0.0
        return score, highlights

    def _compute_v_score(
        self, value_choices: List[str], value_weights: Dict[str, float]
    ) -> Tuple[float, List[str]]:
        if not value_choices or not value_weights:
            return 0.0, []

        total = 0.0
        valid = 0
        highlights = []

        for v in value_choices:
            if not v or not v.strip():
                continue
            weight = value_weights.get(v.strip(), 0.0)
            total += weight
            valid += 1
            if weight > 0.7:
                highlights.append(f"ارزش {v}: هم‌راستایی قوی")

        score = min(1.0, total / valid) if valid > 0 else 0.0
        return score, highlights

    def _build_evidence(
        self, m_evidence: List[Dict],
        s_score: float, s_highlights: List[str],
        v_score: float, v_highlights: List[str]
    ) -> Dict:
        evidence: Dict = {"micro_motives_matched": m_evidence}
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

    # ======================= استخراج نمونه‌های ناهمسویی/همسویی =======================
    def _extract_s_misaligned_traits(
        self, strategy_answers: List[int], strategy_weights: List[List[float]]
    ) -> List[str]:
        """برگرداندن نام چند بُعد که وزن انتخاب کاربر در آن‌ها کمتر از 0.3 است"""
        traits = []
        for i, row in enumerate(strategy_weights):
            if i >= len(strategy_answers):
                continue
            ans = strategy_answers[i]
            if ans < 0 or ans >= len(row):
                continue
            if row[ans] < 0.3:
                q_num = i + 1
                trait = self.trait_map.get(q_num, [""])[ans] if q_num in self.trait_map else "نامشخص"
                traits.append(trait)
        # برگرداندن حداکثر ۳ مورد
        return list(dict.fromkeys(traits))[:3]

    def _extract_v_misaligned_poles(
        self, value_choices: List[str], value_weights: Dict[str, float]
    ) -> List[str]:
        """برگرداندن ارزش‌هایی که گزینهٔ انتخابی کاربر وزن پایینی دارد و گزینهٔ مقابل وزن بالایی"""
        poles = []
        for v in value_choices:
            if not v or not v.strip():
                continue
            user_weight = value_weights.get(v, 0.0)
            opposite = v[0:3] + ("B" if v.endswith("A") else "A")
            opp_weight = value_weights.get(opposite, 0.0)
            if user_weight < 0.4 and opp_weight >= 0.7:
                pole = self.value_poles.get(v, v)
                poles.append(pole)
        return list(dict.fromkeys(poles))[:3]

    # ======================= تولید توضیح سناریومحور =======================
    def _generate_scenario_description(
        self, major_name: str,
        m_evidence: List[Dict],
        m_score: float,
        s_score: float,
        v_score: float,
        strategy_answers: List[int],
        strategy_weights: List[List[float]],
        value_choices: List[str],
        value_weights: Dict[str, float]
    ) -> str:
        m_aligned = m_score >= 0.3
        s_aligned = s_score >= 0.6
        v_aligned = v_score >= 0.6

        desc = f"📌 {major_name}: "

        # --- سناریوها ---
        if m_aligned and s_aligned and v_aligned:
            desc += (
                "هر سه لایهٔ فردیت شما (خرده‌انگیزه‌ها، راهبردهای شخصی و ارزش‌های بنیادین) "
                "با این رشته همخوانی بالایی دارند. "
                "شما می‌توانید در این مسیر یک اسب سیاه باشید — مسیری که با ذات شما هماهنگ است."
            )
        elif m_aligned and (not s_aligned or not v_aligned):
            if not s_aligned and not v_aligned:
                desc += (
                    "خرده‌انگیزه‌های شما با این رشته همسو هستند، "
                    "اما راهبردهای شخصی (سبک یادگیری و حل مسئله) و ارزش‌های بنیادین شما "
                    "با این رشته همخوانی کمتری دارند. "
                    "پیشنهاد می‌شود با آگاهی از این تفاوت‌ها، "
                    "در انتخاب این مسیر باریک دقت بیشتری کنید."
                )
            elif not s_aligned:
                desc += (
                    "خرده‌انگیزه‌های شما با این رشته همسو هستند، "
                    "اما راهبردهای شخصی (سبک یادگیری و حل مسئله) شما "
                    "با این رشته همخوانی کمتری دارد. "
                    "اگر مایلید در این مسیر قدم بگذارید، "
                    "توصیه می‌شود با چشمان باز این ناهماهنگی را در نظر بگیرید."
                )
            elif not v_aligned:
                desc += (
                    "خرده‌انگیزه‌های شما با این رشته همسو هستند، "
                    "اما ارزش‌های بنیادین شما با این رشته همخوانی کمتری دارد. "
                    "این ممکن است به مرور باعث کاهش انگیزه شود. "
                    "با دقت انتخاب کنید."
                )
        elif not m_aligned and (s_aligned or v_aligned):
            if s_aligned and v_aligned:
                desc += (
                    "اگرچه خرده‌انگیزه‌های شما همخوانی مستقیمی با این رشته ندارد، "
                    "اما راهبردهای شخصی (سبک فکری) و ارزش‌های بنیادین شما "
                    "با روحیهٔ این حرفه هماهنگی خوبی نشان می‌دهد. "
                    "این رشته می‌تواند یک گزینهٔ آلترناتیو غیرمنتظره اما بالقوه موفق برای شما باشد."
                )
            elif s_aligned:
                desc += (
                    "خرده‌انگیزه‌های شما با این رشته همسو نیستند، "
                    "اما راهبردهای شخصی (سبک فکری) شما همخوانی خوبی با این حرفه دارد. "
                    "اگر به این مسیر علاقه دارید، می‌توانید آن را به‌عنوان یک انتخاب نامتعارف در نظر بگیرید."
                )
            elif v_aligned:
                desc += (
                    "خرده‌انگیزه‌های شما با این رشته همسو نیستند، "
                    "اما ارزش‌های بنیادین شما همخوانی خوبی با این حرفه دارد. "
                    "این رشته می‌تواند از منظر معنا و رضایت درونی برایتان جذاب باشد، "
                    "هرچند جرقه‌های روزمرهٔ آن را کمتر دوست داشته باشید."
                )
        else:
            desc += (
                "خرده‌انگیزه‌های شما با این رشته همسو هستند. "
                "راهبردهای شخصی و ارزش‌های شما در سطح متوسطی با این رشته هماهنگ‌اند. "
                "می‌توانید این مسیر را به عنوان یک گزینه در نظر بگیرید."
            )

        # --- افزودن نمونه‌های واقعی از ناهمسویی‌ها (در صورت وجود) ---
        if not s_aligned:
            mis_traits = self._extract_s_misaligned_traits(strategy_answers, strategy_weights)
            if mis_traits:
                desc += f" برای مثال، در ابعاد «{', '.join(mis_traits)}» ناهم‌راستایی دیده می‌شود."
        if not v_aligned:
            mis_poles = self._extract_v_misaligned_poles(value_choices, value_weights)
            if mis_poles:
                desc += f" همچنین ارزش‌های «{', '.join(mis_poles)}» با اولویت‌های این رشته فاصله دارند."

        # --- افزودن نمونه جرقه‌ها ---
        if m_evidence:
            sample = "، ".join(m.get("description", m["code"]) for m in m_evidence[:2])
            if len(m_evidence) > 2:
                desc += f" (جرقه‌ها: {sample} و {len(m_evidence)-2} جرقهٔ دیگر)"
            else:
                desc += f" (جرقه‌ها: {sample})"

        return desc

    # ======================= متد اصلی =======================
    def discover_individuality(
        self, user_motives: List[str],
        sjt_answers: Dict[str, str],
        conjoint_choices: Dict[str, str],
    ) -> Dict:
        strategy_answers: List[int] = []
        for i in range(1, 26):
            key = f"sjt_{i}"
            ans = (sjt_answers or {}).get(key, "").strip().upper()
            if len(ans) == 1 and 'A' <= ans <= 'E':
                strategy_answers.append(ord(ans) - ord('A'))
            else:
                strategy_answers.append(-1)

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

                personalized = self._generate_scenario_description(
                    major_data.get("name", ""),
                    m_ev, m_score, s_score, v_score,
                    strategy_answers,
                    major_data.get("strategy_weights", []),
                    value_choices,
                    major_data.get("value_weights", {})
                )

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
                        "prestige_level": major_data.get("prestige_level", 2),
                        "raw_components": {
                            "m_score": round(m_score * 100, 1),
                            "s_score": round(s_score * 100, 1),
                            "v_score": round(v_score * 100, 1),
                        },
                        "evidence": evidence,
                        "personalized_description": personalized,
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
                "principle": "کشف فردیت بر اساس ریزانگیزه‌ها، ۲۵ سوال استراتژی، ۱۵ سوال ارزشی",
                "scoring": "Total = 0.60×M + 0.20×S + 0.20×V",
                "filter": "نمایش رشته‌ها با Total ≥ 30%",
                "version": "14.3 (Scenario + Micro Details, Dark Horse aligned)",
            },
            "next_step": "برای مشاهده شانس قبولی دانشگاه‌ها، اطلاعات سنجش خود را وارد کنید",
        }
