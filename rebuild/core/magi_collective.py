#!/usr/bin/env python3
"""
PTI Collective Calendar - Tuned Version
Cherry-picks the best parts from Production, V2.5, and V3 scripts,
calibrated against 2025 CSV reference data.

Design Decisions:
1. FROM PRODUCTION: Conservative Saturn veto (personal planets only), no helio in base score
2. FROM V2.5: Super Aspects, Cinderella Aspects, time-to-peak, geometry detection (informational)
3. FROM V3: Mars-Uranus deal-breaker (tight only), midpoint Saturn/Chiron heartbreak check
4. NEW CALIBRATIONS:
   - Wider Normal zone (score -2 to +3) to hit ~37% Normal target
   - Tighter Best criteria (require TIGHT super aspect peaking + high score)
   - Worst requires applying + tight/close orb
   - Long-term slow planet aspects heavily dampened (they're background noise)
   - Moon aspects weighted less (too transient to drive daily classification)
   - Slow threshold at score < -2 (not -1)

Target Distribution (from CSV):
  Best: ~7%, Go: ~32%, Normal: ~37%, Slow: ~14%, Worst: ~10%

Usage:
    python pti_tuned.py --start-date 2025-01-01 --days 365
"""

import argparse
import sys
import math
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

try:
    import swisseph as swe
    FULL_MODE = True
except ImportError:
    FULL_MODE = False
    print("Warning: Using simplified calculations (install pyswisseph for full accuracy)")

PLANETS = {
    'Sun': 0 if not FULL_MODE else swe.SUN,
    'Moon': 1 if not FULL_MODE else swe.MOON,
    'Mercury': 2 if not FULL_MODE else swe.MERCURY,
    'Venus': 3 if not FULL_MODE else swe.VENUS,
    'Mars': 4 if not FULL_MODE else swe.MARS,
    'Jupiter': 5 if not FULL_MODE else swe.JUPITER,
    'Saturn': 6 if not FULL_MODE else swe.SATURN,
    'Uranus': 7 if not FULL_MODE else swe.URANUS,
    'Neptune': 8 if not FULL_MODE else swe.NEPTUNE,
    'Pluto': 9 if not FULL_MODE else swe.PLUTO
}

@dataclass
class AspectInfo:
    planet1: str
    planet2: str
    aspect_type: str
    orb: float
    is_applying: bool
    strength_tier: str
    coordinate_type: str
    days_to_peak: Optional[float] = None

FAST_PLANETS = ['Moon', 'Mercury', 'Venus', 'Sun', 'Mars']
SLOW_PLANETS = ['Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto', 'Chiron']
PERSONAL_PLANETS = ['Sun', 'Mercury', 'Venus', 'Mars']
MAGI_BENEFICS = ['Jupiter', 'Venus', 'Chiron', 'Sun']
MAGI_MALEFICS = ['Saturn', 'Pluto']
TRANSCENDENT_PLANETS = {'Venus', 'Jupiter', 'Chiron', 'Neptune', 'Sun'}
CORE_PLANETS = {'Venus', 'Jupiter', 'Sun', 'Chiron'}

GOLDEN_ASPECTS = ['conjunction', 'trine', 'sextile']
TURBULENT_ASPECTS = ['square', 'opposition', 'quincunx']

ASPECT_DEFINITIONS = {
    'conjunction': 0,
    'sextile': 60,
    'square': 90,
    'trine': 120,
    'quincunx': 150,
    'opposition': 180
}

STRENGTH_TIERS = {
    "tight": (0.0, 0.5),
    "close": (0.5, 1.0),
    "moderate": (1.0, 2.0),
    "wide": (2.0, 3.0)
}

SUPER_ASPECTS = {
    'Jupiter-Pluto': 'Super Success',
    'Venus-Jupiter': 'Prosperity & Joy',
    'Mars-Jupiter': 'Bold Success',
    'Mars-Sun': 'Vitality & Leadership',
    'Mars-Mercury': 'Quick Action',
    'Mars-Uranus': 'Breakthrough Energy',
    'Mars-Neptune': 'Inspired Action',
    'Mars-Venus': 'Passionate Energy',
    'Mars-Pluto': 'Power Moves',
    'Venus-Pluto': 'Magnetic Attraction',
    'Pluto-Sun': 'Transformation',
    'Jupiter-Uranus': 'Sudden Fortune',
    'Sun-Jupiter': 'Confidence & Winning',
    'Venus-Chiron': 'True Love/Beauty',
    'Chiron-Neptune': 'Cinderella Magic'
}

CINDERELLA_ASPECTS = {
    'Venus-Chiron': 'Romantic/Creative Elevation',
    'Chiron-Neptune': 'Spiritual/Financial Windfall',
    'Venus-Neptune': 'Divine Beauty/Money'
}


class PTITunedCalendar:

    def __init__(self):
        self.LONGITUDE_ORB = 3.0
        self.DECLINATION_ORB = 1.2

        if FULL_MODE:
            try:
                swe.set_ephe_path('.')
            except:
                pass

    def date_to_julian_day(self, target_date, hour=12.0):
        if isinstance(target_date, datetime):
            target_date = target_date.date()
        if FULL_MODE:
            return swe.julday(target_date.year, target_date.month, target_date.day, hour)
        else:
            if target_date.month <= 2:
                year = target_date.year - 1
                month = target_date.month + 12
            else:
                year = target_date.year
                month = target_date.month
            a = year // 100
            b = 2 - a + (a // 4)
            jd = int(365.25 * (year + 4716)) + int(30.6001 * (month + 1)) + target_date.day + b - 1524.5
            return jd + hour / 24.0

    def get_strength_tier(self, orb: float) -> str:
        for tier_name, (min_orb, max_orb) in STRENGTH_TIERS.items():
            if min_orb <= orb < max_orb:
                return tier_name
        return "wide"

    def get_tier_weight(self, tier: str) -> float:
        weights = {"tight": 3.0, "close": 2.0, "moderate": 1.0, "wide": 0.5}
        return weights.get(tier, 0.5)

    def calculate_days_to_peak(self, orb: float, speed1: float, speed2: float) -> Optional[float]:
        if speed1 == 0 and speed2 == 0:
            return None
        relative_speed = abs(speed1 - speed2)
        if relative_speed < 0.001:
            return None
        days = orb / relative_speed
        return round(days, 1)

    def calculate_positions(self, target_date, latitude=0.0, longitude=0.0):
        if isinstance(target_date, datetime):
            target_date = target_date.date()

        if not FULL_MODE:
            return self._calculate_positions_simple(target_date)

        positions = {}
        jd = self.date_to_julian_day(target_date)

        swe.set_topo(longitude, latitude, 0)

        chiron_available = False
        try:
            test_jd = swe.julday(2025, 1, 1, 12.0)
            swe.calc_ut(test_jd, swe.CHIRON)
            chiron_available = True
        except:
            pass

        planets_to_calc = PLANETS.copy()
        if chiron_available:
            planets_to_calc['Chiron'] = swe.CHIRON

        try:
            for planet_name, planet_id in planets_to_calc.items():
                result = swe.calc_ut(jd, planet_id, swe.FLG_SWIEPH | swe.FLG_TOPOCTR | swe.FLG_SPEED)

                longitude_deg = result[0][0]
                latitude_deg = result[0][1]
                speed = result[0][3]

                obliquity_result = swe.calc_ut(jd, swe.ECL_NUT)
                obliquity = obliquity_result[0][0]

                long_rad = math.radians(longitude_deg)
                lat_rad = math.radians(latitude_deg)
                obl_rad = math.radians(obliquity)

                declination = math.degrees(
                    math.asin(
                        math.sin(lat_rad) * math.cos(obl_rad) +
                        math.cos(lat_rad) * math.sin(obl_rad) * math.sin(long_rad)
                    )
                )

                positions[planet_name] = {
                    'longitude': longitude_deg,
                    'declination': declination,
                    'latitude': latitude_deg,
                    'speed': speed
                }
        except Exception as e:
            print(f"Error calculating positions: {e}")
            return None

        return positions

    def _calculate_positions_simple(self, target_date):
        jd = self.date_to_julian_day(target_date)
        planets = {
            'Sun': {'period': 365.25, 'epoch_jd': 2451545.0, 'epoch_long': 280.0, 'obliquity': 23.44},
            'Moon': {'period': 27.32, 'epoch_jd': 2451545.0, 'epoch_long': 218.3, 'obliquity': 23.44},
            'Mercury': {'period': 87.97, 'epoch_jd': 2451545.0, 'epoch_long': 252.3, 'obliquity': 23.44},
            'Venus': {'period': 224.7, 'epoch_jd': 2451545.0, 'epoch_long': 181.9, 'obliquity': 23.44},
            'Mars': {'period': 686.98, 'epoch_jd': 2451545.0, 'epoch_long': 355.4, 'obliquity': 23.44},
            'Jupiter': {'period': 4332.6, 'epoch_jd': 2451545.0, 'epoch_long': 34.4, 'obliquity': 23.44},
            'Saturn': {'period': 10759.2, 'epoch_jd': 2451545.0, 'epoch_long': 50.1, 'obliquity': 23.44},
            'Uranus': {'period': 30688.5, 'epoch_jd': 2451545.0, 'epoch_long': 314.1, 'obliquity': 23.44},
            'Neptune': {'period': 60182.0, 'epoch_jd': 2451545.0, 'epoch_long': 304.3, 'obliquity': 23.44},
            'Pluto': {'period': 90560.0, 'epoch_jd': 2451545.0, 'epoch_long': 238.9, 'obliquity': 23.44}
        }

        positions = {}
        for planet_name, params in planets.items():
            days_since_epoch = jd - params['epoch_jd']
            mean_motion = 360.0 / params['period']
            longitude = (params['epoch_long'] + mean_motion * days_since_epoch) % 360.0
            obliquity = math.radians(params['obliquity'])
            longitude_rad = math.radians(longitude)
            declination = math.degrees(math.asin(math.sin(obliquity) * math.sin(longitude_rad)))
            positions[planet_name] = {
                'longitude': longitude,
                'declination': declination,
                'speed': mean_motion
            }
        return positions

    def angular_distance(self, pos1: float, pos2: float) -> float:
        diff = abs(pos1 - pos2) % 360.0
        return min(diff, 360.0 - diff)

    def is_aspect_applying(self, lon1, lon2, speed1, speed2, target_angle):
        current_diff = self.angular_distance(lon1, lon2)
        future_lon1 = (lon1 + speed1 * 0.1) % 360
        future_lon2 = (lon2 + speed2 * 0.1) % 360
        future_diff = self.angular_distance(future_lon1, future_lon2)
        current_distance = abs(current_diff - target_angle)
        future_distance = abs(future_diff - target_angle)
        return future_distance < current_distance

    def is_enhancement_aspect(self, aspect_type: str, planet1: str, planet2: str) -> bool:
        if aspect_type in ['conjunction', 'trine', 'sextile', 'parallel']:
            return True
        if aspect_type in ['quincunx', 'contraparallel']:
            if 'Saturn' in {planet1, planet2}:
                return False
            return True
        return False

    def find_longitude_aspects(self, positions_today, positions_tomorrow=None) -> List[AspectInfo]:
        aspects = []
        planet_names = list(positions_today.keys())

        for i, p1 in enumerate(planet_names):
            for p2 in planet_names[i+1:]:
                pos1 = positions_today[p1]
                pos2 = positions_today[p2]

                if 'longitude' not in pos1 or 'longitude' not in pos2:
                    continue

                lon1 = pos1['longitude']
                lon2 = pos2['longitude']
                diff = self.angular_distance(lon1, lon2)

                for aspect_name, target_angle in ASPECT_DEFINITIONS.items():
                    orb = abs(diff - target_angle)
                    if orb <= self.LONGITUDE_ORB:
                        speed1 = pos1.get('speed', 0)
                        speed2 = pos2.get('speed', 0)
                        is_applying = self.is_aspect_applying(lon1, lon2, speed1, speed2, target_angle)
                        days_to_peak = self.calculate_days_to_peak(orb, speed1, speed2) if is_applying else None

                        aspects.append(AspectInfo(
                            planet1=p1,
                            planet2=p2,
                            aspect_type=aspect_name,
                            orb=round(orb, 2),
                            is_applying=is_applying,
                            strength_tier=self.get_strength_tier(orb),
                            coordinate_type='longitude',
                            days_to_peak=days_to_peak
                        ))
        return aspects

    def find_declination_aspects(self, positions_today, positions_tomorrow=None) -> List[AspectInfo]:
        aspects = []
        planet_names = list(positions_today.keys())

        for i, p1 in enumerate(planet_names):
            for p2 in planet_names[i+1:]:
                pos1 = positions_today[p1]
                pos2 = positions_today[p2]

                if 'declination' not in pos1 or 'declination' not in pos2:
                    continue

                decl1 = pos1['declination']
                decl2 = pos2['declination']

                same_sign = (decl1 >= 0 and decl2 >= 0) or (decl1 < 0 and decl2 < 0)
                if same_sign:
                    orb = abs(decl1 - decl2)
                    if orb <= self.DECLINATION_ORB:
                        is_applying = True
                        if positions_tomorrow:
                            try:
                                decl1_tom = positions_tomorrow[p1]['declination']
                                decl2_tom = positions_tomorrow[p2]['declination']
                                orb_tomorrow = abs(decl1_tom - decl2_tom)
                                is_applying = orb_tomorrow < orb
                            except:
                                pass

                        aspects.append(AspectInfo(
                            planet1=p1, planet2=p2, aspect_type='parallel',
                            orb=round(orb, 2), is_applying=is_applying,
                            strength_tier=self.get_strength_tier(orb),
                            coordinate_type='declination'
                        ))
                else:
                    orb = abs(decl1 + decl2)
                    if orb <= self.DECLINATION_ORB:
                        is_applying = True
                        if positions_tomorrow:
                            try:
                                decl1_tom = positions_tomorrow[p1]['declination']
                                decl2_tom = positions_tomorrow[p2]['declination']
                                orb_tomorrow = abs(decl1_tom + decl2_tom)
                                is_applying = orb_tomorrow < orb
                            except:
                                pass

                        aspects.append(AspectInfo(
                            planet1=p1, planet2=p2, aspect_type='contraparallel',
                            orb=round(orb, 2), is_applying=is_applying,
                            strength_tier=self.get_strength_tier(orb),
                            coordinate_type='declination'
                        ))
        return aspects

    def classify_aspect_duration(self, planet1, planet2):
        if planet1 in SLOW_PLANETS and planet2 in SLOW_PLANETS:
            return 'long_term'
        elif planet1 in FAST_PLANETS or planet2 in FAST_PLANETS:
            return 'short_term'
        else:
            return 'medium_term'

    def check_deal_breakers(self, all_aspects: List[AspectInfo]) -> Tuple[bool, List[str]]:
        """
        Deal-breaker detection - calibrated version.
        
        Key differences from other versions:
        - Saturn: Only vetoes with PERSONAL planets, must be applying, tight/close orb
        - Saturn-Jupiter/Chiron: Nuclear/Heartbreak only at tight orb (<1.0°)
        - Mars-Uranus: Only at tight orb (<0.5°) and applying
        - Contraparallels: Only tight (<0.5°) Saturn-personal
        - Saturn-Neptune/Uranus: NEVER a deal-breaker (background noise)
        """
        clash_aspects = ['square', 'opposition']
        deal_breakers = []

        for aspect in all_aspects:
            if not aspect.is_applying:
                continue

            planets = {aspect.planet1, aspect.planet2}

            if 'Saturn' in planets:
                other_planet = (planets - {'Saturn'}).pop()

                if other_planet in PERSONAL_PLANETS:
                    if aspect.aspect_type in clash_aspects:
                        if aspect.strength_tier in ['tight', 'close']:
                            deal_breakers.append(
                                f"Saturn-{other_planet} {aspect.aspect_type} ({aspect.orb}°, applying)"
                            )
                    if aspect.aspect_type == 'contraparallel':
                        if aspect.strength_tier == 'tight':
                            deal_breakers.append(
                                f"Saturn-{other_planet} contraparallel ({aspect.orb}°, applying)"
                            )

                if other_planet == 'Jupiter':
                    if aspect.aspect_type in clash_aspects:
                        if aspect.strength_tier in ['tight', 'close']:
                            deal_breakers.append(
                                f"NUCLEAR: Saturn-Jupiter {aspect.aspect_type} ({aspect.orb}°)"
                            )

                if other_planet == 'Chiron':
                    if aspect.aspect_type in clash_aspects:
                        if aspect.strength_tier in ['tight', 'close']:
                            deal_breakers.append(
                                f"HEARTBREAK: Saturn-Chiron {aspect.aspect_type} ({aspect.orb}°)"
                            )

            if planets == {'Mars', 'Uranus'}:
                if aspect.aspect_type in clash_aspects:
                    if aspect.strength_tier in ['tight', 'close']:
                        deal_breakers.append(
                            f"Mars-Uranus {aspect.aspect_type} ({aspect.orb}°) - chaos risk"
                        )

            if 'Pluto' in planets and 'Saturn' not in planets:
                other_planet = (planets - {'Pluto'}).pop()
                if other_planet in ['Sun', 'Venus']:
                    if aspect.aspect_type in clash_aspects:
                        if aspect.strength_tier == 'tight' and aspect.orb <= 0.3:
                            deal_breakers.append(
                                f"Pluto-{other_planet} {aspect.aspect_type} ({aspect.orb}°)"
                            )

        return len(deal_breakers) > 0, deal_breakers

    def find_super_aspects(self, all_aspects: List[AspectInfo]) -> List[Tuple[str, str, AspectInfo]]:
        super_found = []
        enhancement_types = ['conjunction', 'trine', 'sextile', 'parallel']

        for aspect in all_aspects:
            if not aspect.is_applying:
                continue
            if aspect.aspect_type not in enhancement_types:
                continue

            planets_sorted = tuple(sorted([aspect.planet1, aspect.planet2]))
            aspect_key = f"{planets_sorted[0]}-{planets_sorted[1]}"

            if aspect_key in SUPER_ASPECTS:
                super_found.append((aspect_key, SUPER_ASPECTS[aspect_key], aspect))

        return super_found

    def find_cinderella_aspects(self, all_aspects: List[AspectInfo]) -> List[Tuple[str, str, AspectInfo]]:
        cinderella_found = []
        enhancement_types = ['conjunction', 'trine', 'sextile', 'parallel']

        for aspect in all_aspects:
            if not aspect.is_applying:
                continue
            if aspect.aspect_type not in enhancement_types:
                continue

            planets_sorted = tuple(sorted([aspect.planet1, aspect.planet2]))
            aspect_key = f"{planets_sorted[0]}-{planets_sorted[1]}"

            if aspect_key in CINDERELLA_ASPECTS:
                cinderella_found.append((aspect_key, CINDERELLA_ASPECTS[aspect_key], aspect))

        return cinderella_found

    def detect_planetary_geometry(self, all_aspects: List[AspectInfo]) -> Dict[str, Any]:
        patterns = {'grand_trine': False, 'yod': False, 't_square': False}
        longitude_aspects = [a for a in all_aspects if a.coordinate_type == 'longitude']

        trine_aspects = [a for a in longitude_aspects if a.aspect_type == 'trine']
        if len(trine_aspects) >= 3:
            planets_in_trines = set()
            for aspect in trine_aspects:
                planets_in_trines.add(aspect.planet1)
                planets_in_trines.add(aspect.planet2)
            for p1 in planets_in_trines:
                for p2 in planets_in_trines:
                    for p3 in planets_in_trines:
                        if len({p1, p2, p3}) == 3:
                            has_all = (
                                any(a for a in trine_aspects if {a.planet1, a.planet2} == {p1, p2}) and
                                any(a for a in trine_aspects if {a.planet1, a.planet2} == {p2, p3}) and
                                any(a for a in trine_aspects if {a.planet1, a.planet2} == {p1, p3})
                            )
                            if has_all:
                                patterns['grand_trine'] = True
                                break

        quincunx_aspects = [a for a in longitude_aspects if a.aspect_type == 'quincunx']
        sextile_aspects = [a for a in longitude_aspects if a.aspect_type == 'sextile']
        if len(quincunx_aspects) >= 2 and len(sextile_aspects) >= 1:
            for apex in set([a.planet1 for a in quincunx_aspects] + [a.planet2 for a in quincunx_aspects]):
                quins_to_apex = [a for a in quincunx_aspects if apex in {a.planet1, a.planet2}]
                if len(quins_to_apex) >= 2:
                    base_planets = set()
                    for q in quins_to_apex[:2]:
                        base_planets.add(q.planet1 if q.planet2 == apex else q.planet2)
                    if len(base_planets) == 2:
                        has_sextile = any(a for a in sextile_aspects if set([a.planet1, a.planet2]) == base_planets)
                        if has_sextile:
                            patterns['yod'] = True
                            break

        square_aspects = [a for a in longitude_aspects if a.aspect_type == 'square']
        opposition_aspects = [a for a in longitude_aspects if a.aspect_type == 'opposition']
        if len(square_aspects) >= 2 and len(opposition_aspects) >= 1:
            for apex in set([a.planet1 for a in square_aspects] + [a.planet2 for a in square_aspects]):
                squares_to_apex = [a for a in square_aspects if apex in {a.planet1, a.planet2}]
                if len(squares_to_apex) >= 2:
                    base_planets = set()
                    for s in squares_to_apex[:2]:
                        base_planets.add(s.planet1 if s.planet2 == apex else s.planet2)
                    if len(base_planets) == 2:
                        has_opposition = any(a for a in opposition_aspects if set([a.planet1, a.planet2]) == base_planets)
                        if has_opposition:
                            patterns['t_square'] = True
                            break

        return patterns

    def count_enhancements(self, all_aspects: List[AspectInfo]) -> Tuple[int, int]:
        """
        Count enhancements and transcendent links.
        TUNED: Exclude Saturn, exclude Moon (too transient for collective calendar),
        long-term parallels count only once per pair.
        """
        enhancement_count = 0
        transcendent_count = 0
        seen_pairs = set()

        for aspect in all_aspects:
            if 'Saturn' in {aspect.planet1, aspect.planet2}:
                continue

            pair_key = tuple(sorted([aspect.planet1, aspect.planet2]))
            duration = self.classify_aspect_duration(aspect.planet1, aspect.planet2)

            is_enhancement = False

            if self.is_enhancement_aspect(aspect.aspect_type, aspect.planet1, aspect.planet2):
                if aspect.coordinate_type == 'longitude':
                    is_enhancement = True
                elif aspect.aspect_type == 'parallel':
                    if duration == 'short_term':
                        is_enhancement = True
                    elif duration == 'long_term':
                        if pair_key not in seen_pairs:
                            is_enhancement = True
                            seen_pairs.add(pair_key)
                    else:
                        is_enhancement = True

            if is_enhancement and aspect.is_applying:
                enhancement_count += 1

                is_transcendent = (
                    aspect.planet1 in TRANSCENDENT_PLANETS and
                    aspect.planet2 in TRANSCENDENT_PLANETS and
                    bool(CORE_PLANETS & {aspect.planet1, aspect.planet2}) and
                    aspect.strength_tier in ['tight', 'close'] and
                    duration == 'short_term'
                )
                if is_transcendent:
                    transcendent_count += 1

        return enhancement_count, transcendent_count

    def has_grand_trine(self, all_aspects: List[AspectInfo]) -> bool:
        trine_aspects = [a for a in all_aspects if a.aspect_type == 'trine' and a.coordinate_type == 'longitude']
        if len(trine_aspects) < 3:
            return False
        planets_in_trines = set()
        for aspect in trine_aspects:
            planets_in_trines.add(aspect.planet1)
            planets_in_trines.add(aspect.planet2)
        for p1 in planets_in_trines:
            for p2 in planets_in_trines:
                for p3 in planets_in_trines:
                    if p1 != p2 and p2 != p3 and p1 != p3:
                        has_t1 = any(a for a in trine_aspects if {a.planet1, a.planet2} == {p1, p2})
                        has_t2 = any(a for a in trine_aspects if {a.planet1, a.planet2} == {p2, p3})
                        has_t3 = any(a for a in trine_aspects if {a.planet1, a.planet2} == {p1, p3})
                        if has_t1 and has_t2 and has_t3:
                            return True
        return False

    def get_super_parallels(self, all_aspects: List[AspectInfo]) -> List[str]:
        super_parallels = []
        for aspect in all_aspects:
            if aspect.coordinate_type != 'declination':
                continue
            if aspect.aspect_type != 'parallel':
                continue
            if not aspect.is_applying:
                continue
            duration = self.classify_aspect_duration(aspect.planet1, aspect.planet2)
            if duration == 'long_term':
                continue
            if aspect.planet1 in MAGI_BENEFICS and aspect.planet2 in MAGI_BENEFICS:
                if aspect.strength_tier == 'tight':
                    super_parallels.append(
                        f"{aspect.planet1}-{aspect.planet2} parallel ({aspect.orb}°)"
                    )
        return super_parallels

    def calculate_day_score(self, all_aspects: List[AspectInfo]) -> float:
        """
        TUNED scoring:
        - Moon aspects weighted at 0.3x (too transient for collective calendar)
        - Long-term slow-planet aspects capped at ±0.1 (background noise)
        - Applying bonus reduced to 1.15x (was 1.25x)
        - Peak bonus only for tight/close aspects
        """
        score = 0.0

        for aspect in all_aspects:
            duration = self.classify_aspect_duration(aspect.planet1, aspect.planet2)
            tier_weight = self.get_tier_weight(aspect.strength_tier)

            planets = {aspect.planet1, aspect.planet2}
            has_moon = 'Moon' in planets
            moon_damper = 0.3 if has_moon else 1.0

            is_benefic_pair = aspect.planet1 in MAGI_BENEFICS and aspect.planet2 in MAGI_BENEFICS
            is_malefic_involved = bool(planets & set(MAGI_MALEFICS))

            aspect_score = 0.0

            if is_benefic_pair and aspect.aspect_type in GOLDEN_ASPECTS + ['parallel']:
                if duration == 'short_term':
                    aspect_score = 3.0 * (tier_weight / 3)
                elif duration == 'long_term':
                    aspect_score = 0.1
                else:
                    aspect_score = 0.75
            elif is_malefic_involved and aspect.aspect_type in TURBULENT_ASPECTS + ['contraparallel']:
                personal_involved = bool(planets & set(PERSONAL_PLANETS))
                if personal_involved:
                    if duration == 'short_term':
                        aspect_score = -3.5 * (tier_weight / 3)
                    elif duration == 'long_term':
                        aspect_score = -0.1
                    else:
                        aspect_score = -0.75
                else:
                    if duration == 'long_term':
                        aspect_score = -0.05
                    else:
                        aspect_score = -0.25
            elif aspect.aspect_type in GOLDEN_ASPECTS + ['parallel']:
                if duration == 'short_term':
                    aspect_score = 1.5 * (tier_weight / 3)
                elif duration == 'long_term':
                    aspect_score = 0.1
                else:
                    aspect_score = 0.35
            elif aspect.aspect_type in TURBULENT_ASPECTS + ['contraparallel']:
                if duration == 'short_term':
                    aspect_score = -1.5 * (tier_weight / 3)
                elif duration == 'long_term':
                    aspect_score = -0.1
                else:
                    aspect_score = -0.35

            aspect_score *= moon_damper

            if aspect.is_applying:
                aspect_score *= 1.15

            score += aspect_score

        return round(score, 2)

    def classify_day(self, target_date) -> Dict[str, Any]:
        """
        TUNED classification logic.
        
        Priority:
        1. Deal-breakers → PTI Worst
        2. Best signals (tight super aspects near peak, rare patterns)
        3. Score-based with WIDER Normal zone
        
        Thresholds calibrated for:
          Best ~7%, Go ~32%, Normal ~37%, Slow ~14%, Worst ~10%
        """
        if isinstance(target_date, datetime):
            target_date = target_date.date()
        elif isinstance(target_date, str):
            target_date = datetime.strptime(target_date, "%Y-%m-%d").date()

        positions_today = self.calculate_positions(target_date)
        if not positions_today:
            return {"date": str(target_date), "classification": "Error", "reason": "Position calculation failed"}

        positions_tomorrow = self.calculate_positions(target_date + timedelta(days=1))

        longitude_aspects = self.find_longitude_aspects(positions_today, positions_tomorrow)
        declination_aspects = self.find_declination_aspects(positions_today, positions_tomorrow)
        all_aspects = longitude_aspects + declination_aspects

        has_deal_breakers, deal_breaker_details = self.check_deal_breakers(all_aspects)

        if has_deal_breakers:
            return {
                "date": str(target_date),
                "classification": "PTI Worst",
                "magi_classification": "PTI Worst",
                "reason": "Deal-breaker clash detected",
                "score": 0,
                "details": {"deal_breakers": deal_breaker_details},
                "aspects": all_aspects
            }

        geometry = self.detect_planetary_geometry(all_aspects)
        super_aspects_found = self.find_super_aspects(all_aspects)
        cinderella_aspects_found = self.find_cinderella_aspects(all_aspects)
        enhancement_count, transcendent_count = self.count_enhancements(all_aspects)
        has_gt = self.has_grand_trine(all_aspects)
        super_parallels = self.get_super_parallels(all_aspects)
        day_score = self.calculate_day_score(all_aspects)

        is_best = False
        best_reason = ""

        tight_supers = [s for s in super_aspects_found if s[2].strength_tier == 'tight']
        close_supers = [s for s in super_aspects_found if s[2].strength_tier in ['tight', 'close']]
        imminent_supers = [s for s in tight_supers if s[2].days_to_peak is not None and s[2].days_to_peak <= 1.5]

        if len(imminent_supers) >= 1 and day_score >= 3:
            is_best = True
            best_reason = f"Super Aspect peaking: {imminent_supers[0][1]}"

        if not is_best and len(tight_supers) >= 2 and day_score >= 3:
            is_best = True
            super_names = [s[1] for s in tight_supers[:2]]
            best_reason = f"Multiple Super Aspects: {', '.join(super_names)}"

        if not is_best and len(close_supers) >= 1 and transcendent_count >= 1 and day_score >= 5:
            is_best = True
            best_reason = f"Super Aspect ({close_supers[0][1]}) + transcendent boost"

        if not is_best and has_gt:
            trine_aspects = [a for a in all_aspects if a.aspect_type == 'trine' and a.coordinate_type == 'longitude']
            tight_trines = [a for a in trine_aspects if a.strength_tier in ['tight', 'close']]
            if len(tight_trines) >= 2 and day_score >= 3:
                is_best = True
                best_reason = "Grand Trine with tight legs"

        tight_cinderella = [c for c in cinderella_aspects_found if c[2].strength_tier == 'tight']
        if not is_best and len(tight_cinderella) >= 1:
            if day_score >= 5 and transcendent_count >= 1:
                is_best = True
                best_reason = f"Cinderella: {tight_cinderella[0][1]}"

        if not is_best and transcendent_count >= 3 and day_score >= 5:
            is_best = True
            best_reason = f"Multiple transcendent links ({transcendent_count})"

        if not is_best and len(super_parallels) >= 2 and day_score >= 5:
            is_best = True
            best_reason = f"Multiple super parallels"

        if not is_best and day_score >= 10 and enhancement_count >= 4:
            is_best = True
            best_reason = f"Exceptional enhancement score ({day_score})"

        if is_best:
            return {
                "date": str(target_date),
                "classification": "PTI Best",
                "magi_classification": "PTI Best",
                "reason": best_reason,
                "score": day_score,
                "details": {
                    "enhancement_count": enhancement_count,
                    "transcendent_count": transcendent_count,
                    "grand_trine": has_gt,
                    "super_parallels": super_parallels,
                    "super_aspects": [(s[0], s[1], f"{s[2].orb}°", s[2].days_to_peak) for s in super_aspects_found],
                    "cinderella_aspects": [(c[0], c[1], f"{c[2].orb}°") for c in cinderella_aspects_found],
                    "geometry": geometry
                },
                "aspects": all_aspects
            }

        if day_score <= -6.0:
            classification = "PTI Worst"
            reason = f"Severely negative score ({day_score})"
            return {
                "date": str(target_date),
                "classification": classification,
                "magi_classification": classification,
                "reason": reason,
                "score": day_score,
                "details": {
                    "enhancement_count": enhancement_count,
                    "transcendent_count": transcendent_count,
                    "geometry": geometry
                },
                "aspects": all_aspects
            }

        if day_score >= 3.0:
            classification = "PTI Go"
            reason = f"Strong positive score ({day_score})"
        elif day_score >= 1.5:
            has_quality = enhancement_count >= 1 and any(
                a for a in all_aspects
                if self.is_enhancement_aspect(a.aspect_type, a.planet1, a.planet2)
                and a.is_applying
                and a.strength_tier in ['tight', 'close', 'moderate']
            )
            if has_quality:
                classification = "PTI Go"
                reason = f"Enhancement with positive score ({day_score})"
            else:
                classification = "Normal"
                reason = f"Moderate score, no strong enhancement ({day_score})"
        elif day_score >= -2.0:
            classification = "Normal"
            reason = f"Balanced score ({day_score})"
        elif day_score >= -4.0:
            classification = "PTI Slow"
            reason = f"Negative score ({day_score})"
        else:
            classification = "PTI Slow"
            reason = f"Low score ({day_score})"

        if geometry['t_square'] and classification == "Normal" and day_score < -1:
            classification = "PTI Slow"
            reason += " + T-Square tension"

        return {
            "date": str(target_date),
            "classification": classification,
            "magi_classification": classification,
            "reason": reason,
            "score": day_score,
            "details": {
                "enhancement_count": enhancement_count,
                "transcendent_count": transcendent_count,
                "super_aspects": [(s[0], s[1], f"{s[2].orb}°", s[2].days_to_peak) for s in super_aspects_found],
                "cinderella_aspects": [(c[0], c[1], f"{c[2].orb}°") for c in cinderella_aspects_found],
                "geometry": geometry
            },
            "aspects": all_aspects
        }

    def generate_calendar(self, start_date, num_days: int) -> List[Dict[str, Any]]:
        results = []

        if isinstance(start_date, str):
            start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
        elif isinstance(start_date, datetime):
            start_date = start_date.date()

        current_date = start_date
        for _ in range(num_days):
            result = self.classify_day(current_date)
            result["classification_reason"] = result.get("reason", "")
            results.append(result)
            current_date += timedelta(days=1)

        return results

    def print_calendar(self, results: List[Dict[str, Any]]):
        print("\n" + "=" * 70)
        print("PTI COLLECTIVE CALENDAR - Tuned Version")
        print("=" * 70)

        classifications = {}
        for r in results:
            cls = r['classification']
            classifications[cls] = classifications.get(cls, 0) + 1

        total_days = len(results)
        print(f"Period: {total_days} days analyzed")

        for cls in ["PTI Best", "PTI Go", "Normal", "PTI Slow", "PTI Worst"]:
            count = classifications.get(cls, 0)
            pct = count / total_days * 100 if total_days > 0 else 0
            print(f"{cls}: {count} days ({pct:.1f}%)")
        print("=" * 70 + "\n")

        symbols = {
            "PTI Best": "🌟",
            "PTI Go": "✅",
            "Normal": "➖",
            "PTI Slow": "⚠️",
            "PTI Worst": "❌"
        }

        for result in results:
            cls = result['classification']
            symbol = symbols.get(cls, "?")
            date_str = result['date']
            reason = result.get('reason', '')
            score = result.get('score', '')
            score_str = f" [score: {score}]" if score != '' else ""

            print(f"📅 {date_str} | {symbol} {cls} | {reason}{score_str}")

            details = result.get('details', {})

            if 'deal_breakers' in details:
                for db in details['deal_breakers']:
                    print(f"   🪓 {db}")

            if 'super_aspects' in details and details['super_aspects']:
                for sa in details['super_aspects'][:3]:
                    peak_info = f", peaks in {sa[3]} days" if len(sa) > 3 and sa[3] else ""
                    print(f"   ⭐ {sa[0]} ({sa[1]}) - {sa[2]}{peak_info}")

            if 'cinderella_aspects' in details and details['cinderella_aspects']:
                for ca in details['cinderella_aspects']:
                    print(f"   🎭 {ca[0]} ({ca[1]}) - {ca[2]}")

            if 'super_parallels' in details and details['super_parallels']:
                for sp in details['super_parallels'][:2]:
                    print(f"   ✨ {sp}")

            if 'geometry' in details:
                geom = details['geometry']
                if geom.get('grand_trine'):
                    print(f"   🔺 Grand Trine")
                if geom.get('yod'):
                    print(f"   👆 Yod (Finger of God)")
                if geom.get('t_square'):
                    print(f"   ⚠️ T-Square tension")


def main():
    parser = argparse.ArgumentParser(
        description='PTI Collective Calendar - Tuned Version',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--start-date', '-s', type=str,
                       help='Start date in YYYY-MM-DD format (default: today)')
    parser.add_argument('--days', '-d', type=int, default=30,
                       help='Number of days to analyze (default: 30)')

    args = parser.parse_args()

    if args.start_date:
        start_date = datetime.strptime(args.start_date, "%Y-%m-%d").date()
    else:
        start_date = date.today()

    print("🔮 PTI Collective Calendar - Tuned Version")
    print("=" * 50)
    print(f"Start Date: {start_date}")
    print(f"Days: {args.days}")
    print()

    calendar = PTITunedCalendar()
    results = calendar.generate_calendar(start_date, args.days)
    calendar.print_calendar(results)


PTICollectiveCalendar = PTITunedCalendar

if __name__ == "__main__":
    main()
