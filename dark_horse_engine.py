"""
Dark Horse Engine v13.0 (Personalized Descriptions)
موتور کشف فردیت – نسخه کامل با توضیح شخصی‌سازی‌شده

تغییرات v13:
  + تحلیل سبک فکری و ارزش‌ها از پاسخ‌های کاربر (build_user_profile)
  + تولید توصیف اختصاصی برای هر رشته (generate_major_description)
  + ذخیره‌سازی personalized_description در خروجی
  + هندلینگ پاسخ‌های خالی SJT / Conjoint
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
    # S Score
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

        score = min(1.0, total_weight / valid) if valid > 0 else 0.0
        return score, highlights

    # ============================================================
    # V Score
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
    # NEW: تحلیل شخصیت کاربر (پروفایل متنی)
    # ============================================================
    def _build_user_profile(self, strategy_answers: List[int],
                            value_choices: List[str]) -> str:
        """
        ساخت یک توصیف روان از سبک فکری، یادگیری، محیط کاری ترجیحی
        و ارزش‌های برجسته کاربر بر اساس پاسخ‌هایش.
        """
        # نگاشت trait_hint ها بر اساس سوالات (question number -> list of traits)
        trait_map = {
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

        # شمارش trait ها
        trait_counts = {}
        for i, ans in enumerate(strategy_answers):
            q_num = i + 1
            if q_num in trait_map and ans is not None and 0 <= ans < len(trait_map[q_num]):
                trait = trait_map[q_num][ans]
                trait_counts[trait] = trait_counts.get(trait, 0) + 1

        sorted_traits = sorted(trait_counts.items(), key=lambda x: x[1], reverse=True)
        top_traits = [t[0] for t in sorted_traits[:5]]

        # تحلیل ارزش‌ها
        value_poles = {
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

        pole_counts = {}
        for v in value_choices:
            if v in value_poles:
                pole = value_poles[v]
                pole_counts[pole] = pole_counts.get(pole, 0) + 1

        sorted_poles = sorted(pole_counts.items(), key=lambda x: x[1], reverse=True)
        top_values = [p[0] for p in sorted_poles[:5]]

        # ساخت متن پروفایل
        profile_parts = []

        # سبک حل مسئله
        if "تحلیلی" in top_traits or "ساختاریافته" in top_traits:
            profile_parts.append("مسائل را با تحلیل گام‌به‌گام و ساختارمند حل می‌کنی.")
        elif "تجربی" in top_traits or "پروژه‌محور" in top_traits:
            profile_parts.append("با آزمون و خطا و درگیر شدن مستقیم با پروژه‌ها مسائل را حل می‌کنی.")
        elif "شهودی" in top_traits:
            profile_parts.append("اغلب جرقه‌های ناگهانی و شهود، راه‌حل‌هایت را شکل می‌دهند.")
        elif "اجتماعی" in top_traits or "مشورتی" in top_traits:
            profile_parts.append("از همفکری و گفتگو با دیگران برای رسیدن به پاسخ انرژی می‌گیری.")
        else:
            profile_parts.append("سبکی منعطف و چندوجهی در حل مسائل داری.")

        # سبک یادگیری
        if "مستندات‌محور" in top_traits or "آکادمیک" in top_traits:
            profile_parts.append("یادگیری‌ات از طریق مطالعهٔ عمیق و منابع مکتوب شکل می‌گیرد.")
        elif "بصری" in top_traits or "پروژه‌محور" in top_traits:
            profile_parts.append("با دیدن و انجام دادن بهتر یاد می‌گیری.")
        elif "شنیداری" in top_traits or "گفتگویی" in top_traits:
            profile_parts.append("بحث و تبادل نظر، بهترین روش یادگیری توست.")
        else:
            profile_parts.append("روش یادگیری‌ات ترکیبی از چند سبک است.")

        # محیط و انرژی
        if "سکوت-تنهایی" in top_traits or "تنهایی" in top_traits:
            profile_parts.append("در سکوت و تنهایی بیشترین بازده را داری و انرژی‌ات از تمرکز عمیق می‌آید.")
        elif "تعامل اجتماعی" in top_traits or "تعاملی" in top_traits:
            profile_parts.append("تعامل با دیگران به تو انرژی می‌دهد و در فضاهای شلوغ شکوفا می‌شوی.")
        elif "کارگاه" in top_traits or "طبیعت" in top_traits:
            profile_parts.append("ترجیح می‌دهی در محیط‌های عملی یا در دل طبیعت کار کنی.")
        elif "دفتر" in top_traits:
            profile_parts.append("فضاهای اداری مدرن و منظم برایت الهام‌بخش هستند.")
        # otherwise keep it generic

        # ارزش‌ها
        if top_values:
            profile_parts.append(f"ارزش‌های برجسته‌ات: {'، '.join(top_values[:3])}.")
        else:
            profile_parts.append("ارزش‌های عمیقت ترکیبی متعادل از اولویت‌های فردی و اجتماعی است.")

        return " ".join(profile_parts)

    # ============================================================
    # NEW: تولید توضیح شخصی‌سازی‌شده برای یک رشته
    # ============================================================
    def _generate_major_description(
        self, major_name: str, m_evidence: List[Dict],
        s_score: float, v_score: float,
        user_profile: str
    ) -> str:
        micro_count = len(m_evidence)
        sample_items = [m.get("description", m["code"]) for m in m_evidence[:3]]
        sample_str = "، ".join(sample_items) if sample_items else ""

        desc_parts = []

        if micro_count > 0:
            if micro_count >= 10:
                desc_parts.append(
                    f"🔥 {micro_count} جرقهٔ تو مثل «{sample_str}» با {major_name} هم‌راستاست. "
                    "انگار این مسیر سال‌ها منتظر تو بوده."
                )
            elif micro_count >= 5:
                desc_parts.append(
                    f"✨ {micro_count} جرقه از جمله «{sample_str}» نشان می‌دهد "
                    f"{major_name} می‌تواند برایت لذت‌بخش باشد."
                )
            else:
                desc_parts.append(
                    f"🔹 {micro_count} جرقهٔ کوچک اما معنادار (مانند {sample_str}) "
                    f"در {major_name} پیدا کردی."
                )
        else:
            desc_parts.append(f"هنوز جرقه‌های مشترک زیادی با {major_name} پیدا نکردی، ")

        # سبک فکری
        if s_score >= 0.8:
            desc_parts.append(
                f"سبک فکری‌ات (هم‌خوانی {int(s_score*100)}٪) نشان می‌دهد "
                f"این رشته با روش طبیعی حل مسئله‌ات هماهنگی فوق‌العاده‌ای دارد."
            )
        elif s_score >= 0.6:
            desc_parts.append(
                f"سبک فکری‌ات ({int(s_score*100)}٪ تطابق) می‌تواند در این رشته نیز به خوبی عمل کند."
            )
        elif s_score >= 0.4:
            desc_parts.append(
                "اگرچه سبک فکری‌ات با فضای رایج این رشته تفاوت‌هایی دارد، "
                "اما اسب سیاه درون تو می‌تواند از این تضاد، خلاقیتی نو خلق کند."
            )
        else:
            desc_parts.append(
                "سبک فکری‌ات با این رشته هم‌خوانی پایینی دارد، اما مسیر اسب سیاه همیشه غیرمنتظره است."
            )

        # ارزش‌ها
        if v_score >= 0.8:
            desc_parts.append(
                "ارزش‌های بنیادین‌ات با روح این حرفه هم‌جهت است و به کارت معنای عمیقی می‌بخشد."
            )
        elif v_score >= 0.6:
            desc_parts.append("ارزش‌هایت با این رشته هم‌پوشانی خوبی دارد.")
        elif v_score >= 0.4:
            desc_parts.append(
                "ممکن است برخی ارزش‌هایت در این رشته کمتر دیده شوند، "
                "اما این تضاد می‌تواند به رشد شخصی‌ات کمک کند."
            )
        else:
            desc_parts.append(
                "ارزش‌های بنیادین‌ات با این رشته فاصله دارند، "
                "اما گاهی همین فاصله، جرقهٔ نوآوری است."
            )

        # پروفایل کاربر
        desc_parts.append(f"دربارهٔ تو: {user_profile}")

        return " ".join(desc_parts)

    # ============================================================
    # سطح تناسب (ورودی: درصد)
    # ============================================================
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
                strategy_answers.append(-1)  # پاسخ نامعتبر

        # --- تبدیل V ---
        value_choices: List[str] = []
        for i in range(1, 16):
            key = f"conj_{i}"
            ans = (conjoint_choices or {}).get(key, "").strip().upper()
            value_choices.append(f"Q{i}{ans}" if ans in ('A', 'B') else "")

        # --- ساخت پروفایل متنی کاربر (فقط یک بار) ---
        user_profile_text = self._build_user_profile(strategy_answers, value_choices)

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

                # تولید توضیح شخصی‌سازی‌شده
                personalized = self._generate_major_description(
                    major_data.get("name", ""),
                    m_ev, s_score, v_score,
                    user_profile_text
                )

                # امن‌سازی major_id
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
                "principle": (
                    "کشف فردیت بر اساس ریزانگیزه‌ها، "
                    "۲۵ سوال استراتژی، ۱۵ سوال ارزشی"
                ),
                "scoring": "Total = 0.60×M + 0.20×S + 0.20×V (سند اجرایی)",
                "filter": "نمایش رشته‌ها با Total ≥ 30%",
                "policy_decision": "تصمیم نهایی با داوطلب است",
                "version": "13.0 (Personalized Descriptions)",
            },
            "next_step": (
                "برای مشاهده شانس قبولی دانشگاه‌ها، "
                "اطلاعات سنجش خود را وارد کنید"
            ),
        }
