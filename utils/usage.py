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

    def update_upload_record(self, upload_id, student_count, output_url):
        self.supabase.table('uploads').update({
            'output_file_url': output_url,
            'num_students': student_count,
            'completed_at': datetime.utcnow().isoformat()
        }).eq('id', upload_id).execute()

    def increment_usage(self, user_id):
        result = self.supabase.table('usage').select('*').eq('user_id', user_id).execute()
        if result.data:
            current_count = result.data[0].get('report_count', 0)
            self.supabase.table('usage').update({
                'report_count': current_count + 1,
                'last_used_at': datetime.utcnow().isoformat()
            }).eq('user_id', user_id).execute()
        else:
            self.supabase.table('usage').insert({
                'user_id': user_id,
                'report_count': 1,
                'first_used_at': datetime.utcnow().isoformat(),
                'last_used_at': datetime.utcnow().isoformat()
            }).execute()

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
