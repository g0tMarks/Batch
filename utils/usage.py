import asyncio
from datetime import datetime
from typing import Optional
from supabase_config import supabase

class UsageTrackingError(Exception):
    """Base exception for usage tracking operations"""
    pass

class UsageTrackingService:
    def __init__(self, supabase_client):
        self.supabase = supabase_client

    async def update_upload_record(self, upload_id: str, student_count: int, output_url: str) -> None:
        """Update the upload record with output file URL and student count"""
        try:
            await asyncio.to_thread(
                self.supabase.table('uploads').update({
                    'output_file_url': output_url,
                    'num_students': student_count,
                    'completed_at': datetime.utcnow().isoformat()
                }).eq('id', upload_id).execute
            )
        except Exception as e:
            raise UsageTrackingError(f"Error updating upload record: {str(e)}")

    async def increment_usage(self, user_id: str) -> None:
        """Increment or create usage record for the current user"""
        try:
            # First try to get existing usage record
            result = await asyncio.to_thread(
                self.supabase.table('usage').select('*').eq('user_id', user_id).execute
            )
            
            if result.data:
                # Update existing record
                current_count = result.data[0].get('report_count', 0)
                await asyncio.to_thread(
                    self.supabase.table('usage').update({
                        'report_count': current_count + 1,
                        'last_used_at': datetime.utcnow().isoformat()
                    }).eq('user_id', user_id).execute
                )
            else:
                # Create new record
                await asyncio.to_thread(
                    self.supabase.table('usage').insert({
                        'user_id': user_id,
                        'report_count': 1,
                        'first_used_at': datetime.utcnow().isoformat(),
                        'last_used_at': datetime.utcnow().isoformat()
                    }).execute
                )
        except Exception as e:
            raise UsageTrackingError(f"Error incrementing usage: {str(e)}")

    async def get_usage_stats(self, user_id: str) -> dict:
        """Get usage statistics for a user"""
        try:
            result = await asyncio.to_thread(
                self.supabase.table('usage').select('*').eq('user_id', user_id).execute
            )
            return result.data[0] if result.data else None
        except Exception as e:
            raise UsageTrackingError(f"Error getting usage stats: {str(e)}")

# Create a singleton instance
usage_service = UsageTrackingService(supabase)
