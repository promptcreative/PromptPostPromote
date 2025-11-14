import os
from werkzeug.utils import secure_filename
from models import db, Image, GeneratedAsset, EventAssignment, CalendarEvent
from utils import generate_unique_filename, allowed_file


class ImageAssetService:
    """Service for managing image files and related database operations"""
    
    def __init__(self, upload_folder):
        self.upload_folder = upload_folder
    
    def replace_file(self, image, new_file):
        """
        Replace an image's file while preserving all metadata.
        
        Args:
            image: Image model instance
            new_file: FileStorage object from request.files
            
        Returns:
            dict: Result with success status and message
        """
        if not new_file or not allowed_file(new_file.filename):
            return {'success': False, 'error': 'Invalid file type'}
        
        new_file_path = None
        try:
            original_filename = secure_filename(new_file.filename)
            new_stored_filename = generate_unique_filename(original_filename)
            new_file_path = os.path.join(self.upload_folder, new_stored_filename)
            
            old_stored_filename = image.stored_filename
            old_file_path = os.path.join(self.upload_folder, old_stored_filename) if old_stored_filename else None
            
            new_file.save(new_file_path)
            
            image.original_filename = original_filename
            image.stored_filename = new_stored_filename
            image.media = new_stored_filename
            
            db.session.commit()
            
            if old_file_path and os.path.exists(old_file_path):
                try:
                    os.remove(old_file_path)
                except Exception as e:
                    print(f"Warning: Could not delete old file {old_file_path}: {e}")
            
            return {
                'success': True,
                'message': 'Image replaced successfully',
                'image': image.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            if new_file_path and os.path.exists(new_file_path):
                try:
                    os.remove(new_file_path)
                except:
                    pass
            return {'success': False, 'error': str(e)}
    
    def remove_media_only(self, image):
        """
        Remove only the image file, keeping the database entry.
        Useful for replacing an image later.
        
        Args:
            image: Image model instance
            
        Returns:
            dict: Result with success status and message
        """
        try:
            file_path = os.path.join(self.upload_folder, image.stored_filename) if image.stored_filename else None
            
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
            
            image.stored_filename = None
            image.media = None
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Image file removed (entry preserved)'
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def delete_entry(self, image, cleanup_related=True):
        """
        Delete an image entry completely, including file and optionally all related data.
        
        Args:
            image: Image model instance
            cleanup_related: If True, also clean up GeneratedAssets, EventAssignments, and reset CalendarEvents
            
        Returns:
            dict: Result with success status, message, and cleanup summary
        """
        try:
            cleanup_summary = {
                'generated_assets': 0,
                'event_assignments': 0,
                'calendar_events_reset': 0
            }
            
            if cleanup_related:
                generated_assets = GeneratedAsset.query.filter_by(image_id=image.id).all()
                cleanup_summary['generated_assets'] = len(generated_assets)
                for asset in generated_assets:
                    db.session.delete(asset)
                
                event_assignments = EventAssignment.query.filter_by(image_id=image.id).all()
                cleanup_summary['event_assignments'] = len(event_assignments)
                for assignment in event_assignments:
                    db.session.delete(assignment)
                
                if image.calendar_event_id:
                    event = CalendarEvent.query.get(image.calendar_event_id)
                    if event:
                        event.is_assigned = False
                        event.assigned_image_id = None
                        event.assigned_platform = None
                        cleanup_summary['calendar_events_reset'] += 1
            
            file_path = os.path.join(self.upload_folder, image.stored_filename) if image.stored_filename else None
            
            if file_path and os.path.exists(file_path) and image.original_filename != '[Calendar Slot]':
                os.remove(file_path)
            
            db.session.delete(image)
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Image and related data deleted successfully',
                'cleanup_summary': cleanup_summary
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def bulk_delete_entries(self, image_ids, cleanup_related=True):
        """
        Delete or clean multiple image entries based on mode.
        
        Args:
            image_ids: List of image IDs to process
            cleanup_related: If True, delete entire entries with related data.
                           If False, only remove media files (preserve entries)
            
        Returns:
            dict: Result with success status, count, and cleanup summary
        """
        try:
            images = Image.query.filter(Image.id.in_(image_ids)).all()
            count = len(images)
            
            total_cleanup = {
                'generated_assets': 0,
                'event_assignments': 0,
                'calendar_events_reset': 0
            }
            
            if cleanup_related:
                for image in images:
                    generated_assets = GeneratedAsset.query.filter_by(image_id=image.id).all()
                    total_cleanup['generated_assets'] += len(generated_assets)
                    for asset in generated_assets:
                        db.session.delete(asset)
                    
                    event_assignments = EventAssignment.query.filter_by(image_id=image.id).all()
                    total_cleanup['event_assignments'] += len(event_assignments)
                    for assignment in event_assignments:
                        db.session.delete(assignment)
                    
                    if image.calendar_event_id:
                        event = CalendarEvent.query.get(image.calendar_event_id)
                        if event:
                            event.is_assigned = False
                            event.assigned_image_id = None
                            event.assigned_platform = None
                            total_cleanup['calendar_events_reset'] += 1
                    
                    file_path = os.path.join(self.upload_folder, image.stored_filename) if image.stored_filename else None
                    if file_path and os.path.exists(file_path) and image.original_filename != '[Calendar Slot]':
                        os.remove(file_path)
                    
                    db.session.delete(image)
                
                message = f'Deleted {count} images with all related data'
            else:
                for image in images:
                    file_path = os.path.join(self.upload_folder, image.stored_filename) if image.stored_filename else None
                    if file_path and os.path.exists(file_path):
                        os.remove(file_path)
                    
                    image.stored_filename = None
                    image.media = None
                
                message = f'Removed image files from {count} entries (entries preserved)'
            
            db.session.commit()
            
            return {
                'success': True,
                'deleted_count': count if cleanup_related else 0,
                'media_removed_count': count if not cleanup_related else 0,
                'message': message,
                'cleanup_summary': total_cleanup
            }
            
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}
