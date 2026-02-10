#!/usr/bin/env python3
"""
STEP 1: Bird Batch Filter
Processes panchapakshi.py output to identify and filter top 6 periods per day
Uses the CSV database (pancha_pakshi_db.csv) for authentic calculations
Tier system: Double Boost (💥) > Boost (🚀) > Build (💪)
"""

import sys
import os
import json
from datetime import datetime, timedelta, date
from typing import List, Dict, Any, Tuple
import importlib.util

class BirdBatchFilter:
    """
    Processes bird period data and filters for top favorable combinations
    Uses the new panchapakshi.py with CSV database
    """
    
    def __init__(self):
        self.tier_definitions = {
            "Double Boost": {
                "combinations": [("Ruling", "Ruling")],
                "icon": "💥",
                "priority": 1,
                "description": "Maximum power periods"
            },
            "Boost": {
                "combinations": [("Eating", "Ruling")],
                "icon": "🚀", 
                "priority": 2,
                "description": "High energy periods"
            },
            "Build": {
                "combinations": [("Ruling", "Eating")],
                "icon": "💪",
                "priority": 3,
                "description": "Growth and development periods"
            }
        }
        self._panchapakshi_module = None
    
    def import_panchapakshi(self):
        """
        Import the panchapaskshi_2.py module - uses rebuild's core/panch_pakshi path
        Falls back to top-level panch_pakshi/ if available
        """
        if self._panchapakshi_module:
            return self._panchapakshi_module

        try:
            rebuild_root = os.path.dirname(os.path.dirname(__file__))
            pp_path = os.path.join(rebuild_root, 'core', 'panch_pakshi')

            top_level_pp = os.path.join(os.path.dirname(os.path.dirname(rebuild_root)), 'panch_pakshi')

            for search_path in [pp_path, top_level_pp]:
                candidate = os.path.join(search_path, 'panchapaskshi_2.py')
                if not os.path.exists(candidate):
                    candidate = os.path.join(search_path, 'panchapakshi.py')
                if os.path.exists(candidate):
                    spec = importlib.util.spec_from_file_location("panchapakshi_module", candidate)
                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)
                    self._panchapakshi_module = module
                    return self._panchapakshi_module

            raise FileNotFoundError("panchapakshi module not found in rebuild or top-level paths")
        except Exception as e:
            raise Exception(f"Error importing panchapakshi module: {e}")
    
    def import_personalbirdv3(self):
        """Legacy method - now redirects to panchapakshi"""
        return self.import_panchapakshi()
    
    def run_panchapakshi_for_date_range(self, start_date: str, days: int = 30, 
                                          birth_date: str = None, birth_time: str = None,
                                          birth_latitude: float = None, birth_longitude: float = None,
                                          current_latitude: float = None, current_longitude: float = None) -> Dict[str, Any]:
        """
        Run panchapakshi.py for a date range using the CSV database
        
        Args:
            start_date: Starting date in YYYY-MM-DD format
            days: Number of days to process
            birth_date: Birth date in YYYY-MM-DD format
            birth_time: Birth time in HH:MM:SS format
            birth_latitude: Birth location latitude
            birth_longitude: Birth location longitude
            current_latitude: Current location latitude (for transit calculations)
            current_longitude: Current location longitude
            
        Returns:
            Dictionary containing all periods data
        """
        try:
            pp = self.import_panchapakshi()
            
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            
            b_lat = birth_latitude or 29.2108
            b_lon = birth_longitude or -81.0228
            c_lat = current_latitude or b_lat
            c_lon = current_longitude or b_lon
            
            if birth_date and birth_time:
                birth_dt = datetime.strptime(f"{birth_date} {birth_time}", "%Y-%m-%d %H:%M:%S")
            else:
                birth_dt = datetime(1973, 3, 9, 16, 56)
            
            birth_info = pp.calculate_birth_bird(birth_dt, b_lat, b_lon)
            birth_bird = birth_info['bird']
            
            all_periods = {
                "start_date": start_date,
                "days_processed": days,
                "birth_info": {
                    "bird": birth_bird,
                    "nakshatra": birth_info.get('nakshatra', ''),
                    "paksha": birth_info.get('paksha', '')
                },
                "daily_periods": []
            }
            
            for day_offset in range(days):
                current_date = start_dt + timedelta(days=day_offset)
                date_str = current_date.strftime("%Y-%m-%d")
                
                timing = pp.get_daily_bird_timing(current_date.date(), birth_bird, c_lat, c_lon)
                
                day_periods = self._extract_periods_from_timing(timing)
                
                all_periods["daily_periods"].append({
                    "date": date_str,
                    "weekday": current_date.strftime("%A"),
                    "paksha": timing.get('paksha', ''),
                    "periods": day_periods
                })
            
            return all_periods
            
        except Exception as e:
            raise Exception(f"Error running panchapakshi for date range: {e}")
    
    def run_personalbirdv3_for_date_range(self, start_date: str, days: int = 30) -> Dict[str, Any]:
        """Legacy method - now uses panchapakshi"""
        return self.run_panchapakshi_for_date_range(start_date, days)

    def get_daily_bird_periods(self, start_date: str, days: int = 30, birth_date: str = None, birth_time: str = None, birth_latitude: float = None, birth_longitude: float = None, current_latitude: float = None, current_longitude: float = None, timezone: str = None) -> Dict[str, Any]:
        """
        Get daily bird periods using the panchapakshi.py CSV database
        
        Args:
            start_date: Starting date in YYYY-MM-DD format  
            days: Number of days to process
            birth_date: Birth date in YYYY-MM-DD format
            birth_time: Birth time in HH:MM:SS format
            birth_latitude: Birth latitude
            birth_longitude: Birth longitude
            current_latitude: Current location latitude
            current_longitude: Current location longitude
            timezone: Timezone (not used - calculated from coordinates)
            
        Returns:
            Dictionary containing bird periods data
        """
        try:
            return self.run_panchapakshi_for_date_range(
                start_date, days,
                birth_date=birth_date,
                birth_time=birth_time,
                birth_latitude=birth_latitude,
                birth_longitude=birth_longitude,
                current_latitude=current_latitude,
                current_longitude=current_longitude
            )
        except Exception as e:
            raise Exception(f"Error getting daily bird periods: {e}")
    
    def _extract_periods_from_timing(self, timing: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract periods from panchapakshi timing data (new CSV database format)
        
        Args:
            timing: Dictionary from get_daily_bird_timing with day_main_periods, night_main_periods, etc.
            
        Returns:
            List of period dictionaries with subperiods flattened for tier classification
        """
        all_periods = []
        
        for period in timing.get('day_main_periods', []):
            main_activity = period.get('activity', '')
            
            period_data = {
                "start_time": period.get('start_time', ''),
                "end_time": period.get('end_time', ''),
                "main_activity": main_activity,
                "period_type": "day",
                "period_index": period.get('period_index', 0),
            }
            
            for sub in period.get('subperiods', []):
                sub_activity = sub.get('activity', '')
                sub_data = period_data.copy()
                sub_data.update({
                    "start_time": sub.get('start_time', ''),
                    "end_time": sub.get('end_time', ''),
                    "sub_activity": sub_activity,
                    "combination": f"{main_activity}/{sub_activity}",
                    "is_sub_period": True,
                    "rating": sub.get('rating', 5),
                    "effect": sub.get('effect', 'Average'),
                    "relation": sub.get('relation', 'Neutral')
                })
                all_periods.append(sub_data)
        
        for period in timing.get('night_main_periods', []):
            main_activity = period.get('activity', '')
            
            period_data = {
                "start_time": period.get('start_time', ''),
                "end_time": period.get('end_time', ''),
                "main_activity": main_activity,
                "period_type": "night",
                "period_index": period.get('period_index', 0),
            }
            
            for sub in period.get('subperiods', []):
                sub_activity = sub.get('activity', '')
                sub_data = period_data.copy()
                sub_data.update({
                    "start_time": sub.get('start_time', ''),
                    "end_time": sub.get('end_time', ''),
                    "sub_activity": sub_activity,
                    "combination": f"{main_activity}/{sub_activity}",
                    "is_sub_period": True,
                    "rating": sub.get('rating', 5),
                    "effect": sub.get('effect', 'Average'),
                    "relation": sub.get('relation', 'Neutral')
                })
                all_periods.append(sub_data)
        
        return all_periods
    
    def _extract_periods_for_date(self, pb3_module, target_date: datetime) -> List[Dict[str, Any]]:
        """Legacy method - kept for backward compatibility"""
        return []
    
    def classify_period_tier(self, combination: str) -> Tuple[str, Dict[str, Any]]:
        """
        Classify a period combination into tier system
        
        Args:
            combination: Activity combination like "Ruling/Ruling"
            
        Returns:
            Tuple of (tier_name, tier_info)
        """
        # Parse combination
        if '/' not in combination:
            return "Unclassified", {"icon": "⚪", "priority": 99}
        
        main_activity, sub_activity = combination.split('/')
        activity_pair = (main_activity.strip(), sub_activity.strip())
        
        # Check each tier
        for tier_name, tier_info in self.tier_definitions.items():
            if activity_pair in tier_info["combinations"]:
                return tier_name, tier_info
        
        return "Unclassified", {"icon": "⚪", "priority": 99, "description": "Other combinations"}
    
    def _parse_time(self, time_str: str) -> datetime:
        """Parse time string in various formats"""
        time_str = time_str.strip()
        
        for fmt in ['%I:%M %p', '%I:%M:%S %p', '%H:%M:%S', '%H:%M']:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        
        return datetime.strptime('12:00', '%H:%M')
    
    def filter_top_periods(self, daily_periods: List[Dict[str, Any]], max_periods: int = 6) -> List[Dict[str, Any]]:
        """
        Filter to top periods per day based on tier system
        
        Args:
            daily_periods: List of periods for a single day
            max_periods: Maximum number of periods to return
            
        Returns:
            Filtered and sorted list of top periods
        """
        classified_periods = []
        
        for period in daily_periods:
            if not period.get('is_sub_period', False):
                continue
                
            combination = period.get('combination', '')
            tier_name, tier_info = self.classify_period_tier(combination)
            
            if tier_name == "Unclassified":
                continue
            
            start_dt = self._parse_time(period['start_time'])
            end_dt = self._parse_time(period['end_time'])
            
            if end_dt.time() < start_dt.time():
                end_dt = end_dt + timedelta(days=1)
            
            duration_minutes = int((end_dt - start_dt).total_seconds() / 60)
            if duration_minutes < 0:
                duration_minutes = abs(duration_minutes)
            
            classified_periods.append({
                "start_time": period['start_time'],
                "end_time": period['end_time'],
                "duration_minutes": duration_minutes,
                "main_activity": period.get('main_activity', ''),
                "sub_activity": period.get('sub_activity', ''),
                "combination": combination,
                "tier": tier_name,
                "tier_icon": tier_info["icon"],
                "tier_priority": tier_info["priority"],
                "tier_description": tier_info.get("description", ""),
                "period_type": period.get('period_type', ''),
                "rating": period.get('rating', 5),
                "effect": period.get('effect', 'Average'),
                "relation": period.get('relation', 'Neutral'),
                "period_index": period.get('period_index', 0)
            })
        
        classified_periods.sort(key=lambda x: (x['tier_priority'], -x['duration_minutes']))
        
        return classified_periods[:max_periods]
    
    def process_batch(self, start_date: str, days: int = 30, max_periods_per_day: int = 6,
                       birth_date: str = None, birth_time: str = None,
                       birth_latitude: float = None, birth_longitude: float = None) -> Dict[str, Any]:
        """
        Main method to process bird periods for date range and return filtered results
        
        Args:
            start_date: Starting date in YYYY-MM-DD format
            days: Number of days to process
            max_periods_per_day: Maximum periods per day to return
            birth_date: Birth date in YYYY-MM-DD format
            birth_time: Birth time in HH:MM or HH:MM:SS format
            birth_latitude: Birth latitude
            birth_longitude: Birth longitude
            
        Returns:
            Dictionary with filtered periods and statistics
        """
        try:
            # Run personalbirdv3 for date range with birth data if provided
            if birth_date and birth_time and birth_latitude and birth_longitude:
                all_periods_data = self.run_panchapakshi_for_date_range(
                    start_date, days,
                    birth_date=birth_date,
                    birth_time=birth_time,
                    birth_latitude=birth_latitude,
                    birth_longitude=birth_longitude
                )
            else:
                all_periods_data = self.run_personalbirdv3_for_date_range(start_date, days)
            
            # Process each day
            filtered_results = {
                "metadata": {
                    "start_date": start_date,
                    "days_processed": days,
                    "max_periods_per_day": max_periods_per_day,
                    "tier_system": self.tier_definitions,
                    "generated_at": datetime.now().isoformat()
                },
                "daily_results": [],
                "statistics": {
                    "total_days": 0,
                    "total_periods": 0,
                    "tier_counts": {tier: 0 for tier in self.tier_definitions.keys()}
                }
            }
            
            for day_data in all_periods_data["daily_periods"]:
                date = day_data["date"]
                periods = day_data["periods"]
                
                # Filter top periods for this day
                top_periods = self.filter_top_periods(periods, max_periods_per_day)
                
                if top_periods:  # Only include days with favorable periods
                    day_result = {
                        "date": date,
                        "weekday": day_data["weekday"],
                        "period_count": len(top_periods),
                        "periods": top_periods
                    }
                    
                    filtered_results["daily_results"].append(day_result)
                    
                    # Update statistics
                    filtered_results["statistics"]["total_periods"] += len(top_periods)
                    for period in top_periods:
                        tier = period["tier"]
                        if tier in filtered_results["statistics"]["tier_counts"]:
                            filtered_results["statistics"]["tier_counts"][tier] += 1
            
            filtered_results["statistics"]["total_days"] = len(filtered_results["daily_results"])
            
            return filtered_results
            
        except Exception as e:
            return {"error": str(e), "metadata": {"start_date": start_date, "days": days}}

def main():
    """
    Command line interface for testing
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Bird Batch Filter - Step 1 of Astrobatch API")
    parser.add_argument("--date", "-d", default=datetime.now().strftime("%Y-%m-%d"),
                       help="Start date (YYYY-MM-DD)")
    parser.add_argument("--days", "-n", type=int, default=7,
                       help="Number of days to process")
    parser.add_argument("--max-periods", "-m", type=int, default=6,
                       help="Maximum periods per day")
    parser.add_argument("--output", "-o", help="Output JSON file")
    
    args = parser.parse_args()
    
    try:
        filter_engine = BirdBatchFilter()
        result = filter_engine.process_batch(args.date, args.days, args.max_periods)
        
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