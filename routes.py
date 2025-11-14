import os
from flask import render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from app import app, db
from models import Image, Calendar, CalendarEvent, Collection, GeneratedAsset, EventAssignment
from utils import allowed_file, generate_unique_filename, parse_ics_content
from gpt_service import gpt_service
from dynamic_mockups_service import DynamicMockupsService
from fal_service import FalService
from publer_service import PublerAPI
from io import StringIO, BytesIO
import csv
import json

_image_asset_service = None

def get_image_asset_service():
    global _image_asset_service
    if _image_asset_service is None:
        from image_asset_service import ImageAssetService
        upload_folder = os.path.join(app.static_folder or '', 'uploads')
        _image_asset_service = ImageAssetService(upload_folder)
    return _image_asset_service

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if not file or file.filename == '' or file.filename is None:
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        stored_filename = generate_unique_filename(original_filename)
        
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], stored_filename)
        file.save(file_path)
        
        image = Image()
        image.original_filename = original_filename
        image.stored_filename = stored_filename
        image.status = 'Draft'
        image.media = stored_filename
        
        collection_id = request.form.get('collection_id')
        if collection_id and collection_id.isdigit():
            image.collection_id = int(collection_id)
            collection = Collection.query.get(int(collection_id))
            if collection:
                image.painting_name = collection.name
        
        if not image.painting_name:
            name_without_ext = os.path.splitext(original_filename)[0]
            image.painting_name = name_without_ext.replace('_', ' ').replace('-', ' ').title()
        
        db.session.add(image)
        db.session.commit()
        
        return jsonify(image.to_dict()), 200
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/images', methods=['GET'])
def get_images():
    try:
        images = Image.query.order_by(Image.created_at.desc()).all()
        return jsonify([img.to_dict() for img in images])
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Failed to fetch images', 'details': str(e)}), 500

@app.route('/update/<int:image_id>', methods=['POST'])
def update_image(image_id):
    data = request.get_json()
    if not data or 'field' not in data or 'value' not in data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    field = data['field']
    value = data['value']
    
    valid_fields = [
        'title', 'painting_name', 'materials', 'size', 'artist_note',
        'post_subtype', 'platform', 'date', 'time', 
        'status', 'labels', 'post_url', 'alt_text', 'cta', 'comments', 
        'cover_image_url', 'etsy_description', 'etsy_listing_title', 
        'etsy_price', 'etsy_quantity', 'etsy_sku', 'instagram_first_comment',
        'pinterest_hashtags', 'links', 'media_source', 'media_urls', 
        'pin_board_fb_album_google_category', 'pinterest_description', 
        'pinterest_link_url', 'reminder', 'seo_description', 'seo_tags', 
        'seo_title', 'text', 'video_pin_pdf_title', 'calendar_selection', 
        'collection_id'
    ]
    
    if field not in valid_fields:
        return jsonify({'error': 'Invalid field'}), 400
    
    image = Image.query.get(image_id)
    if not image:
        return jsonify({'error': 'Image not found'}), 404
    
    try:
        setattr(image, field, value)
        db.session.commit()
        return jsonify({'success': True}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/batch_update', methods=['POST'])
def batch_update():
    """Update multiple images at once"""
    data = request.get_json()
    if not data or 'image_ids' not in data or 'updates' not in data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    image_ids = data['image_ids']
    updates = data['updates']
    
    valid_fields = [
        'title', 'painting_name', 'materials', 'size', 'artist_note',
        'post_subtype', 'platform', 'date', 'time', 
        'status', 'labels', 'post_url', 'alt_text', 'cta', 'comments', 
        'cover_image_url', 'etsy_description', 'etsy_listing_title', 
        'etsy_price', 'etsy_quantity', 'etsy_sku', 'instagram_first_comment',
        'pinterest_hashtags', 'links', 'media_source', 'media_urls', 
        'pin_board_fb_album_google_category', 'pinterest_description', 
        'pinterest_link_url', 'reminder', 'seo_description', 'seo_tags', 
        'seo_title', 'text', 'video_pin_pdf_title', 'calendar_selection', 
        'collection_id'
    ]
    
    for field in updates.keys():
        if field not in valid_fields:
            return jsonify({'error': f'Invalid field: {field}'}), 400
    
    try:
        for image_id in image_ids:
            image = Image.query.get(image_id)
            if image:
                for field, value in updates.items():
                    setattr(image, field, value)
        
        db.session.commit()
        return jsonify({'success': True, 'updated_count': len(image_ids)}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/generate_content/<int:image_id>', methods=['POST'])
def generate_content(image_id):
    """Generate AI content for a specific image using vision analysis"""
    image = Image.query.get(image_id)
    if not image:
        return jsonify({'error': 'Image not found'}), 404
    
    data = request.get_json() or {}
    platform = data.get('platform', 'all')
    
    try:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.stored_filename)
        
        if not os.path.exists(image_path):
            return jsonify({'error': 'Image file not found'}), 404
        
        # Pull materials, size, and artist_note from collection if available
        materials = None
        size = None
        artist_note = None
        
        if image.collection_id:
            collection = Collection.query.get(image.collection_id)
            if collection:
                materials = collection.materials
                size = collection.size
                artist_note = collection.artist_note
        
        content = gpt_service.analyze_image_and_generate_content(
            image_path=image_path,
            painting_name=image.painting_name or 'Untitled Artwork',
            platform=platform,
            materials=materials,
            size=size,
            artist_note=artist_note
        )
        
        for field, value in content.items():
            if hasattr(image, field) and value:
                setattr(image, field, value)
        
        db.session.commit()
        return jsonify(image.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/remove_image/<int:image_id>', methods=['POST', 'DELETE'])
def remove_image(image_id):
    """
    Delete an image entry with optional mode selection.
    Supports two modes:
    - 'full' (default): Delete entire entry including all related data
    - 'media_only': Remove only the image file, keep the database entry
    """
    image = Image.query.get(image_id)
    if not image:
        return jsonify({'error': 'Image not found'}), 404
    
    data = request.get_json() if request.is_json else {}
    mode = data.get('mode', 'full')
    
    service = get_image_asset_service()
    if mode == 'media_only':
        result = service.remove_media_only(image)
    else:
        result = service.delete_entry(image, cleanup_related=True)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 500

@app.route('/images/<int:image_id>/file', methods=['PUT', 'POST'])
def replace_image_file(image_id):
    """
    Replace an image file while keeping all metadata intact.
    Accepts a new file upload and swaps the file, preserving all content,
    schedules, and related data.
    """
    image = Image.query.get(image_id)
    if not image:
        return jsonify({'error': 'Image not found'}), 404
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    new_file = request.files['file']
    if not new_file or new_file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    service = get_image_asset_service()
    result = service.replace_file(image, new_file)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 400

@app.route('/delete_empty_slots', methods=['POST'])
@app.route('/delete_all_empty_slots', methods=['POST'])
def delete_all_empty_slots():
    """Delete all calendar slot placeholders (To Be Assigned items)"""
    try:
        # Find all placeholder slots
        empty_slots = Image.query.filter(
            Image.painting_name == 'To Be Assigned',
            Image.original_filename == '[Calendar Slot]'
        ).all()
        
        count = len(empty_slots)
        
        # Also reset calendar events
        for slot in empty_slots:
            if slot.calendar_event_id:
                event = CalendarEvent.query.get(slot.calendar_event_id)
                if event:
                    event.is_assigned = False
                    event.assigned_image_id = None
                    event.assigned_platform = None
        
        # Delete the placeholder images
        for slot in empty_slots:
            db.session.delete(slot)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'deleted_count': count,
            'message': f'Deleted {count} empty calendar slots and reset calendar events'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/bulk_delete', methods=['POST'])
def bulk_delete():
    """
    Delete multiple selected items by their IDs.
    Supports mode selection (default: 'full' with complete cleanup)
    """
    data = request.get_json()
    if not data or 'ids' not in data:
        return jsonify({'error': 'No IDs provided'}), 400
    
    ids = data['ids']
    if not isinstance(ids, list) or len(ids) == 0:
        return jsonify({'error': 'Invalid IDs list'}), 400
    
    mode = data.get('mode', 'full')
    cleanup_related = (mode == 'full')
    
    service = get_image_asset_service()
    result = service.bulk_delete_entries(ids, cleanup_related=cleanup_related)
    
    if result['success']:
        return jsonify(result), 200
    else:
        return jsonify(result), 500

@app.route('/reset_calendar_events', methods=['POST'])
def reset_calendar_events():
    """Reset all calendar events to unassigned state so they can be reused"""
    try:
        # Reset all calendar events
        events = CalendarEvent.query.all()
        reset_count = 0
        
        for event in events:
            if event.is_assigned:
                event.is_assigned = False
                event.assigned_image_id = None
                event.assigned_platform = None
                reset_count += 1
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'reset_count': reset_count,
            'message': f'Reset {reset_count} calendar events to unassigned state'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/collections', methods=['GET'])
def get_collections():
    """Get all collections"""
    try:
        collections = Collection.query.order_by(Collection.created_at.desc()).all()
        return jsonify([col.to_dict() for col in collections])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/collections', methods=['POST'])
def create_collection():
    """Create a new collection"""
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({'error': 'Collection name is required'}), 400
    
    try:
        collection = Collection()
        collection.name = data['name']
        collection.description = data.get('description', '')
        collection.materials = data.get('materials', '')
        collection.size = data.get('size', '')
        collection.artist_note = data.get('artist_note', '')
        collection.thumbnail_image_id = data.get('thumbnail_image_id')
        
        db.session.add(collection)
        db.session.commit()
        
        return jsonify(collection.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/collections/<int:collection_id>', methods=['PUT'])
def update_collection(collection_id):
    """Update a collection"""
    collection = Collection.query.get(collection_id)
    if not collection:
        return jsonify({'error': 'Collection not found'}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    try:
        if 'name' in data:
            collection.name = data['name']
        if 'description' in data:
            collection.description = data['description']
        if 'thumbnail_image_id' in data:
            collection.thumbnail_image_id = data['thumbnail_image_id']
        if 'mockup_template_ids' in data:
            collection.mockup_template_ids = json.dumps(data['mockup_template_ids'])
        
        db.session.commit()
        return jsonify(collection.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/collections/<int:collection_id>', methods=['DELETE'])
def delete_collection(collection_id):
    """Delete a collection (images are preserved, collection_id set to null)"""
    collection = Collection.query.get(collection_id)
    if not collection:
        return jsonify({'error': 'Collection not found'}), 404
    
    try:
        Image.query.filter_by(collection_id=collection_id).update({'collection_id': None})
        db.session.delete(collection)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Collection deleted successfully'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/collections/<int:collection_id>/images', methods=['GET'])
def get_collection_images(collection_id):
    """Get all images in a collection"""
    collection = Collection.query.get(collection_id)
    if not collection:
        return jsonify({'error': 'Collection not found'}), 404
    
    try:
        images = Image.query.filter_by(collection_id=collection_id).order_by(Image.created_at.desc()).all()
        return jsonify([img.to_dict() for img in images])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/calendars', methods=['GET'])
def get_calendars():
    """Get all calendars"""
    try:
        calendars = Calendar.query.all()
        return jsonify([cal.to_dict() for cal in calendars])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/calendar_events_all', methods=['GET'])
def get_all_calendar_events():
    """Get all calendar events grouped by calendar type"""
    try:
        calendar_types = ['AB', 'YP', 'POF']
        result = {}
        
        for cal_type in calendar_types:
            calendar = Calendar.query.filter_by(calendar_type=cal_type).first()
            if calendar:
                events = CalendarEvent.query.filter_by(calendar_id=calendar.id).order_by(CalendarEvent.midpoint_time).all()
                result[cal_type] = {
                    'calendar_name': calendar.calendar_name,
                    'total_events': len(events),
                    'available': sum(1 for e in events if not e.is_assigned),
                    'assigned': sum(1 for e in events if e.is_assigned),
                    'events': [{
                        'id': e.id,
                        'summary': e.summary,
                        'date': e.midpoint_time.strftime('%Y-%m-%d'),
                        'time': e.midpoint_time.strftime('%H:%M'),
                        'datetime': e.midpoint_time.isoformat(),
                        'is_assigned': e.is_assigned,
                        'assigned_platform': e.assigned_platform,
                        'assigned_image_id': e.assigned_image_id
                    } for e in events]
                }
            else:
                result[cal_type] = {
                    'calendar_name': None,
                    'total_events': 0,
                    'available': 0,
                    'assigned': 0,
                    'events': []
                }
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/calendar/import', methods=['POST'])
def import_calendar():
    """Import .ics calendar file"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    calendar_type = request.form.get('calendar_type', 'default')
    calendar_name = request.form.get('calendar_name', file.filename if file.filename else 'Calendar')
    
    if not file or file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    try:
        content = file.read().decode('utf-8')
        events = parse_ics_content(content)
        
        existing_calendar = Calendar.query.filter_by(calendar_type=calendar_type).first()
        if existing_calendar:
            CalendarEvent.query.filter_by(calendar_id=existing_calendar.id).delete()
            calendar = existing_calendar
            calendar.calendar_name = calendar_name
        else:
            calendar = Calendar()
            calendar.calendar_type = calendar_type
            calendar.calendar_name = calendar_name
            db.session.add(calendar)
            db.session.flush()
        
        for event_data in events:
            event = CalendarEvent()
            event.calendar_id = calendar.id
            event.summary = event_data['summary']
            event.start_time = event_data['start_time']
            event.end_time = event_data['end_time']
            event.midpoint_time = event_data['midpoint_time']
            event.event_type = event_data['event_type']
            db.session.add(event)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'calendar': calendar.to_dict(),
            'event_count': len(events)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/calendar/<int:calendar_id>/events', methods=['GET'])
def get_calendar_events(calendar_id):
    """Get all events for a calendar"""
    try:
        events = CalendarEvent.query.filter_by(calendar_id=calendar_id, is_assigned=False).order_by(CalendarEvent.midpoint_time).all()
        return jsonify([event.to_dict() for event in events])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/calendar/<int:calendar_id>', methods=['DELETE'])
def delete_calendar(calendar_id):
    """Delete a calendar and all its events"""
    try:
        calendar = Calendar.query.get(calendar_id)
        if not calendar:
            return jsonify({'error': 'Calendar not found'}), 404
        
        CalendarEvent.query.filter_by(calendar_id=calendar_id).delete()
        db.session.delete(calendar)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Calendar deleted'}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/generate_calendar', methods=['POST'])
def generate_calendar():
    """Generate empty calendar schedule for ALL available days with optional exclusions"""
    from datetime import datetime, timedelta
    from services.smart_scheduler import SmartScheduler
    import random
    
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    # Check for existing unassigned "To Be Assigned" posts
    force_regenerate = data.get('force_regenerate', False)
    existing_placeholders = Image.query.filter_by(painting_name='To Be Assigned').count()
    
    if existing_placeholders > 0 and not force_regenerate:
        return jsonify({
            'error': 'calendar_exists',
            'message': f'Found {existing_placeholders} unassigned calendar slots. Delete them first or confirm to overwrite.',
            'count': existing_placeholders
        }), 409
    
    # Get date range
    start_date_str = data.get('start_date')
    end_date_str = data.get('end_date')
    
    if not start_date_str or not end_date_str:
        return jsonify({'error': 'start_date and end_date are required'}), 400
    
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    
    # Parse and validate excluded dates
    excluded_dates = set()
    if 'exclude_dates' in data and data['exclude_dates']:
        for date_str in data['exclude_dates']:
            try:
                parsed = datetime.strptime(date_str.strip(), '%Y-%m-%d')
                excluded_dates.add(parsed.strftime('%Y-%m-%d'))
            except ValueError:
                return jsonify({'error': f'Invalid date format: {date_str}. Use YYYY-MM-DD'}), 400
    
    config = {
        'instagram_limit': data.get('instagram_limit', 2),
        'pinterest_limit': data.get('pinterest_limit', 2),
        'strategy': data.get('strategy', 'fill_all'),
        'min_spacing': data.get('min_spacing', 180)
    }
    
    # Optimal posting times when no astrology events exist (5am-10pm range, natural varied times)
    optimal_times = [
        '05:30', '06:45', '07:20', '08:15', '09:30', '10:45',
        '11:20', '12:30', '13:45', '14:20', '15:30', '16:45',
        '17:20', '18:30', '19:45', '20:15', '21:30', '21:45'
    ]
    
    try:
        # Get all unassigned events from AB, YP, POF calendars grouped by date and type
        calendar_types = ['AB', 'YP', 'POF']
        events_by_date_and_type = {}
        
        for cal_type in calendar_types:
            calendar = Calendar.query.filter_by(calendar_type=cal_type).first()
            if calendar:
                events = CalendarEvent.query.filter_by(
                    calendar_id=calendar.id,
                    is_assigned=False
                ).order_by(CalendarEvent.midpoint_time).all()
                for event in events:
                    event._calendar_type = cal_type
                    event_date = event.midpoint_time.strftime('%Y-%m-%d')
                    if event_date not in events_by_date_and_type:
                        events_by_date_and_type[event_date] = {'AB': [], 'YP': [], 'POF': []}
                    events_by_date_and_type[event_date][cal_type].append(event)
        
        created_slots = []
        import uuid
        
        # Validate date range
        if start_date > end_date:
            return jsonify({'error': 'Start date must be before or equal to end date'}), 400
        
        days_in_range = (end_date - start_date).days + 1
        if days_in_range > 365:
            return jsonify({'error': 'Date range too large (max 365 days)'}), 400
        
        # Iterate through each day in the range
        current_date = start_date
        while current_date <= end_date:
            date_str = current_date.strftime('%Y-%m-%d')
            
            # Skip excluded dates
            if date_str in excluded_dates:
                current_date += timedelta(days=1)
                continue
            
            # Get events for this day grouped by type with priority: AB first, then YP/POF
            day_events_by_type = events_by_date_and_type.get(date_str, {'AB': [], 'YP': [], 'POF': []})
            
            # Create prioritized event pool: AB events first, then mix YP and POF
            import random as rand
            prioritized_events = []
            prioritized_events.extend(day_events_by_type['AB'])  # AB events first
            
            # Mix YP and POF events with equal priority
            yp_pof_mixed = day_events_by_type['YP'] + day_events_by_type['POF']
            rand.shuffle(yp_pof_mixed)
            prioritized_events.extend(yp_pof_mixed)
            
            day_slots = []  # Track slots for spacing
            platform_counts = {'Instagram': 0, 'Pinterest': 0}  # Track per-platform counts
            has_any_astrology_events = len(prioritized_events) > 0
            
            # Try to create slots for this day
            for platform, limit in [('Instagram', config['instagram_limit']), ('Pinterest', config['pinterest_limit'])]:
                slots_created = 0
                
                while slots_created < limit:
                    event = None
                    calendar_source = 'General'
                    time_str = None
                    event_id = None
                    
                    # Try to use astrology event first (prioritized: AB, then YP/POF)
                    if prioritized_events and not time_str:
                        # Peek at first event without popping
                        candidate_event = prioritized_events[0]
                        calendar_source = candidate_event._calendar_type
                        candidate_time = candidate_event.midpoint_time.strftime('%H:%M')
                        
                        # Check spacing for astrology events
                        time_valid = True
                        candidate_mins = int(candidate_time.split(':')[0]) * 60 + int(candidate_time.split(':')[1])
                        for slot in day_slots:
                            slot_mins = int(slot['time'].split(':')[0]) * 60 + int(slot['time'].split(':')[1])
                            if abs(candidate_mins - slot_mins) < config['min_spacing']:
                                time_valid = False
                                break
                        
                        if time_valid:
                            # Accept this astrology event - now pop it permanently
                            event = prioritized_events.pop(0)
                            time_str = candidate_time
                            event_id = event.id
                        else:
                            # Conflict - remove from prioritized_events to avoid retrying
                            prioritized_events.pop(0)
                    
                    # If no astrology events at all for this day and strategy is 'fill_all', use synthetic time
                    if not time_str and config['strategy'] == 'fill_all' and not has_any_astrology_events:
                        # Pick random optimal time that doesn't conflict with spacing
                        available_times = optimal_times.copy()
                        random.shuffle(available_times)
                        
                        for test_time in available_times:
                            # Check spacing against existing day slots
                            conflict = False
                            test_mins = int(test_time.split(':')[0]) * 60 + int(test_time.split(':')[1])
                            
                            for slot in day_slots:
                                slot_mins = int(slot['time'].split(':')[0]) * 60 + int(slot['time'].split(':')[1])
                                if abs(test_mins - slot_mins) < config['min_spacing']:
                                    conflict = True
                                    break
                            
                            if not conflict:
                                time_str = test_time
                                calendar_source = 'General'
                                break
                    
                    # Stop if we couldn't find a valid time
                    if not time_str:
                        break
                    
                    # Create slot
                    unique_id = str(uuid.uuid4())[:8]
                    placeholder = Image(
                        original_filename='[Calendar Slot]',
                        stored_filename=f'calendar_slot_{unique_id}',
                        title='[Empty Slot]',
                        painting_name='To Be Assigned',
                        platform=platform,
                        date=date_str,
                        time=time_str,
                        calendar_selection=calendar_source,
                        calendar_event_id=event_id,
                        status='Draft'
                    )
                    db.session.add(placeholder)
                    db.session.flush()
                    
                    # Mark astrology event as assigned if used
                    if event:
                        event.is_assigned = True
                        event.assigned_image_id = placeholder.id
                        event.assigned_platform = platform
                    
                    day_slots.append({'time': time_str, 'platform': platform, 'source': calendar_source})
                    created_slots.append({
                        'id': placeholder.id,
                        'platform': platform,
                        'date': date_str,
                        'time': time_str,
                        'calendar_source': calendar_source
                    })
                    
                    platform_counts[platform] += 1
                    slots_created += 1
            
            current_date += timedelta(days=1)
        
        db.session.commit()
        
        # Group slots by date for day-by-day view
        from collections import defaultdict
        from datetime import datetime, time as time_obj
        slots_by_day = defaultdict(list)
        
        for slot in created_slots:
            date_key = slot['date']
            # Parse time for proper sorting (HH:MM format)
            time_parts = slot['time'].split(':')
            time_sort_key = int(time_parts[0]) * 60 + int(time_parts[1])
            
            slots_by_day[date_key].append({
                'time': slot['time'],
                'time_sort_key': time_sort_key,
                'platform': slot['platform'],
                'calendar_source': slot['calendar_source']
            })
        
        # Sort each day's slots by time and sort days chronologically
        schedule_by_day = []
        for date_str in sorted(slots_by_day.keys()):
            day_slots = sorted(slots_by_day[date_str], key=lambda x: x['time_sort_key'])
            # Remove sort key from final output
            for slot in day_slots:
                del slot['time_sort_key']
            schedule_by_day.append({
                'date': date_str,
                'slots': day_slots
            })
        
        # Compute summary
        summary = {
            'Instagram': sum(1 for s in created_slots if s['platform'] == 'Instagram'),
            'Pinterest': sum(1 for s in created_slots if s['platform'] == 'Pinterest'),
            'AB': sum(1 for s in created_slots if s['calendar_source'] == 'AB'),
            'YP': sum(1 for s in created_slots if s['calendar_source'] == 'YP'),
            'POF': sum(1 for s in created_slots if s['calendar_source'] == 'POF'),
            'General': sum(1 for s in created_slots if s['calendar_source'] == 'General')
        }
        
        return jsonify({
            'success': True,
            'created_count': len(created_slots),
            'excluded_dates': list(excluded_dates),
            'slots': created_slots,
            'schedule_by_day': schedule_by_day,
            'summary': summary
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/generate_from_selected', methods=['POST'])
def generate_from_selected():
    """Generate slots from specific cherry-picked calendar events"""
    from services.smart_scheduler import SmartScheduler
    
    data = request.get_json()
    if not data or 'event_ids' not in data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    event_ids = data.get('event_ids', [])
    if not event_ids:
        return jsonify({'error': 'No events selected'}), 400
    
    config = {
        'instagram_limit': data.get('instagram_limit', 2),
        'pinterest_limit': data.get('pinterest_limit', 7),
        'strategy': data.get('strategy', 'fill_all'),
        'min_spacing': data.get('min_spacing', 30)
    }
    
    try:
        # Get selected events
        selected_events = CalendarEvent.query.filter(
            CalendarEvent.id.in_(event_ids),
            CalendarEvent.is_assigned == False
        ).order_by(CalendarEvent.midpoint_time).all()
        
        if not selected_events:
            return jsonify({'error': 'No valid unassigned events found'}), 400
        
        # Determine calendar type for each event
        for event in selected_events:
            calendar = Calendar.query.get(event.calendar_id)
            if calendar:
                event._calendar_type = calendar.calendar_type
        
        # Create dummy IDs
        dummy_ids = list(range(1, len(selected_events) + 1))
        
        # Use scheduler
        scheduler = SmartScheduler(config)
        scheduler.events_by_calendar = {
            'AB': [e for e in selected_events if hasattr(e, '_calendar_type') and e._calendar_type == 'AB'],
            'YP': [e for e in selected_events if hasattr(e, '_calendar_type') and e._calendar_type == 'YP'],
            'POF': [e for e in selected_events if hasattr(e, '_calendar_type') and e._calendar_type == 'POF']
        }
        
        result = scheduler.assign_times(dummy_ids, preview=True, use_provided_events=True)
        
        # Create placeholder records
        created_slots = []
        import uuid
        for assignment in result['assignments']:
            # Generate unique stored_filename to avoid UNIQUE constraint errors
            unique_id = str(uuid.uuid4())[:8]
            placeholder = Image(
                original_filename='[Calendar Slot]',
                stored_filename=f'calendar_slot_{unique_id}',
                title='[Empty Slot]',
                painting_name='To Be Assigned',
                platform=assignment['platform'],
                date=assignment['date'],
                time=assignment['time'],
                calendar_source=assignment['calendar_source'],
                calendar_event_id=assignment['event_id'],
                status='Draft'
            )
            db.session.add(placeholder)
            db.session.flush()
            
            # Mark event as assigned
            event = CalendarEvent.query.get(assignment['event_id'])
            if event:
                event.is_assigned = True
                event.assigned_image_id = placeholder.id
                event.assigned_platform = assignment['platform']
            
            created_slots.append({
                'id': placeholder.id,
                'platform': assignment['platform'],
                'date': assignment['date'],
                'time': assignment['time'],
                'calendar_source': assignment['calendar_source']
            })
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'created_count': len(created_slots),
            'selected_count': len(selected_events),
            'slots': created_slots,
            'summary': result['summary']
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/assign_times_smart', methods=['POST'])
def assign_times_smart():
    """Smart scheduler - assign times with platform limits and calendar priority"""
    from services.smart_scheduler import SmartScheduler
    
    data = request.get_json()
    if not data or 'image_ids' not in data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    config = {
        'instagram_limit': data.get('instagram_limit', 2),
        'pinterest_limit': data.get('pinterest_limit', 7),
        'strategy': data.get('strategy', 'fill_all'),
        'min_spacing': data.get('min_spacing', 30)
    }
    
    preview = data.get('preview', False)
    
    try:
        scheduler = SmartScheduler(config)
        result = scheduler.assign_times(data['image_ids'], preview=preview)
        
        return jsonify({
            'success': True,
            'result': result
        }), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/assign_times', methods=['POST'])
def assign_times():
    """Assign calendar times to selected images"""
    data = request.get_json()
    if not data or 'image_ids' not in data or 'calendar_type' not in data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    image_ids = data['image_ids']
    calendar_type = data['calendar_type']
    
    try:
        calendar = Calendar.query.filter_by(calendar_type=calendar_type).first()
        if not calendar:
            return jsonify({'error': 'Calendar not found'}), 404
        
        available_events = CalendarEvent.query.filter_by(
            calendar_id=calendar.id,
            is_assigned=False
        ).order_by(CalendarEvent.midpoint_time).all()
        
        if not available_events:
            return jsonify({'error': 'No available time slots in this calendar'}), 400
        
        assigned_count = 0
        for i, image_id in enumerate(image_ids):
            image = Image.query.get(image_id)
            if image and i < len(available_events):
                event = available_events[i]
                midpoint = event.midpoint_time
                
                image.date = midpoint.strftime('%Y-%m-%d')
                image.time = midpoint.strftime('%H:%M')
                image.calendar_selection = calendar_type
                
                event.is_assigned = True
                assigned_count += 1
        
        db.session.commit()
        return jsonify({
            'success': True,
            'assigned_count': assigned_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/export', methods=['GET'])
def export_csv():
    """Export all content to Publer-compatible CSV format (12-column format)"""
    import os
    images = Image.query.filter(
        (Image.stored_filename != None) & (Image.stored_filename != '')
    ).order_by(Image.date, Image.time).all()
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Date',
        'Text',
        'Link',
        'Media URLs',
        'Title',
        'Labels',
        'Alt text',
        'Comments',
        'Pin Board/Facebook Album/Google Category',
        'Subtype',
        'CTA',
        'Reminder'
    ])
    
    replit_domain = os.environ.get('REPLIT_DEV_DOMAIN', '')
    if replit_domain:
        base_url = f"http://{replit_domain}"
    else:
        base_url = request.host_url.rstrip('/').replace('https://', 'http://')
    
    for image in images:
        if not image.date or not image.time:
            continue
            
        datetime_str = f"{image.date} {image.time}"
        media_url = f"{base_url}/static/uploads/{image.stored_filename}"
        
        text_content = image.text or ''
        if image.platform == 'Pinterest' and image.pinterest_description:
            text_content = image.pinterest_description
        
        writer.writerow([
            datetime_str,
            text_content,
            image.links or '',
            media_url,
            image.painting_name or image.video_pin_pdf_title or '',
            image.calendar_selection or '',
            image.alt_text or '',
            image.instagram_first_comment or image.comments or '',
            image.pin_board_fb_album_google_category or '',
            image.post_subtype or '',
            image.cta or '',
            image.reminder or ''
        ])
    
    output_string = output.getvalue()
    output.close()
    
    return send_file(
        BytesIO(output_string.encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='publer_all_content.csv'
    )

@app.route('/export_calendar/<int:calendar_id>', methods=['GET'])
def export_calendar(calendar_id):
    """Export calendar events to CSV with midpoint times"""
    calendar = Calendar.query.get(calendar_id)
    if not calendar:
        return jsonify({'error': 'Calendar not found'}), 404
    
    events = CalendarEvent.query.filter_by(calendar_id=calendar_id).order_by(CalendarEvent.midpoint_time).all()
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Calendar Type',
        'Event Summary',
        'Date',
        'Time',
        'Start Time',
        'End Time',
        'Status'
    ])
    
    for event in events:
        status = 'Assigned' if event.is_assigned else 'Available'
        
        writer.writerow([
            calendar.calendar_type,
            event.summary or '',
            event.midpoint_time.strftime('%Y-%m-%d'),
            event.midpoint_time.strftime('%H:%M'),
            event.start_time.strftime('%Y-%m-%d %H:%M'),
            event.end_time.strftime('%Y-%m-%d %H:%M'),
            status
        ])
    
    output_string = output.getvalue()
    output.close()
    
    filename = f'{calendar.calendar_type}_calendar_events.csv'
    
    return send_file(
        BytesIO(output_string.encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name=filename
    )


@app.route('/mockup-templates', methods=['GET'])
def get_mockup_templates():
    """Get available mockup templates from Dynamic Mockups"""
    try:
        service = DynamicMockupsService()
        templates = service.get_templates()
        return jsonify({'templates': templates}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/generate-mockups', methods=['POST'])
def generate_mockups():
    """Generate mockups for selected images using their collection's templates"""
    data = request.get_json()
    if not data or 'image_ids' not in data:
        return jsonify({'error': 'No image_ids provided'}), 400
    
    image_ids = data['image_ids']
    
    try:
        service = DynamicMockupsService()
        results = []
        
        for image_id in image_ids:
            image = Image.query.get(image_id)
            if not image:
                continue
            
            template_ids = []
            if image.collection_id:
                collection = Collection.query.get(image.collection_id)
                if collection and collection.mockup_template_ids:
                    try:
                        template_ids = json.loads(collection.mockup_template_ids)
                    except:
                        template_ids = []
            
            if not template_ids:
                results.append({
                    'image_id': image_id,
                    'error': 'No templates selected for this collection'
                })
                continue
            
            image_url = f"{request.host_url}static/uploads/{image.stored_filename}"
            
            mockups = service.generate_multiple_mockups(image_url, template_ids)
            
            for mockup in mockups:
                asset = GeneratedAsset(
                    image_id=image_id,
                    asset_type='mockup',
                    url=mockup['mockup_url'],
                    template_id=mockup['template_id']
                )
                db.session.add(asset)
            
            db.session.commit()
            
            results.append({
                'image_id': image_id,
                'mockups_generated': len(mockups)
            })
        
        return jsonify({'results': results}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/generate-video', methods=['POST'])
def generate_video():
    """Start async video generation for a single image using Pika 2.2"""
    data = request.get_json()
    if not data or 'image_id' not in data:
        return jsonify({'error': 'No image_id provided'}), 400
    
    image_id = data['image_id']
    prompt = data.get('prompt', 'camera slowly zooming in on the artwork, smooth cinematic movement')
    resolution = data.get('resolution', '720p')
    duration = data.get('duration', 5)
    
    try:
        image = Image.query.get(image_id)
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        image_url = f"{request.host_url}static/uploads/{image.stored_filename}"
        
        service = FalService()
        request_id = service.generate_video_async(image_url, prompt, resolution, duration)
        
        if not request_id:
            return jsonify({'error': 'Failed to start video generation'}), 500
        
        asset = GeneratedAsset(
            image_id=image_id,
            asset_type='video',
            url='',
            asset_metadata=json.dumps({
                'request_id': request_id,
                'prompt': prompt,
                'resolution': resolution,
                'duration': duration,
                'status': 'processing'
            })
        )
        db.session.add(asset)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'asset_id': asset.id,
            'request_id': request_id,
            'status': 'processing'
        }), 202
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/video-status/<int:asset_id>', methods=['GET'])
def check_video_status(asset_id):
    """Check the status of a video generation request"""
    try:
        asset = GeneratedAsset.query.get(asset_id)
        if not asset or asset.asset_type != 'video':
            return jsonify({'error': 'Video asset not found'}), 404
        
        metadata = json.loads(asset.asset_metadata) if asset.asset_metadata else {}
        request_id = metadata.get('request_id')
        
        if not request_id:
            return jsonify({'error': 'No request_id found'}), 400
        
        if asset.url:
            return jsonify({
                'status': 'completed',
                'video_url': asset.url
            }), 200
        
        service = FalService()
        status = service.check_video_status(request_id)
        
        if status['status'] == 'completed':
            asset.url = status['video_url']
            metadata['status'] = 'completed'
            metadata['video_url'] = status['video_url']
            asset.asset_metadata = json.dumps(metadata)
            db.session.commit()
            
            return jsonify({
                'status': 'completed',
                'video_url': status['video_url']
            }), 200
        
        elif status['status'] == 'failed':
            metadata['status'] = 'failed'
            metadata['error'] = status.get('error')
            asset.asset_metadata = json.dumps(metadata)
            db.session.commit()
            
            return jsonify({
                'status': 'failed',
                'error': status.get('error')
            }), 200
        
        elif status['status'] == 'error':
            metadata['status'] = 'error'
            metadata['error'] = status.get('error', 'Network or API error')
            asset.asset_metadata = json.dumps(metadata)
            db.session.commit()
            
            return jsonify({
                'status': 'error',
                'error': status.get('error', 'Network or API error')
            }), 200
        
        else:
            return jsonify({'status': 'processing'}), 200
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/generated-assets/<int:image_id>', methods=['GET'])
def get_generated_assets(image_id):
    """Get all generated assets (mockups, videos) for an image"""
    try:
        assets = GeneratedAsset.query.filter_by(image_id=image_id).all()
        return jsonify([asset.to_dict() for asset in assets]), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/schedule_grid', methods=['GET'])
def get_schedule_grid():
    """Get calendar events grouped by date with assignment information"""
    try:
        from datetime import datetime
        from collections import defaultdict
        
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        collection_id_str = request.args.get('collection_id')
        
        query = CalendarEvent.query
        
        if start_date_str:
            start_date = datetime.fromisoformat(start_date_str)
            query = query.filter(CalendarEvent.midpoint_time >= start_date)
        
        if end_date_str:
            end_date = datetime.fromisoformat(end_date_str)
            query = query.filter(CalendarEvent.midpoint_time <= end_date)
        
        events = query.order_by(CalendarEvent.midpoint_time).all()
        
        events_by_date = defaultdict(list)
        
        for event in events:
            date_key = event.midpoint_time.strftime('%Y-%m-%d')
            
            calendar = Calendar.query.get(event.calendar_id)
            
            assignments = EventAssignment.query.filter_by(calendar_event_id=event.id).all()
            total_assignment_count = len(assignments)
            
            assignment_data = []
            for assignment in assignments:
                image = Image.query.get(assignment.image_id)
                if image:
                    if collection_id_str and collection_id_str.isdigit():
                        if image.collection_id != int(collection_id_str):
                            continue
                    
                    assignment_data.append({
                        'assignment_id': assignment.id,
                        'image_id': image.id,
                        'painting_name': image.painting_name or image.original_filename,
                        'stored_filename': image.stored_filename,
                        'platform': assignment.platform
                    })
            
            event_data = {
                'event_id': event.id,
                'summary': event.summary,
                'time': event.midpoint_time.strftime('%H:%M'),
                'full_datetime': event.midpoint_time.isoformat(),
                'calendar_type': calendar.calendar_type if calendar else '',
                'assignments': assignment_data,
                'total_assignments': total_assignment_count,
                'available_slots': max(0, 3 - total_assignment_count)
            }
            
            events_by_date[date_key].append(event_data)
        
        result = []
        for date_key in sorted(events_by_date.keys()):
            result.append({
                'date': date_key,
                'events': events_by_date[date_key]
            })
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/assign', methods=['POST'])
def assign_content_to_event():
    """Assign content to a calendar event slot for one or more platforms"""
    try:
        data = request.get_json()
        event_id = data.get('event_id')
        image_id = data.get('image_id')
        platforms = data.get('platforms', [])
        
        if not event_id or not image_id:
            return jsonify({'error': 'Missing event_id or image_id'}), 400
        
        if not platforms or not isinstance(platforms, list):
            return jsonify({'error': 'platforms must be a non-empty array'}), 400
        
        event = CalendarEvent.query.get(event_id)
        if not event:
            return jsonify({'error': 'Calendar event not found'}), 404
        
        image = Image.query.get(image_id)
        if not image:
            return jsonify({'error': 'Image not found'}), 404
        
        created_assignments = []
        
        for platform in platforms:
            existing = EventAssignment.query.filter_by(
                calendar_event_id=event_id, 
                image_id=image_id, 
                platform=platform
            ).first()
            
            if existing:
                continue
            
            assignment = EventAssignment()
            assignment.calendar_event_id = event_id
            assignment.image_id = image_id
            assignment.platform = platform
            
            db.session.add(assignment)
            created_assignments.append(assignment)
        
        if created_assignments:
            image.date = event.midpoint_time.strftime('%Y-%m-%d')
            image.time = event.midpoint_time.strftime('%H:%M')
            calendar = Calendar.query.get(event.calendar_id)
            if calendar:
                image.calendar_source = calendar.calendar_type
            
            if image.status == 'Ready':
                image.status = 'Scheduled'
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'assignments': [a.to_dict() for a in created_assignments],
            'count': len(created_assignments),
            'already_assigned': len(platforms) - len(created_assignments)
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/assign/<int:assignment_id>', methods=['DELETE'])
def delete_assignment(assignment_id):
    """Unassign content from a calendar event"""
    try:
        assignment = EventAssignment.query.get(assignment_id)
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        image = Image.query.get(assignment.image_id)
        if image:
            other_assignments = EventAssignment.query.filter(
                EventAssignment.image_id == assignment.image_id,
                EventAssignment.id != assignment_id
            ).first()
            
            if not other_assignments:
                image.platform = None
                image.date = None
                image.time = None
                image.calendar_source = None
        
        db.session.delete(assignment)
        db.session.commit()
        
        return jsonify({'success': True}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/schedule/export_csv', methods=['POST'])
def export_schedule_csv():
    """Export selected calendar events to Publer-compatible CSV"""
    try:
        data = request.get_json() or {}
        event_ids = data.get('event_ids')
        
        if not event_ids or not isinstance(event_ids, list):
            return jsonify({'error': 'event_ids list required'}), 400
        
        events = CalendarEvent.query.filter(CalendarEvent.id.in_(event_ids)).order_by(CalendarEvent.midpoint_time).all()
        
        if not events:
            return jsonify({'error': 'No events found'}), 404
        
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'Date', 'Text', 'Link', 'Media URLs', 'Title', 'Labels', 
            'Alt text', 'Comments', 'Pin Board/Facebook Album/Google Category', 
            'Subtype', 'CTA', 'Reminder'
        ])
        
        for event in events:
            assignments = EventAssignment.query.filter_by(calendar_event_id=event.id).all()
            
            if assignments:
                for assignment in assignments:
                    image = Image.query.get(assignment.image_id)
                    if image:
                        text = image.text or image.instagram_first_comment or image.pinterest_description or ''
                        title = image.painting_name or image.title or ''
                        media_url = f"{request.url_root.rstrip('/')}/static/uploads/{image.stored_filename}"
                        calendar_label = event.calendar.calendar_type if event.calendar else 'Calendar'
                        
                        writer.writerow([
                            event.midpoint_time.strftime('%Y-%m-%d %H:%M'),
                            text,
                            '',
                            media_url,
                            title,
                            calendar_label,
                            image.alt_text or '',
                            image.comments or '',
                            image.pin_board_fb_album_google_category or '',
                            image.post_subtype or '',
                            image.cta or '',
                            'FALSE'
                        ])
            else:
                calendar_label = event.calendar.calendar_type if event.calendar else 'Calendar'
                writer.writerow([
                    event.midpoint_time.strftime('%Y-%m-%d %H:%M'),
                    '[Content placeholder] Add your artwork and description here',
                    '',
                    '',
                    '',
                    calendar_label,
                    '',
                    'Engage with this post!||What do you think?',
                    '',
                    '',
                    '',
                    'FALSE'
                ])
        
        output.seek(0)
        return send_file(
            BytesIO(output.getvalue().encode('utf-8')), 
            mimetype='text/csv', 
            as_attachment=True, 
            download_name='publer_schedule.csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/unassigned_images', methods=['GET'])
def get_unassigned_images():
    """Get images that haven't been assigned to any calendar slot"""
    try:
        collection_id = request.args.get('collection_id')
        
        query = Image.query
        
        if collection_id and collection_id.isdigit():
            query = query.filter_by(collection_id=int(collection_id))
        
        all_images = query.order_by(Image.created_at.desc()).all()
        
        assigned_image_ids = set(
            assignment.image_id 
            for assignment in EventAssignment.query.all()
        )
        
        unassigned_images = [
            {
                'id': img.id,
                'painting_name': img.painting_name or img.original_filename,
                'stored_filename': img.stored_filename,
                'collection_id': img.collection_id,
                'status': img.status
            }
            for img in all_images 
            if img.id not in assigned_image_ids
        ]
        
        return jsonify(unassigned_images), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/scheduled', methods=['GET'])
def get_scheduled_content():
    """Get all scheduled assignments with full details"""
    try:
        assignments = EventAssignment.query.all()
        
        result = []
        for assignment in assignments:
            image = Image.query.get(assignment.image_id)
            event = CalendarEvent.query.get(assignment.calendar_event_id)
            
            if not image or not event:
                continue
            
            calendar = Calendar.query.get(event.calendar_id) if event.calendar_id else None
            
            result.append({
                'assignment_id': assignment.id,
                'image_id': image.id,
                'image_name': image.painting_name or image.original_filename,
                'image_filename': image.stored_filename,
                'platform': assignment.platform,
                'event_date': event.midpoint_time.strftime('%Y-%m-%d'),
                'event_time': event.midpoint_time.strftime('%H:%M'),
                'event_summary': event.summary,
                'calendar_type': calendar.calendar_type if calendar else 'General'
            })
        
        result.sort(key=lambda x: (x['event_date'], x['event_time']))
        
        return jsonify({'assignments': result}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/schedule/export_scheduled_csv', methods=['GET'])
def export_scheduled_csv():
    """Export all scheduled content as Publer-compatible CSV with full 37-column format"""
    try:
        import os
        assignments = EventAssignment.query.all()
        
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'Date',
            'Text',
            'Link',
            'Media URLs',
            'Title',
            'Labels',
            'Alt text',
            'Comments',
            'Pin Board/Facebook Album/Google Category',
            'Subtype',
            'CTA',
            'Reminder'
        ])
        
        replit_domain = os.environ.get('REPLIT_DEV_DOMAIN', '')
        if replit_domain:
            base_url = f"http://{replit_domain}"
        else:
            base_url = request.host_url.rstrip('/').replace('https://', 'http://')
        
        rows = []
        for assignment in assignments:
            image = Image.query.get(assignment.image_id)
            event = CalendarEvent.query.get(assignment.calendar_event_id)
            
            if not image or not event:
                continue
            
            calendar = Calendar.query.get(event.calendar_id) if event.calendar_id else None
            calendar_type = calendar.calendar_type if calendar else 'General'
            
            collection_name = ''
            if image.collection_id:
                collection = Collection.query.get(image.collection_id)
                if collection:
                    collection_name = collection.name
            
            media_url = f"{base_url}/static/uploads/{image.stored_filename}"
            
            datetime_str = f"{event.midpoint_time.strftime('%Y-%m-%d')} {event.midpoint_time.strftime('%H:%M')}"
            
            text_content = image.text or ''
            if assignment.platform == 'Instagram' and image.instagram_first_comment:
                text_content = image.text or ''
            elif assignment.platform == 'Pinterest' and image.pinterest_description:
                text_content = image.pinterest_description
            
            rows.append({
                'datetime': event.midpoint_time,
                'row': [
                    datetime_str,
                    text_content,
                    image.links or '',
                    media_url,
                    image.painting_name or image.video_pin_pdf_title or '',
                    calendar_type,
                    image.alt_text or '',
                    image.instagram_first_comment or image.comments or '',
                    image.pin_board_fb_album_google_category or '',
                    image.post_subtype or '',
                    image.cta or '',
                    image.reminder or ''
                ]
            })
        
        rows.sort(key=lambda x: x['datetime'])
        
        for row in rows:
            writer.writerow(row['row'])
        
        output_string = output.getvalue()
        output.close()
        
        return send_file(
            BytesIO(output_string.encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name='publer_scheduled.csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/export_feedhive', methods=['GET'])
def export_feedhive_csv():
    """Export all content to FeedHive-compatible CSV format (6-column format)"""
    from datetime import datetime
    import os
    images = Image.query.filter(
        (Image.stored_filename != None) & (Image.stored_filename != '')
    ).order_by(Image.date, Image.time).all()
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Text',
        'Title',
        'Media URLs',
        'Labels',
        'Social Medias',
        'Scheduled',
        'Notes'
    ])
    
    replit_domain = os.environ.get('REPLIT_DEV_DOMAIN', '')
    if replit_domain:
        base_url = f"http://{replit_domain}"
    else:
        base_url = request.host_url.rstrip('/').replace('https://', 'http://')
    
    for image in images:
        if not image.date or not image.time:
            continue
        
        try:
            dt = datetime.strptime(f"{image.date} {image.time}", '%Y-%m-%d %H:%M')
            scheduled_iso = dt.strftime('%Y-%m-%dT%H:%M:%S.000Z')
        except:
            continue
        
        media_url = f"{base_url}/static/uploads/{image.stored_filename}"
        
        text_content = image.text or ''
        if image.platform == 'Pinterest' and image.pinterest_description:
            text_content = image.pinterest_description
        elif image.platform == 'Instagram' and image.text:
            text_content = image.text
        
        if image.platform == 'Pinterest':
            if image.pinterest_hashtags:
                text_content = text_content + '\n\n' + image.pinterest_hashtags if text_content else image.pinterest_hashtags
        elif image.platform == 'Instagram':
            if image.instagram_first_comment:
                text_content = text_content + '\n\n' + image.instagram_first_comment if text_content else image.instagram_first_comment
        else:
            if image.instagram_first_comment:
                text_content = text_content + '\n\n' + image.instagram_first_comment if text_content else image.instagram_first_comment
        
        platform_prefix = f"[{image.platform}] " if image.platform else ""
        title = f"{platform_prefix}{image.painting_name or image.video_pin_pdf_title or ''}"
        
        labels_list = []
        if image.platform:
            labels_list.append(image.platform)
        
        hashtag_field = image.pinterest_hashtags if image.platform == 'Pinterest' else image.instagram_first_comment
        if hashtag_field:
            hashtags_only = ' '.join([tag for tag in hashtag_field.split() if tag.startswith('#')])
            if hashtags_only:
                labels_list.append(hashtags_only)
        
        if image.seo_tags:
            labels_list.append(image.seo_tags)
        labels = ', '.join(labels_list) if labels_list else ''
        
        social_medias = ''
        
        notes = f"🔮 {image.calendar_selection}" if image.calendar_selection else ''
        
        writer.writerow([
            text_content,
            title,
            media_url,
            labels,
            social_medias,
            scheduled_iso,
            notes
        ])
    
    output_string = output.getvalue()
    output.close()
    
    return send_file(
        BytesIO(output_string.encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='feedhive_all_content.csv'
    )


@app.route('/schedule/export_scheduled_feedhive', methods=['GET'])
def export_scheduled_feedhive():
    """Export all scheduled content as FeedHive-compatible CSV (6-column format)"""
    from datetime import datetime
    import os
    try:
        assignments = EventAssignment.query.all()
        
        output = StringIO()
        writer = csv.writer(output)
        
        writer.writerow([
            'Text',
            'Title',
            'Media URLs',
            'Labels',
            'Social Medias',
            'Scheduled',
            'Notes'
        ])
        
        replit_domain = os.environ.get('REPLIT_DEV_DOMAIN', '')
        if replit_domain:
            base_url = f"http://{replit_domain}"
        else:
            base_url = request.host_url.rstrip('/').replace('https://', 'http://')
        
        rows = []
        for assignment in assignments:
            image = Image.query.get(assignment.image_id)
            event = CalendarEvent.query.get(assignment.calendar_event_id)
            
            if not image or not event:
                continue
            
            calendar = Calendar.query.get(event.calendar_id) if event.calendar_id else None
            calendar_type = calendar.calendar_type if calendar else 'General'
            
            media_url = f"{base_url}/static/uploads/{image.stored_filename}"
            
            scheduled_iso = event.midpoint_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
            
            text_content = image.text or ''
            if assignment.platform == 'Pinterest' and image.pinterest_description:
                text_content = image.pinterest_description
            elif assignment.platform == 'Instagram' and image.text:
                text_content = image.text
            
            if assignment.platform == 'Pinterest':
                if image.pinterest_hashtags:
                    text_content = text_content + '\n\n' + image.pinterest_hashtags if text_content else image.pinterest_hashtags
            elif assignment.platform == 'Instagram':
                if image.instagram_first_comment:
                    text_content = text_content + '\n\n' + image.instagram_first_comment if text_content else image.instagram_first_comment
            else:
                if image.instagram_first_comment:
                    text_content = text_content + '\n\n' + image.instagram_first_comment if text_content else image.instagram_first_comment
            
            platform_prefix = f"[{assignment.platform}] " if assignment.platform else ""
            title = f"{platform_prefix}{image.painting_name or image.video_pin_pdf_title or ''}"
            
            labels_list = []
            if assignment.platform:
                labels_list.append(assignment.platform)
            
            hashtag_field = image.pinterest_hashtags if assignment.platform == 'Pinterest' else image.instagram_first_comment
            if hashtag_field:
                hashtags_only = ' '.join([tag for tag in hashtag_field.split() if tag.startswith('#')])
                if hashtags_only:
                    labels_list.append(hashtags_only)
            
            if image.seo_tags:
                labels_list.append(image.seo_tags)
            labels = ', '.join(labels_list) if labels_list else ''
            
            social_medias = ''
            
            notes = f"🔮 {calendar_type}"
            
            rows.append({
                'datetime': event.midpoint_time,
                'row': [
                    text_content,
                    title,
                    media_url,
                    labels,
                    social_medias,
                    scheduled_iso,
                    notes
                ]
            })
        
        rows.sort(key=lambda x: x['datetime'])
        
        for row in rows:
            writer.writerow(row['row'])
        
        output_string = output.getvalue()
        output.close()
        
        return send_file(
            BytesIO(output_string.encode()),
            mimetype='text/csv',
            as_attachment=True,
            download_name='feedhive_scheduled.csv'
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/debug/images', methods=['GET'])
def debug_images():
    """Debug endpoint to check image records"""
    try:
        images = Image.query.order_by(Image.id.desc()).limit(20).all()
        
        result = []
        for img in images:
            result.append({
                'id': img.id,
                'painting_name': img.painting_name,
                'original_filename': img.original_filename,
                'stored_filename': img.stored_filename,
                'status': img.status,
                'has_file': bool(img.stored_filename)
            })
        
        empty_count = Image.query.filter(
            (Image.stored_filename == None) | (Image.stored_filename == '')
        ).count()
        
        return jsonify({
            'recent_images': result,
            'empty_records_count': empty_count
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/cleanup/empty_images', methods=['DELETE'])
def cleanup_empty_images():
    """Delete image records that have no actual file"""
    try:
        empty_images = Image.query.filter(
            (Image.stored_filename == None) | (Image.stored_filename == '')
        ).all()
        
        deleted_count = len(empty_images)
        
        for img in empty_images:
            db.session.delete(img)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'deleted_count': deleted_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/publer/test', methods=['GET'])
def test_publer_api():
    """Test Publer API connection and list available resources"""
    try:
        publer = PublerAPI()
        
        connection_test = publer.test_connection()
        accounts_result = publer.get_accounts()
        drafts_result = publer.get_drafts()
        
        return jsonify({
            'connection': connection_test,
            'accounts': accounts_result,
            'drafts': drafts_result
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/publer/create_test_draft', methods=['POST'])
def create_test_draft():
    """Create a test draft in Publer"""
    try:
        data = request.get_json()
        publer = PublerAPI()
        
        result = publer.create_draft(
            text=data.get('text', 'Test draft from Painting Content Planner'),
            account_ids=data.get('account_ids'),
            scheduled_time=data.get('scheduled_time'),
            is_public=data.get('is_public', False)
        )
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/publer/push_days', methods=['POST'])
def push_days_to_publer():
    """Push selected days with their assignments to Publer as drafts"""
    try:
        from datetime import datetime
        data = request.get_json()
        selected_dates = data.get('dates', [])
        
        if not selected_dates:
            return jsonify({'error': 'No dates selected'}), 400
        
        publer = PublerAPI()
        results = []
        draft_count = 0
        
        # Account IDs from the test results
        INSTAGRAM_ACCOUNT_ID = '690d1b4ebe32d2156db74a85'
        PINTEREST_ACCOUNT_ID = '690d29b4f0c7ea9a5833a3bb'
        
        # Get all assignments for the selected dates
        for date_str in selected_dates:
            events = CalendarEvent.query.filter(
                db.func.date(CalendarEvent.midpoint_time) == date_str
            ).all()
            
            for event in events:
                assignments = EventAssignment.query.filter_by(calendar_event_id=event.id).all()
                
                for assignment in assignments:
                    image = Image.query.get(assignment.image_id)
                    if not image:
                        continue
                    
                    # Skip placeholder calendar slots
                    if image.painting_name and '[Calendar Slot]' in image.painting_name:
                        print(f"DEBUG: Skipping placeholder slot: {image.painting_name}")
                        continue
                    
                    # Check if file exists
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], image.stored_filename)
                    if not os.path.exists(file_path):
                        print(f"DEBUG: File not found: {file_path}")
                        results.append({
                            'success': False,
                            'painting_name': image.painting_name or image.original_filename,
                            'platform': assignment.platform,
                            'scheduled_time': event.midpoint_time.isoformat(),
                            'error': 'Image file not found'
                        })
                        continue
                    
                    # Upload image to Publer
                    print(f"DEBUG: Uploading {file_path} to Publer")
                    upload_result = publer.upload_media(file_path)
                    
                    if not upload_result['success']:
                        print(f"DEBUG: Upload failed: {upload_result.get('error')}")
                        results.append({
                            'success': False,
                            'painting_name': image.painting_name or image.original_filename,
                            'platform': assignment.platform,
                            'scheduled_time': event.midpoint_time.isoformat(),
                            'error': upload_result['error']
                        })
                        continue
                    
                    media_id = upload_result['media'].get('id')
                    print(f"DEBUG: Media uploaded with ID: {media_id}")
                    
                    # Determine account ID based on platform
                    account_id = INSTAGRAM_ACCOUNT_ID if assignment.platform == 'instagram' else PINTEREST_ACCOUNT_ID
                    
                    # Get text content
                    text = ''
                    if assignment.platform == 'instagram':
                        text = image.text or image.instagram_first_comment or ''
                    elif assignment.platform == 'pinterest':
                        text = image.pinterest_description or image.text or ''
                    
                    # Create draft
                    draft_result = publer.create_scheduled_draft(
                        account_id=account_id,
                        scheduled_time=event.midpoint_time.isoformat(),
                        text=text,
                        media_ids=[media_id] if media_id else None,
                        network=assignment.platform,
                        is_public=True
                    )
                    
                    if draft_result['success']:
                        draft_count += 1
                        results.append({
                            'success': True,
                            'painting_name': image.painting_name or image.original_filename,
                            'platform': assignment.platform,
                            'scheduled_time': event.midpoint_time.strftime('%Y-%m-%d %H:%M')
                        })
                    else:
                        results.append({
                            'success': False,
                            'painting_name': image.painting_name or image.original_filename,
                            'platform': assignment.platform,
                            'scheduled_time': event.midpoint_time.strftime('%Y-%m-%d %H:%M'),
                            'error': draft_result['error']
                        })
        
        return jsonify({
            'success': True,
            'draft_count': draft_count,
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
