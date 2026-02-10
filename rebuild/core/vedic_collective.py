#!/usr/bin/env python3
"""
Vedic Transit Calendar Generator - EVIDENCE-BASED Version
Implements the 9-layer priority hierarchy discovered from CSV analysis.

Key features:
- Rahu/Ketu node positions calculated
- Oppositions, trines, sextiles, squares (not just conjunction)
- Eclipse detection (highest priority override)
- Lunar illumination factor
- Nakshatra Guna system (7 categories)
- Jupiter/Venus benefic aspects to Moon
- Moon in Saturn's signs (Capricorn/Aquarius) -> BUILD
- Green subtypes (Type I-IV) based on nakshatra guna
- Mars Moon as overlay
"""

from datetime import datetime, timedelta
import math
import swisseph as swe

use_swieph = True
try:
    swe.set_ephe_path('.')
except Exception:
    use_swieph = False
swe.set_sid_mode(swe.SIDM_LAHIRI)


def _calc(jd, planet_id):
    global use_swieph
    try:
        if use_swieph:
            return swe.calc_ut(jd, planet_id)
        else:
            raise Exception("No ephe files")
    except Exception:
        try:
            return swe.calc_ut(jd, planet_id, swe.FLG_MOSEPH)
        except Exception:
            return [[0.0, 0.0, 0.0, 0.0, 0.0, 0.0], []]


NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

NAKSHATRA_GUNA = {
    "Ashwini": "Kshipra", "Bharani": "Ugra", "Krittika": "Mishra",
    "Rohini": "Dhruva", "Mrigashira": "Mridu", "Ardra": "Tikshna",
    "Punarvasu": "Chara", "Pushya": "Kshipra", "Ashlesha": "Tikshna",
    "Magha": "Ugra", "Purva Phalguni": "Ugra", "Uttara Phalguni": "Dhruva",
    "Hasta": "Kshipra", "Chitra": "Mridu", "Swati": "Chara",
    "Vishakha": "Mishra", "Anuradha": "Mridu", "Jyeshtha": "Tikshna",
    "Mula": "Tikshna", "Purva Ashadha": "Ugra", "Uttara Ashadha": "Dhruva",
    "Shravana": "Chara", "Dhanishta": "Chara", "Shatabhisha": "Chara",
    "Purva Bhadrapada": "Ugra", "Uttara Bhadrapada": "Dhruva", "Revati": "Mridu",
}

BENEFIC_GUNA = {"Kshipra", "Mridu"}
MALEFIC_GUNA = {"Ugra", "Tikshna", "Mishra"}
NEUTRAL_GUNA = {"Chara", "Dhruva"}

GREEN_SUBTYPES = {
    "Kshipra": ("Type I", "Light & Swift — beginnings, travel, quick action"),
    "Mridu": ("Type II", "Soft & Tender — arts, romance, learning, healing"),
    "Dhruva": ("Type III", "Fixed & Stable — long-term foundations, durability"),
    "Chara": ("Type IV", "Moveable — change, relocation, new directions"),
}


def angular_separation(lon1, lon2):
    diff = abs(lon1 - lon2) % 360
    if diff > 180:
        diff = 360 - diff
    return diff


def check_aspect(lon1, lon2, aspect_angle, orb):
    sep = angular_separation(lon1, lon2)
    diff_from_aspect = abs(sep - aspect_angle)
    return diff_from_aspect <= orb, diff_from_aspect


def get_sidereal_sign(longitude, ayanamsa):
    sid_long = (longitude - ayanamsa) % 360
    sign_index = int(sid_long / 30)
    signs = [
        "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
        "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
    ]
    return signs[sign_index], sign_index


def get_tithi(sun_long, moon_long):
    phase = (moon_long - sun_long) % 360
    return int(phase // 12) + 1


def get_nakshatra(moon_sid_long):
    nak_index = int(moon_sid_long // (360 / 27))
    return nak_index, NAKSHATRA_NAMES[nak_index]


def lunar_illumination(sun_long, moon_long):
    elongation = (moon_long - sun_long) % 360
    illumination = (1 - math.cos(math.radians(elongation))) / 2 * 100
    return illumination


def check_eclipse_on_day(jd):
    s = _calc(jd, swe.SUN)[0][0]
    m = _calc(jd, swe.MOON)[0][0]
    r = _calc(jd, swe.MEAN_NODE)[0][0]
    k = (r + 180) % 360

    sun_moon_sep = angular_separation(s, m)
    s_r = angular_separation(s, r)
    s_k = angular_separation(s, k)
    m_r = angular_separation(m, r)
    m_k = angular_separation(m, k)

    is_new_moon = sun_moon_sep < 5
    is_full_moon = abs(sun_moon_sep - 180) < 5

    if is_new_moon and (s_r < 12 or s_k < 12):
        return True, "solar"
    if is_full_moon and (m_r < 9 or m_k < 9):
        return True, "lunar"

    return False, None


def get_all_positions(jd):
    planets = {
        'Sun': swe.SUN, 'Moon': swe.MOON, 'Mars': swe.MARS,
        'Jupiter': swe.JUPITER, 'Venus': swe.VENUS,
        'Saturn': swe.SATURN, 'Rahu': swe.MEAN_NODE,
    }
    positions = {}
    for name, pid in planets.items():
        positions[name] = _calc(jd, pid)[0][0]
    positions['Ketu'] = (positions['Rahu'] + 180) % 360
    return positions


def get_moon_aspects(positions):
    moon = positions['Moon']
    aspects = {}

    aspect_checks = {
        'Saturn': {'conjunction': 12, 'opposition': 12, 'square': 8},
        'Mars': {'conjunction': 10, 'opposition': 10},
        'Rahu': {'conjunction': 12, 'opposition': 12},
        'Ketu': {'conjunction': 12, 'opposition': 12},
        'Jupiter': {'conjunction': 10, 'trine': 8, 'sextile': 6},
        'Venus': {'conjunction': 8, 'trine': 8, 'sextile': 6},
    }

    aspect_angles = {
        'conjunction': 0, 'opposition': 180, 'square': 90,
        'trine': 120, 'sextile': 60,
    }

    for planet, checks in aspect_checks.items():
        planet_aspects = {}
        for aspect_name, orb in checks.items():
            angle = aspect_angles[aspect_name]
            is_active, exactness = check_aspect(moon, positions[planet], angle, orb)
            if is_active:
                planet_aspects[aspect_name] = {
                    'active': True,
                    'orb': round(exactness, 2),
                    'separation': round(angular_separation(moon, positions[planet]), 2)
                }
        if planet_aspects:
            aspects[planet] = planet_aspects

    return aspects


def has_benefic_jupiter_aspect(aspects):
    if 'Jupiter' not in aspects:
        return False
    return any(a in aspects['Jupiter'] for a in ['conjunction', 'trine', 'sextile'])


def has_benefic_venus_aspect(aspects):
    if 'Venus' not in aspects:
        return False
    return any(a in aspects['Venus'] for a in ['conjunction', 'trine', 'sextile'])


def has_any_benefic_aspect(aspects):
    return has_benefic_jupiter_aspect(aspects) or has_benefic_venus_aspect(aspects)


def classify_day(dt):
    jd = swe.julday(dt.year, dt.month, dt.day, 12.0)
    ayanamsa = swe.get_ayanamsa_ut(jd)

    positions = get_all_positions(jd)
    moon_long = positions['Moon']
    sun_long = positions['Sun']

    moon_sid = (moon_long - ayanamsa) % 360
    nak_index, nak_name = get_nakshatra(moon_sid)
    nak_guna = NAKSHATRA_GUNA[nak_name]

    tithi = get_tithi(sun_long, moon_long)
    illum = lunar_illumination(sun_long, moon_long)
    moon_sign, moon_sign_idx = get_sidereal_sign(moon_long, ayanamsa)

    aspects = get_moon_aspects(positions)
    eclipse_near, eclipse_type = check_eclipse_on_day(jd)

    mars_moon_overlay = False
    mars_reason = None
    if 'Mars' in aspects:
        mars_a = aspects['Mars']
        if 'conjunction' in mars_a or 'opposition' in mars_a:
            mars_moon_overlay = True
            if 'conjunction' in mars_a:
                mars_reason = f"Moon conjunct Mars (orb {mars_a['conjunction']['orb']})"
            else:
                mars_reason = f"Moon opposite Mars (orb {mars_a['opposition']['orb']})"

    classification = None
    color = None
    layer = None
    reason = None
    green_subtype = None
    green_subtype_desc = None
    rahu_ketu_contact = False
    saturn_contact = False

    if eclipse_near:
        classification = "MEGA RED"
        color = "mega_red"
        layer = "L1"
        reason = f"{'Solar' if eclipse_type == 'solar' else 'Lunar'} eclipse"

    elif tithi in {29, 30}:
        classification = "STOP"
        color = "red"
        layer = "L2"
        reason = "Amavasya (New Moon)" if tithi == 30 else "Chaturdashi Krishna — dark moon phase"

    elif tithi == 1:
        classification = "INWARD"
        color = "red"
        layer = "L2"
        reason = "Pratipada — day after new moon, rest and reflect"

    if classification is None:
        full_moon_tag = tithi == 15
        saturn_reason_detail = None

        if 'Saturn' in aspects:
            sat_a = aspects['Saturn']
            if 'conjunction' in sat_a:
                saturn_contact = True
                saturn_reason_detail = f"Moon conjunct Saturn (orb {sat_a['conjunction']['orb']})"
            elif 'opposition' in sat_a:
                saturn_contact = True
                saturn_reason_detail = f"Moon opposite Saturn (orb {sat_a['opposition']['orb']})"

        if moon_sign in ("Capricorn", "Aquarius") and not has_any_benefic_aspect(aspects):
            saturn_contact = True
            if saturn_reason_detail:
                saturn_reason_detail += f" + Moon in {moon_sign}"
            else:
                saturn_reason_detail = f"Moon transiting {moon_sign} (Saturn's sign) without benefic support"

        if saturn_contact:
            classification = "BUILD"
            color = "purple"
            layer = "L4"
            reason = saturn_reason_detail

        if classification is None:
            moon_rahu_sep = angular_separation(positions['Moon'], positions['Rahu'])
            moon_ketu_sep = angular_separation(positions['Moon'], positions['Ketu'])
            if moon_rahu_sep <= 12:
                rahu_ketu_contact = True
                classification = "SLOW"
                color = "yellow"
                layer = "L6"
                reason = f"Moon near Rahu (separation {moon_rahu_sep:.1f})"
            elif moon_ketu_sep <= 12:
                rahu_ketu_contact = True
                classification = "SLOW"
                color = "yellow"
                layer = "L6"
                reason = f"Moon near Ketu (separation {moon_ketu_sep:.1f})"
            elif 'Saturn' in aspects and 'square' in aspects['Saturn'] and nak_guna in MALEFIC_GUNA:
                classification = "SLOW"
                color = "yellow"
                layer = "L6"
                reason = f"Moon square Saturn + {nak_guna} nakshatra ({nak_name})"
            elif nak_guna in {"Ugra", "Mishra"} and not has_any_benefic_aspect(aspects):
                classification = "SLOW"
                color = "yellow"
                layer = "L6"
                reason = f"{nak_guna} nakshatra ({nak_name}) without benefic Jupiter/Venus aspect"

        if classification is None:
            if nak_guna in BENEFIC_GUNA and has_benefic_jupiter_aspect(aspects) and illum > 50:
                classification = "GO"
                color = "green"
                layer = "L7"
                if nak_guna in GREEN_SUBTYPES:
                    green_subtype, green_subtype_desc = GREEN_SUBTYPES[nak_guna]
                reason = f"Benefic {nak_guna} nakshatra ({nak_name}) + Jupiter aspect + {illum:.0f}% illumination"
            elif nak_guna in BENEFIC_GUNA and has_any_benefic_aspect(aspects) and nak_guna not in MALEFIC_GUNA:
                classification = "GO"
                color = "green"
                layer = "L7"
                if nak_guna in GREEN_SUBTYPES:
                    green_subtype, green_subtype_desc = GREEN_SUBTYPES[nak_guna]
                benefic = "Jupiter" if has_benefic_jupiter_aspect(aspects) else "Venus"
                reason = f"Benefic {nak_guna} nakshatra ({nak_name}) + {benefic} aspect"
            elif nak_guna in {"Dhruva", "Chara"} and has_benefic_jupiter_aspect(aspects) and illum > 50:
                classification = "GO"
                color = "green"
                layer = "L7"
                if nak_guna in GREEN_SUBTYPES:
                    green_subtype, green_subtype_desc = GREEN_SUBTYPES[nak_guna]
                reason = f"{nak_guna} nakshatra ({nak_name}) + Jupiter aspect + {illum:.0f}% illumination"

        if classification is None:
            if nak_guna in BENEFIC_GUNA and not has_any_benefic_aspect(aspects):
                classification = "MILD GO"
                color = "mild_green"
                layer = "L8"
                reason = f"Benefic {nak_guna} nakshatra ({nak_name}) but weaker planetary support"
            elif 'Venus' in aspects and 'conjunction' in aspects['Venus'] and nak_guna not in MALEFIC_GUNA:
                classification = "MILD GO"
                color = "mild_green"
                layer = "L8"
                reason = f"Moon conjunct Venus (orb {aspects['Venus']['conjunction']['orb']}) + {nak_name}"
            elif has_benefic_jupiter_aspect(aspects) and nak_guna not in MALEFIC_GUNA:
                jup_aspect = next(iter(aspects['Jupiter'].keys()))
                classification = "MILD GO"
                color = "mild_green"
                layer = "L8"
                reason = f"Moon {jup_aspect} Jupiter + {nak_name} (no malefic contact)"
            elif tithi in {13, 14, 16} and not saturn_contact and not rahu_ketu_contact:
                classification = "MILD GO"
                color = "mild_green"
                layer = "L8"
                reason = f"Near Full Moon (tithi {tithi}) — elevated lunar energy"

        if classification is None:
            classification = "NEUTRAL"
            color = "neutral"
            layer = "L9"
            reason = "No strong planetary influence on Moon today"

        if full_moon_tag and classification not in ("STOP", "MEGA RED", "INWARD"):
            reason = f"[FULL MOON] {reason}"

    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekday = weekdays[dt.weekday()]

    active_aspects_summary = {}
    for planet, planet_aspects in aspects.items():
        for asp_name, asp_data in planet_aspects.items():
            active_aspects_summary[f"Moon-{planet} {asp_name}"] = asp_data['orb']

    return {
        "date": dt.strftime('%Y-%m-%d'),
        "classification": classification,
        "color": color,
        "layer": layer,
        "reason": reason,
        "rule_reason": reason,
        "rule_number": int(layer[1:]) if layer else 9,
        "green_subtype": green_subtype,
        "green_subtype_desc": green_subtype_desc,
        "mars_moon_overlay": mars_moon_overlay,
        "mars_moon_reason": mars_reason,
        "tithi": tithi,
        "tithi_name": f"Tithi {tithi}",
        "nakshatra": nak_name,
        "nakshatra_guna": nak_guna,
        "moon_sign": moon_sign,
        "lunar_illumination": round(illum, 1),
        "weekday": weekday,
        "eclipse_nearby": eclipse_near,
        "eclipse_type": eclipse_type,
        "active_aspects": active_aspects_summary,
        "moon_longitude": round(moon_long, 2),
        "moon_sidereal": round(moon_sid, 2),
    }


def classify_day_rules(dt):
    return classify_day(dt)
