import os
import uuid
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
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

# Future cloud storage integration placeholder
"""
def upload_to_cloud_storage(file_path):
    # TODO: Implement cloud storage upload
    # For Google Drive:
    # from google.oauth2 import service_account
    # from googleapiclient.discovery import build
    pass

def download_from_cloud_storage(file_id):
    # TODO: Implement cloud storage download
    pass
"""
