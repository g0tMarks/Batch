import os
import asyncio
from typing import Optional
from supabase_config import supabase
import logging

logger = logging.getLogger(__name__)

class StorageError(Exception):
    """Base exception for storage operations"""
    pass

class StorageService:
    def __init__(self, supabase_client):
        self.supabase = supabase_client

    def upload_file(self, local_path: str, bucket: str = "documents", user_id: str = None) -> str:
        """Upload a file to Supabase storage asynchronously"""
        try:
            if not os.path.exists(local_path):
                raise StorageError(f"Local file not found: {local_path}")

            if not user_id:
                raise StorageError("User ID is required for file upload")

            filename = os.path.basename(local_path)
            # Create a user-specific path
            storage_path = f"{user_id}/{filename}"
            logger.debug(f"Uploading file {filename} to bucket {bucket} with path {storage_path}")
            
            # Read file in chunks to handle large files
            chunk_size = 1024 * 1024  # 1MB chunks
            with open(local_path, "rb") as f:
                # Upload file
                try:
                    self.supabase.storage.from_(bucket).upload(
                        file=f,
                        path=storage_path,
                        file_options={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
                    )
                    logger.debug(f"Successfully uploaded {storage_path}")
                except Exception as upload_error:
                    logger.error(f"Error during file upload: {str(upload_error)}")
                    # Try to delete the file if it exists
                    try:
                        self.supabase.storage.from_(bucket).remove([storage_path])
                        logger.debug(f"Cleaned up existing file {storage_path}")
                    except Exception as delete_error:
                        logger.warning(f"Failed to clean up existing file: {str(delete_error)}")
                    raise StorageError(f"Failed to upload file: {str(upload_error)}")

            # Get public URL
            try:
                public_url = self.supabase.storage.from_(bucket).get_public_url(storage_path)
                logger.debug(f"Generated public URL for {storage_path}")
                return public_url
            except Exception as url_error:
                raise StorageError(f"Failed to get public URL: {str(url_error)}")

        except Exception as e:
            logger.error(f"Error in upload_file: {str(e)}")
            raise StorageError(f"Error uploading file to storage: {str(e)}")

    def download_file(self, filename: str, bucket: str = "documents", user_id: str = None, download_path: str = None) -> str:
        """Download a file from Supabase storage asynchronously
        
        Args:
            filename: Name of the file to download
            bucket: Storage bucket name
            user_id: User ID for the file path
            download_path: Optional path to save the file. If not provided, saves to /tmp/reports
            
        Returns:
            str: Path to the downloaded file
            
        Raises:
            StorageError: If file doesn't exist, invalid file type, or other errors
        """
        try:
            if not user_id:
                raise StorageError("User ID is required for file download")

            # Validate file type
            allowed_extensions = {'.docx', '.pdf', '.txt'}
            file_ext = os.path.splitext(filename)[1].lower()
            if file_ext not in allowed_extensions:
                raise StorageError(f"Invalid file type. Allowed types: {', '.join(allowed_extensions)}")

            storage_path = f"{user_id}/{filename}"
            logger.debug(f"Checking if file exists: {storage_path}")

            # Check if file exists in storage
            try:
                file_list = self.supabase.storage.from_(bucket).list(path=user_id)
                
                if not any(f['name'] == filename for f in file_list):
                    raise StorageError(f"File {filename} not found in storage")
                
                logger.debug(f"File {filename} exists in storage")
            except Exception as list_error:
                logger.error(f"Error checking file existence: {str(list_error)}")
                raise StorageError(f"Error checking file existence: {str(list_error)}")

            # Set default download path if not provided
            if not download_path:
                os.makedirs("/tmp/reports", exist_ok=True)
                download_path = os.path.join("/tmp/reports", filename)
            else:
                # Ensure the custom download path directory exists
                os.makedirs(os.path.dirname(download_path), exist_ok=True)

            # Download the file
            try:
                response = self.supabase.storage.from_(bucket).download(storage_path)
                
                # Write the file
                with open(download_path, "wb") as f:
                    f.write(response)
                
                logger.debug(f"Successfully downloaded file to {download_path}")
                return download_path
                
            except Exception as download_error:
                logger.error(f"Error during file download: {str(download_error)}")
                raise StorageError(f"Failed to download file: {str(download_error)}")

        except Exception as e:
            logger.error(f"Error in download_file: {str(e)}")
            raise StorageError(f"Error downloading file from storage: {str(e)}")

    def delete_file(self, filename: str, bucket: str = "documents") -> None:
        """Delete a file from Supabase storage asynchronously"""
        try:
            self.supabase.storage.from_(bucket).remove([filename])
        except Exception as e:
            raise StorageError(f"Error deleting file from storage: {str(e)}")

# Create a singleton instance
storage_service = StorageService(supabase)
