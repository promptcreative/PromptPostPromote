"""
Panch Pakshi Calculator

Main calculation engine for determining bird sequences, activities, and timings
based on traditional Panch Pakshi Shastra principles.

NOTE: This calculator now uses the CSV database (pancha_pakshi_db.csv) for authentic
calculations instead of algorithmic sequences. The database contains 3500 rows
covering all combinations of bird, weekday, paksha, and day/night periods.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Any, Optional
import logging
import os
import pandas as pd
from .data import (
    BIRD_SEQUENCES, ACTIVITY_ORDERS, RULING_DAYS_TABLE, DEATH_DAYS_TABLE,
    DAY_RATING, NIGHT_RATING, FRIENDS, ENEMIES, RATING_MAP, BIRD_EMOJIS,
    ACTIVITY_EMOJIS, DEFAULT_LOCATION
)
from .ephemeris import EphemerisCalculator

logger = logging.getLogger(__name__)

BIRD_INDEX_MAP = {'Vulture': 0, 'Owl': 1, 'Crow': 2, 'Cock': 3, 'Peacock': 4}
ACTIVITY_INDEX_MAP = {'Ruling': 0, 'Eating': 1, 'Walking': 2, 'Sleeping': 3, 'Dying': 4}
INDEX_TO_BIRD = {0: 'Vulture', 1: 'Owl', 2: 'Crow', 3: 'Cock', 4: 'Peacock'}
INDEX_TO_ACTIVITY = {0: 'Ruling', 1: 'Eating', 2: 'Walking', 3: 'Sleeping', 4: 'Dying'}
WEEKDAY_INDEX_MAP = {'Sunday': 0, 'Monday': 1, 'Tuesday': 2, 'Wednesday': 3, 'Thursday': 4, 'Friday': 5, 'Saturday': 6}
PAKSHA_INDEX_MAP = {'Shukla': 0, 'Krishna': 1}

DB_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pancha_pakshi_db.csv')
_cached_db = None

def get_database():
    """Load and cache the Panch Pakshi database"""
    global _cached_db
    if _cached_db is None:
        try:
            _cached_db = pd.read_csv(DB_FILE_PATH, index_col=None, encoding='utf-8')
            logger.info(f"Loaded Panch Pakshi database with {len(_cached_db)} rows")
        except Exception as e:
            logger.error(f"Failed to load database: {e}")
            _cached_db = pd.DataFrame()
    return _cached_db

def query_database(bird_index: int, weekday_index: int, paksha_index: int, daynight_index: int) -> list:
    """Query the database for bird periods based on parameters"""
    db = get_database()
    if db.empty:
        return []
    
    results = db[
        (db.iloc[:, 3] == bird_index) &
        (db.iloc[:, 0] == weekday_index) &
        (db.iloc[:, 1] == paksha_index) &
        (db.iloc[:, 2] == daynight_index)
    ]
    return results.values.tolist()

class PanchPakshiCalculator:
    """
    Main calculator for Panch Pakshi calculations.
    """
    
    def __init__(self):
        """Initialize the calculator with ephemeris calculator."""
        self.ephemeris = EphemerisCalculator()
        
    def calculate_bird_periods(self, date: datetime, time: datetime, 
                             latitude: float, longitude: float, 
                             timezone: str) -> Dict[str, Any]:
        """
        Calculate complete Panch Pakshi data for a given date, time, and location.
        
        Args:
            date: Date for calculation
            time: Time for calculation
            latitude: Latitude in degrees
            longitude: Longitude in degrees
            timezone: Timezone string
            
        Returns:
            Dictionary containing all calculated data
        """
        try:
            # Validate location
            if not self.ephemeris.validate_location(latitude, longitude):
                raise ValueError(f"Invalid coordinates: {latitude}, {longitude}")
            
            # Calculate sun times
            sun_times = self.ephemeris.calculate_sunrise_sunset(
                date, latitude, longitude, timezone
            )
            
            # Calculate paksha
            paksha = self.ephemeris.calculate_paksha(date, latitude, longitude)
            
            # Get weekday
            weekday = date.strftime("%A")
            
            # Get ruling and death birds
            ruling_bird_day = RULING_DAYS_TABLE[paksha]['Day'][weekday]
            dying_bird_day = DEATH_DAYS_TABLE[paksha]['Day'][weekday]
            ruling_bird_night = RULING_DAYS_TABLE[paksha]['Night'][weekday]
            dying_bird_night = DEATH_DAYS_TABLE[paksha]['Night'][weekday]
            
            # Calculate birth star (nakshatra) and birth bird FIRST for database lookup
            birth_star, birth_bird = self.ephemeris.calculate_birth_star(
                date, time, latitude, longitude, timezone
            )
            
            # Calculate day periods using database lookup
            day_periods = self._calculate_periods(
                sun_times['sunrise'], sun_times['sunset'], 
                paksha, 'Day', ruling_bird_day,
                weekday=weekday, birth_bird=birth_bird
            )
            
            # Calculate night periods using database lookup
            night_periods = self._calculate_periods(
                sun_times['sunset'], sun_times['next_sunrise'], 
                paksha, 'Night', ruling_bird_night,
                weekday=weekday, birth_bird=birth_bird
            )
            
            # Determine current period
            current_period = self._find_current_period(
                time, day_periods, night_periods
            )
            
            # Get planetary positions
            planets = self.ephemeris.get_planetary_positions(date)
            
            # Calculate tithi
            tithi_number, tithi_name = self.ephemeris.calculate_lunar_tithi(date)
            
            result = {
                'date': date.strftime('%Y-%m-%d'),
                'time': time.strftime('%H:%M:%S'),
                'location': {
                    'latitude': latitude,
                    'longitude': longitude,
                    'timezone': timezone
                },
                'paksha': paksha,
                'tithi': {
                    'number': tithi_number,
                    'name': tithi_name
                },
                'weekday': weekday,
                'birth_star': birth_star,
                'birth_bird': birth_bird,
                'sun_times': {
                    'sunrise': sun_times['sunrise'].strftime('%H:%M:%S'),
                    'sunset': sun_times['sunset'].strftime('%H:%M:%S'),
                    'next_sunrise': sun_times['next_sunrise'].strftime('%H:%M:%S'),
                    'day_duration': str(sun_times['day_duration']),
                    'night_duration': str(sun_times['night_duration'])
                },
                'ruling_birds': {
                    'day': ruling_bird_day,
                    'night': ruling_bird_night
                },
                'dying_birds': {
                    'day': dying_bird_day,
                    'night': dying_bird_night
                },
                'day_periods': day_periods,
                'night_periods': night_periods,
                'current_period': current_period,
                'planetary_positions': planets
            }
            
            logger.info(f"Calculated Panch Pakshi data for {date.date()} "
                       f"at {time.strftime('%H:%M')} - Paksha: {paksha}, "
                       f"Current: {current_period['bird'] if current_period else 'None'}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error calculating bird periods: {e}")
            raise
    
    def _calculate_periods(self, start_time: datetime, end_time: datetime, 
                          paksha: str, period_type: str, ruling_bird: str,
                          weekday: str = None, birth_bird: str = None) -> List[Dict]:
        """
        Calculate the 5 bird periods for day or night using CSV database lookup.
        
        Args:
            start_time: Start time of the period
            end_time: End time of the period
            paksha: Lunar paksha (Shukla/Krishna)
            period_type: 'Day' or 'Night'
            ruling_bird: The ruling bird for this period
            weekday: Day of the week (e.g., 'Monday')
            birth_bird: User's birth bird for database lookup
            
        Returns:
            List of period dictionaries
        """
        try:
            total_duration = end_time - start_time
            period_duration = total_duration / 5
            
            bird_index = BIRD_INDEX_MAP.get(ruling_bird, 0)
            weekday_index = WEEKDAY_INDEX_MAP.get(weekday, 0) if weekday else start_time.weekday()
            if weekday is None:
                weekday_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                weekday_index = WEEKDAY_INDEX_MAP.get(weekday_names[start_time.weekday()], 0)
            paksha_index = PAKSHA_INDEX_MAP.get(paksha, 0)
            daynight_index = 0 if period_type == 'Day' else 1
            
            db_rows = query_database(bird_index, weekday_index, paksha_index, daynight_index)
            
            periods = []
            current_time = start_time
            
            if db_rows and len(db_rows) == 25:
                period_data_list = []
                for period_num in range(5):
                    row_index = period_num * 5
                    row = db_rows[row_index]
                    main_bird_idx = int(row[5])
                    main_activity_idx = int(row[4])
                    main_bird = INDEX_TO_BIRD.get(main_bird_idx, ruling_bird)
                    main_activity = INDEX_TO_ACTIVITY.get(main_activity_idx, 'Ruling')
                    period_data_list.append((main_bird, main_activity))
                
                for i in range(5):
                    yama_bird, activity_name = period_data_list[i]
                    period_end = current_time + period_duration
                    
                    rating_table = DAY_RATING if period_type == 'Day' else NIGHT_RATING
                    auspiciousness = rating_table.get(yama_bird, {}).get(activity_name, 'average')
                    rating_symbols = RATING_MAP.get(auspiciousness, '++++')
                    
                    sub_periods = self._calculate_sub_periods_from_db(
                        current_time, period_end, db_rows, i, yama_bird, 
                        activity_name, period_type
                    )
                    
                    period_data = {
                        'yama_index': i + 1,
                        'bird': yama_bird,
                        'activity': activity_name,
                        'start_time': current_time.strftime('%H:%M:%S'),
                        'end_time': period_end.strftime('%H:%M:%S'),
                        'duration': str(period_duration),
                        'auspiciousness': auspiciousness,
                        'rating_symbols': rating_symbols,
                        'sub_periods': sub_periods,
                        'period_type': period_type.lower()
                    }
                    
                    periods.append(period_data)
                    current_time = period_end
                
                logger.debug(f"Database lookup: {ruling_bird}/{weekday}/{paksha}/{period_type} -> {[p[1] for p in period_data_list]}")
            else:
                row_count = len(db_rows) if db_rows else 0
                logger.warning(f"Database lookup failed for {ruling_bird}/{weekday}/{paksha}/{period_type} (got {row_count} rows, expected 25), using fallback")
                bird_sequence = BIRD_SEQUENCES[(paksha, period_type)]
                activity_order = ACTIVITY_ORDERS[(paksha, period_type)]
                start_index = bird_sequence.index(ruling_bird)
                rotated_birds = self._rotate_list(bird_sequence, start_index)
                rotated_activities = self._rotate_list(activity_order, start_index)
                
                for i in range(5):
                    bird = rotated_birds[i]
                    activity_name = rotated_activities[i][0]
                    period_end = current_time + period_duration
                    
                    rating_table = DAY_RATING if period_type == 'Day' else NIGHT_RATING
                    auspiciousness = rating_table[bird][activity_name]
                    rating_symbols = RATING_MAP[auspiciousness]
                    
                    sub_periods = self._calculate_sub_periods(
                        current_time, period_end, paksha, period_type, 
                        rotated_birds, i, bird, activity_name
                    )
                    
                    period_data = {
                        'yama_index': i + 1,
                        'bird': bird,
                        'activity': activity_name,
                        'start_time': current_time.strftime('%H:%M:%S'),
                        'end_time': period_end.strftime('%H:%M:%S'),
                        'duration': str(period_duration),
                        'auspiciousness': auspiciousness,
                        'rating_symbols': rating_symbols,
                        'sub_periods': sub_periods,
                        'period_type': period_type.lower()
                    }
                    
                    periods.append(period_data)
                    current_time = period_end
                
            return periods
            
        except Exception as e:
            logger.error(f"Error calculating periods: {e}")
            raise
    
    def _calculate_sub_periods_from_db(self, start_time: datetime, end_time: datetime,
                                       db_rows: list, period_num: int, main_bird: str,
                                       main_activity: str, period_type: str) -> List[Dict]:
        """Calculate sub-periods from database rows"""
        sub_periods = []
        total_duration = end_time - start_time
        sub_duration = total_duration / 5
        current_time = start_time
        
        for i in range(5):
            row_index = period_num * 5 + i
            if row_index < len(db_rows):
                row = db_rows[row_index]
                sub_bird_idx = int(row[5])
                sub_activity_idx = int(row[6])
                rating = int(row[11]) if len(row) > 11 else 5
                
                sub_bird = INDEX_TO_BIRD.get(sub_bird_idx, 'Vulture')
                sub_activity = INDEX_TO_ACTIVITY.get(sub_activity_idx, 'Ruling')
            else:
                sub_bird = main_bird
                sub_activity = main_activity
                rating = 5
            
            sub_end_time = current_time + sub_duration
            
            rating_table = DAY_RATING if period_type == 'Day' else NIGHT_RATING
            auspiciousness = rating_table.get(sub_bird, {}).get(sub_activity, 'average')
            rating_symbols = RATING_MAP.get(auspiciousness, '++++')
            
            relationship = self._get_bird_relationship(main_bird, sub_bird, 'Shukla')
            
            sub_periods.append({
                'sub_index': i + 1,
                'bird': sub_bird,
                'activity': sub_activity,
                'start_time': current_time.strftime('%H:%M:%S'),
                'end_time': sub_end_time.strftime('%H:%M:%S'),
                'auspiciousness': auspiciousness,
                'rating_symbols': rating_symbols,
                'relationship': relationship,
                'db_rating': rating
            })
            
            current_time = sub_end_time
        
        return sub_periods
    
    def _calculate_sub_periods(self, start_time: datetime, end_time: datetime,
                              paksha: str, period_type: str, bird_sequence: List[str],
                              main_index: int, main_bird: str, main_activity: str) -> List[Dict]:
        """
        Calculate sub-periods (Apahara) for a main period.
        
        Args:
            start_time: Start time of main period
            end_time: End time of main period
            paksha: Lunar paksha
            period_type: 'Day' or 'Night'
            bird_sequence: Rotated bird sequence
            main_index: Index of main period
            main_bird: Main bird for this period
            
        Returns:
            List of sub-period dictionaries
        """
        try:
            # Get activity order for sub-periods
            activity_order = ACTIVITY_ORDERS[(paksha, period_type)]
            
            # Rotate bird sequence starting from main bird
            sub_bird_sequence = self._rotate_list(bird_sequence, main_index)
            
            # For sub-periods, use traditional DrikPanchang method:
            # Start with main activity, then follow fixed order ["Eating", "Dying", "Sleeping", "Ruling", "Walking"]
            base_activity_names = ["Eating", "Dying", "Sleeping", "Ruling", "Walking"]
            # main_activity is now passed as a parameter
            
            # Find position of main activity in base order
            if main_activity in base_activity_names:
                main_activity_index = base_activity_names.index(main_activity)
                # Create sub-period activities starting from main activity
                sub_activity_names = base_activity_names[main_activity_index:] + base_activity_names[:main_activity_index]
                # Use traditional durations for DrikPanchang method
                durations = [12, 6, 8, 20, 10]  # Traditional Apahara durations in minutes
                use_traditional_method = True
            else:
                # Fallback to rotated order if main activity not found
                sub_activity_order = self._rotate_list(activity_order, main_index)
                sub_activity_names = [act[0] for act in sub_activity_order]
                durations = [act[1] for act in sub_activity_order]
                use_traditional_method = False
            
            # Calculate duration for each sub-period
            total_duration = end_time - start_time
            total_minutes = sum(durations)
            
            sub_periods = []
            current_time = start_time
            
            for i in range(5):
                sub_bird = sub_bird_sequence[i]
                sub_activity = sub_activity_names[i]
                duration_minutes = durations[i]
                
                # Calculate proportional duration
                sub_duration = total_duration * (duration_minutes / total_minutes)
                sub_end_time = current_time + sub_duration
                
                # Get auspiciousness rating
                rating_table = DAY_RATING if period_type == 'Day' else NIGHT_RATING
                auspiciousness = rating_table[sub_bird][sub_activity]
                rating_symbols = RATING_MAP[auspiciousness]
                
                # Get relationship with main bird
                relationship = self._get_bird_relationship(main_bird, sub_bird, paksha)
                
                sub_period_data = {
                    'apahara_index': i + 1,
                    'bird': sub_bird,
                    'activity': sub_activity,
                    'start_time': current_time.strftime('%H:%M:%S'),
                    'end_time': sub_end_time.strftime('%H:%M:%S'),
                    'duration': str(sub_duration),
                    'auspiciousness': auspiciousness,
                    'rating_symbols': rating_symbols,
                    'relationship': relationship,
                    'duration_minutes': duration_minutes
                }
                
                sub_periods.append(sub_period_data)
                current_time = sub_end_time
                
            return sub_periods
            
        except Exception as e:
            logger.error(f"Error calculating sub-periods: {e}")
            return []
    
    def _find_current_period(self, query_time: datetime, 
                           day_periods: List[Dict], 
                           night_periods: List[Dict]) -> Optional[Dict]:
        """
        Find the current active period for a given time.
        
        Args:
            query_time: Time to check
            day_periods: List of day periods
            night_periods: List of night periods
            
        Returns:
            Current period data or None
        """
        try:
            # Check day periods
            for period in day_periods:
                start_time = datetime.strptime(period['start_time'], '%H:%M:%S').time()
                end_time = datetime.strptime(period['end_time'], '%H:%M:%S').time()
                query_time_only = query_time.time()
                
                if start_time <= query_time_only < end_time:
                    # Find current sub-period
                    current_sub = None
                    for sub in period['sub_periods']:
                        sub_start = datetime.strptime(sub['start_time'], '%H:%M:%S').time()
                        sub_end = datetime.strptime(sub['end_time'], '%H:%M:%S').time()
                        if sub_start <= query_time_only < sub_end:
                            current_sub = sub
                            break
                    
                    return {
                        'type': 'day',
                        'yama_index': period['yama_index'],
                        'bird': period['bird'],
                        'activity': period['activity'],
                        'auspiciousness': period['auspiciousness'],
                        'current_sub_period': current_sub,
                        'period_data': period
                    }
            
            # Check night periods
            for period in night_periods:
                start_time = datetime.strptime(period['start_time'], '%H:%M:%S').time()
                end_time = datetime.strptime(period['end_time'], '%H:%M:%S').time()
                query_time_only = query_time.time()
                
                # Handle night periods that cross midnight
                if start_time > end_time:  # Period crosses midnight
                    if query_time_only >= start_time or query_time_only < end_time:
                        # Find current sub-period
                        current_sub = None
                        for sub in period['sub_periods']:
                            sub_start = datetime.strptime(sub['start_time'], '%H:%M:%S').time()
                            sub_end = datetime.strptime(sub['end_time'], '%H:%M:%S').time()
                            if sub_start > sub_end:  # Sub-period crosses midnight
                                if query_time_only >= sub_start or query_time_only < sub_end:
                                    current_sub = sub
                                    break
                            else:
                                if sub_start <= query_time_only < sub_end:
                                    current_sub = sub
                                    break
                        
                        return {
                            'type': 'night',
                            'yama_index': period['yama_index'],
                            'bird': period['bird'],
                            'activity': period['activity'],
                            'auspiciousness': period['auspiciousness'],
                            'current_sub_period': current_sub,
                            'period_data': period
                        }
                else:
                    if start_time <= query_time_only < end_time:
                        # Find current sub-period
                        current_sub = None
                        for sub in period['sub_periods']:
                            sub_start = datetime.strptime(sub['start_time'], '%H:%M:%S').time()
                            sub_end = datetime.strptime(sub['end_time'], '%H:%M:%S').time()
                            if sub_start <= query_time_only < sub_end:
                                current_sub = sub
                                break
                        
                        return {
                            'type': 'night',
                            'yama_index': period['yama_index'],
                            'bird': period['bird'],
                            'activity': period['activity'],
                            'auspiciousness': period['auspiciousness'],
                            'current_sub_period': current_sub,
                            'period_data': period
                        }
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding current period: {e}")
            return None
    
    def _rotate_list(self, lst: List, n: int) -> List:
        """
        Rotate a list by n positions.
        
        Args:
            lst: List to rotate
            n: Number of positions to rotate
            
        Returns:
            Rotated list
        """
        n = n % len(lst)
        return lst[n:] + lst[:n]
    
    def _get_bird_relationship(self, main_bird: str, sub_bird: str, paksha: str) -> str:
        """
        Get the relationship between two birds.
        
        Args:
            main_bird: Main bird
            sub_bird: Sub bird
            paksha: Lunar paksha
            
        Returns:
            Relationship string
        """
        if sub_bird == main_bird:
            return 'Self'
        elif sub_bird in FRIENDS[paksha][main_bird]:
            return 'Friend'
        elif sub_bird in ENEMIES[paksha][main_bird]:
            return 'Enemy'
        else:
            return 'Neutral'
    
    def get_favorable_periods(self, periods: List[Dict], min_rating: str) -> List[Dict]:
        """
        Filter periods to show only those with minimum rating.
        
        Args:
            periods: List of period dictionaries
            min_rating: Minimum auspiciousness rating to include
            
        Returns:
            Filtered list of periods
        """
        rating_hierarchy = ['very bad', 'bad', 'average', 'good', 'very good']
        min_index = rating_hierarchy.index(min_rating)
        
        favorable_periods = []
        for period in periods:
            rating_index = rating_hierarchy.index(period['auspiciousness'])
            if rating_index >= min_index:
                favorable_periods.append(period)
        
        return favorable_periods
    
    def calculate_batch(self, locations: List[Dict], dates: List[datetime], 
                       times: List[datetime]) -> List[Dict]:
        """
        Calculate Panch Pakshi data for multiple locations, dates, and times.
        
        Args:
            locations: List of location dictionaries
            dates: List of dates
            times: List of times
            
        Returns:
            List of calculation results
        """
        try:
            results = []
            
            for location in locations:
                for date in dates:
                    for time in times:
                        try:
                            result = self.calculate_bird_periods(
                                date, time,
                                location['latitude'],
                                location['longitude'],
                                location['timezone']
                            )
                            result['location_name'] = location.get('name', 'Unknown')
                            results.append(result)
                            
                        except Exception as e:
                            logger.error(f"Error in batch calculation for "
                                       f"{location.get('name', 'Unknown')}, "
                                       f"{date.date()}, {time.strftime('%H:%M')}: {e}")
                            continue
            
            logger.info(f"Completed batch calculation: {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in batch calculation: {e}")
            raise
    
    def get_favorable_periods(self, periods: List[Dict], 
                            min_rating: str = 'average') -> List[Dict]:
        """
        Filter periods based on minimum auspiciousness rating.
        
        Args:
            periods: List of period dictionaries
            min_rating: Minimum rating ('very good', 'good', 'average', 'bad', 'very bad')
            
        Returns:
            List of favorable periods
        """
        rating_order = ['very bad', 'bad', 'average', 'good', 'very good']
        min_index = rating_order.index(min_rating)
        
        favorable = []
        for period in periods:
            period_rating = period.get('auspiciousness', 'bad')
            if rating_order.index(period_rating) >= min_index:
                favorable.append(period)
        
        return favorable
    
    def generate_birth_star_calendar(self, birth_date: datetime, birth_time: datetime,
                                   latitude: float, longitude: float, timezone: str, 
                                   start_date: datetime, days: int = 7) -> Dict:
        """
        Generate a personal calendar based on birth star, tracking the birth bird's activities.
        
        Args:
            birth_date: Birth date
            birth_time: Birth time
            latitude: Location latitude
            longitude: Location longitude
            timezone: Timezone string
            start_date: Calendar start date
            days: Number of days to generate
            
        Returns:
            Dictionary containing birth star info and daily activities
        """
        try:
            from .data import RATING_MAP
            
            # Calculate birth star and birth bird
            birth_star, birth_bird = self.ephemeris.calculate_birth_star(
                birth_date, birth_time, latitude, longitude, timezone
            )
            
            calendar_data = {
                'birth_star': birth_star,
                'birth_bird': birth_bird,
                'start_date': start_date.strftime('%Y-%m-%d'),
                'days': days,
                'daily_activities': [],
                'summary': {
                    'total_periods': 0,
                    'favorable_periods': 0,
                    'unfavorable_periods': 0,
                    'best_periods': [],
                    'periods_to_avoid': []
                }
            }
            
            for day_offset in range(days):
                current_date = start_date + timedelta(days=day_offset)
                
                # Calculate full day data
                day_result = self.calculate_bird_periods(
                    current_date, datetime.combine(current_date.date(), datetime.min.time()),
                    latitude, longitude, timezone
                )
                
                # Extract birth bird periods from both day and night
                birth_bird_periods = []
                
                # Check day periods
                for period in day_result['day_periods']:
                    if period['bird'] == birth_bird:
                        birth_bird_periods.append({
                            'time_period': 'day',
                            'yama_index': period['yama_index'],
                            'activity': period['activity'],
                            'start_time': period['start_time'],
                            'end_time': period['end_time'],
                            'auspiciousness': period['auspiciousness'],
                            'rating': RATING_MAP[period['auspiciousness']],
                            'sub_periods': period.get('sub_periods', [])
                        })
                
                # Check night periods
                for period in day_result['night_periods']:
                    if period['bird'] == birth_bird:
                        birth_bird_periods.append({
                            'time_period': 'night',
                            'yama_index': period['yama_index'],
                            'activity': period['activity'],
                            'start_time': period['start_time'],
                            'end_time': period['end_time'],
                            'auspiciousness': period['auspiciousness'],
                            'rating': RATING_MAP[period['auspiciousness']],
                            'sub_periods': period.get('sub_periods', [])
                        })
                
                # Classify periods
                favorable = []
                unfavorable = []
                for period in birth_bird_periods:
                    if period['auspiciousness'] in ['very good', 'good']:
                        favorable.append(period)
                        calendar_data['summary']['favorable_periods'] += 1
                        
                        if period['auspiciousness'] == 'very good':
                            calendar_data['summary']['best_periods'].append(
                                f"{current_date.strftime('%Y-%m-%d')} {period['start_time']}-{period['end_time']} "
                                f"({birth_bird} {period['activity']})"
                            )
                    elif period['auspiciousness'] in ['bad', 'very bad']:
                        unfavorable.append(period)
                        calendar_data['summary']['unfavorable_periods'] += 1
                        
                        if period['auspiciousness'] == 'very bad':
                            calendar_data['summary']['periods_to_avoid'].append(
                                f"{current_date.strftime('%Y-%m-%d')} {period['start_time']}-{period['end_time']} "
                                f"({birth_bird} {period['activity']})"
                            )
                
                day_data = {
                    'date': current_date.strftime('%Y-%m-%d'),
                    'weekday': current_date.strftime('%A'),
                    'paksha': day_result['paksha'],
                    'birth_bird_periods': birth_bird_periods,
                    'favorable_periods': favorable,
                    'unfavorable_periods': unfavorable,
                    'summary': {
                        'best_activity': None,
                        'worst_activity': None,
                        'total_birth_bird_periods': len(birth_bird_periods)
                    }
                }
                
                # Find best and worst activities for the day
                if favorable:
                    best = max(favorable, key=lambda x: ['bad', 'average', 'good', 'very good'].index(x['auspiciousness']))
                    day_data['summary']['best_activity'] = f"{best['activity']} ({best['start_time']}-{best['end_time']})"
                
                if unfavorable:
                    worst = min(unfavorable, key=lambda x: ['very bad', 'bad', 'average', 'good'].index(x['auspiciousness']))
                    day_data['summary']['worst_activity'] = f"{worst['activity']} ({worst['start_time']}-{worst['end_time']})"
                
                calendar_data['daily_activities'].append(day_data)
                calendar_data['summary']['total_periods'] += len(birth_bird_periods)
            
            logger.info(f"Generated {days}-day birth star calendar for {birth_bird} bird")
            return calendar_data
            
        except Exception as e:
            logger.error(f"Error generating birth star calendar: {e}")
            raise
