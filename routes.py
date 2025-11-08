import os
from flask import render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from app import app, db
from models import Image, Calendar, CalendarEvent
from utils import allowed_file, generate_unique_filename, parse_ics_content
from gpt_service import gpt_service
from io import StringIO, BytesIO
import csv

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
        'title', 'painting_name', 'post_subtype', 'platform', 'date', 'time', 
        'status', 'labels', 'post_url', 'alt_text', 'cta', 'comments', 
        'cover_image_url', 'etsy_description', 'etsy_listing_title', 
        'etsy_price', 'etsy_quantity', 'etsy_sku', 'instagram_first_comment',
        'links', 'media_source', 'media_urls', 'pin_board_fb_album_google_category',
        'pinterest_description', 'pinterest_link_url', 'reminder',
        'seo_description', 'seo_tags', 'seo_title', 'text', 'video_pin_pdf_title',
        'calendar_selection'
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
        'title', 'painting_name', 'post_subtype', 'platform', 'date', 'time', 
        'status', 'labels', 'post_url', 'alt_text', 'cta', 'comments', 
        'cover_image_url', 'etsy_description', 'etsy_listing_title', 
        'etsy_price', 'etsy_quantity', 'etsy_sku', 'instagram_first_comment',
        'links', 'media_source', 'media_urls', 'pin_board_fb_album_google_category',
        'pinterest_description', 'pinterest_link_url', 'reminder',
        'seo_description', 'seo_tags', 'seo_title', 'text', 'video_pin_pdf_title',
        'calendar_selection'
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
        
        content = gpt_service.analyze_image_and_generate_content(
            image_path=image_path,
            painting_name=image.painting_name or 'Untitled Artwork',
            platform=platform
        )
        
        for field, value in content.items():
            if hasattr(image, field) and value:
                setattr(image, field, value)
        
        db.session.commit()
        return jsonify(image.to_dict()), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/remove_image/<int:image_id>', methods=['POST'])
def remove_image(image_id):
    image = Image.query.get(image_id)
    if not image:
        return jsonify({'error': 'Image not found'}), 404
        
    try:
        if app.static_folder and image.stored_filename:
            file_path = os.path.join(app.static_folder, 'uploads', image.stored_filename)
            if os.path.exists(file_path):
                os.remove(file_path)
            
        db.session.delete(image)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Image removed successfully'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to remove image: {str(e)}'}), 500

@app.route('/calendars', methods=['GET'])
def get_calendars():
    """Get all calendars"""
    try:
        calendars = Calendar.query.all()
        return jsonify([cal.to_dict() for cal in calendars])
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
    """Export to Publer-compatible CSV format with all required columns"""
    images = Image.query.order_by(Image.date, Image.time).all()
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Title',
        'Painting Name',
        'Post subtype',
        'Platform',
        'Date',
        'Time',
        'Status',
        'Label(s)',
        'Post URL',
        'Alt text(s)',
        'CTA',
        'Comment(s)',
        'Cover Image URL',
        'Etsy Description',
        'Etsy Listing Title',
        'Etsy Price',
        'Etsy Quantity',
        'Etsy SKU',
        'Instagram First Comment',
        'Link(s)',
        'Media',
        'Media Source',
        'Media URL(s)',
        'Pin board, FB album, or Google category',
        'Pinterest Description',
        'Pinterest Link URL',
        'Reminder',
        'SEO Description',
        'SEO Tags',
        'SEO Title',
        'Text',
        'Title - For the video, pin, PDF',
        'Calendar Selection'
    ])
    
    for image in images:
        writer.writerow([
            image.title or '',
            image.painting_name or '',
            image.post_subtype or '',
            image.platform or '',
            image.date or '',
            image.time or '',
            image.status or '',
            image.labels or '',
            image.post_url or '',
            image.alt_text or '',
            image.cta or '',
            image.comments or '',
            image.cover_image_url or '',
            image.etsy_description or '',
            image.etsy_listing_title or '',
            image.etsy_price or '',
            image.etsy_quantity or '',
            image.etsy_sku or '',
            image.instagram_first_comment or '',
            image.links or '',
            image.media or '',
            image.media_source or '',
            image.media_urls or '',
            image.pin_board_fb_album_google_category or '',
            image.pinterest_description or '',
            image.pinterest_link_url or '',
            image.reminder or '',
            image.seo_description or '',
            image.seo_tags or '',
            image.seo_title or '',
            image.text or '',
            image.video_pin_pdf_title or '',
            image.calendar_selection or ''
        ])
    
    output_string = output.getvalue()
    output.close()
    
    return send_file(
        BytesIO(output_string.encode()),
        mimetype='text/csv',
        as_attachment=True,
        download_name='publer_content.csv'
    )
