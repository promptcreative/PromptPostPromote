################################################################
#                   VEDIC BURST ONE (VB1)                        #
#                                                               #
# Purpose: Calculate D9 (Navamsa) transits                      #
# Transits Checked:                                            #
#   - Rahu to D9 Ascendant                                     #
#   - Jupiter to D9 Descendant                                 #
#   - Saturn to D9 Descendant                                  #
#   - Sun to D9 Descendant                                     #
#   - Venus to D9 Descendant                                   #
#   - Yogi Planet to D9 Ascendant                             #
#                                                               #
# Time Period: Determined by input start and end dates          #
# Method: Minute-by-minute check with configurable orb         #
################################################################

import swisseph as swe
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from decimal import Decimal, getcontext
import os
import csv

getcontext().prec = 20

################################################################
#                         CONSTANTS                              #
################################################################

# Default Settings (can be overridden by API parameters)
DEFAULT_AYANAMSA = 23.85
DEFAULT_ORB = 2.5
DEFAULT_ORBTIGHT = 0.0001
SCRIPT_PREFIX = "VB1"
EXPORTS_FOLDER = "exports"

# Global variables for script compatibility
AYANAMSA = DEFAULT_AYANAMSA
ORB = DEFAULT_ORB
ORBTIGHT = DEFAULT_ORBTIGHT
BIRTH_DATE = None
BIRTH_LAT = None
BIRTH_LON = None

# Set ephemeris path
ephe_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'ephe')
if not os.path.exists(ephe_path):
    os.makedirs(ephe_path)
swe.set_ephe_path(ephe_path)

# Transit Types and Counters
TRANSIT_COUNTS = {
    'RAHU-ASC': {'count': 0, 'name': 'Rahu to D9 Ascendant'},
    'JUPITER-DSC': {'count': 0, 'name': 'Jupiter to D9 Descendant'},
    'SATURN-DSC': {'count': 0, 'name': 'Saturn to D9 Descendant'},
    'SUN-DSC': {'count': 0, 'name': 'Sun to D9 Descendant'},
    'VENUS-DSC': {'count': 0, 'name': 'Venus to D9 Descendant'},
    'YOGI-ASC': {'count': 0, 'name': 'Yogi Planet to D9 Ascendant'}
}

SIGNS = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
         'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']

def convert_jd_to_datetime(jd):
    """Convert Julian Day to datetime."""
    y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
    return datetime(y, m, d, int(h), int((h % 1) * 60))

def convert_local_to_ut(local_dt):
    """Convert local time to UT."""
    local_tz = ZoneInfo("America/New_York")
    local_dt = local_dt.replace(tzinfo=local_tz)
    return local_dt.astimezone(ZoneInfo("UTC"))

def get_julian_day(dt):
    """Convert datetime to Julian Day."""
    ut_time = convert_local_to_ut(dt)
    return swe.julday(ut_time.year, ut_time.month, ut_time.day,
                     ut_time.hour + ut_time.minute/60.0 + ut_time.second/3600.0)

def format_position(lon):
    """Format longitude as sign degree minute with raw degrees."""
    sign_num = int(lon / 30)
    deg = int(lon % 30)
    min = int((lon % 1) * 60)
    sec = int(((lon % 1) * 60 % 1) * 60)
    return f"{SIGNS[sign_num]} {deg}°{min:02d}'{sec:02d}\" ({lon:.6f}°)"


def check_orb(pos1, pos2):
    """Check if positions are within orb."""
    diff = abs(pos1 - pos2)
    return min(diff, 360 - diff)


################################################################
#                    D9 CALCULATIONS                             #
################################################################

def calculate_d9(lon):
    """Calculate D9 (Navamsa) position."""
    # Calculate D9 using multiplication method
    d9_pos = (lon * 9) % 360
    return d9_pos

def get_sidereal_position(jd, planet_id):
    """Get sidereal position using Lahiri ayanamsa."""
    flags = swe.FLG_SIDEREAL
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    return swe.calc_ut(jd, planet_id, flags)[0][0]

def get_ascendant(jd, lat, lon):
    """Calculate sidereal ascendant."""
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    # swe.houses() always returns tropical positions, so we need to subtract ayanamsa
    tropical_asc = swe.houses(jd, lat, lon, b'P')[0][0]
    ayanamsa = swe.get_ayanamsa(jd)
    sidereal_asc = (tropical_asc - ayanamsa) % 360
    return sidereal_asc

def calculate_natal_d9_points():
    """Calculate natal D9 ascendant and descendant."""
    jd = get_julian_day(BIRTH_DATE)

    asc_sid = get_ascendant(jd, BIRTH_LAT, BIRTH_LON)
    d9_asc = calculate_d9(asc_sid)
    d9_dsc = (d9_asc + 180) % 360

    print("\nDebug - Natal Points:")
    print(f"Sidereal ASC: {format_position(asc_sid)}")
    print(f"D9 ASC: {format_position(d9_asc)}")
    print(f"D9 DSC: {format_position(d9_dsc)}")

    return d9_asc, d9_dsc

def calculate_yogi_point():
    """Calculate Yogi Point."""
    jd = get_julian_day(BIRTH_DATE)

    sun_pos = get_sidereal_position(jd, swe.SUN)
    moon_pos = get_sidereal_position(jd, swe.MOON)

    yogi_point = (sun_pos + moon_pos + 93.33) % 360
    yogi_d9 = calculate_d9(yogi_point)

    print("\nDebug - Yogi Point:")
    print(f"Sidereal Yogi: {format_position(yogi_point)}")
    print(f"D9 Yogi: {format_position(yogi_d9)}")

    return swe.JUPITER, yogi_point, yogi_d9

################################################################
#                    TRANSIT CALCULATIONS                        #
################################################################

def check_transit(jd, planet_id, target_pos):
    """Check if planet is in transit to target position."""
    planet_pos = get_sidereal_position(jd, planet_id)
    orb_diff = check_orb(planet_pos, target_pos)
    return orb_diff <= ORB, planet_pos

def find_exact_transit(start_jd, end_jd, planet_id, target_pos):
    """Find exact transit time using binary search."""
    mid_jd = (start_jd + end_jd) / 2

    if (end_jd - start_jd) < 0.000001:  # About 0.1 seconds
        return mid_jd

    pos = get_sidereal_position(mid_jd, planet_id)
    orb = check_orb(pos, target_pos)

    if orb <= ORBTIGHT:
        return mid_jd

    pos_start = get_sidereal_position(start_jd, planet_id)
    orb_start = check_orb(pos_start, target_pos)

    if orb_start < orb:
        return find_exact_transit(start_jd, mid_jd, planet_id, target_pos)
    else:
        return find_exact_transit(mid_jd, end_jd, planet_id, target_pos)

def is_conjunct(pos1, pos2, orb=DEFAULT_ORB):
    """Check if two positions are in conjunction within orb."""
    diff = abs((pos1 - pos2 + 180) % 360 - 180)
    return diff <= orb, diff

def calculate_d9_ascendant(birth_jd, birth_lat, birth_lon):
    """Calculate D9 Ascendant for birth chart."""
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    tropical_asc = swe.houses(birth_jd, birth_lat, birth_lon, b'P')[0][0]
    ayanamsa = swe.get_ayanamsa(birth_jd)
    sidereal_asc = (tropical_asc - ayanamsa) % 360
    d9_asc = calculate_d9(sidereal_asc)
    return d9_asc

def calculate_yogi_planet(birth_jd):
    """Calculate Yogi Planet from birth chart."""
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    sun_pos = swe.calc_ut(birth_jd, swe.SUN, swe.FLG_SIDEREAL)[0][0]
    moon_pos = swe.calc_ut(birth_jd, swe.MOON, swe.FLG_SIDEREAL)[0][0]
    yogi_point = (sun_pos + moon_pos + 93.33) % 360
    return swe.JUPITER

def process_transits(start_date, end_date):
    """Process all transits within the given date range (legacy function)."""
    global BIRTH_DATE, BIRTH_LAT, BIRTH_LON
    
    if BIRTH_DATE is None:
        BIRTH_DATE = datetime(1973, 3, 9, 16, 56)
        BIRTH_LAT = 29.2108
        BIRTH_LON = -81.0228
    
    birth_jd = get_julian_day(BIRTH_DATE)
    d9_asc = calculate_d9_ascendant(birth_jd, BIRTH_LAT, BIRTH_LON)
    d9_dsc = (d9_asc + 180) % 360
    yogi_planet_id = calculate_yogi_planet(birth_jd)

    return process_transits_with_params(
        BIRTH_DATE, BIRTH_LAT, BIRTH_LON,
        BIRTH_LAT, BIRTH_LON,
        start_date, end_date, ORB
    )

def process_transits_with_params(birth_date, birth_lat, birth_lon, transit_lat, transit_lon, start_date, end_date, orb=DEFAULT_ORB):
    """Process VB1 transits with API parameters - MINUTE-BY-MINUTE scanning."""
    print(f"\n{SCRIPT_PREFIX} - D9 Transit Calculator (Minute-by-Minute)")
    print("-" * 50)
    print(f"Birth: {birth_date.strftime('%Y-%m-%d %H:%M')} at {birth_lat}°N, {birth_lon}°W")
    print(f"Transit Location: {transit_lat}°N, {transit_lon}°W")
    print(f"Period: {start_date} to {end_date}")
    
    ny_tz = ZoneInfo("America/New_York")
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=ny_tz)
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=ny_tz)
    
    birth_jd = get_julian_day(birth_date)
    d9_asc = calculate_d9_ascendant(birth_jd, birth_lat, birth_lon)
    d9_dsc = (d9_asc + 180) % 360
    yogi_planet_id = calculate_yogi_planet(birth_jd)
    
    print(f"D9 Ascendant: {format_position(d9_asc)}")
    print(f"D9 Descendant: {format_position(d9_dsc)}")

    all_transits = []
    active_transits = {}
    current_time = start_date
    last_day_logged = None
    
    transit_configs = [
        (swe.MEAN_NODE, d9_asc, 'RAHU-ASC', 'Rahu to D9 Ascendant'),
        (swe.JUPITER, d9_dsc, 'JUPITER-DSC', 'Jupiter to D9 Descendant'),
        (swe.SATURN, d9_dsc, 'SATURN-DSC', 'Saturn to D9 Descendant'),
        (swe.SUN, d9_dsc, 'SUN-DSC', 'Sun to D9 Descendant'),
        (swe.VENUS, d9_dsc, 'VENUS-DSC', 'Venus to D9 Descendant'),
        (yogi_planet_id, d9_asc, 'YOGI-ASC', 'Yogi Planet to D9 Ascendant')
    ]

    while current_time <= end_date:
        current_jd = get_julian_day(current_time)
        
        if current_time.day != last_day_logged:
            print(f"Processing {current_time.strftime('%Y-%m-%d')}...")
            last_day_logged = current_time.day

        for planet_id, target_pos, transit_code, description in transit_configs:
            planet_pos = get_sidereal_position(current_jd, planet_id)
            is_active, orb_diff = is_conjunct(planet_pos, target_pos, orb)

            if is_active and transit_code not in active_transits:
                transit = {
                    'start': current_time,
                    'end': None,
                    'jd': current_jd,
                    'type': description,
                    'transit_code': transit_code,
                    'orb': orb_diff,
                    'planet_pos': {'longitude': planet_pos, 'latitude': 0},
                    'target_pos': target_pos
                }
                active_transits[transit_code] = transit
                TRANSIT_COUNTS[transit_code]['count'] += 1

            elif not is_active and transit_code in active_transits:
                transit = active_transits.pop(transit_code)
                transit['end'] = current_time
                all_transits.append(transit)

        current_time += timedelta(minutes=1)

    for transit_code, transit in active_transits.items():
        transit['end'] = end_date
        all_transits.append(transit)

    print(f"\nFound {len(all_transits)} VB1 transits")
    return all_transits

def export_transits(transit_events):
    """Export transit events in Google Calendar compatible format."""
    export_folder = os.environ.get('EXPORT_FOLDER')
    if not export_folder:
        print("Error: EXPORT_FOLDER environment variable not set")
        return

    if not os.path.exists(export_folder):
        os.makedirs(export_folder)

    file_path = os.path.join(export_folder, f"{SCRIPT_PREFIX}_transits.csv")

    headers = [
        "Subject", "Start Date", "Start Time", "End Date", "End Time",
        "All Day Event", "Description", "Location", "Private"
    ]

    try:
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            if not transit_events:
                print(f"No transits found for {SCRIPT_PREFIX}")
                return

            for idx, event in enumerate(sorted(transit_events, key=lambda x: x['jd']), 1):
                start_dt = convert_jd_to_datetime(event['jd'])
                end_dt = start_dt + timedelta(minutes=30)  # 30 minute duration

                # Format position details
                planet_pos = format_position(event['planet_pos']['longitude'])
                target_pos = format_position(event['target_pos'])

                # Create detailed description
                description = (
                    f"{SCRIPT_PREFIX}: {event['type']}\n"
                    f"Planet Position: {planet_pos}\n"
                    f"Target Position: {target_pos}\n"
                    f"Transit ID: {SCRIPT_PREFIX}-{event['type']}-{idx:03d}"
                )

                writer.writerow([
                    f"{SCRIPT_PREFIX} {event['type']}",           # Subject
                    start_dt.strftime('%Y-%m-%d'),               # Start Date
                    start_dt.strftime('%H:%M:%S'),               # Start Time
                    end_dt.strftime('%Y-%m-%d'),                 # End Date
                    end_dt.strftime('%H:%M:%S'),                 # End Time
                    "FALSE",                                      # All Day Event
                    description,                                  # Description
                    "",                                          # Location
                    "FALSE"                                      # Private
                ])

        print(f"\nExported {len(transit_events)} {SCRIPT_PREFIX} transits to: {file_path}")
    except Exception as e:
        print(f"Error exporting transits: {str(e)}")

def calculate_vb1_transits(birth_date, birth_lat, birth_lon, transit_lat, transit_lon, start_date, end_date, ayanamsa=DEFAULT_AYANAMSA, orb=DEFAULT_ORB):
    """
    API function to calculate VB1 (D9) transits.
    
    Parameters:
    - birth_date: datetime object for birth date/time
    - birth_lat: float, birth latitude in degrees
    - birth_lon: float, birth longitude in degrees  
    - transit_lat: float, transit location latitude in degrees
    - transit_lon: float, transit location longitude in degrees
    - start_date: datetime object for start of period
    - end_date: datetime object for end of period
    - ayanamsa: float, ayanamsa value (default: 23.85)
    - orb: float, orb in degrees (default: 2.5)
    
    Returns:
    - List of transit events with timing and position data
    """
    global AYANAMSA, ORB
    AYANAMSA = ayanamsa
    ORB = orb
    
    for transit_type in TRANSIT_COUNTS:
        TRANSIT_COUNTS[transit_type]['count'] = 0
    
    transit_events = process_transits_with_params(
        birth_date, birth_lat, birth_lon,
        transit_lat, transit_lon,
        start_date, end_date, orb
    )
    
    return transit_events

def main():
    """Main execution function - for backward compatibility."""
    # Default hardcoded values for testing
    birth_date = datetime(1973, 3, 9, 16, 56)
    birth_lat = 29.2108
    birth_lon = -81.0228
    transit_lat = 40.7128
    transit_lon = -74.0060
    start_date = datetime(2024, 11, 15, 0, 0)
    end_date = datetime(2024, 12, 15, 23, 59)
    
    transit_events = calculate_vb1_transits(birth_date, birth_lat, birth_lon, transit_lat, transit_lon, start_date, end_date)
    export_transits(transit_events)

    print("\nTransit Counts:")
    for transit_type, data in TRANSIT_COUNTS.items():
        print(f"{data['name']}: {data['count']}")

    print(f"\nResults exported to {EXPORTS_FOLDER}/{SCRIPT_PREFIX}_transits.csv")

if __name__ == "__main__":
    main()