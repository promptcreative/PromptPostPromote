"""
Utility functions for Astrobatching
Calendar range, normalization, serialization, Double GO logic
"""

import re
from datetime import datetime, date, time, timedelta
from flask import session


def make_json_serializable(obj):
    if isinstance(obj, dict):
        return {k: make_json_serializable(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_serializable(item) for item in obj]
    elif isinstance(obj, (datetime, date, time)):
        return obj.isoformat()
    elif hasattr(obj, '__dict__') and not isinstance(obj, type):
        return {k: make_json_serializable(v) for k, v in obj.__dict__.items()}
    else:
        return obj


def get_user_calendar_range(user_email=None):
    from database.models import UserProfile
    calendar_range_days = 60

    if user_email:
        try:
            user_profile = UserProfile.query.filter_by(email=user_email).first()
            if user_profile and user_profile.calendar_range_days:
                calendar_range_days = user_profile.calendar_range_days
        except Exception:
            pass

    if not user_email and 'user_info' in session:
        user_email = session['user_info'].get('email')
        if user_email:
            try:
                user_profile = UserProfile.query.filter_by(email=user_email).first()
                if user_profile and user_profile.calendar_range_days:
                    calendar_range_days = user_profile.calendar_range_days
            except Exception:
                pass

    today = date.today()
    start_date = date(today.year, today.month, 1)
    end_date = start_date + timedelta(days=calendar_range_days - 1)
    return start_date, end_date, calendar_range_days


def get_two_month_range():
    user_info = session.get('user_info', {})
    user_email = user_info.get('email')
    return get_user_calendar_range(user_email)


_PTI_DOUBLE_GO_VALUES = ['PTI BEST', 'PTI GO', 'BEST']
_VEDIC_DOUBLE_GO_VALUES = ['GO', 'BUILD']


def calculate_is_double_go(pti_quality: str, vedic_quality: str) -> bool:
    if not pti_quality or not vedic_quality:
        return False
    pti_clean = re.sub(r'[\U0001F300-\U0001F9FF\U0001FA00-\U0001FAFF\u2600-\u26FF\u2700-\u27BF]', '', str(pti_quality))
    pti_normalized = ' '.join(pti_clean.split()).upper()
    vedic_normalized = str(vedic_quality).strip().upper()
    pti_ok = any(valid in pti_normalized for valid in _PTI_DOUBLE_GO_VALUES)
    vedic_ok = vedic_normalized in _VEDIC_DOUBLE_GO_VALUES
    return pti_ok and vedic_ok


def apply_double_go_to_combined_results(combined_results: list, pti_by_date: dict, vedic_by_date: dict) -> int:
    changes_count = 0
    for day_result in combined_results:
        if not isinstance(day_result, dict):
            continue
        day_date = day_result.get("date")
        if not day_date:
            continue

        if day_date in pti_by_date:
            pti_item = pti_by_date[day_date]
            pti_quality = pti_item.get("classification") or pti_item.get("magi_classification") or ""
        else:
            pti_quality = day_result.get("system_breakdown", {}).get("pti_collective", {}).get("quality", "")

        if day_date in vedic_by_date:
            vedic_quality = vedic_by_date[day_date].get("classification") or ""
        else:
            vedic_quality = day_result.get("system_breakdown", {}).get("vedic_pti", {}).get("quality", "")

        system_breakdown = day_result.get("system_breakdown", {})
        if pti_quality and "pti_collective" in system_breakdown:
            system_breakdown["pti_collective"]["quality"] = pti_quality
        if vedic_quality and "vedic_pti" in system_breakdown:
            system_breakdown["vedic_pti"]["quality"] = vedic_quality

        new_is_double_go = calculate_is_double_go(pti_quality, vedic_quality)
        old_is_double_go = day_result.get("is_double_go", False)

        day_result["is_double_go"] = new_is_double_go
        day_result["double_go_label"] = "DOUBLE GO" if new_is_double_go else None

        if old_is_double_go != new_is_double_go:
            changes_count += 1

    return changes_count


def normalize_dashboard_data(dashboard_data: dict) -> dict:
    data = dict(dashboard_data or {})
    calendars = dict(data.get("calendars") or {})

    if "pti" in calendars and "pti_collective" not in calendars:
        calendars["pti_collective"] = calendars["pti"]
    if "goslow" in calendars and "vedic_pti" not in calendars:
        calendars["vedic_pti"] = calendars["goslow"]

    if "personal" in calendars:
        p = calendars["personal"] or {}
        if "data" in p and isinstance(p.get("data"), dict):
            inner_data = p["data"]
            daily_results = inner_data.get("daily_periods") or inner_data.get("daily_results") or []
        else:
            daily_results = p.get("daily_results") or []

        daily_scores = []
        for dr in daily_results:
            if isinstance(dr, dict):
                daily_scores.append({
                    "date": dr.get("date"),
                    "quality": dr.get("quality", dr.get("overall_quality", "neutral")),
                    "score": dr.get("total_score", dr.get("score", 0)),
                    "moon_house": dr.get("moon_house"),
                    "moon_house_name": dr.get("moon_house_name", ""),
                    "tithi_name": dr.get("tithi_name", ""),
                    "nakshatra": dr.get("nakshatra", ""),
                    "score_breakdown": dr.get("score_breakdown", {}),
                })

        calendars["personal"] = {
            "calendar_type": "Personal_Calendar",
            "data": {
                "daily_periods": daily_results,
                "daily_scores": daily_scores,
            },
            "generated": bool(daily_results),
            "period": p.get("period", {}),
        }

    if "pti_collective" in calendars:
        pti = calendars["pti_collective"] or {}
        if "data" in pti and isinstance(pti.get("data"), dict):
            timing_data = pti["data"].get("timing_data") or []
        else:
            timing_data = pti.get("timing_data") or []

        calendars["pti_collective"] = {
            "calendar_type": "PTI_Collective_Calendar",
            "data": {
                "timing_data": timing_data
            },
            "generated": bool(timing_data),
            "period": pti.get("period", {}),
        }

    if "vedic_pti" in calendars:
        v = calendars["vedic_pti"] or calendars.get("goslow") or {}
        if "data" in v and isinstance(v.get("data"), dict):
            results = v["data"].get("results") or []
        else:
            results = v.get("results") or []
        calendars["vedic_pti"] = {
            "calendar_type": "Vedic_PTI_Calendar",
            "data": {
                "results": results
            },
            "generated": bool(results),
            "period": v.get("period", {}),
        }

    if "combined" in calendars:
        c = calendars["combined"] or {}
        if "data" in c and isinstance(c.get("data"), dict):
            results = c["data"].get("results") or []
        else:
            results = c.get("results") or []

        pti_data = calendars.get("pti_collective", {}).get("data", {}).get("timing_data", [])
        vedic_data = calendars.get("vedic_pti", {}).get("data", {}).get("results", [])
        pti_by_date = {}
        for td in pti_data:
            if isinstance(td, dict) and td.get("date"):
                pti_by_date[td["date"]] = td
        vedic_by_date = {}
        for vd in vedic_data:
            if isinstance(vd, dict) and vd.get("date"):
                vedic_by_date[vd["date"]] = vd

        if results:
            apply_double_go_to_combined_results(results, pti_by_date, vedic_by_date)

        calendars["combined"] = {
            "calendar_type": "Combined_Calendar",
            "data": {
                "results": results
            },
            "generated": bool(results),
            "period": c.get("period", {}),
        }

    if "bird_batch" in calendars:
        b = calendars["bird_batch"] or {}
        filtered = b.get("filtered_periods") or b.get("results") or []
        calendars["bird_batch"] = {
            "calendar_type": "Bird_Batch",
            "data": {
                "filtered_periods": filtered
            },
            "generated": bool(filtered),
        }

    for dead in ("pti", "goslow", "electional"):
        calendars.pop(dead, None)

    data["calendars"] = calendars
    return data
