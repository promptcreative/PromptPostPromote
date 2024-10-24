import os
import csv
from io import StringIO
from flask import render_template, request, jsonify, send_file
from werkzeug.utils import secure_filename
from app import app, db
from models import Image
from utils import allowed_file, generate_unique_filename, generate_placeholder_content

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        original_filename = secure_filename(file.filename)
        stored_filename = generate_unique_filename(original_filename)
        
        # Save file
        file_path = os.path.join(app.static_folder, 'uploads', stored_filename)
        file.save(file_path)
        
        # Generate placeholder content
        description, hashtags = generate_placeholder_content(original_filename)
        
        # Save to database
        image = Image(
            original_filename=original_filename,
            stored_filename=stored_filename,
            description=description,
            hashtags=hashtags
        )
        db.session.add(image)
        db.session.commit()
        
        return jsonify(image.to_dict()), 200
    
    return jsonify({'error': 'Invalid file type'}), 400

@app.route('/images', methods=['GET'])
def get_images():
    images = Image.query.order_by(Image.created_at.desc()).all()
    return jsonify([img.to_dict() for img in images])

@app.route('/update/<int:image_id>', methods=['POST'])
def update_image(image_id):
    data = request.get_json()
    if not data or 'field' not in data or 'value' not in data:
        return jsonify({'error': 'Invalid request data'}), 400
    
    field = data['field']
    value = data['value']
    
    if field not in ['description', 'hashtags']:
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

@app.route('/export', methods=['GET'])
def export_csv():
    images = Image.query.all()
    
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(['Original Filename', 'Stored Filename', 'Description', 'Hashtags', 'Created At'])
    
    for image in images:
        cw.writerow([
            image.original_filename,
            image.stored_filename,
            image.description,
            image.hashtags,
            image.created_at
        ])
    
    output = si.getvalue()
    si.close()
    
    return send_file(
        StringIO(output),
        mimetype='text/csv',
        as_attachment=True,
        download_name='artwork_data.csv'
    )
