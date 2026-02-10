"""
Astronomical helper functions
Moon position, nakshatra calculations using Swiss Ephemeris
"""

import os
import swisseph as swe
from datetime import datetime, timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo

NAKSHATRA_RULERS = [
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
    "Ketu", "Venus", "Sun", "Moon", "Mars", "Rahu", "Jupiter", "Saturn", "Mercury",
]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha",
    "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha",
    "Shravana", "Dhanishta", "Shatabhisha", "Purva Bhadrapada",
    "Uttara Bhadrapada", "Revati"
]

NAKSHATRA_SPAN = 360.0 / 27.0


def _ensure_swe_path():
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        swe.set_ephe_path(current_dir)
    except Exception:
        pass


def get_moon_sidereal_position(dt, lat=0, lon=0, tz_offset=-5, tz_name=None):
    _ensure_swe_path()

    if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
        utc_dt = dt.astimezone(dt_timezone.utc).replace(tzinfo=None)
    elif tz_name:
        try:
            local_tz = ZoneInfo(tz_name)
            local_aware = dt.replace(tzinfo=local_tz)
            utc_dt = local_aware.astimezone(dt_timezone.utc).replace(tzinfo=None)
        except Exception:
            utc_dt = dt - timedelta(hours=tz_offset)
    else:
        utc_dt = dt - timedelta(hours=tz_offset)

    jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day,
                    utc_dt.hour + utc_dt.minute / 60.0 + utc_dt.second / 3600.0)

    try:
        swe.set_topo(lon, lat, 0)
        moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_TOPOCTR)[0][0]
    except Exception:
        try:
            moon_pos = swe.calc_ut(jd, swe.MOON)[0][0]
        except Exception:
            moon_pos = swe.calc_ut(jd, swe.MOON, swe.FLG_MOSEPH)[0][0]

    swe.set_sid_mode(swe.SIDM_LAHIRI)
    ayanamsa = swe.get_ayanamsa_ut(jd)
    sidereal_moon = (moon_pos - ayanamsa) % 360.0

    return sidereal_moon


def get_nakshatra_from_longitude(sidereal_lon):
    nak_num = int(sidereal_lon / NAKSHATRA_SPAN)
    if nak_num >= 27:
        nak_num = 26
    nak_name = NAKSHATRA_NAMES[nak_num]
    nak_ruler = NAKSHATRA_RULERS[nak_num]
    return nak_num, nak_name, nak_ruler


def find_nakshatra_periods_for_day(day_date, tz_offset=-5, lat=0, lon=0, tz_name=None):
    day_start = datetime.combine(day_date, datetime.min.time())
    day_end = datetime.combine(day_date, datetime.max.time().replace(microsecond=0))

    def local_to_utc(local_dt):
        if tz_name:
            try:
                local_tz = ZoneInfo(tz_name)
                local_aware = local_dt.replace(tzinfo=local_tz)
                return local_aware.astimezone(dt_timezone.utc).replace(tzinfo=None)
            except Exception:
                pass
        return local_dt - timedelta(hours=tz_offset)

    moon_lon = get_moon_sidereal_position(day_start, lat, lon, tz_offset, tz_name)
    current_nak_num, current_nak_name, current_nak_ruler = get_nakshatra_from_longitude(moon_lon)

    current_start = day_start
    check_time = day_start + timedelta(minutes=30)
    periods = []

    while check_time <= day_end:
        moon_lon = get_moon_sidereal_position(check_time, lat, lon, tz_offset, tz_name)
        nak_num, nak_name, nak_ruler = get_nakshatra_from_longitude(moon_lon)

        if nak_num != current_nak_num:
            search_start = check_time - timedelta(minutes=30)
            search_end = check_time

            while (search_end - search_start).total_seconds() > 60:
                mid_time = search_start + (search_end - search_start) / 2
                moon_mid = get_moon_sidereal_position(mid_time, lat, lon, tz_offset, tz_name)
                nak_mid_num, _, _ = get_nakshatra_from_longitude(moon_mid)

                if nak_mid_num == current_nak_num:
                    search_start = mid_time
                else:
                    search_end = mid_time

            transition_time = search_end
            start_utc = local_to_utc(current_start)
            end_utc = local_to_utc(transition_time)

            periods.append({
                'nakshatra_num': current_nak_num,
                'nakshatra_name': current_nak_name,
                'ruler': current_nak_ruler,
                'start_time': start_utc,
                'end_time': end_utc,
                'start_local': current_start,
                'end_local': transition_time
            })

            current_start = transition_time
            current_nak_num = nak_num
            current_nak_name = nak_name
            current_nak_ruler = nak_ruler
            check_time = transition_time

        check_time += timedelta(minutes=30)

    start_utc = local_to_utc(current_start)
    end_utc = local_to_utc(day_end)

    periods.append({
        'nakshatra_num': current_nak_num,
        'nakshatra_name': current_nak_name,
        'ruler': current_nak_ruler,
        'start_time': start_utc,
        'end_time': end_utc,
        'start_local': current_start,
        'end_local': day_end
    })

    return periods


def find_nakshatra_transits_for_range(start_date, end_date, tz_offset=-5, lat=0, lon=0, tz_name=None):
    all_periods = []
    current_date = start_date
    while current_date <= end_date:
        day_periods = find_nakshatra_periods_for_day(current_date, tz_offset, lat, lon, tz_name)
        all_periods.extend(day_periods)
        current_date += timedelta(days=1)
    return all_periods
