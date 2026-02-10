from datetime import datetime, timezone
import pytz


def parse_ics_content(ics_content):
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
                    start_dt = parse_ics_datetime(current_event['start'], current_event.get('start_tzid'))
                    end_dt = parse_ics_datetime(current_event['end'], current_event.get('end_tzid'))

                    if start_dt and end_dt:
                        midpoint_dt = calculate_midpoint(start_dt, end_dt)
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
                if ';TZID=' in line:
                    parts = line.split(':')
                    tzid_part = parts[0]
                    datetime_part = parts[1] if len(parts) > 1 else ''
                    tzid = tzid_part.split('TZID=')[1] if 'TZID=' in tzid_part else None
                    current_event['start'] = datetime_part
                    current_event['start_tzid'] = tzid
                else:
                    current_event['start'] = line.split(':', 1)[1] if ':' in line else ''
            elif line.startswith('DTEND'):
                if ';TZID=' in line:
                    parts = line.split(':')
                    tzid_part = parts[0]
                    datetime_part = parts[1] if len(parts) > 1 else ''
                    tzid = tzid_part.split('TZID=')[1] if 'TZID=' in tzid_part else None
                    current_event['end'] = datetime_part
                    current_event['end_tzid'] = tzid
                else:
                    current_event['end'] = line.split(':', 1)[1] if ':' in line else ''
            elif line.startswith('SUMMARY'):
                current_event['summary'] = line.split(':', 1)[1] if ':' in line else ''

    return events


def parse_ics_datetime(dt_string, tzid=None):
    if not dt_string:
        return None

    dt_string = dt_string.strip()

    try:
        if 'T' in dt_string:
            is_utc = dt_string.endswith('Z')
            dt_string_clean = dt_string.rstrip('Z')

            if len(dt_string_clean) == 15:
                dt = datetime.strptime(dt_string_clean, '%Y%m%dT%H%M%S')
            elif len(dt_string_clean) == 13:
                dt = datetime.strptime(dt_string_clean, '%Y%m%dT%H%M')
            else:
                return None

            if is_utc:
                dt = pytz.utc.localize(dt)
                local_tz = pytz.timezone('US/Eastern')
                dt = dt.astimezone(local_tz)
                return dt.replace(tzinfo=None)
            elif tzid:
                try:
                    tz = pytz.timezone(tzid)
                    dt = tz.localize(dt)
                    return dt.replace(tzinfo=None)
                except Exception as e:
                    print(f"Unknown timezone '{tzid}': {e}")
                    return dt
            else:
                return dt
        else:
            if len(dt_string) == 8:
                return datetime.strptime(dt_string, '%Y%m%d')
    except Exception as e:
        print(f"Error parsing datetime '{dt_string}': {e}")
        return None

    return None


def calculate_midpoint(start_time, end_time):
    midpoint_timestamp = (start_time.timestamp() + end_time.timestamp()) / 2
    return datetime.fromtimestamp(midpoint_timestamp)
