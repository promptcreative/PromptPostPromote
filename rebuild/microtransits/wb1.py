############################################
# TRANSIT CALCULATOR WITH YOGI POINT ASPECTS
# Calculation Period: Dec 22, 2024 - Nov 9, 2025
# Location: New York (40.7128°N, 74.0060°W)
############################################

import swisseph as swe
from datetime import datetime, timedelta
from decimal import Decimal, getcontext
from zoneinfo import ZoneInfo
import os
import csv
import statistics

#=============================================
# SECTION 1: CONFIGURATION AND CONSTANTS
#=============================================

# Precision settings
getcontext().prec = 20

# Default Astrological Settings (can be overridden by API parameters)
DEFAULT_AYANAMSA = 23.85
DEFAULT_ORB = 1.0  # Standard 1-degree orb to match yp.py and vb2.py
DEFAULT_ORBTIGHT = 0.0001

# Global variables for script compatibility
AYANAMSA = DEFAULT_AYANAMSA
ORB = DEFAULT_ORB
ORBTIGHT = DEFAULT_ORBTIGHT
BIRTH_DATE = None  # Will be set by API calls
TRANSIT_LOCATION = (40.7128, -74.0060)  # Default NYC coordinates

# Export Settings
EXPORTS_FOLDER = "exports"
SCRIPT_PREFIX = "WB1"
CALENDAR_COLOR = "#FFA500"  # Orange
CATEGORY = "Western Transits"

# Transit Types Configuration - Updated to match abaspect.csv
TRANSIT_CONFIGS = [
    # (Name, Type, Description, Named LT)
    ("Yogi-POF", "POF", "Yogi Point Conjunct Part of Fortune", "E1"),
    ("Yogi-Rising", "RISING", "Your Yogi Planet Rising", "U1"),
    ("Yogi-Transit", "TRANSIT_YOGI", "Yogi Point conjunct transit yogi point", "v1"),
    ("Yogi-Moon", "MOON", "Yogi Point Conjunct Moon", None),
    ("Yogi-Sun", "SUN", "Yogi Point Conjunct Sun", None),
    ("Yogi-Jupiter", "JUPITER", "Yogi Point Conjunct Jupiter", None)
]

#=============================================
# SECTION 2: CORE CALCULATION FUNCTIONS
#=============================================

def convert_local_to_ut(local_dt):
    """Convert local time to UT."""
    local_tz = ZoneInfo("America/New_York")
    local_dt = local_dt.replace(tzinfo=local_tz)
    return local_dt.astimezone(ZoneInfo("UTC"))

def calculate_yogi_point(jd):
    """Calculate sidereal Yogi point using Swiss Ephemeris."""
    flags = swe.FLG_SIDEREAL
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

    sun_pos = swe.calc_ut(jd, swe.SUN, flags)[0][0]
    moon_pos, _ = calculate_moon_position(jd) # Use improved moon calculation

    return (sun_pos + moon_pos + 93.20) % 360

def calculate_moon_position(jd):
    """Calculate Moon position with improved precision."""
    flags = swe.FLG_SIDEREAL | swe.FLG_SPEED
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

    # Get moon position with speed
    moon_data = swe.calc_ut(jd, swe.MOON, flags)
    pos = moon_data[0][0]
    speed = moon_data[0][3]

    # Adjust position based on moon's speed for sub-minute precision
    # This helps account for the moon's rapid motion
    return pos % 360, speed

def calculate_pof(asc, sun, moon):
    """
    Calculate Part of Fortune using correct day/night formula.
    For day charts (Sun above Asc): POF = Asc + Moon - Sun
    For night charts (Sun below Asc): POF = Asc - Moon + Sun

    All angles are in degrees and normalized to 0-360 range.
    """
    # Normalize all positions to 0-360 range
    asc = asc % 360
    sun = sun % 360
    moon = moon % 360

    # Determine if it's a day or night chart
    # If Sun is ahead of Asc in zodiacal order, it's above horizon (day chart)
    sun_ahead = (sun - asc + 360) % 360 <= 180

    if sun_ahead:  # Day chart
        pof = (asc + moon - sun) % 360
    else:  # Night chart
        pof = (asc - moon + sun) % 360

    return pof

def get_planet_position(jd, planet_id):
    """Get sidereal planet position with improved precision."""
    flags = swe.FLG_SIDEREAL
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)

    if planet_id == swe.MOON:
        pos, _ = calculate_moon_position(jd)
        return pos
    return swe.calc_ut(jd, planet_id, flags)[0][0]

def calculate_positions(jd):
    """Calculate all required positions with POF."""
    # Get house cusps and Ascendant
    cusps, ascmc = swe.houses(jd, TRANSIT_LOCATION[0], TRANSIT_LOCATION[1], b'P')
    transit_asc = cusps[0]

    # Calculate sun and moon positions
    transit_sun = get_planet_position(jd, swe.SUN)
    transit_moon = get_planet_position(jd, swe.MOON)

    # Calculate POF with corrected formula
    transit_pof = calculate_pof(transit_asc, transit_sun, transit_moon)

    return {
        'POF': transit_pof,
        'ASC': transit_asc,
        'SUN': transit_sun,
        'MOON': transit_moon,
        'JUP': get_planet_position(jd, swe.JUPITER),
    }


#=============================================
# SECTION 3: POSITION AND FORMAT FUNCTIONS
#=============================================

def format_position(lon):
    """Format longitude with zodiac sign and degrees."""
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    sign_num = int(lon / 30)
    deg = int(lon % 30)
    min = int((lon % 1) * 60)
    sec = int(((lon % 1) * 60 % 1) * 60)
    return f"{signs[sign_num]} {deg}°{min:02d}'{sec:02d}\""

#=============================================
# SECTION 4: TRANSIT DETECTION FUNCTIONS
#=============================================

def find_exact_transit_time(start_dt, end_dt, transit_type, target_pos):
    """Find exact transit time using binary search."""
    while (end_dt - start_dt) > timedelta(seconds=1):
        mid_dt = start_dt + (end_dt - start_dt)/2
        ut = convert_local_to_ut(mid_dt)
        jd = swe.julday(ut.year, ut.month, ut.day,
                       ut.hour + ut.minute/60.0 + ut.second/3600.0)

        # Get position based on transit type
        positions = calculate_positions(jd)
        if transit_type == 'POF':
            pos = positions['POF']
        elif transit_type == 'ASC':
            pos = positions['ASC']
        elif transit_type == 'RISING':
            pos = positions['JUP']
        elif transit_type == 'TRANSIT_YOGI':
            pos = calculate_yogi_point(jd)
        elif transit_type == 'MOON':
            pos = positions['MOON']
        elif transit_type == 'SUN':
            pos = positions['SUN']
        elif transit_type == 'JUPITER':
            pos = positions['JUP']
        else:
            raise ValueError(f"Unknown transit type: {transit_type}")


        if abs(pos - target_pos) < ORBTIGHT:
            return mid_dt
        elif pos < target_pos:
            start_dt = mid_dt
        else:
            end_dt = mid_dt

    return start_dt

def find_transit_edges(exact_time, transit_type, target_pos):
    """Find applying and separating edges of transit window."""
    start_time = exact_time
    prev_orb = 0

    # Find applying edge (going backwards)
    while True:
        ut = convert_local_to_ut(start_time)
        jd = swe.julday(ut.year, ut.month, ut.day,
                       ut.hour + ut.minute/60.0)
        positions = calculate_positions(jd)
        if transit_type == 'POF':
            pos = positions['POF']
        elif transit_type == 'ASC':
            pos = positions['ASC']
        elif transit_type == 'RISING':
            pos = positions['JUP']
        elif transit_type == 'TRANSIT_YOGI':
            pos = calculate_yogi_point(jd)
        elif transit_type == 'MOON':
            pos = positions['MOON']
        elif transit_type == 'SUN':
            pos = positions['SUN']
        elif transit_type == 'JUPITER':
            pos = positions['JUP']
        else:
            raise ValueError(f"Unknown transit type: {transit_type}")

        current_orb = abs(pos - target_pos)
        if current_orb > ORB or current_orb <= prev_orb:
            break
        prev_orb = current_orb
        start_time -= timedelta(minutes=1)

    # Reset prev_orb for separating edge
    prev_orb = 0
    end_time = exact_time

    # Find separating edge (going forwards)
    while True:
        ut = convert_local_to_ut(end_time)
        jd = swe.julday(ut.year, ut.month, ut.day,
                       ut.hour + ut.minute/60.0)
        positions = calculate_positions(jd)
        if transit_type == 'POF':
            pos = positions['POF']
        elif transit_type == 'ASC':
            pos = positions['ASC']
        elif transit_type == 'RISING':
            pos = positions['JUP']
        elif transit_type == 'TRANSIT_YOGI':
            pos = calculate_yogi_point(jd)
        elif transit_type == 'MOON':
            pos = positions['MOON']
        elif transit_type == 'SUN':
            pos = positions['SUN']
        elif transit_type == 'JUPITER':
            pos = positions['JUP']
        else:
            raise ValueError(f"Unknown transit type: {transit_type}")

        current_orb = abs(pos - target_pos)
        if current_orb > ORB or current_orb <= prev_orb:
            break
        prev_orb = current_orb
        end_time += timedelta(minutes=1)

    return start_time + timedelta(minutes=1), end_time - timedelta(minutes=1)



#=============================================
# SECTION 5: MAIN TRANSIT SEARCH FUNCTION
#=============================================

def find_transits(birth_yogi_point):
    """Find all transits to the Yogi Point."""
    transits = []

    print(f"\nCalculating Western Burst One (WB1) transits...")
    print(f"Birth Yogi Point: {format_position(birth_yogi_point)}")

    # Track timing for validation
    calculation_times = []
    prev_time = None

    for transit_name, transit_type, description, named_lt in TRANSIT_CONFIGS:
        print(f"\nChecking {transit_name} transits...")
        active_transits = {}  # Track active transits for this type
        current_dt = START_DATE

        while current_dt <= END_DATE:
            # Track time intervals for validation
            if prev_time:
                interval = (current_dt - prev_time).total_seconds()
                calculation_times.append(interval)
            prev_time = current_dt

            ut = convert_local_to_ut(current_dt)
            jd = swe.julday(ut.year, ut.month, ut.day,
                           ut.hour + ut.minute/60.0)

            positions = calculate_positions(jd)
            if transit_type == 'POF':
                pos = positions['POF']
            elif transit_type == 'ASC':
                pos = positions['ASC']
            elif transit_type == 'RISING':
                pos = positions['JUP']
            elif transit_type == 'TRANSIT_YOGI':
                pos = calculate_yogi_point(jd)
            elif transit_type == 'MOON':
                pos = positions['MOON']
            elif transit_type == 'SUN':
                pos = positions['SUN']
            elif transit_type == 'JUPITER':
                pos = positions['JUP']
            else:
                raise ValueError(f"Unknown transit type: {transit_type}")

            orb = abs(pos - birth_yogi_point)

            # Check for transit entry
            if orb <= ORB:
                if transit_name not in active_transits:
                    exact_time = find_exact_transit_time(
                        current_dt - timedelta(minutes=2),
                        current_dt + timedelta(minutes=2),
                        transit_type,
                        birth_yogi_point
                    )

                    active_transits[transit_name] = {
                        'name': f"{SCRIPT_PREFIX} {transit_name}",
                        'type': transit_type,
                        'start': current_dt,
                        'exact': exact_time,
                        'target_pos': format_position(birth_yogi_point),
                        'transit_pos': format_position(pos),
                        'description': description,
                        'transit_code': transit_type,
                        'named_lt': named_lt,
                        'calculation_interval': statistics.mean(calculation_times) if calculation_times else 60.0,
                        'start_pos': pos,
                        'min_orb': orb
                    }

            # Check for transit exit
            elif transit_name in active_transits:
                transit = active_transits[transit_name]
                transit['end'] = current_dt - timedelta(minutes=1)
                transit['orb'] = transit['min_orb']
                duration = transit['end'] - transit['start']
                transit['exact_precision'] = duration >= timedelta(minutes=1)
                if not transit['exact_precision']:
                    transit['end'] = transit['start'] + timedelta(minutes=1)
                transits.append(transit)
                del active_transits[transit_name]

            # Update minimum orb for active transit
            elif transit_name in active_transits:
                active_transits[transit_name]['min_orb'] = min(
                    active_transits[transit_name]['min_orb'],
                    orb
                )

            # Check each minute
            current_dt += timedelta(minutes=1)

    return sorted(transits, key=lambda x: x['exact'])

#=============================================
# SECTION 6: EXPORT FUNCTIONS
#=============================================

def export_transits(transits):
    """Export transits to CSV files with consistent format."""
    export_folder = os.environ.get('EXPORT_FOLDER')
    if not export_folder:
        batch_folder = datetime.now().strftime("%Y%m%d_%H%M")
        export_folder = os.path.join(EXPORTS_FOLDER, batch_folder)

    if not os.path.exists(export_folder):
        os.makedirs(export_folder)

    file_path = os.path.join(export_folder, f"{SCRIPT_PREFIX}_transits.csv")

    headers = [
        "Subject", "Start Date", "Start Time", "End Date", "End Time",
        "Description", "Duration", "Transit ID", "Category", "Calendar Color"
    ]

    try:
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            for idx, transit in enumerate(transits, 1):
                duration = int((transit['end'] - transit['start']).total_seconds() / 60)
                transit_id = f"{SCRIPT_PREFIX}-{transit['transit_code']}-{idx:03d}"
                writer.writerow([
                    f"{SCRIPT_PREFIX} {transit['type']}",
                    transit['start'].strftime('%m/%d/%Y'),
                    transit['start'].strftime('%H:%M'),
                    transit['end'].strftime('%m/%d/%Y'),
                    transit['end'].strftime('%H:%M'),
                    f"{SCRIPT_PREFIX}: {transit['type']} | Orb: {transit['orb']:.2f}° | Duration: {duration}m",
                    f"{duration}m",
                    transit_id,
                    CATEGORY,
                    CALENDAR_COLOR
                ])

        print(f"\nExported {len(transits)} {SCRIPT_PREFIX} transits to: {file_path}")
    except Exception as e:
        print(f"Error exporting transits: {str(e)}")


#=============================================
# SECTION 7: MAIN EXECUTION
#=============================================

def main():
    """Main execution function."""
    try:
        swe.set_ephe_path()

        # Calculate birth Yogi Point
        birth_ut = convert_local_to_ut(BIRTH_DATE)
        birth_jd = swe.julday(birth_ut.year, birth_ut.month, birth_ut.day,
                             birth_ut.hour + birth_ut.minute/60.0)
        birth_yogi_point = calculate_yogi_point(birth_jd)

        # Find and export transits
        transits = find_transits(birth_yogi_point)
        export_transits(transits)

        print("\nCalculation complete! Files exported to 'exports' folder.")
        print(f"Date Range: {START_DATE.strftime('%B %d')} - {END_DATE.strftime('%B %d, %Y')}")
        print(f"Total transits found: {len(transits)}")

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        swe.close()

def process_transits(start_date=None, end_date=None):
    """Process WB1 transits between two dates with minute-by-minute precision."""
    if start_date is None or end_date is None:
        raise ValueError("Both start_date and end_date must be provided")

    print("\nCalculating Western Burst One (WB1) transits...")
    print(f"Period: {start_date} to {end_date}")

    # Ensure we have timezone-aware datetime objects
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=ZoneInfo("UTC"))
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=ZoneInfo("UTC"))

    # Convert start and end dates to JD
    birth_ut = convert_local_to_ut(BIRTH_DATE)
    birth_jd = swe.julday(birth_ut.year, birth_ut.month, birth_ut.day,
                         birth_ut.hour + birth_ut.minute/60.0)
    birth_yogi_point = calculate_yogi_point(birth_jd)

    # Set global date range for find_transits
    global START_DATE, END_DATE
    START_DATE = start_date
    END_DATE = end_date

    # Find transits
    transits = find_transits(birth_yogi_point)

    if transits:
        export_transits(transits)
        print(f"\nFound {len(transits)} WB1 transits")
    else:
        print("\nNo transits found in the specified period.")
        # Create empty export files
        export_transits([])

    return transits


################################################################
#                    API WRAPPER FUNCTIONS                      #
################################################################

def calculate_wb1_transits(birth_date, birth_time, birth_latitude, birth_longitude, start_date, days_span):
    """
    API wrapper function for WB1 transit calculations
    Returns transits in the format expected by the API
    """
    try:
        global BIRTH_DATE, TRANSIT_LOCATION
        
        # Set global birth date from parameters
        if isinstance(birth_date, str):
            BIRTH_DATE = datetime.fromisoformat(birth_date)
        else:
            BIRTH_DATE = birth_date
            
        # Parse birth time if provided as string
        if isinstance(birth_time, str):
            time_parts = birth_time.split(':')
            BIRTH_DATE = BIRTH_DATE.replace(
                hour=int(time_parts[0]), 
                minute=int(time_parts[1]),
                second=int(time_parts[2]) if len(time_parts) > 2 else 0
            )
        
        # Set transit location (using current location from parameters)
        TRANSIT_LOCATION = (float(birth_latitude), float(birth_longitude))
        
        # Convert parameters to datetime objects
        if isinstance(start_date, str):
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        else:
            start_dt = start_date
            
        end_dt = start_dt + timedelta(days=days_span)
        
        # Call the main processing function
        transits = process_transits(start_dt, end_dt)
        
        # Convert to API format
        api_transits = []
        for transit in transits:
            api_transits.append({
                'date': transit['start'].strftime('%Y-%m-%d'),
                'time': f"{transit['start'].strftime('%H:%M')}-{transit['end'].strftime('%H:%M')}",
                'type': transit['type'],
                'description': f"WB1: {transit['description']}",
                'script': 'wb1.py',
                'datetime': transit['start'].isoformat(),  # For iCal export
                'start_time': transit['start'].isoformat(),  # Alternative format
                'end_time': transit['end'].isoformat()
            })
            
        return api_transits
        
    except Exception as e:
        print(f"Error in calculate_wb1_transits: {str(e)}")
        return []

if __name__ == "__main__":
    try:
        # Example date range for standalone testing
        start_date = datetime(2025, 1, 10, 0, 0)  # Today
        end_date = datetime(2025, 1, 20, 23, 59)  # 10 days from now

        transits = process_transits(start_date, end_date)

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        swe.close()