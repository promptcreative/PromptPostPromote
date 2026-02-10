################################################################
#                   VEDIC BURST TWO (VB2)                        #
#                                                               #
# Purpose: Calculate transits to natal Yogi Point               #
# Transits Checked:                                            #
#   - Sun to Yogi Point                                        #
#   - Moon to Yogi Point                                       #
#   - Jupiter to Yogi Point                                    #
#   - Ascendant to Yogi Point                                  #
#                                                               #
# Time Period: Determined by input start and end dates          #
# Method: Minute-by-minute check with 1° orb                   #
################################################################

import swisseph as swe
from datetime import datetime, timedelta
import os
import csv
from zoneinfo import ZoneInfo
from decimal import Decimal, getcontext

# Set decimal precision
getcontext().prec = 10

################################################################
#                         CONSTANTS                              #
################################################################

# Script Settings
SCRIPT_PREFIX = "VB2"
CATEGORY = "Vedic Transits"
CALENDAR_COLOR = "#228B22"  # Forest Green
EXPORTS_FOLDER = "exports"

# Default Calculation Settings (can be overridden by API parameters)
DEFAULT_AYANAMSA = 23.85  # Fixed Lahiri ayanamsa value
DEFAULT_ORB = 1.0  # Standard 1-degree orb
DEFAULT_ORBTIGHT = 0.0001  # For exact aspect timing

# Global variables for script compatibility
AYANAMSA = DEFAULT_AYANAMSA
ORB = DEFAULT_ORB
ORBTIGHT = DEFAULT_ORBTIGHT
BIRTH_DATE = None  # Will be set by API calls
BIRTH_LAT = None  # Birth latitude
BIRTH_LON = None  # Birth longitude

# Set ephemeris path
ephe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ephe')
if not os.path.exists(ephe_path):
    os.makedirs(ephe_path)
swe.set_ephe_path(ephe_path)

def convert_local_to_ut(local_dt):
    """Convert local time to UT."""
    try:
        local_tz = ZoneInfo("America/New_York")
        local_dt = local_dt.replace(tzinfo=local_tz)
        return local_dt.astimezone(ZoneInfo("UTC"))
    except Exception as e:
        print(f"Error converting time to UT: {str(e)}")
        raise

def get_julian_day(dt):
    """Convert datetime to Julian Day."""
    try:
        ut_time = convert_local_to_ut(dt)
        jd = swe.julday(ut_time.year, ut_time.month, ut_time.day,
                       ut_time.hour + ut_time.minute/60.0 + ut_time.second/3600.0)
        return jd
    except Exception as e:
        print(f"Error calculating Julian Day: {str(e)}")
        raise

def calculate_natal_yogi_point():
    """Calculate natal Yogi point in sidereal zodiac."""
    try:
        print("\nCalculating Natal Yogi Point:")
        print(f"Birth Date: {BIRTH_DATE}")
        print(f"Birth Location: {BIRTH_LAT}°N, {abs(BIRTH_LON)}°W")
        print(f"Ayanamsa: {AYANAMSA}°")

        birth_jd = get_julian_day(BIRTH_DATE)
        print(f"Birth JD: {birth_jd}")

        # Set ayanamsa for sidereal calculations
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        # Calculate Sun and Moon positions
        sun_result = swe.calc_ut(birth_jd, swe.SUN, swe.FLG_SIDEREAL)
        moon_result = swe.calc_ut(birth_jd, swe.MOON, swe.FLG_SIDEREAL)

        if sun_result is None or moon_result is None:
            raise ValueError("Failed to calculate Sun or Moon positions")

        sun_sid = float(sun_result[0][0])
        moon_sid = float(moon_result[0][0])

        print(f"\nSidereal Positions:")
        print(f"Sun: {sun_sid:.6f}° ({int(sun_sid)}°{int((sun_sid % 1) * 60)}'{((sun_sid % 1) * 60 % 1) * 60:.2f}\")")
        print(f"Moon: {moon_sid:.6f}° ({int(moon_sid)}°{int((moon_sid % 1) * 60)}'{((moon_sid % 1) * 60 % 1) * 60:.2f}\")")

        # Calculate Yogi point using sidereal positions
        sum_points = sun_sid + moon_sid
        print(f"\nCalculation Steps:")
        print(f"1. Sun + Moon: {sum_points:.6f}°")
        print(f"2. Adding constant (93.33°): {sum_points + 93.33:.6f}°")

        yogi_point = (sum_points + 93.33) % 360

        print(f"\nFinal Yogi Point: {yogi_point:.6f}°")
        print(f"In DMS: {int(yogi_point)}°{int((yogi_point % 1) * 60)}'{((yogi_point % 1) * 60 % 1) * 60:.2f}\"")

        return yogi_point

    except Exception as e:
        print(f"Error calculating natal Yogi point: {str(e)}")
        raise

def calculate_positions(jd):
    """Calculate all required positions in sidereal zodiac."""
    try:
        # Set sidereal mode
        swe.set_sid_mode(swe.SIDM_LAHIRI)

        positions = {}
        # Calculate planetary positions in sidereal zodiac
        for planet, name in [(swe.SUN, 'SUN'), (swe.MOON, 'MOON'), (swe.JUPITER, 'JUP')]:
            result = swe.calc_ut(jd, planet, swe.FLG_SIDEREAL)
            if result is None:
                raise ValueError(f"Failed to calculate {name} position")
            positions[name] = float(result[0][0]) % 360

        # Get sidereal Ascendant position using standard houses function with sidereal flag
        cusps, ascmc = swe.houses(jd, 40.7128, -74.0060, b'P')  # Default location

        if cusps is None or ascmc is None:
            raise ValueError("Failed to calculate houses and Ascendant")

        # Get Ascendant from ascmc[0] and apply sidereal offset
        asc_tropical = float(ascmc[0])
        positions['ASC'] = (asc_tropical - DEFAULT_AYANAMSA) % 360

        return positions

    except Exception as e:
        print(f"Error calculating positions: {str(e)}")
        raise

def is_conjunct(pos1, pos2):
    """Check if two positions are in conjunction within orb."""
    try:
        diff = abs((pos1 - pos2 + 180) % 360 - 180)
        return diff <= DEFAULT_ORB, diff
    except Exception as e:
        print(f"Error checking conjunction: {str(e)}")
        raise

def process_transits(start_date=None, end_date=None):
    """Process VB2 transits between two dates."""
    if start_date is None or end_date is None:
        raise ValueError("Both start_date and end_date must be provided")

    ny_tz = ZoneInfo("America/New_York")

    # Standardize timezone handling
    start_date = start_date.astimezone(ny_tz) if start_date.tzinfo else start_date.replace(tzinfo=ny_tz)
    end_date = end_date.astimezone(ny_tz) if end_date.tzinfo else end_date.replace(tzinfo=ny_tz)

    print("\nProcessing VB2 transits...")
    print(f"Period: {start_date} to {end_date}")

    # Calculate birth positions (using legacy hardcoded values)
    birth_date = datetime(1973, 3, 9, 16, 56)
    birth_ut = convert_local_to_ut(birth_date)
    birth_jd = swe.julday(birth_ut.year, birth_ut.month, birth_ut.day,
                         birth_ut.hour + birth_ut.minute/60.0)
    birth_positions = calculate_positions(birth_jd)

    natal_yogi_point = calculate_natal_yogi_point() #Added to get the yogi point

    print("\nStarting transit search...")
    transits = find_transits(natal_yogi_point, start_date, end_date)

    if transits:
        print(f"\nFound {len(transits)} VB2 transits")
        return transits
    else:
        print("\nNo VB2 transits found in the specified period")
        return []


def find_transits(natal_yogi_point, start_date, end_date):
    """Find transits to Yogi Point."""
    try:
        transits = []
        active_transits = {}

        transit_configs = {
            'SUN': {'code': 'SUN-YOG', 'name': 'Sun-Yogi'},
            'MOON': {'code': 'MOON-YOG', 'name': 'Moon-Yogi'},
            'JUP': {'code': 'JUP-YOG', 'name': 'Jupiter-Yogi'},
            'ASC': {'code': 'ASC-YOG', 'name': 'ASC-Yogi'}
        }

        print(f"\nStarting transit search for Yogi Point at {natal_yogi_point:.6f}°")

        current_time = start_date
        prev_positions = None

        while current_time <= end_date:
            try:
                jd = get_julian_day(current_time)
                positions = calculate_positions(jd)

                if prev_positions is None:
                    prev_positions = positions
                    current_time += timedelta(minutes=1)
                    continue

                for body_name, body_config in transit_configs.items():
                    transit_key = body_config['code']
                    current_pos = float(positions.get(body_name, 0)) % 360
                    prev_pos = float(prev_positions.get(body_name, 0)) % 360

                    # Normalize natal Yogi point
                    normalized_yogi = float(natal_yogi_point) % 360

                    # Calculate orb with normalized positions
                    in_orb_now = abs((current_pos - normalized_yogi + 180) % 360 - 180) <= DEFAULT_ORB
                    in_orb_prev = abs((prev_pos - normalized_yogi + 180) % 360 - 180) <= DEFAULT_ORB

                    # Calculate actual orb distance
                    diff_now = abs((current_pos - normalized_yogi + 180) % 360 - 180)

                    # Transit entry
                    if in_orb_now and not in_orb_prev:
                        active_transits[transit_key] = {
                            'type': body_config['name'],
                            'start': current_time,
                            'transit_code': transit_key,
                            'description': f"{body_name} conjunct Natal Yogi Point",
                            'start_pos': current_pos,
                            'min_diff': diff_now
                        }
                        print(f"\nTransit start detected - {body_config['name']}")
                        print(f"Time: {current_time}")
                        print(f"Position: {current_pos:.6f}°")
                        print(f"Orb: {diff_now:.6f}°")

                    # Update minimum orb
                    elif transit_key in active_transits:
                        if diff_now < active_transits[transit_key].get('min_diff', ORB):
                            active_transits[transit_key]['min_diff'] = diff_now
                            active_transits[transit_key]['exact'] = current_time

                    # Transit exit
                    if not in_orb_now and in_orb_prev and transit_key in active_transits:
                        transit = active_transits.pop(transit_key)
                        transit['end'] = current_time
                        transit['end_pos'] = current_pos

                        if 'exact' not in transit:
                            transit['exact'] = transit['start'] + (transit['end'] - transit['start'])/2

                        print(f"\nTransit end detected - {body_config['name']}")
                        print(f"End Time: {current_time}")
                        print(f"Duration: {(current_time - transit['start']).total_seconds() / 60:.1f} minutes")
                        print(f"Minimum Orb: {transit['min_diff']:.6f}°")

                        transits.append(transit)

                prev_positions = positions
                current_time += timedelta(minutes=1)

            except Exception as e:
                print(f"Error processing time {current_time}: {str(e)}")
                current_time += timedelta(minutes=1)
                continue

        return sorted(transits, key=lambda x: x['start'])

    except Exception as e:
        print(f"Error finding transits: {str(e)}")
        raise

def get_export_filenames(script_prefix):
    """Generate filenames with current timestamp."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return (
        f"{script_prefix}_Windows_{timestamp}.csv",
        f"{script_prefix}_Exact_{timestamp}.csv"
    )

def export_transits(transits, script_prefix, export_path=EXPORTS_FOLDER):
    """Export transits in standardized format."""
    if not transits:
        return

    export_folder = os.environ.get('EXPORT_FOLDER', export_path)
    if not export_folder:
        print("Error: EXPORT_FOLDER environment variable not set")
        return

    windows_filename, exact_filename = get_export_filenames(script_prefix)
    file_path = os.path.join(export_folder, windows_filename)

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
                transit_id = f"{SCRIPT_PREFIX}-{transit['type']}-{idx:03d}"

                # Convert times to NY timezone for display
                ny_tz = ZoneInfo("America/New_York")
                start_ny = transit['start'].astimezone(ny_tz)
                end_ny = transit['end'].astimezone(ny_tz)

                writer.writerow([
                    f"{SCRIPT_PREFIX} {transit['type']}",                    
                    start_ny.strftime('%m/%d/%Y'),  # Start Date
                    start_ny.strftime('%H:%M'),     # Start Time
                    end_ny.strftime('%m/%d/%Y'),    # End Date
                    end_ny.strftime('%H:%M'),       # End Time
                    f"{SCRIPT_PREFIX}: {transit['type']} | Orb: {transit.get('min_diff', 0):.2f}° | Duration: {duration}m",
                    f"{duration}m",
                    transit_id,
                    CATEGORY,
                    CALENDAR_COLOR
                ])

        print(f"\nExported {len(transits)} {SCRIPT_PREFIX} transits to: {file_path}")
    except Exception as e:
        print(f"Error exporting transits: {str(e)}")


    # Export exact times
    file_path = os.path.join(export_folder, exact_filename)
    try:
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            for idx, transit in enumerate(transits, 1):
                transit_id = f"{SCRIPT_PREFIX}-{transit['type']}-{idx:03d}-EX"

                writer.writerow([
                    f"{transit['type']} ⚡",
                    transit['exact'].strftime('%Y-%m-%d'),
                    transit['exact'].strftime('%H:%M:%S'),
                    transit['exact'].strftime('%Y-%m-%d'),
                    transit['exact'].strftime('%H:%M:%S'),
                    f"⚡ {SCRIPT_PREFIX}: {transit['type']} | Peak Transit",
                    "0m",
                    transit_id,
                    CATEGORY,
                    CALENDAR_COLOR
                ])

        print(f"\nExported {len(transits)} {SCRIPT_PREFIX} exact transits to: {file_path}")
    except Exception as e:
        print(f"Error exporting exact transits: {str(e)}")


def print_calculation_summary(transits):
    """Print summary of found transits."""
    print("\n=== Vedic Burst Two (VB2)Transit Calculation Summary ===")

    transit_counts = {
        'Sun-Yogi': 0,
        'Moon-Yogi': 0,
        'Jupiter-Yogi': 0,
        'ASC-Yogi': 0
    }

    for transit in transits:
        for transit_type in transit_counts.keys():
            if transit_type in transit['type']:
                transit_counts[transit_type] += 1

    print("\nTransits Found:")
    for transit_type, count in transit_counts.items():
        print(f"- {transit_type}: {count} periods")

    print("\nExport Details:")
    print(f"- Window transits exported to: {EXPORTS_FOLDER}/VB2_Windows_*.csv")
    print(f"- Exact times exported to: {EXPORTS_FOLDER}/VB2_Exact_*.csv")
    print("\nComplete! ✨")

################################################################
#                    API WRAPPER FUNCTIONS                      #
################################################################

def calculate_vb2_transits(birth_date, birth_time, birth_latitude, birth_longitude, start_date, days_span):
    """
    API wrapper function for VB2 transit calculations
    Returns transits in the format expected by the API
    """
    try:
        global BIRTH_DATE, BIRTH_LAT, BIRTH_LON
        
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
        
        # Set global location variables
        BIRTH_LAT = float(birth_latitude)
        BIRTH_LON = float(birth_longitude)
        
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
                'description': f"VB2: {transit['type']} Transit",
                'script': 'vb2.py',
                'datetime': transit['start'].isoformat(),  # For iCal export
                'start_time': transit['start'].isoformat(),  # Alternative format
                'end_time': transit['end'].isoformat()
            })
            
        return api_transits
        
    except Exception as e:
        print(f"Error in calculate_vb2_transits: {str(e)}")
        return []

def calculate_yogi_point_transits(birth_date, birth_time, birth_latitude, birth_longitude, start_date, days_span):
    """
    API wrapper function for Yogi Point transit calculations (same as VB2)
    """
    try:
        global BIRTH_DATE, BIRTH_LAT, BIRTH_LON
        
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
        
        # Set global location variables
        BIRTH_LAT = float(birth_latitude)
        BIRTH_LON = float(birth_longitude)
        
        return calculate_vb2_transits(birth_date, birth_time, birth_latitude, birth_longitude, start_date, days_span)
    except Exception as e:
        print(f"Error in calculate_yogi_point_transits: {str(e)}")
        return []

################################################################
#                    MAIN EXECUTION                             #
################################################################

if __name__ == "__main__":
    try:
        # Example date range for standalone testing
        start_date = datetime(2025, 1, 10, 0, 0)  # Today
        end_date = datetime(2025, 1, 20, 23, 59)  # 10 days from now

        transits = process_transits(start_date, end_date)
        export_transits(transits, SCRIPT_PREFIX)
        print_calculation_summary(transits)

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        swe.close()