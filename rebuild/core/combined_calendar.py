#!/usr/bin/env python3
"""
Combined Calendar System - Smart 4th Calendar
Analyzes Personal + PTI Collective + Vedic PTI to find optimal timing patterns

Classification tiers:
  OMNI       = PTI (Best/Go) + Vedic (GO/Mild GO/Build) + Personal (power/supportive)
  DOUBLE GO  = PTI (Best/Go) + Vedic (GO/Mild GO/Build) — ignores Personal
  GOOD       = Any 2 systems positive, but NOT if PTI Worst
  NEUTRAL    = Mixed or single system positive
  SLOW       = 2 systems adverse
  CAUTION    = 3 systems adverse or PTI Worst + another adverse

Background days (posting recommended) = OMNI + DOUBLE GO + GOOD
PTI Worst days are NEVER background days.
"""

import re
from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional


class CombinedCalendarAnalyzer:

    def __init__(self):
        self.pti_go_values = {'PTI BEST', 'PTI GO', 'BEST', 'GO'}
        self.pti_worst_values = {'PTI WORST', 'WORST', 'PTI SLOW'}

        self.vedic_go_values = {'GO', 'MILD GO', 'BUILD'}
        self.vedic_bad_values = {'STOP', 'MEGA RED', 'MEGA_STOP', 'SLOW'}

        self.personal_good_values = {'power', 'supportive'}
        self.personal_bad_values = {'avoid'}

        self.classifications = {
            'omni': {
                'label': 'OMNI',
                'description': 'All 3 systems aligned — optimal for major content batching',
                'is_background': True,
            },
            'double_go': {
                'label': 'DOUBLE GO',
                'description': 'PTI + Vedic aligned — strong collective momentum',
                'is_background': True,
            },
            'good': {
                'label': 'GOOD',
                'description': '2 systems aligned — favorable timing',
                'is_background': True,
            },
            'neutral': {
                'label': 'NEUTRAL',
                'description': 'Mixed signals — routine activities only',
                'is_background': False,
            },
            'slow': {
                'label': 'SLOW',
                'description': '2 systems adverse — proceed carefully',
                'is_background': False,
            },
            'caution': {
                'label': 'CAUTION',
                'description': 'Multiple systems adverse — avoid major launches',
                'is_background': False,
            },
        }

    def _normalize(self, label: str) -> str:
        if not label:
            return ''
        clean = re.sub(r'[^\w\s-]', '', str(label))
        return ' '.join(clean.split()).upper()

    def _pti_is_go(self, raw: str) -> bool:
        return self._normalize(raw) in self.pti_go_values

    def _pti_is_worst(self, raw: str) -> bool:
        return self._normalize(raw) in self.pti_worst_values

    def _vedic_is_go(self, raw: str) -> bool:
        return str(raw).strip().upper() in self.vedic_go_values

    def _vedic_is_bad(self, raw: str) -> bool:
        return str(raw).strip().upper() in self.vedic_bad_values

    def _personal_is_good(self, raw: str) -> bool:
        return str(raw).strip().lower() in self.personal_good_values

    def _personal_is_bad(self, raw: str) -> bool:
        return str(raw).strip().lower() in self.personal_bad_values

    def classify_day(self, pti_quality: str, vedic_quality: str, personal_quality: str) -> Dict[str, Any]:
        pti_go = self._pti_is_go(pti_quality)
        pti_worst = self._pti_is_worst(pti_quality)
        vedic_go = self._vedic_is_go(vedic_quality)
        vedic_bad = self._vedic_is_bad(vedic_quality)
        personal_good = self._personal_is_good(personal_quality)
        personal_bad = self._personal_is_bad(personal_quality)

        is_double_go = pti_go and vedic_go

        if is_double_go and personal_good:
            key = 'omni'
            reason = "All 3 aligned: PTI ({}) + Vedic ({}) + Personal ({})".format(
                pti_quality, vedic_quality, personal_quality)
        elif is_double_go:
            key = 'double_go'
            reason = "PTI ({}) + Vedic ({}) aligned".format(pti_quality, vedic_quality)
        elif pti_worst:
            bad_count = sum([vedic_bad, personal_bad])
            if bad_count >= 1:
                key = 'caution'
            else:
                key = 'slow'
            reason = "PTI Worst ({}) — excluded from background".format(pti_quality)
        else:
            good_count = sum([pti_go, vedic_go, personal_good])
            bad_count = sum([
                (not pti_go and not pti_worst and self._normalize(pti_quality) not in {'NORMAL', ''}) or False,
                vedic_bad,
                personal_bad
            ])

            if good_count >= 2:
                key = 'good'
                parts = []
                if pti_go: parts.append("PTI ({})".format(pti_quality))
                if vedic_go: parts.append("Vedic ({})".format(vedic_quality))
                if personal_good: parts.append("Personal ({})".format(personal_quality))
                reason = "2 systems aligned: {}".format(' + '.join(parts))
            elif vedic_bad and personal_bad:
                key = 'caution'
                reason = "Vedic ({}) + Personal ({}) adverse".format(vedic_quality, personal_quality)
            elif bad_count >= 2:
                key = 'slow'
                reason = "Multiple systems adverse"
            else:
                key = 'neutral'
                reason = "Mixed: PTI ({}) + Vedic ({}) + Personal ({})".format(
                    pti_quality, vedic_quality, personal_quality)

        cls_info = self.classifications[key]
        return {
            'classification': cls_info['label'],
            'classification_key': key,
            'description': cls_info['description'],
            'reason': reason,
            'is_background': cls_info['is_background'],
            'is_double_go': is_double_go,
            'system_breakdown': {
                'pti': {'quality': pti_quality, 'is_go': pti_go, 'is_worst': pti_worst},
                'vedic': {'quality': vedic_quality, 'is_go': vedic_go},
                'personal': {'quality': personal_quality, 'is_good': personal_good},
            },
        }

    def calculate_combined_classification(self, personal_quality: str,
                                          pti_quality: str,
                                          vedic_quality: str) -> Dict[str, Any]:
        result = self.classify_day(pti_quality, vedic_quality, personal_quality)
        result['systems_aligned'] = []
        if result['system_breakdown']['pti']['is_go']:
            result['systems_aligned'].append('PTI Collective')
        if result['system_breakdown']['vedic']['is_go']:
            result['systems_aligned'].append('Vedic PTI')
        if result['system_breakdown']['personal']['is_good']:
            result['systems_aligned'].append('Personal')
        result['good_count'] = len(result['systems_aligned'])
        result['bad_count'] = sum([
            result['system_breakdown']['pti']['is_worst'],
            self._vedic_is_bad(vedic_quality),
            self._personal_is_bad(personal_quality),
        ])
        return result

    def _is_double_go(self, pti_quality: str, vedic_quality: str) -> bool:
        return self._pti_is_go(pti_quality) and self._vedic_is_go(vedic_quality)

    def analyze_calendar_data(self, calendar_data: Dict[str, Any]) -> Dict[str, Any]:
        personal_data = calendar_data.get('personal', {}).get('data', {})
        pti_data = calendar_data.get('pti_collective', {}).get('data', {})
        vedic_data = calendar_data.get('vedic_pti', {}).get('data', {})

        personal_scores = personal_data.get('daily_scores', {})
        personal_periods = personal_data.get('daily_periods', [])
        pti_results = pti_data.get('results', []) or pti_data.get('timing_data', [])
        vedic_results = vedic_data.get('results', [])

        print("COMBINED CALENDAR DEBUG:")
        print("   personal_scores type: {}".format(type(personal_scores)))
        print("   personal_scores length: {}".format(len(personal_scores) if personal_scores else 0))
        if personal_scores:
            first_key = list(personal_scores.keys())[0]
            print("   First item: {} -> {}".format(first_key, personal_scores[first_key]))

        personal_by_date = {}
        if personal_scores:
            for date_key, score_data in personal_scores.items():
                if isinstance(score_data, dict) and score_data.get('quality'):
                    personal_by_date[date_key] = score_data.get('quality', 'neutral')
        if not personal_by_date and personal_periods:
            for period in personal_periods:
                date_key = period.get('date')
                if date_key and period.get('personal_score'):
                    personal_by_date[date_key] = period['personal_score'].get('quality', 'neutral')

        pti_by_date = {}
        print("   PTI results count: {}".format(len(pti_results)))
        if pti_results:
            print("   First PTI result sample: {}".format(pti_results[0]))
            print("   PTI result keys: {}".format(list(pti_results[0].keys()) if isinstance(pti_results[0], dict) else []))
        for result in pti_results:
            date_key = result.get('date')
            if date_key:
                pti_by_date[date_key] = result.get('classification', 'Normal')

        vedic_by_date = {}
        print("   Vedic results count: {}".format(len(vedic_results)))
        if vedic_results:
            print("   First vedic result sample: {}".format(vedic_results[0]))
        for result in vedic_results:
            date_key = result.get('date')
            if date_key:
                vedic_by_date[date_key] = result.get('classification', 'NEUTRAL')

        all_dates = set()
        all_dates.update(personal_by_date.keys())
        all_dates.update(pti_by_date.keys())
        all_dates.update(vedic_by_date.keys())

        combined_results = []
        classification_stats = {
            'omni': 0, 'double_go': 0, 'good': 0,
            'caution': 0, 'slow': 0, 'neutral': 0
        }
        background_days = []

        for date_str in sorted(all_dates):
            personal_quality = personal_by_date.get(date_str, 'neutral')
            pti_quality = pti_by_date.get(date_str, 'Normal')
            vedic_quality = vedic_by_date.get(date_str, 'NEUTRAL')

            day_result = self.classify_day(pti_quality, vedic_quality, personal_quality)
            classification_stats[day_result['classification_key']] += 1

            if day_result['is_background']:
                background_days.append(date_str)

            pti_label = pti_quality
            vedic_label = vedic_quality
            personal_label = personal_quality

            result_entry = {
                'date': date_str,
                'classification': day_result['classification'],
                'classification_key': day_result['classification_key'],
                'description': day_result['description'],
                'reason': day_result['reason'],
                'is_background': day_result['is_background'],
                'is_double_go': day_result['is_double_go'],
                'systems_aligned': [],
                'system_breakdown': day_result['system_breakdown'],
                'pti_label': pti_label,
                'vedic_label': vedic_label,
                'personal_label': personal_label,
                'label': day_result['classification'],
            }

            if day_result['system_breakdown']['pti']['is_go']:
                result_entry['systems_aligned'].append('PTI')
            if day_result['system_breakdown']['vedic']['is_go']:
                result_entry['systems_aligned'].append('Vedic')
            if day_result['system_breakdown']['personal']['is_good']:
                result_entry['systems_aligned'].append('Personal')

            combined_results.append(result_entry)

        total_days = len(combined_results)
        summary = {
            'total_days': total_days,
            'classification_counts': classification_stats,
            'omni_days': classification_stats['omni'],
            'double_go_days': classification_stats['double_go'],
            'good_days': classification_stats['good'],
            'background_day_count': len(background_days),
            'favorable_days': classification_stats['omni'] + classification_stats['double_go'] + classification_stats['good'],
            'adverse_days': classification_stats['caution'] + classification_stats['slow'],
        }

        return {
            'calendar_type': 'Combined_Smart_Calendar',
            'generated': True,
            'results': combined_results,
            'background_days': background_days,
            'summary': summary,
            'methodology': {
                'description': 'Smart combined calendar: PTI + Vedic + Personal',
                'omni': 'PTI (Best/Go) + Vedic (GO/Mild GO/Build) + Personal (power/supportive)',
                'double_go': 'PTI (Best/Go) + Vedic (GO/Mild GO/Build)',
                'good': '2 systems positive, never PTI Worst',
                'exclusion': 'PTI Worst days never count as background days',
            }
        }


def main():
    analyzer = CombinedCalendarAnalyzer()

    test_cases = [
        ('PTI Best', 'GO', 'power'),
        ('PTI Best', 'MILD GO', 'power'),
        ('PTI Go', 'BUILD', 'neutral'),
        ('PTI Go', 'MILD GO', 'avoid'),
        ('PTI Best', 'NEUTRAL', 'power'),
        ('PTI Worst', 'GO', 'power'),
        ('Normal', 'STOP', 'avoid'),
        ('Normal', 'NEUTRAL', 'neutral'),
        ('PTI Go', 'SLOW', 'power'),
        ('Normal', 'MILD GO', 'power'),
    ]

    print("Combined Calendar Classification Test:")
    print("=" * 80)
    print("{:<14} {:<10} {:<12} -> {:<12} {}".format("PTI", "Vedic", "Personal", "Class", "Background?"))
    print("-" * 80)

    for pti, vedic, personal in test_cases:
        result = analyzer.classify_day(pti, vedic, personal)
        bg = "YES" if result['is_background'] else "no"
        print("{:<14} {:<10} {:<12} -> {:<12} {}".format(
            pti, vedic, personal, result['classification'], bg))

    print("=" * 80)


if __name__ == "__main__":
    main()
