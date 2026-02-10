#!/usr/bin/env python3
"""
Combined Calendar System - Smart 4th Calendar
Analyzes Personal + PTI Collective + Vedic PTI to find optimal timing patterns
Implements OMNI/DOUBLE GO/GOOD/CAUTION/SLOW/NEUTRAL classification system
"""

import sys
import os
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional

class CombinedCalendarAnalyzer:
    """
    Smart Combined Calendar that analyzes 3 base calendars for optimal timing patterns
    """
    
    def __init__(self):
        """Initialize the combined calendar analyzer"""
        
        # Define quality mappings for each calendar system
        self.personal_good = ['power', 'supportive']
        self.personal_bad = ['avoid']
        self.personal_neutral = ['neutral', 'aware']
        
        self.pti_good = ['BEST', 'MAYBE', 'PTI Best', 'PTI Go', 'PTI BEST', 'PTI GO'] 
        self.pti_bad = ['NO', 'PTI Slow', 'PTI SLOW']
        self.pti_neutral = ['Normal', 'NORMAL']
        
        self.vedic_good = ['GO', 'FOCUS', 'BUILD']
        self.vedic_bad = ['STOP', 'MEGA_STOP', 'SLOW', 'INWARD']
        self.vedic_neutral = ['NEUTRAL']
        
        # DOUBLE GO specific lists (stricter than general good)
        self.pti_double_go = ['PTI BEST', 'PTI GO', 'BEST']
        self.vedic_double_go = ['GO', 'BUILD']  # NOT FOCUS
        
        # Classification emojis and descriptions
        self.classifications = {
            'omni': {
                'emoji': '⚡',
                'label': 'OMNI',
                'description': 'Perfect 3-system alignment - optimal for major activities'
            },
            'double_go': {
                'emoji': '🚀',
                'label': 'DOUBLE GO',
                'description': 'PTI + Vedic aligned - powerful momentum regardless of personal'
            },
            'good': {
                'emoji': '💚',
                'label': 'GOOD',
                'description': '2 systems aligned - favorable timing'
            },
            'caution': {
                'emoji': '🔴',
                'label': 'CAUTION',
                'description': '3 systems adverse - avoid major decisions'
            },
            'slow': {
                'emoji': '🟡',
                'label': 'SLOW',
                'description': '2 systems adverse - proceed carefully'
            },
            'neutral': {
                'emoji': '⚪',
                'label': 'NEUTRAL',
                'description': 'Mixed signals - routine activities'
            }
        }
    
    def _normalize_label(self, label: str) -> str:
        """
        Normalize a calendar label by stripping emojis and extra whitespace.
        Handles strings like 'PTI Best 💜⚡' -> 'PTI BEST'
        """
        if not label:
            return ''
        # Remove common emojis and symbols
        import re
        # Remove emoji characters (Unicode ranges for most emojis)
        clean = re.sub(r'[^\w\s-]', '', label)
        # Normalize whitespace and uppercase
        return ' '.join(clean.split()).upper()
    
    def _is_double_go(self, pti_quality: str, vedic_quality: str) -> bool:
        """
        Check if PTI + Vedic combination qualifies for DOUBLE GO.
        
        DOUBLE GO = PTI (Best/Go) + Vedic (GO/BUILD) alignment
        Completely ignores Personal calendar - this is a standalone indicator.
        
        IMPORTANT: This logic MUST match calculate_is_double_go() in astrobatch_api.py
        to ensure consistency across all calendar outputs.
        """
        import re
        
        if not pti_quality or not vedic_quality:
            return False
        
        # Normalize PTI: strip emojis and whitespace, uppercase
        # Uses extended emoji regex to catch all Unicode emoji ranges
        pti_clean = re.sub(r'[\U0001F300-\U0001F9FF\U0001FA00-\U0001FAFF\u2600-\u26FF\u2700-\u27BF]', '', str(pti_quality))
        pti_normalized = ' '.join(pti_clean.split()).upper()
        
        # Normalize Vedic: strip whitespace, uppercase
        vedic_normalized = str(vedic_quality).strip().upper()
        
        # Valid values for DOUBLE GO (same as in astrobatch_api.py)
        pti_double_go_values = ['PTI BEST', 'PTI GO', 'BEST', 'GO']
        vedic_double_go_values = ['GO', 'BUILD']  # NOT FOCUS, SLOW, STOP, etc.
        
        # Check PTI: must contain one of the valid values
        pti_ok = any(valid in pti_normalized for valid in pti_double_go_values)
        
        # Check Vedic: must be exactly GO or BUILD (not FOCUS, SLOW, etc.)
        vedic_ok = vedic_normalized in vedic_double_go_values
        
        return pti_ok and vedic_ok
    
    def classify_calendar_quality(self, calendar_type: str, quality: str) -> str:
        """
        Classify individual calendar quality as good/bad/neutral
        """
        if calendar_type == 'personal':
            if quality in self.personal_good:
                return 'good'
            elif quality in self.personal_bad:
                return 'bad'
            else:
                return 'neutral'
                
        elif calendar_type == 'pti_collective':
            if quality in self.pti_good:
                return 'good'
            elif quality in self.pti_bad:
                return 'bad'
            else:
                return 'neutral'
                
        elif calendar_type == 'vedic_pti':
            if quality in self.vedic_good:
                return 'good'
            elif quality in self.vedic_bad:
                return 'bad'
            else:
                return 'neutral'
        
        return 'neutral'  # Default fallback
    
    def calculate_combined_classification(self, personal_quality: str, 
                                        pti_quality: str, 
                                        vedic_quality: str) -> Dict[str, Any]:
        """
        Calculate combined classification using user's smart logic:
        - OMNI = all 3 good
        - DOUBLE GO = PTI + Vedic good (ignores Personal)
        - GOOD = 2 good
        - CAUTION = 3 bad
        - SLOW = 2 bad  
        - NEUTRAL = 1 bad or mixed
        """
        
        # Classify each calendar
        personal_class = self.classify_calendar_quality('personal', personal_quality)
        pti_class = self.classify_calendar_quality('pti_collective', pti_quality)
        vedic_class = self.classify_calendar_quality('vedic_pti', vedic_quality)
        
        # Count good and bad systems
        good_systems = [personal_class, pti_class, vedic_class].count('good')
        bad_systems = [personal_class, pti_class, vedic_class].count('bad')
        
        # OMNI: All 3 systems good - HIGHEST PRIORITY (must check first!)
        if good_systems == 3:
            classification_key = 'omni'
            reason = f"Perfect alignment: Personal ({personal_quality}) + PTI ({pti_quality}) + Vedic ({vedic_quality})"
            systems_aligned = ['Personal', 'PTI Collective', 'Vedic PTI']
            
        # Special case: DOUBLE GO (PTI Best/Go + Vedic GO/BUILD specifically)
        elif self._is_double_go(pti_quality, vedic_quality):
            classification_key = 'double_go'
            reason = f"PTI ({pti_quality}) + Vedic ({vedic_quality}) aligned"
            systems_aligned = ['PTI Collective', 'Vedic PTI']
            
        # GOOD: 2 systems good
        elif good_systems == 2:
            classification_key = 'good'
            aligned_systems = []
            if personal_class == 'good': aligned_systems.append(f"Personal ({personal_quality})")
            if pti_class == 'good': aligned_systems.append(f"PTI ({pti_quality})")
            if vedic_class == 'good': aligned_systems.append(f"Vedic ({vedic_quality})")
            reason = f"2 systems aligned: {' + '.join(aligned_systems)}"
            systems_aligned = [s.split(' (')[0] for s in aligned_systems]
            
        # CAUTION: 3 systems bad
        elif bad_systems == 3:
            classification_key = 'caution'
            reason = f"All systems cautioning: Personal ({personal_quality}) + PTI ({pti_quality}) + Vedic ({vedic_quality})"
            systems_aligned = []
            
        # SLOW: 2 systems bad
        elif bad_systems == 2:
            classification_key = 'slow'
            adverse_systems = []
            if personal_class == 'bad': adverse_systems.append(f"Personal ({personal_quality})")
            if pti_class == 'bad': adverse_systems.append(f"PTI ({pti_quality})")
            if vedic_class == 'bad': adverse_systems.append(f"Vedic ({vedic_quality})")
            reason = f"2 systems adverse: {' + '.join(adverse_systems)}"
            systems_aligned = []
            
        # NEUTRAL: 1 bad or mixed signals
        else:
            classification_key = 'neutral'
            reason = f"Mixed signals: Personal ({personal_quality}) + PTI ({pti_quality}) + Vedic ({vedic_quality})"
            systems_aligned = []
        
        # Get classification details
        classification_data = self.classifications[classification_key]
        
        return {
            'classification': classification_data['label'],
            'emoji': classification_data['emoji'],
            'description': classification_data['description'],
            'reason': reason,
            'systems_aligned': systems_aligned,
            'system_breakdown': {
                'personal': {'quality': personal_quality, 'class': personal_class},
                'pti_collective': {'quality': pti_quality, 'class': pti_class},
                'vedic_pti': {'quality': vedic_quality, 'class': vedic_class}
            },
            'good_count': good_systems,
            'bad_count': bad_systems,
            'classification_key': classification_key
        }
    
    def analyze_calendar_data(self, calendar_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze existing 3-calendar data to generate combined calendar
        
        Args:
            calendar_data: Dictionary containing personal, pti_collective, vedic_pti calendar data
            
        Returns:
            Combined calendar with daily classifications
        """
        
        # Extract calendar data
        personal_data = calendar_data.get('personal', {}).get('data', {})
        pti_data = calendar_data.get('pti_collective', {}).get('data', {})
        vedic_data = calendar_data.get('vedic_pti', {}).get('data', {})
        
        # Extract daily periods/results from each calendar
        # Try multiple formats: daily_results (current), daily_scores, daily_periods (legacy)
        personal_periods = personal_data.get('daily_periods', [])
        personal_scores = personal_data.get('daily_scores', {})
        personal_results = personal_data.get('daily_results', {})
        # PTI uses 'results' field before normalization (Combined runs before normalization)
        # After normalization it's in 'timing_data', so check both
        pti_results = pti_data.get('results', []) or pti_data.get('timing_data', [])
        vedic_results = vedic_data.get('results', [])
        
        combined_results = []
        classification_stats = {
            'omni': 0, 'double_go': 0, 'good': 0,
            'caution': 0, 'slow': 0, 'neutral': 0
        }
        
        # Create date-indexed data for easier lookup
        personal_by_date = {}
        
        # DEBUG: See what Personal data we're receiving
        print(f"🔍 PERSONAL DATA DEBUG:")
        print(f"   personal_scores type: {type(personal_scores)}")
        print(f"   personal_scores length: {len(personal_scores) if personal_scores else 0}")
        if personal_scores:
            first_key = list(personal_scores.keys())[0] if personal_scores else None
            if first_key:
                print(f"   First item: {first_key} → {personal_scores[first_key]}")
        
        # First try daily_scores (dict) - it's already date-indexed and reliable
        if personal_scores:
            for date_key, score_data in personal_scores.items():
                if isinstance(score_data, dict) and score_data.get('quality'):
                    personal_by_date[date_key] = score_data.get('quality', 'neutral')
        
        # Fall back to daily_periods (old format) if nothing else found
        if not personal_by_date and personal_periods:
            for period in personal_periods:
                date_key = period.get('date')
                if date_key and period.get('personal_score'):
                    personal_by_date[date_key] = period['personal_score'].get('quality', 'neutral')
        
        pti_by_date = {}
        print(f"🔍 PTI results count: {len(pti_results)}")
        if pti_results and len(pti_results) > 0:
            print(f"🔍 First PTI result sample: {pti_results[0]}")
            print(f"🔍 PTI result keys: {list(pti_results[0].keys() if isinstance(pti_results[0], dict) else [])}")
        
        for result in pti_results:
            date_key = result.get('date')
            if date_key:
                # PTI stores classification in 'classification' field  
                pti_classification = result.get('classification', 'NO')
                pti_by_date[date_key] = pti_classification
                # Debug key dates
                if date_key in ['2025-10-16', '2025-10-24', '2025-10-28']:
                    print(f"🔍 PTI extraction {date_key}: {pti_classification} (from result with keys: {list(result.keys())})")
        
        vedic_by_date = {}
        print(f"🔍 Vedic results count: {len(vedic_results)}")
        if vedic_results and len(vedic_results) > 0:
            print(f"🔍 First vedic result sample: {vedic_results[0]}")
        
        for result in vedic_results:
            date_key = result.get('date')
            if date_key:
                classification = result.get('classification', 'NEUTRAL')
                vedic_by_date[date_key] = classification
                # Debug key dates
                if date_key in ['2025-10-16', '2025-10-24', '2025-10-28']:
                    print(f"🔍 Vedic extraction {date_key}: {classification} (from {result})")
        
        # Debug logging for key dates
        debug_dates = ['2025-10-16', '2025-10-24', '2025-10-25', '2025-10-28']
        for debug_date in debug_dates:
            if debug_date in personal_by_date or debug_date in pti_by_date or debug_date in vedic_by_date:
                print(f"🔍 COMBINED DEBUG {debug_date}:")
                print(f"   Personal: {personal_by_date.get(debug_date, 'NOT FOUND')}")
                print(f"   PTI: {pti_by_date.get(debug_date, 'NOT FOUND')}")
                print(f"   Vedic: {vedic_by_date.get(debug_date, 'NOT FOUND')}")
        
        # Get all dates from any calendar that has data
        all_dates = set()
        all_dates.update(personal_by_date.keys())
        all_dates.update(pti_by_date.keys())
        all_dates.update(vedic_by_date.keys())
        
        # Analyze each date
        for date_str in sorted(all_dates):
            personal_quality = personal_by_date.get(date_str, 'neutral')
            pti_quality = pti_by_date.get(date_str, 'NO')
            vedic_quality = vedic_by_date.get(date_str, 'NEUTRAL')
            
            # Calculate combined classification
            combined_analysis = self.calculate_combined_classification(
                personal_quality, pti_quality, vedic_quality
            )
            
            # Update statistics
            classification_stats[combined_analysis['classification_key']] += 1
            
            # Check if this day qualifies for DOUBLE GO (PTI Best/Go + Vedic GO/BUILD)
            # This is a separate flag that can be displayed even if classification is different
            is_double_go = self._is_double_go(pti_quality, vedic_quality)
            
            # Create result entry
            result_entry = {
                'date': date_str,
                'classification': combined_analysis['classification'],
                'emoji': combined_analysis['emoji'],
                'description': combined_analysis['description'],
                'reason': combined_analysis['reason'],
                'systems_aligned': combined_analysis['systems_aligned'],
                'system_breakdown': combined_analysis['system_breakdown'],
                'details': combined_analysis,
                'is_double_go': is_double_go,
                'double_go_label': '🚀 DOUBLE GO' if is_double_go else None
            }
            
            combined_results.append(result_entry)
        
        # Generate summary
        total_days = len(combined_results)
        summary = {
            'total_days': total_days,
            'classification_counts': classification_stats,
            'classification_percentages': {
                key: (count / total_days * 100) if total_days > 0 else 0
                for key, count in classification_stats.items()
            },
            'double_go_days': classification_stats['double_go'],
            'omni_days': classification_stats['omni'],
            'favorable_days': classification_stats['omni'] + classification_stats['double_go'] + classification_stats['good'],
            'adverse_days': classification_stats['caution'] + classification_stats['slow']
        }
        
        return {
            'calendar_type': 'Combined_Smart_Calendar',
            'generated': True,
            'results': combined_results,
            'summary': summary,
            'methodology': {
                'description': 'Smart 4th calendar analyzing Personal + PTI Collective + Vedic PTI',
                'classifications': list(self.classifications.keys()),
                'special_logic': 'DOUBLE GO ignores Personal calendar for PTI+Vedic alignment'
            }
        }

def main():
    """Command line interface for testing"""
    analyzer = CombinedCalendarAnalyzer()
    
    # Test classification logic
    test_cases = [
        ('power', 'BEST', 'GO'),      # Should be OMNI
        ('avoid', 'BEST', 'GO'),      # Should be DOUBLE GO
        ('power', 'BEST', 'NEUTRAL'), # Should be GOOD
        ('avoid', 'NO', 'STOP'),      # Should be CAUTION
        ('avoid', 'NO', 'NEUTRAL'),   # Should be SLOW
        ('neutral', 'MAYBE', 'NEUTRAL'), # Should be NEUTRAL
    ]
    
    print("🎯 Combined Calendar Classification Test:")
    print("="*60)
    
    for personal, pti, vedic in test_cases:
        result = analyzer.calculate_combined_classification(personal, pti, vedic)
        print(f"{result['emoji']} {result['classification']:>10} | "
              f"Personal: {personal:>10} | PTI: {pti:>5} | Vedic: {vedic:>10}")
        print(f"   Reason: {result['reason']}")
        print()
    
    print("="*60)

if __name__ == "__main__":
    main()