import os
import csv
from io import StringIO, BytesIO
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
            hashtags=hashtags,
            category=""  # Initialize empty category
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
    
    if field not in ['description', 'hashtags', 'category']:
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

@app.route('/generate_category_content', methods=['POST'])
def generate_category_content():
    data = request.get_json()
    if not data or 'category' not in data:
        return jsonify({'error': 'Category is required'}), 400
    
    category = data['category']
    if not category:
        return jsonify({'error': 'Category cannot be empty'}), 400
    
    try:
        # Get all images in the category
        images = Image.query.filter_by(category=category).all()
        if not images:
            return jsonify({'error': 'No images found in this category'}), 404
        
        # Update each image with generated content (placeholder for now)
        for image in images:
            # For now, using placeholder content
            image.description = f"Generated description for {image.original_filename} in category {category}"
            image.hashtags = f"#generated #{category.lower().replace(' ', '')} #artwork"
        
        db.session.commit()
        
        # Return updated images
        return jsonify({
            'success': True,
            'images': [img.to_dict() for img in images]
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/export', methods=['GET'])
def export_csv():
    images = Image.query.all()
    
    output = BytesIO()
    writer = csv.writer(output)
    writer.writerow(['Original Filename', 'Category', 'Stored Filename', 'Description', 'Hashtags', 'Created At'])
    
    for image in images:
        writer.writerow([
            image.original_filename,
            image.category,
            image.stored_filename,
            image.description,
            image.hashtags,
            image.created_at
        ])
    
    output.seek(0)
    return send_file(
        output,
        mimetype='text/csv',
        as_attachment=True,
        download_name='artwork_data.csv'
    )
