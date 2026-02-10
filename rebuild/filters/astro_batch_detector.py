#!/usr/bin/env python3
"""
STEP 2: Astro Batch Detector
Takes filtered bird periods from Step 1 and runs all micro-transit scripts
to find "supercharged moments" where transits overlap with favorable bird periods
"""

import sys
import os
import json
import importlib.util
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
import pytz
from zoneinfo import ZoneInfo

class AstroBatchDetector:
    """
    Detects overlaps between favorable bird periods and micro-transit events
    """
    
    def __init__(self):
        self.micro_transit_scripts = [
            'vb1.py',  # D9 transit events
            'vb2.py',  # Yogi Point transits
            'wb1.py',  # Western transits with Yogi aspects
            'wb2.py',  # Additional western transits
            'wb3.py',  # More western transits
            'yp.py'    # Yogi Point specific transits
        ]
    
    def import_script(self, script_name: str):
        """
        Dynamically import a micro-transit script
        """
        try:
            script_path = os.path.join(os.path.dirname(__file__), 'micro_transits', script_name)
            
            if not os.path.exists(script_path):
                raise FileNotFoundError(f"{script_name} not found at {script_path}")
            
            # Import the module
            module_name = script_name.replace('.py', '')
            spec = importlib.util.spec_from_file_location(module_name, script_path)
            module = importlib.util.module_from_spec(spec)
            
            # Set up module environment if needed
            sys.modules[module_name] = module
            spec.loader.exec_module(module)
            
            return module
            
        except Exception as e:
            print(f"Warning: Could not import {script_name}: {e}")
            return None
    
    def setup_script_environment(self, script_module, start_date: datetime, end_date: datetime, birth_date=None, birth_latitude=None, birth_longitude=None, latitude=None, longitude=None):
        """
        Set up environment variables and parameters needed by transit scripts
        """
        try:
            # Use actual birth data instead of hardcoded defaults
            birth_params = {
                'BIRTH_DATE': birth_date if birth_date else datetime(1973, 3, 9, 16, 56),
                'BIRTH_LAT': birth_latitude if birth_latitude is not None else 29.2108,
                'BIRTH_LON': birth_longitude if birth_longitude is not None else -81.0228,
                'TRANSIT_LOCATION': [latitude if latitude is not None else 29.2108, longitude if longitude is not None else -81.0228]
            }
            
            # Set up environment variables - create exports in root
            exports_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'exports')
            os.makedirs(exports_dir, exist_ok=True)
            os.environ['EXPORT_FOLDER'] = exports_dir
            
            # Set module attributes if they exist
            for attr, value in birth_params.items():
                if hasattr(script_module, attr):
                    setattr(script_module, attr, value)
                elif hasattr(script_module, attr.lower()):
                    setattr(script_module, attr.lower(), value)
                # Force set the attribute even if it doesn't exist
                setattr(script_module, attr, value)
            
            # Set ORB variables if needed
            if hasattr(script_module, 'DEFAULT_ORB'):
                script_module.ORB = script_module.DEFAULT_ORB
            else:
                script_module.ORB = 1.0
            
            return True
            
        except Exception as e:
            print(f"Warning: Could not set up environment for script: {e}")
            return False
    
    def run_micro_transit_script(self, script_name: str, start_date: datetime, end_date: datetime, 
                                birth_date=None, birth_time=None, birth_latitude=None, birth_longitude=None,
                                current_latitude=None, current_longitude=None) -> List[Dict[str, Any]]:
        """
        Run a single micro-transit script and return its results
        """
        try:
            script_module = self.import_script(script_name)
            if not script_module:
                return []
            
            # Parse birth date and time if provided
            if birth_date and birth_time:
                if isinstance(birth_date, str):
                    birth_dt = datetime.strptime(birth_date, '%Y-%m-%d')
                else:
                    birth_dt = birth_date
                
                if isinstance(birth_time, str):
                    time_parts = birth_time.split(':')
                    birth_dt = birth_dt.replace(
                        hour=int(time_parts[0]),
                        minute=int(time_parts[1]) if len(time_parts) > 1 else 0
                    )
            else:
                birth_dt = datetime(1973, 3, 9, 16, 56)  # Default
            
            # Set up the script environment with actual birth data
            self.setup_script_environment(script_module, start_date, end_date, 
                                        birth_date=birth_dt,
                                        birth_latitude=birth_latitude,
                                        birth_longitude=birth_longitude,
                                        latitude=current_latitude,
                                        longitude=current_longitude)
            
            # Call the process_transits function
            if hasattr(script_module, 'process_transits'):
                print(f"Running {script_name}...")
                
                # Convert dates to timezone-aware if needed
                ny_tz = ZoneInfo("America/New_York")
                if start_date.tzinfo is None:
                    start_date = start_date.replace(tzinfo=ny_tz)
                if end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=ny_tz)
                
                transits = script_module.process_transits(start_date, end_date)
                
                # Normalize the output format
                normalized_transits = self._normalize_transit_output(transits, script_name)
                print(f"Found {len(normalized_transits)} transits from {script_name}")
                
                return normalized_transits
            else:
                print(f"Warning: {script_name} does not have process_transits function")
                return []
                
        except Exception as e:
            print(f"Error running {script_name}: {e}")
            return []
    
    def _normalize_transit_output(self, transits: List[Any], script_name: str) -> List[Dict[str, Any]]:
        """
        Normalize different transit output formats to a standard structure
        """
        normalized = []
        
        for transit in transits:
            try:
                # Convert different formats to standard structure
                if isinstance(transit, dict):
                    # Handle Julian Day conversion if present
                    if 'jd' in transit:
                        import swisseph as swe
                        jd = transit['jd']
                        y, m, d, h = swe.revjul(jd, swe.GREG_CAL)
                        transit_dt = datetime(y, m, d, int(h), int((h % 1) * 60))
                        
                        normalized_transit = {
                            'datetime': transit_dt.isoformat(),
                            'timestamp': transit_dt,
                            'type': transit.get('type', 'Unknown'),
                            'script': script_name,
                            'planet_pos': transit.get('planet_pos', {}),
                            'target_pos': transit.get('target_pos', 0),
                            'raw_data': transit
                        }
                    elif 'start' in transit:
                        # Handle wb2.py format with 'start' and 'end' datetime
                        start_time_val = transit.get('start', '')
                        end_time_val = transit.get('end', '')
                        
                        # Parse start time
                        if isinstance(start_time_val, str):
                            try:
                                start_dt = datetime.fromisoformat(start_time_val.replace('Z', '+00:00'))
                            except:
                                start_dt = datetime.strptime(start_time_val[:19], '%Y-%m-%d %H:%M:%S')
                        else:
                            start_dt = start_time_val  # Already a datetime object
                        
                        # Parse end time
                        end_dt = None
                        if end_time_val:
                            if isinstance(end_time_val, str):
                                try:
                                    end_dt = datetime.fromisoformat(end_time_val.replace('Z', '+00:00'))
                                except:
                                    end_dt = datetime.strptime(end_time_val[:19], '%Y-%m-%d %H:%M:%S')
                            else:
                                end_dt = end_time_val  # Already a datetime object
                        
                        normalized_transit = {
                            'datetime': start_dt.isoformat(),
                            'timestamp': start_dt,
                            'start': start_dt,  # Preserve actual start time
                            'end': end_dt,      # Preserve actual end time
                            'type': transit.get('type', 'Unknown'),
                            'script': script_name,
                            'transit_code': transit.get('transit_code', ''),
                            'orb': transit.get('orb', 0),
                            'raw_data': transit
                        }
                    elif 'start_time' in transit:
                        # Handle time-based format
                        start_time_str = transit.get('start_time', '')
                        try:
                            transit_dt = datetime.fromisoformat(start_time_str)
                        except:
                            transit_dt = None
                        
                        normalized_transit = {
                            'datetime': start_time_str,
                            'timestamp': transit_dt,
                            'type': transit.get('transit_type', transit.get('type', 'Unknown')),
                            'script': script_name,
                            'raw_data': transit
                        }
                    else:
                        # Generic fallback
                        normalized_transit = {
                            'datetime': str(transit),
                            'timestamp': None,
                            'type': 'Unknown',
                            'script': script_name,
                            'raw_data': transit
                        }
                    
                    normalized.append(normalized_transit)
                    
            except Exception as e:
                print(f"Warning: Could not normalize transit {transit} from {script_name}: {e}")
                continue
        
        return normalized
    
    def detect_overlaps(self, bird_periods: List[Dict[str, Any]], transit_events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Overlap detection between bird periods and micro-transit events
        Uses range overlap detection: transit window overlaps bird window
        Returns automation moments chronologically
        """
        from zoneinfo import ZoneInfo
        ny_tz = ZoneInfo("America/New_York")
        
        automation_moments = []
        
        # Debug: Log sample data
        if bird_periods and transit_events:
            print(f"🔍 OVERLAP DEBUG: Checking {len(bird_periods)} bird periods against {len(transit_events)} transits")
        
        for period in bird_periods:
            try:
                # Parse period times - try multiple formats
                start_time_str = period.get('start_time', '00:00')
                end_time_str = period.get('end_time', '23:59')
                
                period_start = None
                period_end = None
                
                # Try multiple time formats (same as ICS feed)
                for fmt in ['%I:%M %p', '%I:%M:%S %p', '%H:%M:%S', '%H:%M']:
                    if period_start is None:
                        try:
                            period_start = datetime.strptime(start_time_str, fmt).time()
                        except ValueError:
                            continue
                
                for fmt in ['%I:%M %p', '%I:%M:%S %p', '%H:%M:%S', '%H:%M']:
                    if period_end is None:
                        try:
                            period_end = datetime.strptime(end_time_str, fmt).time()
                        except ValueError:
                            continue
                
                if period_start is None or period_end is None:
                    print(f"⚠️ Could not parse bird period times: {start_time_str} - {end_time_str}")
                    continue
                
                # Get period date
                period_date_str = period.get('date', datetime.now().strftime('%Y-%m-%d'))
                period_date = datetime.strptime(period_date_str, '%Y-%m-%d').date()
                
                # Create timezone-aware datetime for bird period
                period_start_dt = datetime.combine(period_date, period_start).replace(tzinfo=ny_tz)
                period_end_dt = datetime.combine(period_date, period_end).replace(tzinfo=ny_tz)
                
                # Handle overnight periods
                if period_end < period_start:
                    period_end_dt += timedelta(days=1)
                
                # Find transits that OVERLAP with this bird period (range overlap detection)
                overlapping_transits = []
                
                for transit in transit_events:
                    # Get transit start time - try multiple fields
                    transit_start = transit.get('start') or transit.get('timestamp')
                    if transit_start is None:
                        continue
                    
                    # Get transit end time
                    transit_end = transit.get('end')
                    if transit_end is None:
                        duration = transit.get('duration_minutes', 10)
                        transit_end = transit_start + timedelta(minutes=duration)
                    
                    # Normalize timezone for start
                    if transit_start.tzinfo is None:
                        transit_start = transit_start.replace(tzinfo=ny_tz)
                    else:
                        transit_start = transit_start.astimezone(ny_tz)
                    
                    # Normalize timezone for end
                    if transit_end.tzinfo is None:
                        transit_end = transit_end.replace(tzinfo=ny_tz)
                    else:
                        transit_end = transit_end.astimezone(ny_tz)
                    
                    # Check if transit is on the SAME DATE as this bird period
                    transit_date = transit_start.date()
                    if transit_date != period_date:
                        continue  # Skip transit - wrong date
                    
                    # Range overlap check: transit_start < period_end AND transit_end > period_start
                    overlaps = transit_start < period_end_dt and transit_end > period_start_dt
                    
                    if overlaps:
                        # Store normalized times for later use
                        transit['_normalized_start'] = transit_start
                        transit['_normalized_end'] = transit_end
                        overlapping_transits.append(transit)
                
                # Create automation moment for any overlaps
                if overlapping_transits:
                    is_enhanced = period.get('combination') == 'Ruling/Ruling'
                    
                    # Calculate overlap window for combined transits
                    overlap_starts = []
                    overlap_ends = []
                    
                    for transit in overlapping_transits:
                        t_start = transit.get('_normalized_start')
                        t_end = transit.get('_normalized_end')
                        
                        # Actual overlap = max(starts), min(ends)
                        overlap_start = max(t_start, period_start_dt)
                        overlap_end = min(t_end, period_end_dt)
                        
                        if overlap_start < overlap_end:
                            overlap_starts.append(overlap_start)
                            overlap_ends.append(overlap_end)
                    
                    # Combined overlap window
                    combined_start = min(overlap_starts) if overlap_starts else period_start_dt
                    combined_end = max(overlap_ends) if overlap_ends else period_end_dt
                    
                    automation_moment = {
                        'date': period_date_str,
                        'time': f"{period['start_time']}-{period['end_time']}",
                        'overlap_window': f"{combined_start.strftime('%I:%M %p')}-{combined_end.strftime('%I:%M %p')}",
                        'bird_combination': period.get('combination', ''),
                        'bird_tier': period.get('tier', ''),
                        'enhanced': is_enhanced,
                        'micro_transits': [
                            {
                                'time': t.get('_normalized_start', t.get('timestamp')).strftime('%H:%M:%S') if t.get('_normalized_start') or t.get('timestamp') else 'unknown',
                                'type': t.get('type', 'Unknown'),
                                'script': t.get('script', 'unknown')
                            } for t in overlapping_transits
                        ],
                        'automation_ready': True
                    }
                    
                    automation_moments.append(automation_moment)
                    
            except Exception as e:
                print(f"Error detecting overlaps for period {period}: {e}")
                continue
        
        print(f"🔍 OVERLAP RESULT: Found {len(automation_moments)} automation moments from {len(bird_periods)} periods")
        
        # Sort chronologically by date and time
        automation_moments.sort(key=lambda x: (x['date'], x['time']))
        
        return automation_moments
    
    def get_yogi_point_transits(self, start_date: datetime, end_date: datetime,
                                 birth_date=None, birth_time=None, birth_latitude=None, birth_longitude=None) -> List[Dict[str, Any]]:
        """
        Get Yogi Point transits by combining results from vb2.py, yp.py, and wb1.py
        Returns standardized transit events without bird period data
        """
        try:
            print(f"Processing Yogi Point transits for {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
            # Scripts that contain Yogi Point calculations
            yogi_scripts = ['vb2.py', 'yp.py', 'wb1.py']
            all_yogi_transits = []
            
            for script_name in yogi_scripts:
                print(f"\n--- Running {script_name} for Yogi Point transits ---")
                script_transits = self.run_micro_transit_script(script_name, start_date, end_date,
                    birth_date=birth_date, birth_time=birth_time,
                    birth_latitude=birth_latitude, birth_longitude=birth_longitude)
                
                # Filter for Yogi Point related transits
                # YOGI-POF appears in BOTH YP and POF calendars (no exclusion)
                yogi_transits = []
                for transit in script_transits:
                    # Get uppercase versions for comparison
                    transit_code = transit.get('transit_code', '').upper()
                    transit_type = transit.get('type', '').upper()
                    transit_name = transit.get('name', '').upper()
                    transit_desc = transit.get('description', '').upper()
                    
                    # Check if it's a Yogi transit
                    is_yogi = False
                    
                    # VB2.py formats: ASC-Yogi, Sun-Yogi, Moon-Yogi, Jupiter-Yogi
                    if script_name == 'vb2.py':
                        if any(x in transit_code for x in ['ASC-YOG', 'SUN-YOG', 'MOON-YOG', 'JUPITER-YOG']):
                            is_yogi = True
                        if any(x in transit_type for x in ['ASC-YOGI', 'SUN-YOGI', 'MOON-YOGI', 'JUPITER-YOGI']):
                            is_yogi = True
                    
                    # YP.py formats: All YOGI transits including YOGI-POF
                    if script_name == 'yp.py':
                        if 'YOGI' in transit_type or 'YOGI' in transit_code:
                            is_yogi = True
                        # Also check for arrow notation
                        if '→ YOGI' in transit_type or 'YOGI →' in transit_type or 'YOGI POINT' in transit_type:
                            is_yogi = True
                    
                    # WB1.py formats: ALL Yogi- prefixed transits including Yogi-POF
                    # Yogi-ASC, Yogi-Rising, Yogi-Transit, Yogi-Moon, Yogi-Sun, Yogi-Jupiter, Yogi-POF
                    if script_name == 'wb1.py':
                        # WB1 uses type codes for non-POF Yogi transits
                        if transit_type in ['ASC', 'MOON', 'SUN', 'JUPITER', 'RISING', 'TRANSIT_YOGI']:
                            is_yogi = True
                        # Check name field for ANY Yogi- prefix (captures Yogi-POF via name, not type)
                        if transit_name.startswith('YOGI-'):
                            is_yogi = True
                    
                    # General check for any script - include all YOGI transits
                    if 'YOGI' in transit_type or 'YOGI' in transit_code:
                        is_yogi = True
                    
                    if is_yogi:
                        yogi_transits.append(transit)
                
                print(f"Found {len(yogi_transits)} Yogi Point transits from {script_name}")
                all_yogi_transits.extend(yogi_transits)
            
            # Sort chronologically by timestamp
            all_yogi_transits.sort(key=lambda x: x['timestamp'] if x['timestamp'] else datetime.min)
            
            print(f"\nTotal Yogi Point transits found: {len(all_yogi_transits)}")
            return all_yogi_transits
            
        except Exception as e:
            print(f"Error getting Yogi Point transits: {e}")
            return []
    
    def get_part_of_fortune_transits(self, start_date: datetime, end_date: datetime,
                                      birth_date=None, birth_time=None, birth_latitude=None, birth_longitude=None) -> List[Dict[str, Any]]:
        """
        Get Part of Fortune transits by combining results from wb1.py, wb2.py, and wb3.py
        Returns standardized transit events without bird period data
        """
        try:
            print(f"Processing Part of Fortune transits for {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
            
            # Scripts that contain Part of Fortune calculations
            pof_scripts = ['wb1.py', 'wb2.py', 'wb3.py']
            all_pof_transits = []
            
            for script_name in pof_scripts:
                print(f"\n--- Running {script_name} for Part of Fortune transits ---")
                script_transits = self.run_micro_transit_script(script_name, start_date, end_date,
                    birth_date=birth_date, birth_time=birth_time,
                    birth_latitude=birth_latitude, birth_longitude=birth_longitude)
                
                # Filter for Part of Fortune related transits (POF, Regulus, POI, NN)
                # Use inclusion-based rules: POF codes always go to POF section
                pof_transits = []
                for transit in script_transits:
                    # Get uppercase versions for comparison
                    transit_code = transit.get('transit_code', '').upper()
                    transit_type = transit.get('type', '').upper()
                    transit_name = transit.get('name', '').upper()
                    
                    # Check if it's a POF transit
                    is_pof = False
                    
                    # WB1: Yogi-POF
                    if script_name == 'wb1.py':
                        if transit_type == 'POF' or 'YOGI-POF' in transit_name or 'YOGI-POF' in transit_code:
                            is_pof = True
                    
                    # WB2: All POF- and -POF codes
                    if script_name == 'wb2.py':
                        # Comprehensive list of WB2 POF codes
                        wb2_pof_codes = [
                            'POF-NAT', 'POF-SUN', 'POF-MOON', 'NAT-POF', 
                            'POF-ASC', 'POF-JUP', 'NAT-MOON-POF',  # Critical transit
                            'POF-INC', 'POF-RAHU', 'POF-LAGNA', 'REG-POF'
                        ]
                        if transit_code in wb2_pof_codes:
                            is_pof = True
                        # Also catch any POF- prefix or -POF suffix
                        if transit_code.startswith('POF-') or transit_code.endswith('-POF'):
                            is_pof = True
                    
                    # WB3: POI, Regulus, NN transits
                    if script_name == 'wb3.py':
                        wb3_pof_codes = ['POI-POF', 'REG-ASC', 'POI-MOON', 'NN-MOON']
                        if transit_code in wb3_pof_codes:
                            is_pof = True
                    
                    # General checks for any script
                    # POF codes from any source
                    all_pof_codes = [
                        'YOGI-POF', 'POF-NAT', 'POF-SUN', 'POF-MOON', 'NAT-POF',
                        'POF-ASC', 'POF-JUP', 'NAT-MOON-POF', 'POF-INC',
                        'POF-RAHU', 'POF-LAGNA', 'POI-POF', 'REG-ASC',
                        'POI-MOON', 'NN-MOON', 'REG-POF'
                    ]
                    if transit_code in all_pof_codes:
                        is_pof = True
                    
                    # Check type field for Part of Fortune
                    if 'POF' in transit_type or 'FORTUNE' in transit_type:
                        is_pof = True
                    
                    # YP script: YOGI-POF goes to POF section
                    if 'YOGI-POF' in transit_code or 'YOGI-POF' in transit_type:
                        is_pof = True
                    
                    if is_pof:
                        pof_transits.append(transit)
                
                print(f"Found {len(pof_transits)} Part of Fortune transits from {script_name}")
                all_pof_transits.extend(pof_transits)
            
            # Sort chronologically by timestamp
            all_pof_transits.sort(key=lambda x: x['timestamp'] if x['timestamp'] else datetime.min)
            
            print(f"\nTotal Part of Fortune transits found: {len(all_pof_transits)}")
            return all_pof_transits
            
        except Exception as e:
            print(f"Error getting Part of Fortune transits: {e}")
            return []

    def process_batch(self, bird_batch_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main method to process bird periods and detect transit overlaps
        
        Args:
            bird_batch_result: Output from bird_batch_filter.py (Step 1)
            
        Returns:
            Dictionary with supercharged moments and statistics
        """
        try:
            metadata = bird_batch_result.get('metadata', {})
            start_date_str = metadata.get('start_date', datetime.now().strftime('%Y-%m-%d'))
            days_processed = metadata.get('days_processed', 7)
            
            # Calculate date range
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            end_date = start_date + timedelta(days=days_processed)
            
            print(f"Processing astro batch detection for {start_date_str} to {end_date.strftime('%Y-%m-%d')}")
            
            # Run all micro-transit scripts
            all_transit_events = []
            script_results = {}
            
            for script_name in self.micro_transit_scripts:
                print(f"\n--- Running {script_name} ---")
                script_transits = self.run_micro_transit_script(script_name, start_date, end_date)
                
                script_results[script_name] = {
                    'transit_count': len(script_transits),
                    'transits': script_transits
                }
                
                all_transit_events.extend(script_transits)
            
            print(f"\nTotal transit events collected: {len(all_transit_events)}")
            
            # Collect all bird periods from all days
            all_bird_periods = []
            for day_result in bird_batch_result.get('daily_results', []):
                for period in day_result.get('periods', []):
                    # Add date context to period
                    period_with_date = period.copy()
                    period_with_date['date'] = day_result['date']
                    all_bird_periods.append(period_with_date)
            
            print(f"Total favorable bird periods: {len(all_bird_periods)}")
            
            # Detect overlaps - simple automation moments
            automation_moments = self.detect_overlaps(all_bird_periods, all_transit_events)
            
            # Generate results
            result = {
                'metadata': {
                    'start_date': start_date_str,
                    'end_date': end_date.strftime('%Y-%m-%d'),
                    'days_processed': days_processed,
                    'generated_at': datetime.now().isoformat(),
                    'input_bird_periods': len(all_bird_periods),
                    'total_transit_events': len(all_transit_events),
                    'automation_moments_found': len(automation_moments)
                },
                'script_results': script_results,
                'automation_moments': automation_moments,
                'statistics': {
                    'total_automation_moments': len(automation_moments),
                    'enhanced_moments': len([m for m in automation_moments if m.get('enhanced', False)]),
                    'chronological_order': True
                }
            }
            
            return result
            
        except Exception as e:
            return {
                'error': str(e),
                'metadata': {
                    'start_date': start_date_str if 'start_date_str' in locals() else 'unknown',
                    'generated_at': datetime.now().isoformat()
                }
            }
    


def main():
    """
    Command line interface for testing
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Astro Batch Detector - Step 2 of Astrobatch API")
    parser.add_argument("--input", "-i", required=True,
                       help="Input JSON file from bird_batch_filter.py")
    parser.add_argument("--output", "-o", help="Output JSON file")
    
    args = parser.parse_args()
    
    try:
        # Load input from Step 1
        with open(args.input, 'r') as f:
            bird_batch_result = json.load(f)
        
        detector = AstroBatchDetector()
        result = detector.process_batch(bird_batch_result)
        
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(result, f, indent=2, default=str)
            print(f"Results saved to {args.output}")
        else:
            print(json.dumps(result, indent=2, default=str))
            
    except Exception as e:
        print(f"Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())