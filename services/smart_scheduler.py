from datetime import datetime, timedelta
from collections import defaultdict
from models import Calendar, CalendarEvent, Image
from app import db

class SmartScheduler:
    """Smart scheduling service that assigns optimal posting times using astrology calendars"""
    
    def __init__(self, config):
        """
        Initialize scheduler with configuration
        
        Args:
            config: dict with keys:
                - instagram_limit: int (daily post limit)
                - pinterest_limit: int (daily post limit)
                - strategy: str ('astrology_only', 'fill_all', 'split_test')
                - min_spacing: int (minutes between posts)
        """
        self.config = config
        self.instagram_limit = config.get('instagram_limit', 2)
        self.pinterest_limit = config.get('pinterest_limit', 7)
        self.strategy = config.get('strategy', 'fill_all')
        self.min_spacing = config.get('min_spacing', 30)  # minutes
        
        # Usage tracking: {(date, platform): count}
        self.usage = defaultdict(int)
        
        # Last post time tracking: {(date, platform): datetime}
        self.last_post_time = {}
        
        # Available events by calendar type
        self.events_by_calendar = {}
        
    def load_events(self):
        """Load all available calendar events from AB, YP, POF calendars"""
        calendar_types = ['AB', 'YP', 'POF']
        
        for cal_type in calendar_types:
            calendar = Calendar.query.filter_by(calendar_type=cal_type).first()
            if calendar:
                events = CalendarEvent.query.filter_by(
                    calendar_id=calendar.id,
                    is_assigned=False
                ).order_by(CalendarEvent.midpoint_time).all()
                self.events_by_calendar[cal_type] = events
            else:
                self.events_by_calendar[cal_type] = []
        
        # Seed usage tracking from existing assigned events
        assigned_events = CalendarEvent.query.filter_by(is_assigned=True).all()
        for event in assigned_events:
            if event.assigned_platform and event.midpoint_time:
                date_str = self.get_date_str(event.midpoint_time)
                self.usage[(date_str, event.assigned_platform)] += 1
                key = (date_str, event.assigned_platform)
                # Track the latest post time for spacing
                if key not in self.last_post_time or event.midpoint_time > self.last_post_time[key]:
                    self.last_post_time[key] = event.midpoint_time
    
    def get_date_str(self, dt):
        """Get date string from datetime"""
        return dt.strftime('%Y-%m-%d')
    
    def check_daily_limit(self, event_datetime, platform):
        """Check if posting on this date/platform would exceed daily limit"""
        date_str = self.get_date_str(event_datetime)
        current_count = self.usage[(date_str, platform)]
        
        if platform == 'Instagram':
            return current_count < self.instagram_limit
        elif platform == 'Pinterest':
            return current_count < self.pinterest_limit
        else:
            return True  # No limit for other platforms
    
    def check_spacing(self, event_datetime, platform):
        """Check if this time respects minimum spacing from last post"""
        date_str = self.get_date_str(event_datetime)
        key = (date_str, platform)
        
        if key not in self.last_post_time:
            return True
        
        last_time = self.last_post_time[key]
        time_diff = (event_datetime - last_time).total_seconds() / 60  # minutes
        
        return time_diff >= self.min_spacing
    
    def find_available_event(self, platform, calendar_priority=['AB', 'YP', 'POF']):
        """
        Find next available event that satisfies constraints
        
        Args:
            platform: str ('Instagram' or 'Pinterest')
            calendar_priority: list of calendar types in priority order
            
        Returns:
            tuple (event, calendar_source) or (None, None)
        """
        for cal_type in calendar_priority:
            events = self.events_by_calendar.get(cal_type, [])
            
            for event in events:
                # Check if event already used
                if hasattr(event, '_used') and event._used:
                    continue
                
                # Check daily limit
                if not self.check_daily_limit(event.midpoint_time, platform):
                    continue
                
                # Check spacing
                if not self.check_spacing(event.midpoint_time, platform):
                    continue
                
                # Found a valid event!
                return event, cal_type
        
        return None, None
    
    def mark_event_used(self, event, platform):
        """Mark event as used and update tracking"""
        event._used = True
        date_str = self.get_date_str(event.midpoint_time)
        self.usage[(date_str, platform)] += 1
        self.last_post_time[(date_str, platform)] = event.midpoint_time
    
    def assign_times(self, image_ids, preview=False):
        """
        Assign times to selected images
        
        Args:
            image_ids: list of image IDs to schedule
            preview: bool - if True, don't commit to database
            
        Returns:
            dict with:
                - assignments: list of {image_id, platform, date, time, calendar_source, event_id}
                - unassigned: list of image_ids that couldn't be scheduled
                - summary: dict with stats
        """
        self.load_events()
        
        assignments = []
        unassigned = []
        
        # Alternate platforms
        platforms = ['Instagram', 'Pinterest']
        platform_index = 0
        
        for image_id in image_ids:
            current_platform_idx = platform_index % len(platforms)
            platform = platforms[current_platform_idx]
            
            # Find available event
            event, calendar_source = self.find_available_event(platform)
            
            if event is None:
                # Try other platform (the one we didn't just try)
                alt_platform_idx = (current_platform_idx + 1) % len(platforms)
                alt_platform = platforms[alt_platform_idx]
                event, calendar_source = self.find_available_event(alt_platform)
                if event:
                    platform = alt_platform
            
            platform_index += 1
            
            if event is None:
                unassigned.append(image_id)
                continue
            
            # Create assignment
            assignment = {
                'image_id': image_id,
                'platform': platform,
                'date': event.midpoint_time.strftime('%Y-%m-%d'),
                'time': event.midpoint_time.strftime('%H:%M'),
                'calendar_source': calendar_source,
                'event_id': event.id,
                'midpoint_time': event.midpoint_time.isoformat()
            }
            
            assignments.append(assignment)
            self.mark_event_used(event, platform)
        
        # Commit to database if not preview
        if not preview and assignments:
            self._commit_assignments(assignments)
        
        # Generate summary
        summary = {
            'total_assigned': len(assignments),
            'total_unassigned': len(unassigned),
            'by_calendar': {
                'AB': sum(1 for a in assignments if a['calendar_source'] == 'AB'),
                'YP': sum(1 for a in assignments if a['calendar_source'] == 'YP'),
                'POF': sum(1 for a in assignments if a['calendar_source'] == 'POF'),
            },
            'by_platform': {
                'Instagram': sum(1 for a in assignments if a['platform'] == 'Instagram'),
                'Pinterest': sum(1 for a in assignments if a['platform'] == 'Pinterest'),
            }
        }
        
        return {
            'assignments': assignments,
            'unassigned': unassigned,
            'summary': summary
        }
    
    def _commit_assignments(self, assignments):
        """Commit assignments to database"""
        for assignment in assignments:
            # Update Image
            image = Image.query.get(assignment['image_id'])
            if image:
                image.platform = assignment['platform']
                image.date = assignment['date']
                image.time = assignment['time']
                image.calendar_source = assignment['calendar_source']
                image.calendar_event_id = assignment['event_id']
            
            # Update CalendarEvent
            event = CalendarEvent.query.get(assignment['event_id'])
            if event:
                event.is_assigned = True
                event.assigned_image_id = assignment['image_id']
                event.assigned_platform = assignment['platform']
        
        db.session.commit()
