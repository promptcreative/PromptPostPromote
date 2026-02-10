#!/usr/bin/env python3
"""
Enhanced Personal Transit Calendar - Vedic Astrology Daily Scoring System
Calculates personalized daily transit scores based on birth chart including Yogi/Avayogi analysis
"""

import sys
import os
import json
import calendar as std_calendar
from datetime import date, datetime, timedelta
from collections import defaultdict
import swisseph as swe

# Add drik-panchanga to path
sys.path.insert(0, '../drik-panchanga')

class EnhancedPersonalTransitCalculator:
    def __init__(self):
        self.weekdays = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
        self.tithi_names = [
            "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami", "Ashtami",
            "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya/Purnima"
        ]
        self.nakshatra_names = [
            "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya",
            "Ashlesha", "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati",
            "Vishakha", "Anuradha", "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
            "Dhanishta", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
        ]
        self.sign_names = [
            "Aries", "Taurus", "Gemini", "Cancer", "Leo", "Virgo",
            "Libra", "Scorpio", "Sagittarius", "Capricorn", "Aquarius", "Pisces"
        ]

        # House scoring reweighted to reduce neutral clustering
        self.house_scores = {
            1: 2.5,   # Lagna - Self (Boosted from 2.0)
            2: 1.0,   # Wealth (Boosted from 0.5)
            3: 1.5,   # Courage (Boosted from 1.0)
            4: 1.5,   # Home (Boosted from 1.0)
            5: 3.0,   # Creativity, Children (Maximum positive - Trikona)
            6: -1.0,  # Health/Service (Awareness - Dushtana)
            7: 1.5,   # Partnership (Boosted from 1.0 - Kendra)
            8: -2.5,  # Transformation (STOP level - Major Dushtana)
            9: 3.0,   # Fortune, Dharma (Maximum positive - Trikona)
            10: 2.5,  # Career (Boosted from 2.0 - Strong Kendra)
            11: 2.5,  # Gains, Friends (Very strong - Upachaya)
            12: -1.0  # Expenses/Spirituality (Awareness - same as 6th)
        }
        
        # Raw house scores for reference
        self.house_scores_raw = {
            1: 2.0, 2: 0.5, 3: 1.0, 4: 1.0, 5: 2.5, 6: -0.5,
            7: 1.0, 8: -0.5, 9: 2.5, 10: 1.5, 11: 2.0, 12: -1.0
        }

        # House-centric vs Composite scoring modes
        self.scoring_mode = 'composite'  # 'house_centric' or 'composite'
        
        # House descriptions for positive messaging
        self.house_themes_detailed = {
            1: "Perfect for new beginnings and personal initiatives",
            2: "Excellent for financial planning and resource management", 
            3: "Great for communication and connecting with others",
            4: "Ideal for home activities and emotional healing",
            5: "Wonderful for creativity and time with children",
            6: "Good for health routines and being of service",
            7: "Focus on partnerships and collaborative efforts",
            8: "Deep research and transformational work favored",
            9: "High spiritual potential and wisdom seeking",
            10: "Career matters and public recognition highlighted",
            11: "Friendships and goal achievement supported",
            12: "Meditation and spiritual practices enhanced"
        }

        # Comprehensive house awareness messages for all 12 houses with Yogi context
        self.house_awareness = {
            1: {
                'subject': 'Power Day: Self & New Beginnings',
                'base_description': 'Moon transiting 1st house (Lagna) - Focus on self, identity, and new beginnings. Excellent for personal initiatives and fresh starts.',
                'yogi_enhancement': 'Plus Moon in your Yogi nakshatra - perfect time for major personal decisions with enhanced clarity.',
                'avayogi_enhancement': 'Plus Moon in your Avayogi nakshatra - be authentic rather than trying to impress others.'
            },
            2: {
                'subject': 'Supportive: Wealth & Resources',
                'base_description': 'Moon transiting 2nd house - Areas of wealth, resources, and values. Good for financial planning and stabilizing resources.',
                'yogi_enhancement': 'Plus Moon in your Yogi nakshatra - wise financial decisions and recognizing true value.',
                'avayogi_enhancement': 'Plus Moon in your Avayogi nakshatra - avoid impulse purchases or overvaluing material things.'
            },
            3: {
                'subject': 'Supportive: Courage & Communication',
                'base_description': 'Moon transiting 3rd house - Areas of courage, communication, and short journeys. Great for bold communication and connecting with siblings.',
                'yogi_enhancement': 'Plus Moon in your Yogi nakshatra - inspired communication and courageous right action.',
                'avayogi_enhancement': 'Plus Moon in your Avayogi nakshatra - speak from the heart rather than trying to prove a point.'
            },
            4: {
                'subject': 'Supportive: Home & Inner Peace',
                'base_description': 'Moon transiting 4th house - Areas of home, mother, and inner peace. Excellent for domestic activities and emotional healing.',
                'yogi_enhancement': 'Plus Moon in your Yogi nakshatra - deep emotional healing and finding your true center.',
                'avayogi_enhancement': 'Plus Moon in your Avayogi nakshatra - be gentle with family rather than demanding perfection.'
            },
            5: {
                'subject': 'Power Day: Creativity & Joy',
                'base_description': 'Moon transiting 5th house - Areas of creativity, children, and joy. Excellent for creative projects and playful activities.',
                'yogi_enhancement': 'Plus Moon in your Yogi nakshatra - inspired creativity and joyful expression of your gifts.',
                'avayogi_enhancement': 'Plus Moon in your Avayogi nakshatra - create for the joy of it rather than for recognition.'
            },
            6: {
                'subject': 'Personal Alert: Be aware - yellow day',
                'base_description': 'Moon transiting 6th house - Areas of service and health. Be mindful of daily routines and energy levels.',
                'yogi_enhancement': 'Plus Moon in your Yogi nakshatra - use wisdom to navigate daily pressures with ease.',
                'avayogi_enhancement': 'Plus Moon in your Avayogi nakshatra - watch for over-efforting in work and trying to prove yourself.'
            },
            7: {
                'subject': 'Supportive: Partnership & Balance',
                'base_description': 'Moon transiting 7th house - Areas of partnership and relationships. Good for collaboration and finding balance with others.',
                'yogi_enhancement': 'Plus Moon in your Yogi nakshatra - harmonious partnerships and wise relationship decisions.',
                'avayogi_enhancement': 'Plus Moon in your Avayogi nakshatra - be yourself in relationships rather than people-pleasing.'
            },
            8: {
                'subject': 'Personal Alert: Slow - be aware', 
                'base_description': 'Moon transiting 8th house - Areas of transformation and change. Take time with important decisions.',
                'yogi_enhancement': 'Plus Moon in your Yogi nakshatra - transformation has wisdom and deeper purpose.',
                'avayogi_enhancement': 'Plus Moon in your Avayogi nakshatra - avoid forcing change or pushing against resistance.'
            },
            9: {
                'subject': 'Power Day: Fortune & Higher Purpose',
                'base_description': 'Moon transiting 9th house - Areas of higher learning, dharma, and fortune. Excellent for spiritual practices and big-picture decisions.',
                'yogi_enhancement': 'Plus Moon in your Yogi nakshatra - profound spiritual insights and alignment with your dharma.',
                'avayogi_enhancement': 'Plus Moon in your Avayogi nakshatra - trust your inner wisdom rather than seeking external validation.'
            },
            10: {
                'subject': 'Supportive: Career & Public Recognition',
                'base_description': 'Moon transiting 10th house - Areas of career and public reputation. Good for professional activities and gaining recognition.',
                'yogi_enhancement': 'Plus Moon in your Yogi nakshatra - career decisions aligned with your higher purpose.',
                'avayogi_enhancement': 'Plus Moon in your Avayogi nakshatra - focus on contribution rather than status or ego.'
            },
            11: {
                'subject': 'Power Day: Gains & Friendships',
                'base_description': 'Moon transiting 11th house - Areas of gains, friends, and wishes fulfilled. Excellent for networking and achieving goals.',
                'yogi_enhancement': 'Plus Moon in your Yogi nakshatra - wishes fulfilled through wise action and good karma.',
                'avayogi_enhancement': 'Plus Moon in your Avayogi nakshatra - share success generously rather than hoarding benefits.'
            },
            12: {
                'subject': 'Personal Alert: Be aware - yellow day',
                'base_description': 'Moon transiting 12th house - Areas of reflection and expenses. Good time for inner work and mindful spending.',
                'yogi_enhancement': 'Plus Moon in your Yogi nakshatra - excellent for spiritual insights and letting go.',
                'avayogi_enhancement': 'Plus Moon in your Avayogi nakshatra - watch for escapism or avoiding responsibilities.'
            }
        }

        # Bulletproof Authentic Vedic Tithi Classification
        # Exact mapping to prevent fallback errors
        self.tithi_score_map = {
            # Poorna (Fullness) – Completion & Fulfillment
            5: 3.0, 10: 3.0, 15: 3.0, 20: 3.0, 25: 3.0,
            
            # Nanda (Joy) – Auspicious beginnings
            1: 2.0, 6: 2.0, 11: 2.0, 16: 2.0, 21: 2.0, 26: 2.0,
            
            # Bhadra (Grace) – Growth and learning
            2: 1.5, 7: 1.5, 12: 1.5, 17: 1.5, 22: 1.5, 27: 1.5,
            
            # Jaya (Victory) – Success with effort
            3: 1.0, 8: 1.0, 13: 1.0, 18: 1.0, 23: 1.0, 28: 1.0,
            
            # Rikta (Empty) – Avoid starts, spiritual, endings
            4: -2.0, 9: -2.0, 14: -2.0, 19: -2.0, 24: -2.0, 29: -2.0,
            
            # Amavasya – Spiritual, avoid material activity
            30: -3.0
        }
        
        # Tithi type mapping for transparency
        self.tithi_type_map = {
            5: "Poorna (Fullness)", 10: "Poorna (Fullness)", 15: "Poorna (Fullness)", 
            20: "Poorna (Fullness)", 25: "Poorna (Fullness)",
            1: "Nanda (Joy)", 6: "Nanda (Joy)", 11: "Nanda (Joy)", 
            16: "Nanda (Joy)", 21: "Nanda (Joy)", 26: "Nanda (Joy)",
            2: "Bhadra (Grace)", 7: "Bhadra (Grace)", 12: "Bhadra (Grace)", 
            17: "Bhadra (Grace)", 22: "Bhadra (Grace)", 27: "Bhadra (Grace)",
            3: "Jaya (Victory)", 8: "Jaya (Victory)", 13: "Jaya (Victory)", 
            18: "Jaya (Victory)", 23: "Jaya (Victory)", 28: "Jaya (Victory)",
            4: "Rikta (Empty)", 9: "Rikta (Empty)", 14: "Rikta (Empty)", 
            19: "Rikta (Empty)", 24: "Rikta (Empty)", 29: "Rikta (Empty)",
            30: "Amavasya (New Moon)"
        }
        
        # Tithi names for all 30 tithis
        self.tithi_names_full = [
            "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",      # 1-5
            "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",           # 6-10
            "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",  # 11-15
            "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",      # 16-20
            "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",           # 21-25
            "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya"  # 26-30
        ]

        # Nakshatra quality scoring
        self.excellent_nakshatras = [4, 8, 13, 17]  # Rohini, Pushya, Hasta, Anuradha
        self.good_nakshatras = [1, 5, 11, 12, 15, 20, 22, 27]  # Generally favorable
        self.challenging_nakshatras = [2, 6, 9, 18, 25]  # Bharani, Ardra, Ashlesha, Jyeshtha, Purva Bhadrapada

    def get_nakshatra_ruler(self, nakshatra_num):
        """Get ruling planet of nakshatra"""
        rulers = {
            1: 'Ketu', 2: 'Venus', 3: 'Sun', 4: 'Moon', 5: 'Mars',
            6: 'Rahu', 7: 'Jupiter', 8: 'Saturn', 9: 'Mercury',
            10: 'Ketu', 11: 'Venus', 12: 'Sun', 13: 'Moon', 14: 'Mars',
            15: 'Rahu', 16: 'Jupiter', 17: 'Saturn', 18: 'Mercury',
            19: 'Ketu', 20: 'Venus', 21: 'Sun', 22: 'Moon', 23: 'Mars',
            24: 'Rahu', 25: 'Jupiter', 26: 'Saturn', 27: 'Mercury'
        }
        return rulers[nakshatra_num]

    def get_house_ruler(self, degree):
        """Get ruling planet of house cusp"""
        sign_num = int(degree / 30)
        rulers = {
            0: 'Mars', 1: 'Venus', 2: 'Mercury', 3: 'Moon',
            4: 'Sun', 5: 'Mercury', 6: 'Venus', 7: 'Mars',
            8: 'Jupiter', 9: 'Saturn', 10: 'Saturn', 11: 'Jupiter'
        }
        return rulers[sign_num]

    def get_nakshatra_info(self, lon):
        """Get nakshatra number and name"""
        if lon < 0:
            lon = lon % 360
        nakshatra_num = int(lon * 27 / 360)
        return nakshatra_num + 1, self.nakshatra_names[nakshatra_num]

    def calculate_yogi_avayogi_points(self, birth_date, birth_time, latitude, longitude, timezone):
        """Calculate Yogi and Avayogi points from birth chart"""
        try:
            # Convert to UTC
            birth_datetime = datetime.combine(birth_date, birth_time)
            birth_jd = swe.julday(birth_datetime.year, birth_datetime.month, birth_datetime.day, 
                                 birth_datetime.hour + birth_datetime.minute/60.0 - timezone)

            # Set ayanamsa
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            ayanamsa = swe.get_ayanamsa_ut(birth_jd)

            # Get Sun and Moon positions
            sun_data = swe.calc_ut(birth_jd, swe.SUN)
            moon_data = swe.calc_ut(birth_jd, swe.MOON)

            sun_longitude = sun_data[0][0]
            moon_longitude = moon_data[0][0]

            # Convert to sidereal
            sun_sidereal = (sun_longitude - ayanamsa) % 360
            moon_sidereal = (moon_longitude - ayanamsa) % 360

            # Calculate Yogi Point: Sun + Moon + 93.33 degrees
            yogi_point = (sun_sidereal + moon_sidereal + 93.33) % 360
            yogi_nakshatra_num, yogi_nakshatra_name = self.get_nakshatra_info(yogi_point)

            # Calculate Avayogi Point: Yogi Point + 186 degrees
            avayogi_point = (yogi_point + 186) % 360
            avayogi_nakshatra_num, avayogi_nakshatra_name = self.get_nakshatra_info(avayogi_point)

            # Calculate Duplicate Yogi: sign ruler of Yogi Point
            duplicate_yogi_planet = self.get_house_ruler(float(yogi_point - (yogi_point % 30)))

            return {
                'yogi_nakshatra_num': yogi_nakshatra_num,
                'yogi_nakshatra_name': yogi_nakshatra_name,
                'yogi_planet': self.get_nakshatra_ruler(yogi_nakshatra_num),
                'avayogi_nakshatra_num': avayogi_nakshatra_num,
                'avayogi_nakshatra_name': avayogi_nakshatra_name,
                'avayogi_planet': self.get_nakshatra_ruler(avayogi_nakshatra_num),
                'duplicate_yogi_planet': duplicate_yogi_planet
            }

        except Exception as e:
            print(f"Error calculating Yogi/Avayogi points: {e}")
            return None

    def calculate_birth_chart(self, birth_date, birth_time, latitude, longitude, timezone):
        """Calculate natal chart positions including Yogi/Avayogi points"""
        try:
            # Convert to UTC
            birth_datetime = datetime.combine(birth_date, birth_time)
            birth_jd = swe.julday(birth_datetime.year, birth_datetime.month, birth_datetime.day, 
                                 birth_datetime.hour + birth_datetime.minute/60.0 - timezone)

            # Set ayanamsa
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            ayanamsa = swe.get_ayanamsa_ut(birth_jd)

            # Calculate Lagna (Ascendant)
            houses = swe.houses(birth_jd, latitude, longitude, b'P')  # Placidus houses
            lagna_longitude = houses[1][0]  # Ascendant longitude

            # Calculate Moon position
            moon_data = swe.calc_ut(birth_jd, swe.MOON)
            moon_longitude = moon_data[0][0]

            # Calculate sidereal positions
            lagna_sidereal = (lagna_longitude - ayanamsa) % 360
            moon_sidereal = (moon_longitude - ayanamsa) % 360

            # Determine signs
            lagna_sign = int(lagna_sidereal / 30) + 1
            moon_sign = int(moon_sidereal / 30) + 1

            # Determine Moon nakshatra
            moon_nakshatra = int(moon_sidereal / (360/27)) + 1

            # Calculate Yogi/Avayogi points
            yogi_info = self.calculate_yogi_avayogi_points(birth_date, birth_time, latitude, longitude, timezone)

            result = {
                'lagna_sign': lagna_sign,
                'moon_sign': moon_sign,
                'moon_nakshatra': moon_nakshatra,
                'lagna_longitude': lagna_longitude,
                'moon_longitude': moon_longitude,
                'birth_jd': birth_jd,
                'ayanamsa': ayanamsa
            }

            # Add Yogi/Avayogi info if calculated successfully
            if yogi_info:
                result.update(yogi_info)

            return result

        except Exception as e:
            print(f"Error calculating birth chart: {e}")
            return None

    def calculate_daily_transits(self, test_date, latitude, longitude, timezone):
        """Calculate daily transit positions"""
        try:
            # Convert to Julian Day
            jd = swe.julday(test_date.year, test_date.month, test_date.day, 12.0)  # Noon

            # Set ayanamsa
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            ayanamsa = swe.get_ayanamsa_ut(jd)

            # Calculate planetary positions
            sun_data = swe.calc_ut(jd, swe.SUN)
            moon_data = swe.calc_ut(jd, swe.MOON)
            mars_data = swe.calc_ut(jd, swe.MARS)
            saturn_data = swe.calc_ut(jd, swe.SATURN)

            sun_longitude = sun_data[0][0]
            moon_longitude = moon_data[0][0]
            mars_longitude = mars_data[0][0]
            saturn_longitude = saturn_data[0][0]

            # Calculate sidereal positions
            sun_sidereal = (sun_longitude - ayanamsa) % 360
            moon_sidereal = (moon_longitude - ayanamsa) % 360
            mars_sidereal = (mars_longitude - ayanamsa) % 360
            saturn_sidereal = (saturn_longitude - ayanamsa) % 360

            # Determine signs
            moon_sign = int(moon_sidereal / 30) + 1

            # Calculate tithi
            lunar_phase = (moon_longitude - sun_longitude) % 360
            tithi = min(int(lunar_phase / 12) + 1, 15)

            # Calculate nakshatra
            moon_nakshatra = min(int(moon_sidereal / (360/27)) + 1, 27)

            # Check aspects to Moon with new binary logic
            saturn_aspect_penalty = self.check_saturn_aspect(saturn_sidereal, moon_sidereal)
            mars_aspect_penalty = self.check_mars_aspect(mars_sidereal, moon_sidereal)

            return {
                'moon_sign': moon_sign,
                'moon_nakshatra': moon_nakshatra,
                'tithi': tithi,
                'saturn_aspect_penalty': saturn_aspect_penalty,
                'mars_aspect_penalty': mars_aspect_penalty,
                'julian_day': jd,
                'moon_longitude': moon_longitude,
                'lunar_phase': lunar_phase
            }

        except Exception as e:
            print(f"Error calculating daily transits for {test_date}: {e}")
            return None

    def check_saturn_aspect(self, saturn_longitude, moon_longitude):
        """Check Saturn aspect to Moon with binary degree-based logic"""
        diff = abs(saturn_longitude - moon_longitude)
        if diff > 180:
            diff = 360 - diff
        
        if diff <= 6:
            return -3.0  # Full penalty
        elif diff <= 9:
            return -1.5  # Mild penalty
        else:
            return 0.0  # No penalty
    
    def check_mars_aspect(self, mars_longitude, moon_longitude):
        """Check Mars aspect to Moon with binary degree-based logic"""
        diff = abs(mars_longitude - moon_longitude)
        if diff > 180:
            diff = 360 - diff
        
        if diff <= 5:
            return -2.0  # Strong penalty
        elif diff <= 8:
            return -1.0  # Mild penalty
        else:
            return 0.0  # No penalty

    def calculate_moon_house_from_lagna(self, natal_lagna_sign, transit_moon_sign):
        """Calculate which house the Moon is transiting from natal Lagna"""
        house = ((transit_moon_sign - natal_lagna_sign) % 12) + 1
        return house

    def score_personal_day(self, birth_chart, daily_transits, scoring_mode='composite'):
        """Calculate personal transit score for a day with Yogi/Avayogi enhancement"""
        if not birth_chart or not daily_transits:
            return None

        score = 0
        factors = []
        component_scores = {}

        # 1. Moon House Score (from Lagna)
        moon_house = self.calculate_moon_house_from_lagna(
            birth_chart['lagna_sign'], 
            daily_transits['moon_sign']
        )
        house_score = self.house_scores.get(moon_house, 0)
        component_scores['house'] = house_score
        
        # Apply house score based on scoring mode
        if scoring_mode == 'house_centric':
            # In house-centric mode, house score has more weight
            weighted_house_score = house_score * 1.5
            score += weighted_house_score
            factors.append(f"House {moon_house} (house-centric mode): {weighted_house_score:+.1f}")
        else:
            score += house_score

        # 2. Yogi/Avayogi Nakshatra Analysis
        yogi_avayogi_bonus = 0
        yogi_message = ""

        # Check if Moon is in personal Yogi nakshatra (reduced impact to prevent extreme swings)
        if ('yogi_nakshatra_num' in birth_chart and 
            daily_transits['moon_nakshatra'] == birth_chart['yogi_nakshatra_num']):
            yogi_avayogi_bonus += 1  # Reduced from 2.0 to 1.0
            yogi_message = f"Moon in your Yogi nakshatra ({birth_chart['yogi_nakshatra_name']}) - enhanced wisdom and flow available"
            factors.append(f"Yogi nakshatra bonus: +1.0 - {yogi_message}")

        # Check if Moon is in personal Avayogi nakshatra
        elif ('avayogi_nakshatra_num' in birth_chart and 
              daily_transits['moon_nakshatra'] == birth_chart['avayogi_nakshatra_num']):
            yogi_avayogi_bonus -= 1  # Reduced from -2.0 to -1.0
            yogi_message = f"Moon in your Avayogi nakshatra ({birth_chart['avayogi_nakshatra_name']}) - watch for over-efforting"
            factors.append(f"Avayogi nakshatra: -1.0 - {yogi_message}")
            
        component_scores['yogi_avayogi'] = yogi_avayogi_bonus
        score += yogi_avayogi_bonus

        # Enhanced house awareness for ALL houses with Yogi context
        awareness = self.house_awareness.get(moon_house, {})
        base_msg = awareness.get('base_description', f'Moon in {moon_house}th house')

        # Add Yogi/Avayogi enhancement to house message for all houses
        if ('yogi_nakshatra_num' in birth_chart and 
            daily_transits['moon_nakshatra'] == birth_chart['yogi_nakshatra_num']):
            enhanced_msg = f"{base_msg} {awareness.get('yogi_enhancement', '')}"
        elif ('avayogi_nakshatra_num' in birth_chart and 
              daily_transits['moon_nakshatra'] == birth_chart['avayogi_nakshatra_num']):
            enhanced_msg = f"{base_msg} {awareness.get('avayogi_enhancement', '')}"
        else:
            enhanced_msg = base_msg

        factors.append(f"Moon in {moon_house}th house: {house_score:+.1f} - {enhanced_msg}")

        # 3. Bulletproof Authentic Vedic Tithi Score
        tithi = daily_transits['tithi']
        tithi_name = self.tithi_names_full[tithi-1] if tithi <= 30 else f"Tithi {tithi}"
        
        # Get score from bulletproof mapping
        tithi_score = self.tithi_score_map.get(tithi, 0.0)  # Fallback to 0 if undefined
        tithi_type = self.tithi_type_map.get(tithi, "Unknown")
        
        # Failsafe test - catch unexpected +3.0 scores
        if tithi_score == 3.0 and tithi not in [5, 10, 15, 20, 25]:
            print(f"⚠️ WARNING: Unexpected +3.0 Tithi score on Tithi {tithi}")
            factors.append(f"⚠️ DEBUG: Tithi {tithi} got +3.0 unexpectedly")
        
        # Add appropriate factor message based on type
        if tithi == 30:
            factors.append(f"Amavasya - {tithi_name}: {tithi_score:+.1f} (spiritual introspection, avoid material starts)")
        elif tithi_type.startswith("Poorna"):
            factors.append(f"Poorna tithi - {tithi_name}: {tithi_score:+.1f} (completion, fulfillment, results)")
        elif tithi_type.startswith("Nanda"):
            factors.append(f"Nanda tithi - {tithi_name}: {tithi_score:+.1f} (joyful beginnings, optimistic starts)")
        elif tithi_type.startswith("Bhadra"):
            factors.append(f"Bhadra tithi - {tithi_name}: {tithi_score:+.1f} (growth, learning, creativity)")
        elif tithi_type.startswith("Jaya"):
            factors.append(f"Jaya tithi - {tithi_name}: {tithi_score:+.1f} (victory through effort, struggle then success)")
        elif tithi_type.startswith("Rikta"):
            factors.append(f"Rikta tithi - {tithi_name}: {tithi_score:+.1f} (emptiness, avoid new starts, good for endings)")
        else:
            factors.append(f"Unknown tithi - {tithi_name}: {tithi_score:+.1f}")
        
        component_scores['tithi'] = tithi_score
        component_scores['tithi_type'] = tithi_type
        score += tithi_score
        
        # Debug Tithi source data
        if tithi < 1 or tithi > 30:
            print(f"⚠️ WARNING: Invalid Tithi value: {tithi}")
            factors.append(f"⚠️ DEBUG: Invalid Tithi {tithi} detected")

        # 4. Nakshatra Score (normalized to -3 to +3 scale)
        nakshatra = daily_transits['moon_nakshatra']

        # Check for natal nakshatra return
        if nakshatra == birth_chart['moon_nakshatra']:
            nakshatra_score = 3  # Maximum positive - natal return
            factors.append(f"Natal nakshatra return ({self.nakshatra_names[nakshatra-1]}): +3.0")
        elif nakshatra in self.excellent_nakshatras:
            nakshatra_score = 2
            factors.append(f"Excellent nakshatra ({self.nakshatra_names[nakshatra-1]}): +2.0")
        elif nakshatra in self.good_nakshatras:
            nakshatra_score = 1
            factors.append(f"Good nakshatra ({self.nakshatra_names[nakshatra-1]}): +1.0")
        elif nakshatra in self.challenging_nakshatras:
            nakshatra_score = -3  # Maximum negative for challenging
            factors.append(f"Challenging nakshatra ({self.nakshatra_names[nakshatra-1]}): -3.0")
        else:
            nakshatra_score = 0
            factors.append(f"Neutral nakshatra ({self.nakshatra_names[nakshatra-1]}): 0.0")
        
        component_scores['nakshatra'] = nakshatra_score
        score += nakshatra_score

        # Optional: Moon dignity modifier for subtle variation
        dignity_bonus = 0
        moon_sign_num = daily_transits['moon_sign']
        
        # Moon dignity: exaltation, own sign, debilitation
        if moon_sign_num == 2:  # Taurus - Moon exalted
            dignity_bonus = 0.5
            factors.append("Moon exalted (Taurus): +0.5")
        elif moon_sign_num == 4:  # Cancer - Moon own sign
            dignity_bonus = 0.3
            factors.append("Moon in own sign (Cancer): +0.3")
        elif moon_sign_num == 8:  # Scorpio - Moon debilitated
            dignity_bonus = -0.5
            factors.append("Moon debilitated (Scorpio): -0.5")
        
        component_scores['moon_dignity'] = dignity_bonus
        score += dignity_bonus

        # 5. Simplified Binary Aspect Logic (Saturn and Mars only)
        saturn_penalty = daily_transits.get('saturn_aspect_penalty', 0)
        mars_penalty = daily_transits.get('mars_aspect_penalty', 0)
        total_aspect_penalty = saturn_penalty + mars_penalty
        
        # Add factor explanations
        if saturn_penalty < 0:
            factors.append(f"Saturn aspect to Moon: {saturn_penalty:+.1f}")
        if mars_penalty < 0:
            factors.append(f"Mars aspect to Moon: {mars_penalty:+.1f}")
        if saturn_penalty == 0 and mars_penalty == 0:
            factors.append("No malefic aspects to Moon: 0.0")
        
        component_scores['aspects'] = total_aspect_penalty
        score += total_aspect_penalty

        # Determine quality with tightened thresholds (reduce neutral zone)
        awareness_day = moon_house in [6, 12]  # Track awareness houses (removed 8th house - should be caution)
        
        if awareness_day:  # Houses of awareness
            quality = "aware"
        elif score >= 6:  # Tightened: was 7 - more days get "power"
            quality = "power"
        elif score >= 2:  # Tightened: was 3 - more days get "supportive"  
            quality = "supportive"
        elif score > -1:  # Changed >= to > so 8th house (-1.0) becomes "avoid" (caution)
            quality = "neutral"
        else:
            quality = "avoid"

        # Generate subject line based on house awareness or quality
        subject_line = None
        if moon_house in [6, 12]:  # Removed 8th house - it's now caution, not awareness
            subject_line = self.house_awareness.get(moon_house, {}).get('subject', f"Personal - {moon_house}th house")
        elif quality in ['power', 'supportive']:
            subject_line = "Personal - good"

        # Generate detailed score breakdown for transparency
        score_breakdown = {
            'house_score': component_scores.get('house', 0),
            'house_component': f"House {moon_house}: {component_scores.get('house', 0):+.1f}",
            'nakshatra_score': component_scores.get('nakshatra', 0),
            'nakshatra_component': f"Nakshatra: {component_scores.get('nakshatra', 0):+.1f}",
            'tithi_score': component_scores.get('tithi', 0),
            'tithi_component': f"Tithi: {component_scores.get('tithi', 0):+.1f}",
            'tithi_type': component_scores.get('tithi_type', 'Unknown'),
            'tithi_name': tithi_name,
            'aspect_score': component_scores.get('aspects', 0),
            'aspect_component': f"Aspects: {component_scores.get('aspects', 0):+.1f}",
            'yogi_score': component_scores.get('yogi_avayogi', 0),
            'yogi_component': f"Yogi/Avayogi: {component_scores.get('yogi_avayogi', 0):+.1f}",
            'moon_dignity_score': component_scores.get('moon_dignity', 0),
            'moon_dignity_component': f"Moon Dignity: {component_scores.get('moon_dignity', 0):+.1f}",
            'total_score': score,
            'scoring_mode': scoring_mode,
            'awareness_day': awareness_day
        }

        # House of the Day - positive messaging even on challenging days
        house_theme = {
            1: "Self & Identity", 2: "Wealth & Values", 3: "Courage & Communication",
            4: "Home & Inner Peace", 5: "Creativity & Children", 6: "Service & Health",
            7: "Partnership & Others", 8: "Transformation & Research", 9: "Wisdom & Fortune",
            10: "Career & Recognition", 11: "Gains & Friendships", 12: "Spirituality & Release"
        }
        
        house_of_day = {
            'house_number': moon_house,
            'house_theme': house_theme.get(moon_house, f"{moon_house}th house"),
            'house_message': self.house_awareness.get(moon_house, {}).get('base_description', f'Moon transiting {moon_house}th house'),
            'positive_potential': self.house_themes_detailed.get(moon_house, f"Focus on {moon_house}th house matters today")
        }

        return {
            'score': score,
            'quality': quality,
            'factors': factors,
            'score_breakdown': score_breakdown,
            'moon_house': moon_house,
            'house_of_day': house_of_day,
            'transits': daily_transits,
            'subject_line': subject_line,
            'awareness_message': self.house_awareness.get(moon_house, {}).get('base_description', None),
            'yogi_enhancement': yogi_message
        }

    def generate_personal_calendar(self, birth_chart, start_date, end_date, latitude, longitude, timezone, scoring_mode='composite'):
        """Generate personal transit calendar for date range"""
        print(f"Generating enhanced personal transit calendar from {start_date} to {end_date} (Mode: {scoring_mode})")

        calendar_data = {}
        current_date = start_date

        while current_date <= end_date:
            daily_transits = self.calculate_daily_transits(current_date, latitude, longitude, timezone)
            personal_score = self.score_personal_day(birth_chart, daily_transits, scoring_mode=scoring_mode)

            calendar_data[current_date.isoformat()] = {
                'date': current_date,
                'weekday': current_date.strftime('%A'),
                'personal_score': personal_score
            }

            current_date += timedelta(days=1)

        return calendar_data

    def print_personal_calendar(self, calendar_data, birth_chart):
        """Print formatted personal transit calendar"""
        print(f"\n{'='*80}")
        print(f"ENHANCED PERSONAL TRANSIT CALENDAR WITH YOGI/AVAYOGI ANALYSIS")
        print(f"{'='*80}")
        print(f"Birth Chart: Lagna {self.sign_names[birth_chart['lagna_sign']-1]}, "
              f"Moon {self.sign_names[birth_chart['moon_sign']-1]}, "
              f"Moon Nakshatra {self.nakshatra_names[birth_chart['moon_nakshatra']-1]}")

        # Display Yogi/Avayogi info if available
        if 'yogi_nakshatra_name' in birth_chart:
            print(f"Yogi Nakshatra: {birth_chart['yogi_nakshatra_name']} (Planet: {birth_chart.get('yogi_planet', 'Unknown')})")
            print(f"Avayogi Nakshatra: {birth_chart['avayogi_nakshatra_name']} (Planet: {birth_chart.get('avayogi_planet', 'Unknown')})")
            print(f"Duplicate Yogi: {birth_chart.get('duplicate_yogi_planet', 'Unknown')}")

        print(f"{'='*80}")

        # Print header
        print(f"{'Date':>12} {'Day':>10} {'Quality':>12} {'Score':>6} {'Moon Sign':>12} {'House':>6} {'Nakshatra':>15}")
        print("-" * 80)

        # Quality counters
        quality_counts = defaultdict(int)
        power_days = []
        supportive_days = []
        avoid_days = []

        for date_str, data in sorted(calendar_data.items()):
            if data['personal_score']:
                score_data = data['personal_score']
                quality = score_data['quality']
                quality_counts[quality] += 1

                # Quality symbols
                quality_symbol = {
                    'power': '💜',
                    'supportive': '💚',
                    'neutral': '⚪',
                    'avoid': '🔴',
                    'aware': '🟡'
                }.get(quality, '?')

                transits = score_data['transits']
                moon_sign = self.sign_names[transits['moon_sign']-1]
                nakshatra = self.nakshatra_names[transits['moon_nakshatra']-1][:13]

                print(f"{data['date'].strftime('%Y-%m-%d'):>12} {data['weekday']:>10} "
                      f"{quality_symbol} {quality:>10} {score_data['score']:>6.1f} "
                      f"{moon_sign:>12} {score_data['moon_house']:>6} {nakshatra:>15}")

                # Collect special days
                if quality == 'power':
                    power_days.append(data['date'])
                elif quality == 'supportive':
                    supportive_days.append(data['date'])
                elif quality == 'avoid':
                    avoid_days.append(data['date'])

        # Print summary
        print(f"\n{'='*80}")
        print("ENHANCED PERSONAL TRANSIT SUMMARY:")
        print(f"💜 Power Days: {quality_counts['power']}")
        print(f"💚 Supportive Days: {quality_counts['supportive']}")
        print(f"⚪ Neutral Days: {quality_counts['neutral']}")
        print(f"🟡 Aware Days: {quality_counts['aware']}")
        print(f"🔴 Avoid Days: {quality_counts['avoid']}")

        # Show special days
        if power_days:
            print(f"\nPOWER DAYS FOR MAJOR ACTIVITIES: {', '.join(d.strftime('%m-%d') for d in power_days)}")

        if supportive_days:
            print(f"SUPPORTIVE DAYS: {', '.join(d.strftime('%m-%d') for d in supportive_days)}")

        if avoid_days:
            print(f"DAYS TO AVOID: {', '.join(d.strftime('%m-%d') for d in avoid_days)}")

        print(f"{'='*80}")

def main():
    calculator = EnhancedPersonalTransitCalculator()

    # Example birth data - March 9, 1973, 4:56 PM EST, Daytona Beach, FL
    birth_date = date(1973, 3, 9)
    birth_time = datetime.strptime("16:56", "%H:%M").time()  # 4:56 PM
    latitude = 29.2108  # Daytona Beach, FL
    longitude = -81.0228
    timezone = -5.0  # EST

    print("Enhanced Personal Transit Calendar Generator")
    print("=" * 50)
    print(f"Birth Data: {birth_date.strftime('%B %d, %Y')} at {birth_time.strftime('%I:%M %p')}")
    print(f"Location: Daytona Beach, FL ({latitude:.4f}°N, {longitude:.4f}°W)")
    print(f"Timezone: EST (UTC{timezone:+.1f})")

    # Calculate birth chart with Yogi/Avayogi points
    birth_chart = calculator.calculate_birth_chart(birth_date, birth_time, latitude, longitude, timezone)

    if birth_chart:
        print(f"\nBirth Chart Calculated:")
        print(f"Lagna (Ascendant): {calculator.sign_names[birth_chart['lagna_sign']-1]}")
        print(f"Moon Sign: {calculator.sign_names[birth_chart['moon_sign']-1]}")
        print(f"Moon Nakshatra: {calculator.nakshatra_names[birth_chart['moon_nakshatra']-1]}")

        if 'yogi_nakshatra_name' in birth_chart:
            print(f"\nYogi/Avayogi Analysis:")
            print(f"Yogi Nakshatra: {birth_chart['yogi_nakshatra_name']} (ruled by {birth_chart.get('yogi_planet', 'Unknown')})")
            print(f"Avayogi Nakshatra: {birth_chart['avayogi_nakshatra_name']} (ruled by {birth_chart.get('avayogi_planet', 'Unknown')})")
            print(f"Duplicate Yogi Planet: {birth_chart.get('duplicate_yogi_planet', 'Unknown')}")

        # Generate 30-day calendar starting from today
        start_date = date.today()
        end_date = start_date + timedelta(days=30)

        print(f"\nGenerating 30-day enhanced personal transit calendar ({start_date} to {end_date})...")

        calendar_data = calculator.generate_personal_calendar(
            birth_chart, start_date, end_date, latitude, longitude, timezone
        )

        # Print calendar
        calculator.print_personal_calendar(calendar_data, birth_chart)

        # Save as JSON
        filename = f"enhanced_personal_transit_calendar_{start_date.strftime('%Y%m%d')}.json"
        json_data = {
            'birth_chart': birth_chart,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'location': f"Daytona Beach, FL ({latitude:.4f}°N, {longitude:.4f}°W)",
            'days': {}
        }

        for date_str, data in calendar_data.items():
            if data['personal_score']:
                json_data['days'][date_str] = {
                    'date': date_str,
                    'weekday': data['weekday'],
                    'quality': data['personal_score']['quality'],
                    'score': data['personal_score']['score'],
                    'factors': data['personal_score']['factors'],
                    'moon_house': data['personal_score']['moon_house'],
                    'transits': data['personal_score']['transits'],
                    'yogi_enhancement': data['personal_score'].get('yogi_enhancement', '')
                }

        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False, default=str)

        print(f"\nEnhanced personal transit calendar saved to {filename}")

    else:
        print("Error: Could not calculate birth chart")

if __name__ == "__main__":
    main()