"""Yogi Point Transit Calculator."""
import swisseph as swe
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import csv

# Configuration Constants
SCRIPT_PREFIX = "YP"
CALENDAR_COLOR = "#9C27B0"  # Purple for Yogi Point
CATEGORY = "Yogi Point Transits"
EXPORTS_FOLDER = "exports"
DEFAULT_ORB = 1.0

# Global variables for script compatibility
ORB = DEFAULT_ORB
TRANSIT_LOCATION = (40.7128, -74.0060)  # Default NYC coordinates

def calculate_pof(asc, sun, moon):
    """
    Calculate Part of Fortune using correct day/night formula.
    For day charts (Sun above Asc): POF = Asc + Moon - Sun
    For night charts (Sun below Asc): POF = Asc - Moon + Sun
    
    All angles are in degrees and normalized to 0-360 range.
    """
    asc = asc % 360
    sun = sun % 360
    moon = moon % 360
    
    sun_ahead = (sun - asc + 360) % 360 <= 180
    
    if sun_ahead:  # Day chart
        pof = (asc + moon - sun) % 360
    else:  # Night chart
        pof = (asc - moon + sun) % 360
    
    return pof

def calculate_yogi_point(jd):
    """Calculate Yogi Point from Sun and Moon positions."""
    flags = swe.FLG_SIDEREAL
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    sun_pos = float(swe.calc_ut(jd, swe.SUN, flags)[0][0])
    moon_pos = float(swe.calc_ut(jd, swe.MOON, flags)[0][0])
    return (sun_pos + moon_pos + 93.33) % 360

def get_planetary_positions(jd):
    """Calculate required planetary positions."""
    flags = swe.FLG_SIDEREAL
    swe.set_sid_mode(swe.SIDM_LAHIRI, 0, 0)
    positions = {}

    # Calculate planetary positions
    for planet in [swe.SUN, swe.MOON, swe.JUPITER]:
        pos = float(swe.calc_ut(jd, planet, flags)[0][0])
        positions[planet] = pos

    # Calculate ASC
    positions['ASC'] = float(swe.houses(jd, TRANSIT_LOCATION[0], TRANSIT_LOCATION[1], b'P')[0][0])

    # Calculate POF using proper day/night formula
    asc = positions['ASC']
    sun = positions[swe.SUN]
    moon = positions[swe.MOON]
    positions['POF'] = calculate_pof(asc, sun, moon)

    return positions

def is_conjunct(pos1, pos2, orb=ORB):
    """Check if two positions are conjunct within orb."""
    diff = abs(pos1 - pos2)
    min_diff = min(diff, 360 - diff)
    return min_diff <= orb, min_diff

def process_transits(start_date=None, end_date=None):
    """Process Yogi Point transits between two dates."""
    if start_date is None or end_date is None:
        raise ValueError("Both start_date and end_date must be provided")

    # Ensure timezone-aware datetime objects
    if start_date.tzinfo is None:
        start_date = start_date.replace(tzinfo=ZoneInfo("UTC"))
    if end_date.tzinfo is None:
        end_date = end_date.replace(tzinfo=ZoneInfo("UTC"))

    print("\nCalculating Yogi Point transits...")
    print(f"Processing period: {start_date} to {end_date}")

    all_transits = []
    current_time = start_date
    active_transits = {}

    while current_time <= end_date:
        jd = swe.julday(current_time.year, current_time.month, current_time.day,
                       current_time.hour + current_time.minute/60.0)

        yogi_point = calculate_yogi_point(jd)
        positions = get_planetary_positions(jd)

        # Define transit configurations
        transit_configs = [
            (positions[swe.MOON], yogi_point, 'MOON-YOGI', 'Moon to Yogi Point'),
            (positions[swe.SUN], yogi_point, 'SUN-YOGI', 'Sun to Yogi Point'),
            (positions[swe.JUPITER], yogi_point, 'JUP-YOGI', 'Jupiter to Yogi Point'),
            (positions['ASC'], yogi_point, 'ASC-YOGI', 'ASC to Yogi Point'),
            (yogi_point, positions[swe.MOON], 'YOGI-MOON', 'Yogi Point to Moon'),
            (yogi_point, positions[swe.SUN], 'YOGI-SUN', 'Yogi Point to Sun'),
            (yogi_point, positions[swe.JUPITER], 'YOGI-JUP', 'Yogi Point to Jupiter'),
            (yogi_point, positions['POF'], 'YOGI-POF', 'Yogi Point to POF'),
            (yogi_point, calculate_yogi_point(jd), 'YOGI-TRANSIT', 'Yogi Point to Transit Yogi Point')
        ]

        for pos1, pos2, transit_code, description in transit_configs:
            is_active, orb = is_conjunct(pos1, pos2)

            if is_active and transit_code not in active_transits:
                transit = {
                    'start': current_time,
                    'end': None,
                    'type': description,
                    'transit_code': transit_code,
                    'orb': orb
                }
                active_transits[transit_code] = transit

            elif not is_active and transit_code in active_transits:
                transit = active_transits.pop(transit_code)
                transit['end'] = current_time
                all_transits.append(transit)

        current_time += timedelta(minutes=1)

    return all_transits

def export_transits(transits):
    """Export transits in standardized format."""
    export_folder = os.environ.get('EXPORT_FOLDER')
    if not export_folder:
        # Create default export folder with timestamp if env var not set
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        export_folder = os.path.join("exports", timestamp)
        print(f"Using default export folder: {export_folder}")

    os.makedirs(export_folder, exist_ok=True)
    file_path = os.path.join(export_folder, f"{SCRIPT_PREFIX}_transits.csv")

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

            if not transits:
                print(f"No transits found for {SCRIPT_PREFIX}")
                return

            for idx, transit in enumerate(transits, 1):
                duration = int((transit['end'] - transit['start']).total_seconds() / 60)
                writer.writerow([
                    f"{SCRIPT_PREFIX} {transit['type']}",
                    transit['start'].strftime('%Y-%m-%d'),
                    transit['start'].strftime('%H:%M:%S'),
                    transit['end'].strftime('%Y-%m-%d'),
                    transit['end'].strftime('%H:%M:%S'),
                    f"{SCRIPT_PREFIX}: {transit['type']} | Orb: {transit['orb']:.2f}° | Duration: {duration}m",
                    f"{duration}m",
                    f"{SCRIPT_PREFIX}-{transit['transit_code']}-{idx:03d}",
                    CATEGORY,
                    CALENDAR_COLOR
                ])

        print(f"\nExported {len(transits)} {SCRIPT_PREFIX} transits to: {file_path}")
    except Exception as e:
        print(f"Error exporting transits: {str(e)}")

if __name__ == "__main__":
    try:
        swe.set_ephe_path()
        start_date = datetime(2025, 1, 10, 0, 0)
        end_date = datetime(2025, 1, 20, 23, 59)

        transits = process_transits(start_date, end_date)
        if transits:
            export_transits(transits)

    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        swe.close()