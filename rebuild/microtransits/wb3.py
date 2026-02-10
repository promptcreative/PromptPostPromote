
"""Western Burst Three (WB3) Transit Calculator."""
import swisseph as swe
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import csv

# Configuration Constants
SCRIPT_PREFIX = "WB3"
CALENDAR_COLOR = "#4CAF50"  # Green
CATEGORY = "Western Transits"
EXPORTS_FOLDER = "exports"
DEFAULT_ORB = 1.0

# Global variables for script compatibility
ORB = DEFAULT_ORB
BIRTH_DATE = None  # Will be set by API calls
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

def process_transits(start_date=None, end_date=None):
    """Process WB3 transits between two dates."""
    if start_date is None or end_date is None:
        raise ValueError("Both start_date and end_date must be provided")

    print("\nCalculating Western Burst Three (WB3) transits...")
    # Implementation will follow
    return []

################################################################
#                    API WRAPPER FUNCTIONS                      #
################################################################

def calculate_wb3_transits(birth_date, birth_time, birth_latitude, birth_longitude, start_date, days_span):
    """
    API wrapper function for WB3 transit calculations
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
                'date': transit.get('start', start_dt).strftime('%Y-%m-%d') if hasattr(transit.get('start', start_dt), 'strftime') else start_dt.strftime('%Y-%m-%d'),
                'time': f"{transit.get('start', start_dt).strftime('%H:%M') if hasattr(transit.get('start', start_dt), 'strftime') else '00:00'}-{transit.get('end', start_dt).strftime('%H:%M') if hasattr(transit.get('end', start_dt), 'strftime') else '01:00'}",
                'type': transit.get('type', 'WB3 Transit'),
                'description': f"WB3: {transit.get('type', 'Western Burst Three')}",
                'script': 'wb3.py'
            })
            
        return api_transits
        
    except Exception as e:
        print(f"Error in calculate_wb3_transits: {str(e)}")
        return []

if __name__ == "__main__":
    try:
        start_date = datetime(2025, 1, 10, 0, 0)
        end_date = datetime(2025, 1, 20, 23, 59)
        transits = process_transits(start_date, end_date)
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        swe.close()
import swisseph as swe
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import os
import csv

# Configuration Constants  
SCRIPT_PREFIX = "WB3"
CALENDAR_COLOR = "#E67C73"  # Coral Red
CATEGORY = "Western Burst Three"
EXPORTS_FOLDER = "exports"
DEFAULT_ORB = 1.0

def get_positions(jd):
    """Calculate required planetary positions."""
    positions = {}

    # Calculate POF using proper day/night formula
    cusps, ascmc = swe.houses(jd, TRANSIT_LOCATION[0], TRANSIT_LOCATION[1], b'P')
    asc = float(ascmc[0])
    sun_pos = float(swe.calc_ut(jd, swe.SUN)[0][0])
    moon_pos = float(swe.calc_ut(jd, swe.MOON)[0][0])
    positions['POF'] = calculate_pof(asc, sun_pos, moon_pos)

    # Calculate POI (Part of Increase)
    positions['POI'] = (asc + float(swe.calc_ut(jd, swe.JUPITER)[0][0]) - sun_pos) % 360

    # Get Moon position
    positions['MOON'] = moon_pos

    # Get Regulus position (fixed star)
    positions['REGULUS'] = 149.50  # Fixed position for Regulus

    # Get North Node position
    positions['NORTH_NODE'] = float(swe.calc_ut(jd, swe.MEAN_NODE)[0][0])

    return positions

def is_conjunct(pos1, pos2, orb=ORB):
    """Check if two positions are conjunct within orb."""
    diff = abs(pos1 - pos2)
    min_diff = min(diff, 360 - diff)
    return min_diff <= orb, min_diff

def process_transits(start_date=None, end_date=None):
    """Process WB3 transits between two dates."""
    if start_date is None or end_date is None:
        raise ValueError("Both start_date and end_date must be provided")

    print("\nCalculating Western Burst Three (WB3) transits...")

    # Calculate birth positions
    birth_jd = swe.julday(BIRTH_DATE.year, BIRTH_DATE.month, BIRTH_DATE.day,
                         BIRTH_DATE.hour + BIRTH_DATE.minute/60.0)
    birth_positions = get_positions(birth_jd)

    transits = []
    current_time = start_date
    active_transits = {}

    while current_time <= end_date:
        jd = swe.julday(current_time.year, current_time.month, current_time.day,
                       current_time.hour + current_time.minute/60.0)

        positions = get_positions(jd)

        # Define transit configurations
        transit_configs = [
            (birth_positions['POI'], positions['POF'], 'POI-POF', 'Natal POI to Transit POF'),
            (birth_positions['POI'], positions['MOON'], 'POI-MOON', 'Natal POI to Transit Moon'),
            (positions['REGULUS'], birth_positions['POF'], 'REG-ASC', 'Regulus to Natal Ascendant'),
            (positions['NORTH_NODE'], positions['MOON'], 'NN-MOON', 'North Node to Moon')
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
                transits.append(transit)

        current_time += timedelta(minutes=1)

    return transits

def export_transits(transits):
    """Export transits to CSV files with consistent format."""
    export_folder = os.environ.get('EXPORT_FOLDER')
    if not export_folder:
        # Create default export folder with timestamp if env var not set
        timestamp = datetime.now().strftime('%Y%m%d_%H%M')
        export_folder = os.path.join("exports", timestamp)
        print(f"Using default export folder: {export_folder}")

    os.makedirs(export_folder, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    windows_filename = os.path.join(export_folder, f"{SCRIPT_PREFIX}_Windows_Test_User_{timestamp}.csv")
    exact_filename = os.path.join(export_folder, f"{SCRIPT_PREFIX}_Exact_Test_User_{timestamp}.csv")

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

            for idx, transit in enumerate(sorted(transits, key=lambda x: x['start']), 1):
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
