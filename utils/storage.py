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

    async def upload_file(self, local_path: str, bucket: str = "documents", user_id: str = None) -> str:
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
                    await asyncio.to_thread(
                        self.supabase.storage.from_(bucket).upload,
                        file=f,
                        path=storage_path,
                        file_options={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
                    )
                    logger.debug(f"Successfully uploaded {storage_path}")
                except Exception as upload_error:
                    logger.error(f"Error during file upload: {str(upload_error)}")
                    # Try to delete the file if it exists
                    try:
                        await asyncio.to_thread(
                            self.supabase.storage.from_(bucket).remove,
                            [storage_path]
                        )
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

    async def delete_file(self, filename: str, bucket: str = "documents") -> None:
        """Delete a file from Supabase storage asynchronously"""
        try:
            await asyncio.to_thread(
                self.supabase.storage.from_(bucket).remove,
                [filename]
            )
        except Exception as e:
            raise StorageError(f"Error deleting file from storage: {str(e)}")

# Create a singleton instance
storage_service = StorageService(supabase)
