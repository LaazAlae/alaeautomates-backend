###############################################################################
# CLEANUP MANAGER
# Automated file cleanup to manage storage
###############################################################################

import os
import shutil
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

logger = logging.getLogger(__name__)

class CleanupManager:
    """Manages automatic cleanup of temporary files"""
    
    def __init__(self):
        self.cleanup_folders = ['uploads', 'results', 'separate_results']
        self.max_file_age_hours = 24
        self.cleanup_interval_hours = 6
        self._cleanup_thread = None
        self._running = False
    
    def start_background_cleanup(self):
        """Start background cleanup thread"""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return
        
        self._running = True
        self._cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self._cleanup_thread.start()
        logger.info("Background file cleanup started")
    
    def stop_background_cleanup(self):
        """Stop background cleanup"""
        self._running = False
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=5)
    
    def _cleanup_loop(self):
        """Main cleanup loop"""
        while self._running:
            try:
                self.cleanup_old_files()
                time.sleep(self.cleanup_interval_hours * 3600)
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                time.sleep(3600)  # Wait an hour before retrying
    
    def cleanup_old_files(self) -> Dict[str, Any]:
        """Clean up old files"""
        stats = {
            'files_deleted': 0,
            'folders_cleaned': 0,
            'space_freed_mb': 0,
            'errors': []
        }
        
        cutoff_time = datetime.now() - timedelta(hours=self.max_file_age_hours)
        
        for folder in self.cleanup_folders:
            if not os.path.exists(folder):
                continue
            
            try:
                folder_stats = self._clean_folder(folder, cutoff_time)
                stats['files_deleted'] += folder_stats['files_deleted']
                stats['space_freed_mb'] += folder_stats['space_freed_mb']
                stats['folders_cleaned'] += 1
                
            except Exception as e:
                error_msg = f"Error cleaning {folder}: {e}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
        
        if stats['files_deleted'] > 0:
            logger.info(f"Cleanup completed: {stats['files_deleted']} files deleted, "
                       f"{stats['space_freed_mb']:.1f}MB freed")
        
        return stats
    
    def _clean_folder(self, folder_path: str, cutoff_time: datetime) -> Dict[str, Any]:
        """Clean files in a specific folder"""
        stats = {
            'files_deleted': 0,
            'space_freed_mb': 0
        }
        
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                
                try:
                    # Get file modification time
                    file_mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    if file_mtime < cutoff_time:
                        # Get file size before deletion
                        file_size = os.path.getsize(file_path)
                        
                        # Delete the file
                        os.remove(file_path)
                        
                        stats['files_deleted'] += 1
                        stats['space_freed_mb'] += file_size / (1024 * 1024)
                        
                except Exception as e:
                    logger.warning(f"Could not delete {file_path}: {e}")
            
            # Remove empty directories
            for dir_name in dirs:
                dir_path = os.path.join(root, dir_name)
                try:
                    if not os.listdir(dir_path):  # Empty directory
                        os.rmdir(dir_path)
                except Exception as e:
                    logger.debug(f"Could not remove empty directory {dir_path}: {e}")
        
        return stats
    
    def manual_cleanup(self) -> Dict[str, Any]:
        """Perform manual cleanup of all files"""
        stats = {
            'files_deleted': 0,
            'folders_cleaned': 0,
            'space_freed_mb': 0,
            'errors': []
        }
        
        for folder in self.cleanup_folders:
            if not os.path.exists(folder):
                continue
            
            try:
                # Get folder size before cleanup
                folder_size = self._get_folder_size(folder)
                
                # Remove all contents
                for root, dirs, files in os.walk(folder, topdown=False):
                    # Delete all files
                    for file in files:
                        file_path = os.path.join(root, file)
                        try:
                            os.remove(file_path)
                            stats['files_deleted'] += 1
                        except Exception as e:
                            stats['errors'].append(f"Could not delete {file_path}: {e}")
                    
                    # Remove subdirectories
                    for dir_name in dirs:
                        dir_path = os.path.join(root, dir_name)
                        try:
                            if dir_path != folder:  # Don't remove the main folder
                                os.rmdir(dir_path)
                        except Exception as e:
                            stats['errors'].append(f"Could not remove {dir_path}: {e}")
                
                stats['space_freed_mb'] += folder_size / (1024 * 1024)
                stats['folders_cleaned'] += 1
                
            except Exception as e:
                error_msg = f"Error during manual cleanup of {folder}: {e}"
                logger.error(error_msg)
                stats['errors'].append(error_msg)
        
        logger.info(f"Manual cleanup completed: {stats['files_deleted']} files deleted")
        return stats
    
    def _get_folder_size(self, folder_path: str) -> int:
        """Get total size of folder in bytes"""
        total_size = 0
        
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    total_size += os.path.getsize(file_path)
                except Exception:
                    continue
        
        return total_size
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Get current storage statistics"""
        stats = {
            'folders': {},
            'total_size_mb': 0,
            'total_files': 0
        }
        
        for folder in self.cleanup_folders:
            if not os.path.exists(folder):
                stats['folders'][folder] = {
                    'exists': False,
                    'size_mb': 0,
                    'file_count': 0
                }
                continue
            
            folder_size = self._get_folder_size(folder)
            file_count = sum(len(files) for _, _, files in os.walk(folder))
            
            stats['folders'][folder] = {
                'exists': True,
                'size_mb': round(folder_size / (1024 * 1024), 2),
                'file_count': file_count
            }
            
            stats['total_size_mb'] += folder_size / (1024 * 1024)
            stats['total_files'] += file_count
        
        stats['total_size_mb'] = round(stats['total_size_mb'], 2)
        return stats

# Global cleanup manager instance
cleanup_manager = CleanupManager()