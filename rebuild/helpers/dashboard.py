"""
Dashboard generation core logic
Generates all calendar data for the dashboard view
"""

import os
import sys
import json
import math
import traceback
from datetime import date, datetime, timedelta
from flask import session

from helpers.utils import (
    get_user_calendar_range, get_two_month_range,
    make_json_serializable, normalize_dashboard_data,
    calculate_is_double_go, apply_double_go_to_combined_results
)
from helpers.astro import find_nakshatra_transits_for_range
from database.manager import db_manager
from database.models import UserProfile


def get_user_defaults():
    user_profile = session.get('user_profile', {})
    defaults = {}
    if user_profile:
        defaults.update({
            'birth_date': user_profile.get('birth_date'),
            'birth_time': user_profile.get('birth_time'),
            'birth_latitude': user_profile.get('birth_location', {}).get('latitude'),
            'birth_longitude': user_profile.get('birth_location', {}).get('longitude'),
            'birth_location_name': user_profile.get('birth_location', {}).get('name'),
            'latitude': user_profile.get('current_location', {}).get('latitude'),
            'longitude': user_profile.get('current_location', {}).get('longitude'),
            'location': user_profile.get('current_location', {}).get('name'),
            'timezone': user_profile.get('timezone', 'America/New_York')
        })
    return defaults


def _json_sanitize(obj):
    if obj is None or isinstance(obj, (str, int, bool)):
        return obj
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
        return obj
    if isinstance(obj, (date, datetime)):
        return obj.isoformat()
    if isinstance(obj, dict):
        return {str(k): _json_sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [_json_sanitize(v) for v in obj]
    if hasattr(obj, '__dict__'):
        try:
            return _json_sanitize(vars(obj))
        except Exception:
            pass
    return str(obj)


def normalize_for_ui(dashboard_data: dict) -> dict:
    try:
        calendars = (dashboard_data or {}).get("calendars", {})
        personal = calendars.get("personal")
        if isinstance(personal, dict) and isinstance(personal.get("daily_results"), list):
            by_date, daily_scores = {}, {}
            for item in personal["daily_results"]:
                dk = item.get("date")
                if not dk:
                    continue
                by_date[dk] = item
                ds = item.get("day_score")
                if isinstance(ds, dict):
                    quality = ds.get("quality", "neutral")
                    score = ds.get("score", 0)
                else:
                    try:
                        score = float(ds)
                    except Exception:
                        score = 0.0
                    quality = "good" if score > 0 else ("bad" if score < 0 else "neutral")
                daily_scores[dk] = {"quality": quality, "score": score, "moon_house": item.get("moon_house")}
            personal["daily_results_by_date"] = by_date
            personal["daily_scores"] = daily_scores
    except Exception as e:
        print(f"normalize_for_ui error: {e}")
    return dashboard_data


def _tz_offset_hours(data, defaults, fallback=-5.0):
    try:
        if "timezone_offset" in data and data["timezone_offset"] is not None:
            return float(data["timezone_offset"])
        if "utc_offset_minutes" in data and data["utc_offset_minutes"] is not None:
            return float(data["utc_offset_minutes"]) / 60.0
        if "timezone_offset" in defaults and defaults["timezone_offset"] is not None:
            return float(defaults["timezone_offset"])
    except Exception:
        pass
    tz = (data.get("timezone") or defaults.get("timezone") or "").lower()
    if tz in {"america/new_york", "us/eastern", "eastern"}:
        return -5.0
    if tz in {"america/los_angeles", "us/pacific", "pacific"}:
        return -8.0
    if tz in {"america/chicago", "us/central", "central"}:
        return -6.0
    if tz in {"america/denver", "us/mountain", "mountain"}:
        return -7.0
    return float(fallback)


def _normalize_personal_rows(rows, start_d, end_d):
    PERSONAL_KEYS = ("date", "day_score", "moon_house", "moon_sign", "moon_nakshatra", "tithi", "transits")
    by_date = {}
    for r in rows or []:
        d = r.get("date")
        if isinstance(d, date):
            ds = d.isoformat()
        else:
            ds = str(d) if d else None
        if not ds:
            continue
        norm = {k: r.get(k) for k in PERSONAL_KEYS}
        norm["date"] = ds
        if norm.get("transits") is None:
            norm["transits"] = {}
        by_date[ds] = norm

    out = []
    cur = start_d
    while cur <= end_d:
        ds = cur.isoformat()
        out.append(by_date.get(ds, {
            "date": ds, "day_score": None, "moon_house": None,
            "moon_sign": None, "moon_nakshatra": None, "tithi": None, "transits": {},
        }))
        cur += timedelta(days=1)
    return out


def generate_dashboard_core(data: dict, user_id: str = None) -> dict:
    if user_id and data.get("force_regenerate"):
        try:
            db_manager.clear_calendar_data(user_id)
        except Exception:
            pass

    try:
        if user_id and not data.get("force_regenerate"):
            saved = db_manager.get_calendar_data(user_id)
            if saved:
                cached_days = saved.get("period", {}).get("days", 60)
                requested_days = data.get("days")
                if requested_days is None:
                    _, _, requested_days = get_two_month_range()
                try:
                    requested_days = int(requested_days) if requested_days else 60
                    cached_days = int(cached_days) if cached_days else 60
                except (ValueError, TypeError):
                    requested_days = 60
                    cached_days = 60

                if abs(cached_days - requested_days) <= 2:
                    cached_result = {
                        "dashboard_type": "Complete_6_Calendar_Dashboard",
                        "period": {"days": cached_days, "generated_at": saved.get("period", {}).get("generated_at")},
                        "calendars": saved.get("calendars", {}),
                        "from_cache": True,
                        "background_days": saved.get("background_days", []),
                    }
                    cached_result = normalize_dashboard_data(cached_result)
                    return cached_result
    except Exception:
        traceback.print_exc()

    user_defaults = get_user_defaults()

    birth_date = data.get("birth_date") or user_defaults.get("birth_date")
    birth_time = data.get("birth_time") or user_defaults.get("birth_time")
    birth_latitude = float(data.get("birth_latitude") or user_defaults.get("birth_latitude", 25.76))
    birth_longitude = float(data.get("birth_longitude") or user_defaults.get("birth_longitude", -80.19))
    location = data.get("location") or user_defaults.get("location", "Miami, FL")
    latitude = float(data.get("latitude") or user_defaults.get("latitude", 25.76))
    longitude = float(data.get("longitude") or user_defaults.get("longitude", -80.19))
    timezone_offset = _tz_offset_hours(data, user_defaults, fallback=-5.0)
    timezone_label = data.get("timezone") or user_defaults.get("timezone")

    if "days" in data and data.get("days") is not None:
        days = int(data.get("days"))
    else:
        _, _, days = get_two_month_range()

    dashboard_results = {
        "dashboard_type": "Complete_6_Calendar_Dashboard",
        "period": {"days": days, "generated_at": datetime.now().isoformat()},
        "calendars": {},
    }

    # 1) Bird Batch
    try:
        from filters.bird_batch_filter import BirdBatchFilter
        bird_filter = BirdBatchFilter()
        bird_result = bird_filter.process_batch(
            start_date=datetime.now().strftime("%Y-%m-%d"),
            days=days, max_periods_per_day=6,
            birth_date=birth_date,
            birth_time=birth_time if ':' in str(birth_time or '') else None,
            birth_latitude=birth_latitude,
            birth_longitude=birth_longitude,
        )
        dashboard_results["calendars"]["bird_batch"] = bird_result
    except Exception as e:
        dashboard_results["calendars"]["bird_batch"] = {"error": str(e)}

    # 2) Personal
    if birth_date and birth_time:
        try:
            from personal_calendar.personal_transit_yp import EnhancedPersonalTransitCalculator
            personal_calc = EnhancedPersonalTransitCalculator()

            if isinstance(birth_date, str):
                birth_date_obj = datetime.strptime(birth_date, "%Y-%m-%d").date()
            else:
                birth_date_obj = birth_date
            if isinstance(birth_time, str):
                try:
                    birth_time_obj = datetime.strptime(birth_time, "%H:%M:%S").time()
                except ValueError:
                    birth_time_obj = datetime.strptime(birth_time, "%H:%M").time()
            else:
                birth_time_obj = birth_time

            p_start, p_end, _ = get_two_month_range()
            expected_days = (p_end - p_start).days + 1

            bulk_rows = None
            try:
                if hasattr(personal_calc, "generate_personal_calendar"):
                    birth_chart = personal_calc.calculate_birth_chart(
                        birth_date_obj, birth_time_obj, birth_latitude,
                        birth_longitude, timezone_offset
                    )
                    if birth_chart:
                        bulk = personal_calc.generate_personal_calendar(
                            birth_chart, p_start, p_end,
                            birth_latitude, birth_longitude,
                            timezone_offset, "composite"
                        )
                        if isinstance(bulk, dict):
                            bulk_rows = []
                            for date_str, day_data in bulk.items():
                                if day_data.get('personal_score'):
                                    bulk_rows.append({
                                        'date': date_str,
                                        'day_score': {
                                            'quality': day_data['personal_score'].get('quality', 'neutral'),
                                            'score': day_data['personal_score'].get('score', 0),
                                            'factors': day_data['personal_score'].get('factors', []),
                                        },
                                        'moon_house': day_data['personal_score'].get('moon_house'),
                                        'moon_sign': day_data['personal_score'].get('transits', {}).get('moon_sign'),
                                        'weekday': day_data.get('weekday', '')
                                    })
            except Exception as e:
                print(f"Personal bulk failed: {e}")
                bulk_rows = None

            personal_rows = bulk_rows if bulk_rows and len(bulk_rows) == expected_days else []
            if not personal_rows:
                try:
                    birth_chart = personal_calc.calculate_birth_chart(
                        birth_date_obj, birth_time_obj, birth_latitude,
                        birth_longitude, timezone_offset
                    )
                    cur = p_start
                    while cur <= p_end:
                        try:
                            daily_transits = personal_calc.calculate_daily_transits(
                                cur, birth_latitude, birth_longitude, timezone_offset
                            )
                            if daily_transits and birth_chart:
                                day_score = personal_calc.score_personal_day(birth_chart, daily_transits)
                                moon_house = personal_calc.calculate_moon_house_from_lagna(
                                    birth_chart["lagna_sign"], daily_transits["moon_sign"]
                                )
                                personal_rows.append({
                                    "date": cur.isoformat(),
                                    "day_score": day_score,
                                    "moon_house": moon_house,
                                    "moon_sign": daily_transits.get("moon_sign"),
                                    "transits": daily_transits,
                                })
                        except Exception:
                            pass
                        cur += timedelta(days=1)
                except Exception as e:
                    print(f"Personal fallback error: {e}")

            personal_rows = _normalize_personal_rows(personal_rows, p_start, p_end)

            try:
                birth_chart_payload = personal_calc.calculate_birth_chart(
                    birth_date_obj, birth_time_obj, birth_latitude, birth_longitude, timezone_offset
                )
            except Exception:
                birth_chart_payload = {}

            nakshatra_transits_serializable = []
            try:
                from timezonefinder import TimezoneFinder
                tf = TimezoneFinder()
                tz_name = tf.timezone_at(lat=birth_latitude, lng=birth_longitude)
                nakshatra_transits_raw = find_nakshatra_transits_for_range(
                    p_start, p_end, tz_offset=timezone_offset,
                    lat=birth_latitude, lon=birth_longitude, tz_name=tz_name
                )
                for t in nakshatra_transits_raw:
                    nakshatra_transits_serializable.append({
                        'nakshatra_num': t.get('nakshatra_num'),
                        'nakshatra_name': t.get('nakshatra_name'),
                        'ruler': t.get('ruler'),
                        'entry_time': t.get('entry_time').isoformat() if t.get('entry_time') else None,
                        'exit_time': t.get('exit_time').isoformat() if t.get('exit_time') else None,
                    })
            except Exception:
                pass

            dashboard_results["calendars"]["personal"] = {
                "calendar_type": "Enhanced_Personal_Transit",
                "birth_chart": birth_chart_payload,
                "period": {"start_date": p_start.isoformat(), "end_date": p_end.isoformat()},
                "total_periods": len(personal_rows),
                "daily_results": personal_rows,
                "nakshatra_transits": nakshatra_transits_serializable,
            }
        except Exception as e:
            print(f"Personal calendar error: {e}")
            traceback.print_exc()
            dashboard_results["calendars"]["personal"] = {"error": str(e)}
    else:
        dashboard_results["calendars"]["personal"] = {"error": "Birth data required"}

    # 3) PTI Collective
    try:
        from core.magi_collective import PTICollectiveCalendar
        pti_system = PTICollectiveCalendar()
        start_date_pti, end_date_pti, _ = get_two_month_range()
        start_dt = datetime.combine(start_date_pti, datetime.min.time())
        days_count_pti = (end_date_pti - start_date_pti).days + 1
        pti_result = pti_system.generate_calendar(start_dt, days_count_pti)
        dashboard_results["calendars"]["pti"] = {
            "calendar_type": "PTI_Collective",
            "results": pti_result,
            "period": {"start_date": start_date_pti.isoformat(), "end_date": end_date_pti.isoformat()},
            "generated": True,
        }
    except Exception as e:
        print(f"PTI Collective error: {e}")
        traceback.print_exc()
        dashboard_results["calendars"]["pti"] = {"error": str(e), "generated": False}

    # 4) Vedic Collective
    try:
        from core.vedic_collective import classify_day_rules
        start_date_vs, end_date_vs, _ = get_two_month_range()
        cur = start_date_vs
        vedic_results = []
        while cur <= end_date_vs:
            day_result = classify_day_rules(cur)
            vedic_results.append(day_result)
            cur += timedelta(days=1)
        dashboard_results["calendars"]["goslow"] = {
            "calendar_type": "Vedic_Collective_Calendar",
            "period": {"start_date": start_date_vs.isoformat(), "end_date": end_date_vs.isoformat()},
            "results": vedic_results,
            "generated": True,
        }
    except Exception as e:
        print(f"Vedic Collective error: {e}")
        traceback.print_exc()
        dashboard_results["calendars"]["goslow"] = {"error": str(e), "generated": False}

    # 5) Combined
    try:
        from core.combined_calendar import CombinedCalendarAnalyzer
        combined_calc = CombinedCalendarAnalyzer()
        personal_data = dashboard_results["calendars"].get("personal", {})
        daily_results = personal_data.get("daily_results", [])
        daily_scores = {}
        for item in daily_results:
            try:
                date_key = item.get("date")
                ds = item.get("day_score") or {}
                if isinstance(ds, dict) and date_key:
                    daily_scores[date_key] = {
                        "quality": ds.get("quality", "neutral"),
                        "score": float(ds.get("score", 0.0)),
                        "moon_house": item.get("moon_house"),
                    }
            except Exception:
                continue

        calendar_data_for_combined = {
            "personal": {"data": {"daily_periods": daily_results, "daily_scores": daily_scores}},
            "pti_collective": {"data": dashboard_results["calendars"].get("pti", {})},
            "vedic_pti": {"data": dashboard_results["calendars"].get("goslow", {})},
        }
        combined_result = combined_calc.analyze_calendar_data(calendar_data_for_combined)
        dashboard_results["calendars"]["combined"] = {
            "calendar_type": "Combined_All_Calendar",
            "results": combined_result.get("results", []),
            "summary": combined_result.get("summary", {}),
            "generated": True,
        }
    except Exception as e:
        print(f"Combined calendar error: {e}")
        traceback.print_exc()
        dashboard_results["calendars"]["combined"] = {"error": str(e), "generated": False}

    # Save to DB
    background_days_to_save = []
    try:
        if user_id:
            selected_dates_from_request = data.get("selected_dates")
            if selected_dates_from_request is not None:
                background_days_to_save = selected_dates_from_request
            else:
                try:
                    existing_saved = db_manager.get_calendar_data(user_id)
                    if existing_saved:
                        background_days_to_save = existing_saved.get("background_days", [])
                except Exception:
                    pass

            calendar_data_to_save = {
                "birth_data": {
                    "birth_date": birth_date, "birth_time": birth_time,
                    "birth_latitude": birth_latitude, "birth_longitude": birth_longitude,
                    "timezone_offset": timezone_offset, "timezone": timezone_label,
                },
                "location": {"name": location, "latitude": latitude, "longitude": longitude},
                "background_days": background_days_to_save,
                "calendars": dashboard_results["calendars"],
                "period": {"days": days, "generated_at": datetime.now().isoformat()},
            }
            calendar_data_to_save = make_json_serializable(calendar_data_to_save)
            json.dumps(calendar_data_to_save)
            db_manager.save_calendar_data(user_id, calendar_data_to_save)
    except Exception:
        traceback.print_exc()

    dashboard_results["background_days"] = background_days_to_save
    return dashboard_results
