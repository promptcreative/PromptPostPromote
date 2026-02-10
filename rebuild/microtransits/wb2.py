################################################################
#                   WESTERN BURST TWO (WB2)                      #
#                                                               #
# Purpose: Calculate natal POF/POI transits and special aspects #
# Method: Minute-by-minute check with 1° orb                   #
################################################################

import swisseph as swe
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import csv
import os

################################################################
#                         CONSTANTS                              #
################################################################

# Script Settings
SCRIPT_PREFIX = "WB2"
CALENDAR_COLOR = "#228B22"  # Forest Green
CATEGORY = "Western Transits"
EXPORTS_FOLDER = "exports"
DEFAULT_ORB = 1.0  # Standard 1-degree orb for transits
DEFAULT_ORBTIGHT = 0.0001  # For exact aspect timing

# Global variables for script compatibility
ORB = DEFAULT_ORB
ORBTIGHT = DEFAULT_ORBTIGHT

################################################################
#                    CALCULATION FUNCTIONS                       #
################################################################

def convert_local_to_ut(local_dt):
    """Convert local time to UT."""
    local_tz = ZoneInfo("America/New_York")
    local_dt = local_dt.replace(tzinfo=local_tz)
    return local_dt.astimezone(ZoneInfo("UTC"))

def calculate_pof(asc, sun, moon):
    """
    Calculate Part of Fortune using correct day/night formula.
    Day chart (Sun above horizon): POF = ASC + Moon - Sun
    Night chart (Sun below horizon): POF = ASC + Sun - Moon
    
    Day/Night determination: Sun is above horizon when it's in the upper 
    hemisphere (between DSC and ASC going through the top of the chart).
    This occurs when (ASC - Sun + 360) % 360 < 180.
    """
    # Normalize all positions to 0-360 range
    asc = asc % 360
    sun = sun % 360
    moon = moon % 360

    # Determine if it's a day or night chart based on Sun's horizon position
    # Day = Sun in upper hemisphere (houses 7-12, above horizon)
    # If Sun needs to travel < 180° to reach ASC, it's above horizon
    is_day_chart = (asc - sun + 360) % 360 < 180

    if is_day_chart:  # Day chart - Sun above horizon
        pof = (asc + moon - sun) % 360
    else:  # Night chart - Sun below horizon
        pof = (asc + sun - moon) % 360

    return pof

def calculate_positions_with_location(jd, lat, lon):
    """Calculate all required positions for given location."""
    positions = {}

    # Calculate house cusps and Ascendant
    cusps, ascmc = swe.houses(jd, lat, lon, b'P')
    positions['ASC'] = float(ascmc[0])

    # Calculate planetary positions
    for planet, name in [(swe.SUN, 'SUN'), (swe.MOON, 'MOON'), (swe.JUPITER, 'JUP')]:
        positions[name] = float(swe.calc_ut(jd, planet)[0][0])

    # Calculate POF and POI
    positions['POF'] = calculate_pof(
        positions['ASC'],
        positions['SUN'],
        positions['MOON']
    )
    positions['POI'] = (positions['ASC'] + positions['JUP'] - positions['SUN']) % 360
    positions['RAHU'] = float(swe.calc_ut(jd, swe.MEAN_NODE)[0][0])
    positions['LAGNA_LORD'] = calculate_lagna_lord(positions['ASC'], jd)
    
    # Calculate Regulus position using Swiss Ephemeris (proper precession)
    try:
        regulus_data = swe.fixstar_ut('Regulus', jd)
        positions['REGULUS'] = float(regulus_data[0][0])
    except Exception:
        # Fallback to approximate current position if fixstar fails
        positions['REGULUS'] = 150.0  # ~0° Virgo (Regulus crossed into Virgo in 2012)

    return positions

def calculate_lagna_lord(asc_pos, jd):
    """Calculate the position of the Lagna Lord based on Ascendant sign"""
    # Determine Ascendant sign (0 = Aries, 1 = Taurus, etc.)
    asc_sign = int(asc_pos / 30)

    # Map signs to ruling planets
    rulers = {
        0: swe.MARS,    # Aries
        1: swe.VENUS,   # Taurus
        2: swe.MERCURY, # Gemini
        3: swe.MOON,    # Cancer
        4: swe.SUN,     # Leo
        5: swe.MERCURY, # Virgo
        6: swe.VENUS,   # Libra
        7: swe.MARS,    # Scorpio
        8: swe.JUPITER, # Sagittarius
        9: swe.SATURN,  # Capricorn
        10: swe.SATURN, # Aquarius
        11: swe.JUPITER # Pisces
    }

    ruler_planet = rulers[asc_sign]
    return float(swe.calc_ut(jd, ruler_planet)[0][0])

def is_conjunct(pos1, pos2, orb=DEFAULT_ORB):
    """Check if two positions are within orb."""
    diff = abs(pos1 - pos2)
    min_diff = min(diff, 360 - diff)
    return min_diff <= orb, min_diff

def calculate_wb2_transits(birth_date, birth_lat, birth_lon, transit_lat, transit_lon, start_date, end_date, orb=DEFAULT_ORB):
    """
    API function to calculate WB2 (Western Burst Two) transits.
    
    Parameters:
    - birth_date: datetime object for birth date/time
    - birth_lat: float, birth latitude in degrees
    - birth_lon: float, birth longitude in degrees  
    - transit_lat: float, transit location latitude in degrees
    - transit_lon: float, transit location longitude in degrees
    - start_date: datetime object for start of period
    - end_date: datetime object for end of period
    - orb: float, orb in degrees (default: 1.0)
    
    Returns:
    - List of transit events with timing and position data
    """
    return process_transits_with_params(birth_date, birth_lat, birth_lon, transit_lat, transit_lon, start_date, end_date, orb)

def get_natal_lagna_lord_planet(natal_asc):
    """Get the ruling planet ID for the natal Ascendant sign."""
    asc_sign = int(natal_asc / 30)
    rulers = {
        0: swe.MARS,    # Aries
        1: swe.VENUS,   # Taurus
        2: swe.MERCURY, # Gemini
        3: swe.MOON,    # Cancer
        4: swe.SUN,     # Leo
        5: swe.MERCURY, # Virgo
        6: swe.VENUS,   # Libra
        7: swe.MARS,    # Scorpio
        8: swe.JUPITER, # Sagittarius
        9: swe.SATURN,  # Capricorn
        10: swe.SATURN, # Aquarius
        11: swe.JUPITER # Pisces
    }
    return rulers[asc_sign]

def process_transits_with_params(birth_date, birth_lat, birth_lon, transit_lat, transit_lon, start_date, end_date, orb=DEFAULT_ORB):
    """Process WB2 transits with API parameters."""
    print("\nProcessing WB2 transits...")
    print(f"Birth: {birth_date.strftime('%Y-%m-%d %H:%M')} at {birth_lat}°N, {birth_lon}°W")
    print(f"Transit Location: {transit_lat}°N, {transit_lon}°W")
    print(f"Period: {start_date} to {end_date}")

    # Calculate birth positions
    birth_ut = convert_local_to_ut(birth_date)
    birth_jd = swe.julday(birth_ut.year, birth_ut.month, birth_ut.day,
                         birth_ut.hour + birth_ut.minute/60.0)
    birth_positions = calculate_positions_with_location(birth_jd, birth_lat, birth_lon)
    
    # Get natal Lagna Lord planet (based on natal ASC sign, not transit ASC)
    natal_lagna_lord_planet = get_natal_lagna_lord_planet(birth_positions['ASC'])
    planet_names = {swe.SUN: 'Sun', swe.MOON: 'Moon', swe.MARS: 'Mars', swe.MERCURY: 'Mercury',
                   swe.JUPITER: 'Jupiter', swe.VENUS: 'Venus', swe.SATURN: 'Saturn'}
    print(f"Natal Lagna Lord: {planet_names.get(natal_lagna_lord_planet, 'Unknown')}")

    all_transits = []
    current_time = start_date
    active_transits = {}

    while current_time <= end_date:
        ut = convert_local_to_ut(current_time)
        jd = swe.julday(ut.year, ut.month, ut.day,
                       ut.hour + ut.minute/60.0)

        positions = calculate_positions_with_location(jd, transit_lat, transit_lon)
        
        # Get transit position of the NATAL Lagna Lord planet (A1 fix)
        transit_natal_lagna_lord = float(swe.calc_ut(jd, natal_lagna_lord_planet)[0][0])

        # Define transit configurations (duplicates removed)
        transit_configs = [
            ('POF-NAT', birth_positions['POF'], positions['POF'], 'Natal Part of Fortune Conjunct Transit Part of Fortune', None),
            ('POF-SUN', positions['SUN'], positions['POF'], 'Part of Fortune Conjunct Sun', None),
            ('POF-MOON', positions['MOON'], positions['POF'], 'Part of Fortune Conjunct Moon', None),
            ('NAT-POF', birth_positions['ASC'], positions['POF'], 'Natal Ascendant Conjunct Transit Part of Fortune', 'K1'),
            ('POF-ASC', positions['ASC'], positions['POF'], 'Part of Fortune Conjunct Transit Ascendant', None),
            ('POF-JUP', positions['JUP'], positions['POF'], 'Part of Fortune Conjunct Jupiter', None),
            ('NAT-MOON-POF', birth_positions['MOON'], positions['POF'], 'Part of Fortune Conjunct Natal Moon', None),
            ('POF-INC', positions['POI'], positions['POF'], 'Part of Fortune Conjunct Part of Increase', None),
            ('POF-RAHU', positions['RAHU'], positions['POF'], 'Part of Fortune Conjunct North Node (Rahu)', 'C1'),
            ('POF-LAGNA', transit_natal_lagna_lord, positions['POF'], 'Part of Fortune Conjunct Lagna Lord', 'A1'),
            ('REG-POF', positions['REGULUS'], positions['POF'], 'Regulus Conjunct Part of Fortune', None),
        ]

        for transit_code, pos1, pos2, description, named_lt in transit_configs:
            is_active, orb_diff = is_conjunct(pos1, pos2, orb)

            # Transit entry
            if is_active and transit_code not in active_transits:
                transit = {
                    'start': current_time,
                    'end': None,
                    'type': description,
                    'transit_code': transit_code,
                    'orb': orb_diff,
                }
                active_transits[transit_code] = transit

            # Transit exit
            elif not is_active and transit_code in active_transits:
                transit = active_transits.pop(transit_code)
                transit['end'] = current_time
                all_transits.append(transit)

        current_time += timedelta(minutes=1)

    print(f"Found {len(all_transits)} WB2 transits")
    return all_transits

def process_transits(start_date=None, end_date=None):
    """Legacy function for backward compatibility."""
    # Default hardcoded values for testing
    birth_date = datetime(1973, 3, 9, 16, 56)
    birth_lat = 29.2108
    birth_lon = -81.0228
    transit_lat = 40.7128
    transit_lon = -74.0060
    
    return process_transits_with_params(birth_date, birth_lat, birth_lon, transit_lat, transit_lon, start_date, end_date)

def format_position(lon):
    """Format position with sign and degrees."""
    signs = ['Aries', 'Taurus', 'Gemini', 'Cancer', 'Leo', 'Virgo',
             'Libra', 'Scorpio', 'Sagittarius', 'Capricorn', 'Aquarius', 'Pisces']
    sign_num = int(lon / 30)
    deg = int(lon % 30)
    min = int((lon % 1) * 60)
    return f"{signs[sign_num]} {deg}°{min:02d}'"

def export_transits(transits):
    """Export transits in Google Calendar compatible format."""
    export_folder = os.environ.get('EXPORT_FOLDER')
    if not export_folder:
        # Create default export folder with timestamp if env var not set
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        export_folder = os.path.join("exports", timestamp)
        print(f"Using default export folder: {export_folder}")

    if not os.path.exists(export_folder):
        os.makedirs(export_folder, exist_ok=True)

    file_path = os.path.join(export_folder, f"{SCRIPT_PREFIX}_transits.csv")

    headers = [
        "Subject", "Start Date", "Start Time", "End Date", "End Time",
        "All Day Event", "Description", "Location", "Private"
    ]

    try:
        with open(file_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(headers)

            if not transits:
                print(f"No transits found for {SCRIPT_PREFIX}")
                return

            for idx, transit in enumerate(sorted(transits, key=lambda x: x['start']), 1):
                duration = int((transit['end'] - transit['start']).total_seconds() / 60)
                transit_id = f"{SCRIPT_PREFIX}-{transit['transit_code']}-{idx:03d}"
                start_dt = transit['start']
                end_dt = transit['end']

                description = (
                    f"{SCRIPT_PREFIX}: {transit['type']}\n"
                    f"Orb: {transit.get('orb', 0):.2f}°\n"
                    f"Duration: {duration}m\n"
                    f"Transit ID: {transit_id}"
                )

                writer.writerow([
                    f"{SCRIPT_PREFIX} {transit['type']}",           # Subject
                    start_dt.strftime('%Y-%m-%d'),                 # Start Date
                    start_dt.strftime('%H:%M:%S'),                 # Start Time
                    end_dt.strftime('%Y-%m-%d'),                   # End Date
                    end_dt.strftime('%H:%M:%S'),                   # End Time
                    "FALSE",                                        # All Day Event
                    description,                                    # Description
                    "",                                            # Location
                    "FALSE"                                        # Private
                ])

        print(f"\nExported {len(transits)} {SCRIPT_PREFIX} transits to: {file_path}")
    except Exception as e:
        print(f"Error exporting transits: {str(e)}")


if __name__ == "__main__":
    try:
        swe.set_ephe_path()

        # Example usage
        start_date = datetime(2025, 1, 10, 0, 0)
        end_date = datetime(2025, 1, 20, 23, 59)

        transits = process_transits(start_date, end_date)
        print(f"\nTransits found: {len(transits)}")

        for transit in transits:
            print(f"\nTransit: {transit['type']}")
            print(f"Start: {transit['start']}")
            print(f"End: {transit['end']}")
            print(f"Orb: {transit['orb']:.4f}°")
        if transits:
            export_transits(transits)

    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        swe.close()