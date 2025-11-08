import os
import uuid
from werkzeug.utils import secure_filename
from datetime import datetime
import re

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi', 'webm'}
UPLOAD_FOLDER = 'static/uploads'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_unique_filename(original_filename):
    """Generate a unique filename while preserving the original extension"""
    ext = original_filename.rsplit('.', 1)[1].lower()
    return f"artwork_{uuid.uuid4().hex[:8]}.{ext}"

def generate_placeholder_content(filename):
    """Generate placeholder description and hashtags"""
    description = f"Description for {filename}"
    hashtags = f"#artwork #image #{filename.split('.')[0]}"
    return description, hashtags


def parse_ics_content(ics_content):
    """Parse .ics file content and extract events"""
    events = []
    current_event = {}
    
    lines = ics_content.split('\n')
    in_event = False
    
    for line in lines:
        line = line.strip()
        
        if line == 'BEGIN:VEVENT':
            in_event = True
            current_event = {}
        elif line == 'END:VEVENT':
            if current_event and 'start' in current_event and 'end' in current_event:
                try:
                    start_dt = parse_ics_datetime(current_event['start'])
                    end_dt = parse_ics_datetime(current_event['end'])
                    
                    if start_dt and end_dt:
                        midpoint_timestamp = (start_dt.timestamp() + end_dt.timestamp()) / 2
                        midpoint_dt = datetime.fromtimestamp(midpoint_timestamp)
                        
                        events.append({
                            'summary': current_event.get('summary', ''),
                            'start_time': start_dt,
                            'end_time': end_dt,
                            'midpoint_time': midpoint_dt,
                            'event_type': current_event.get('event_type', 'default')
                        })
                except Exception as e:
                    print(f"Error parsing event: {e}")
                    continue
            in_event = False
            current_event = {}
        elif in_event:
            if line.startswith('DTSTART'):
                current_event['start'] = line.split(':', 1)[1] if ':' in line else ''
            elif line.startswith('DTEND'):
                current_event['end'] = line.split(':', 1)[1] if ':' in line else ''
            elif line.startswith('SUMMARY'):
                current_event['summary'] = line.split(':', 1)[1] if ':' in line else ''
    
    return events


def parse_ics_datetime(dt_string):
    """Parse iCalendar datetime string to Python datetime object"""
    if not dt_string:
        return None
    
    dt_string = dt_string.strip()
    
    try:
        if 'T' in dt_string:
            dt_string = dt_string.split('Z')[0]
            
            if len(dt_string) == 15:
                return datetime.strptime(dt_string, '%Y%m%dT%H%M%S')
            elif len(dt_string) == 13:
                return datetime.strptime(dt_string, '%Y%m%dT%H%M')
        else:
            if len(dt_string) == 8:
                return datetime.strptime(dt_string, '%Y%m%d')
    except Exception as e:
        print(f"Error parsing datetime '{dt_string}': {e}")
        return None
    
    return None


def calculate_midpoint(start_time, end_time):
    """Calculate midpoint between two datetime objects"""
    midpoint_timestamp = (start_time.timestamp() + end_time.timestamp()) / 2
    return datetime.fromtimestamp(midpoint_timestamp)
