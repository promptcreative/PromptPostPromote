import os
from flask import render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from app import app, db
from models import Image, Calendar, CalendarEvent, Collection, GeneratedAsset
from utils import allowed_file, generate_unique_filename, parse_ics_content
from gpt_service import gpt_service
from dynamic_mockups_service import DynamicMockupsService
from fal_service import FalService
from io import StringIO, BytesIO
import csv
import json

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
        'links', 'media_source', 'media_urls', 'pin_board_fb_album_google_category',
        'pinterest_description', 'pinterest_link_url', 'reminder',
        'seo_description', 'seo_tags', 'seo_title', 'text', 'video_pin_pdf_title',
        'calendar_selection', 'collection_id'
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
        'links', 'media_source', 'media_urls', 'pin_board_fb_album_google_category',
        'pinterest_description', 'pinterest_link_url', 'reminder',
        'seo_description', 'seo_tags', 'seo_title', 'text', 'video_pin_pdf_title',
        'calendar_selection', 'collection_id'
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
    """Export to Publer-compatible CSV format with all required columns"""
    images = Image.query.order_by(Image.date, Image.time).all()
    
    output = StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'Collection',
        'Title',
        'Painting Name',
        'Materials',
        'Size',
        'Artist Note',
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
        collection_name = ''
        if image.collection_id:
            collection = Collection.query.get(image.collection_id)
            if collection:
                collection_name = collection.name
        
        writer.writerow([
            collection_name,
            image.title or '',
            image.painting_name or '',
            image.materials or '',
            image.size or '',
            image.artist_note or '',
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
