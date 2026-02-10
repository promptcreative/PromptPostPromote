"""
Ephemeris Calculator

Handles all astronomical calculations using Swiss Ephemeris and Astral libraries.
Provides precise sunrise/sunset times and lunar paksha calculations.
"""

import swisseph as swe
from astral import LocationInfo
from astral.sun import sun
from datetime import datetime, timedelta
import pytz
import logging
from typing import Dict, Tuple, Any

logger = logging.getLogger(__name__)

class EphemerisCalculator:
    """
    Calculator for astronomical data using Swiss Ephemeris.
    """
    
    def __init__(self):
        """Initialize the ephemeris calculator."""
        # Set Swiss Ephemeris path if needed
        try:
            # Try to set ephemeris path from environment variable
            import os
            ephe_path = os.getenv('SWISSEPH_PATH', '')
            if ephe_path:
                swe.set_ephe_path(ephe_path)
                logger.info(f"Swiss Ephemeris path set to: {ephe_path}")
        except Exception as e:
            logger.warning(f"Could not set Swiss Ephemeris path: {e}")
            
    def calculate_sunrise_sunset(self, date: datetime, latitude: float, 
                                longitude: float, timezone: str) -> Dict[str, datetime]:
        """
        Calculate precise sunrise and sunset times for a given location and date.
        
        Args:
            date: Date for calculation
            latitude: Latitude in degrees
            longitude: Longitude in degrees  
            timezone: Timezone string (e.g., 'Asia/Kolkata')
            
        Returns:
            Dictionary containing sunrise and sunset times
        """
        try:
            # Create location info
            location = LocationInfo(
                name="Location", 
                timezone=timezone, 
                latitude=latitude, 
                longitude=longitude
            )
            
            # Get timezone
            tz = pytz.timezone(timezone)
            
            # Calculate sun times
            sun_times = sun(location.observer, date=date.date(), tzinfo=tz)
            
            # Calculate next day's sunrise for night calculations
            next_sunrise = sun(location.observer, 
                             date=date.date() + timedelta(days=1), 
                             tzinfo=tz)['sunrise']
            
            result = {
                'sunrise': sun_times['sunrise'],
                'sunset': sun_times['sunset'],
                'next_sunrise': next_sunrise,
                'day_duration': sun_times['sunset'] - sun_times['sunrise'],
                'night_duration': next_sunrise - sun_times['sunset']
            }
            
            logger.debug(f"Calculated sun times for {date.date()}: "
                        f"sunrise={result['sunrise'].strftime('%H:%M')}, "
                        f"sunset={result['sunset'].strftime('%H:%M')}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating sunrise/sunset: {e}")
            raise
    
    def calculate_paksha(self, date: datetime, latitude: float = 19.0760, 
                        longitude: float = 72.8777, timezone_offset: float = 5.5) -> str:
        """
        Calculate lunar paksha (Shukla/Krishna) using Swiss Ephemeris.
        
        Args:
            date: Date for calculation
            latitude: Latitude in degrees (default: Mumbai)
            longitude: Longitude in degrees (default: Mumbai)
            timezone_offset: Timezone offset in hours (default: IST +5.5)
            
        Returns:
            'Shukla' or 'Krishna' paksha
        """
        try:
            # Set Lahiri Ayanamsa for sidereal calculations (Vedic standard)
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            
            # Create datetime at noon local time
            dt = datetime(date.year, date.month, date.day, 12, 0, 0)
            
            # Convert to Julian Day (UTC)
            jd = swe.julday(dt.year, dt.month, dt.day, dt.hour - timezone_offset)
            
            # Calculate sidereal Sun and Moon longitudes
            sun_data = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)
            moon_data = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)
            
            sun_longitude = sun_data[0][0]
            moon_longitude = moon_data[0][0]
            
            # Calculate moon-sun difference
            diff = (moon_longitude - sun_longitude) % 360
            
            # Determine paksha
            paksha = 'Shukla' if diff <= 180 else 'Krishna'
            
            logger.debug(f"Paksha calculation for {date.date()}: "
                        f"Sun={sun_longitude:.2f}°, Moon={moon_longitude:.2f}°, "
                        f"Diff={diff:.2f}°, Paksha={paksha}")
            
            return paksha
            
        except Exception as e:
            logger.error(f"Error calculating paksha: {e}")
            raise
    
    def calculate_lunar_tithi(self, date: datetime, timezone_offset: float = 5.5) -> Tuple[int, str]:
        """
        Calculate lunar tithi (lunar day) and tithi name.
        
        Args:
            date: Date for calculation
            timezone_offset: Timezone offset in hours
            
        Returns:
            Tuple of (tithi_number, tithi_name)
        """
        try:
            # Set Lahiri Ayanamsa for sidereal calculations (Vedic standard)
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            
            # Create datetime at noon local time
            dt = datetime(date.year, date.month, date.day, 12, 0, 0)
            
            # Convert to Julian Day (UTC)
            jd = swe.julday(dt.year, dt.month, dt.day, dt.hour - timezone_offset)
            
            # Calculate sidereal Sun and Moon longitudes
            sun_data = swe.calc_ut(jd, swe.SUN, swe.FLG_SIDEREAL)
            moon_data = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)
            
            sun_longitude = sun_data[0][0]
            moon_longitude = moon_data[0][0]
            
            # Calculate tithi
            diff = (moon_longitude - sun_longitude) % 360
            tithi_number = int(diff / 12) + 1
            
            # Tithi names
            tithi_names = [
                'Pratipada', 'Dwitiya', 'Tritiya', 'Chaturthi', 'Panchami',
                'Shashthi', 'Saptami', 'Ashtami', 'Navami', 'Dashami',
                'Ekadashi', 'Dwadashi', 'Trayodashi', 'Chaturdashi', 'Purnima'
            ]
            
            # Adjust for Krishna paksha
            if diff > 180:
                tithi_number = tithi_number - 15
                if tithi_number <= 0:
                    tithi_number = 15
                    
            tithi_name = tithi_names[tithi_number - 1] if tithi_number <= 15 else 'Amavasya'
            
            logger.debug(f"Tithi calculation for {date.date()}: "
                        f"Tithi {tithi_number} - {tithi_name}")
            
            return tithi_number, tithi_name
            
        except Exception as e:
            logger.error(f"Error calculating tithi: {e}")
            raise
    
    def get_planetary_positions(self, date: datetime, timezone_offset: float = 5.5) -> Dict[str, float]:
        """
        Get positions of major planets for the given date.
        
        Args:
            date: Date for calculation
            timezone_offset: Timezone offset in hours
            
        Returns:
            Dictionary of planet positions in degrees
        """
        try:
            # Set Lahiri Ayanamsa for sidereal calculations (Vedic standard)
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            
            # Create datetime at noon local time
            dt = datetime(date.year, date.month, date.day, 12, 0, 0)
            
            # Convert to Julian Day (UTC)
            jd = swe.julday(dt.year, dt.month, dt.day, dt.hour - timezone_offset)
            
            # Define planets
            planets = {
                'Sun': swe.SUN,
                'Moon': swe.MOON,
                'Mars': swe.MARS,
                'Mercury': swe.MERCURY,
                'Jupiter': swe.JUPITER,
                'Venus': swe.VENUS,
                'Saturn': swe.SATURN,
                'Rahu': swe.MEAN_NODE,
                'Ketu': swe.MEAN_NODE  # Ketu is 180° opposite to Rahu
            }
            
            positions = {}
            
            for planet_name, planet_id in planets.items():
                try:
                    planet_data = swe.calc_ut(jd, planet_id, swe.FLG_SIDEREAL)
                    longitude = planet_data[0][0]
                    
                    # For Ketu, add 180 degrees
                    if planet_name == 'Ketu':
                        longitude = (longitude + 180) % 360
                        
                    positions[planet_name] = longitude
                    
                except Exception as e:
                    logger.warning(f"Could not calculate position for {planet_name}: {e}")
                    positions[planet_name] = 0.0
            
            logger.debug(f"Planetary positions for {date.date()}: "
                        f"Sun={positions.get('Sun', 0):.2f}°, "
                        f"Moon={positions.get('Moon', 0):.2f}°")
            
            return positions
            
        except Exception as e:
            logger.error(f"Error calculating planetary positions: {e}")
            raise
    
    def calculate_birth_star(self, date: datetime, time: datetime, 
                           latitude: float, longitude: float, timezone: str) -> Tuple[str, str]:
        """
        Calculate the birth star (nakshatra) and corresponding birth bird.
        
        Args:
            date: Birth date
            time: Birth time
            latitude: Location latitude
            longitude: Location longitude
            timezone: Timezone string
            
        Returns:
            Tuple of (nakshatra_name, birth_bird)
        """
        try:
            from .data import NAKSHATRA_LIST, PAKSHA_BIRD_RANGES
            
            # Combine date and time, convert to UTC
            birth_datetime = datetime.combine(date.date(), time.time())
            
            # Get timezone object and localize
            tz = pytz.timezone(timezone)
            localized_dt = tz.localize(birth_datetime)
            utc_dt = localized_dt.astimezone(pytz.UTC)
            
            # Set Lahiri Ayanamsa for sidereal calculations (Vedic standard)
            swe.set_sid_mode(swe.SIDM_LAHIRI)
            
            # Convert to Julian Day
            jd = swe.julday(utc_dt.year, utc_dt.month, utc_dt.day, 
                           utc_dt.hour + utc_dt.minute/60.0 + utc_dt.second/3600.0)
            
            # Calculate Moon's sidereal position at birth time
            moon_data = swe.calc_ut(jd, swe.MOON, swe.FLG_SIDEREAL)
            moon_longitude = moon_data[0][0]
            
            # Find nakshatra and its number (1-27)
            nakshatra_name = None
            nakshatra_number = None
            for i, (name, start_degree) in enumerate(NAKSHATRA_LIST):
                end_degree = start_degree + 13.333  # Each nakshatra is 13°20'
                if i == 26:  # Last nakshatra wraps around
                    end_degree = 360.0
                    
                if start_degree <= moon_longitude < end_degree:
                    nakshatra_name = name
                    nakshatra_number = i + 1  # Convert to 1-27 numbering
                    break
            
            # Handle wrap-around case for Revati
            if nakshatra_name is None and moon_longitude >= 346.667:
                nakshatra_name = 'Revati'
                nakshatra_number = 27
            
            # Calculate paksha at birth time
            paksha = self.calculate_paksha(date, latitude, longitude)
            
            # Determine birth bird using paksha and nakshatra number
            birth_bird = self._get_birth_bird_from_paksha_nakshatra(paksha, nakshatra_number)
            
            logger.info(f"Birth star calculation: Moon at {moon_longitude:.2f}°, "
                       f"Nakshatra: {nakshatra_name} (#{nakshatra_number}), "
                       f"Paksha: {paksha}, Birth Bird: {birth_bird}")
            
            return nakshatra_name, birth_bird
            
        except Exception as e:
            logger.error(f"Error calculating birth star: {e}")
            # Return default values on error
            return 'Rohini', 'Cock'
    
    def _get_birth_bird_from_paksha_nakshatra(self, paksha: str, nakshatra_number: int) -> str:
        """
        Determine birth bird using paksha and nakshatra number according to traditional formula.
        
        Args:
            paksha: 'Shukla' or 'Krishna'
            nakshatra_number: Nakshatra number (1-27)
            
        Returns:
            Birth bird name
        """
        try:
            from .data import PAKSHA_BIRD_RANGES
            
            # Get the appropriate ranges for this paksha
            ranges = PAKSHA_BIRD_RANGES.get(paksha, PAKSHA_BIRD_RANGES['Shukla'])
            
            # Find which range the nakshatra falls into
            for (start, end), bird in ranges.items():
                if start <= nakshatra_number <= end:
                    return bird
            
            # Default fallback
            return 'Vulture'
            
        except Exception as e:
            logger.error(f"Error determining birth bird: {e}")
            return 'Vulture'

    def validate_location(self, latitude: float, longitude: float) -> bool:
        """
        Validate latitude and longitude coordinates.
        
        Args:
            latitude: Latitude in degrees
            longitude: Longitude in degrees
            
        Returns:
            True if valid, False otherwise
        """
        if not (-90 <= latitude <= 90):
            logger.error(f"Invalid latitude: {latitude}. Must be between -90 and 90.")
            return False
            
        if not (-180 <= longitude <= 180):
            logger.error(f"Invalid longitude: {longitude}. Must be between -180 and 180.")
            return False
            
        return True
    
    def get_ephemeris_info(self) -> Dict[str, Any]:
        """
        Get information about the Swiss Ephemeris being used.
        
        Returns:
            Dictionary with ephemeris information
        """
        try:
            # Get Swiss Ephemeris version
            version = swe.version
            
            # Get ephemeris path
            ephe_path = getattr(swe, 'get_ephe_path', lambda: 'Not available')()
            
            info = {
                'version': version,
                'path': ephe_path,
                'available_planets': [
                    'Sun', 'Moon', 'Mercury', 'Venus', 'Mars', 
                    'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Pluto',
                    'Mean Node (Rahu)', 'True Node', 'Chiron'
                ]
            }
            
            logger.info(f"Swiss Ephemeris version: {version}")
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting ephemeris info: {e}")
            return {'version': 'Unknown', 'path': '', 'available_planets': []}
