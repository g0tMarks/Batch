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

    async def update_upload_record(self, upload_id, student_count, output_url):
        try:
            # Log the update operation
            print(f"Updating upload record {upload_id} with output_file_url: {output_url}")
            
            # Create update data - only use output_file_url which exists in the table
            update_data = {
                'output_file_url': output_url,
                'num_students': student_count,
                'completed_at': datetime.utcnow().isoformat()
            }
            
            print(f"Update data: {update_data}")
            
            # Update the record directly
            result = self.supabase.table('uploads').update(update_data).eq('id', upload_id).execute()
            
            # Log the result
            print(f"Update result: {result.data if hasattr(result, 'data') else result}")
            
            # Double-check the update
            check_result = self.supabase.table('uploads').select('*').eq('id', upload_id).execute()
            if check_result.data:
                print(f"Verified update: {check_result.data[0]}")
                # Check if the output_file_url was actually set
                updated_record = check_result.data[0]
                if not updated_record.get('output_file_url'):
                    print("WARNING: output_file_url was not set in the database!")
                    # Try one more time with a different approach
                    retry_result = self.supabase.table('uploads').update({
                        'output_file_url': str(output_url)
                    }).eq('id', upload_id).execute()
                    print(f"Retry update result: {retry_result.data if hasattr(retry_result, 'data') else retry_result}")
            
            return result
        except Exception as e:
            print(f"Error updating upload record: {str(e)}")
            import traceback
            traceback.print_exc()
            raise UsageTrackingError(f"Failed to update upload record: {str(e)}")

    async def increment_usage(self, user_id):
        try:
            # Get current usage directly
            print(f"Getting usage data for user {user_id}")
            result = self.supabase.table('usage').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                current_count = result.data[0].get('report_count', 0)
                print(f"Incrementing usage count for user {user_id} from {current_count} to {current_count + 1}")
                
                # Update usage count directly
                update_data = {
                    'report_count': current_count + 1,
                    'last_used_at': datetime.utcnow().isoformat()
                }
                print(f"Update data: {update_data}")
                
                update_result = self.supabase.table('usage').update(update_data).eq('user_id', user_id).execute()
                
                print(f"Usage update result: {update_result.data if hasattr(update_result, 'data') else update_result}")
                return update_result
            else:
                print(f"Creating new usage record for user {user_id}")
                
                # Create new usage record directly
                insert_data = {
                    'user_id': user_id,
                    'report_count': 1,
                    'first_used_at': datetime.utcnow().isoformat(),
                    'last_used_at': datetime.utcnow().isoformat()
                }
                print(f"Insert data: {insert_data}")
                
                insert_result = self.supabase.table('usage').insert(insert_data).execute()
                
                print(f"Usage insert result: {insert_result.data if hasattr(insert_result, 'data') else insert_result}")
                return insert_result
        except Exception as e:
            print(f"Error incrementing usage: {str(e)}")
            import traceback
            traceback.print_exc()
            raise UsageTrackingError(f"Failed to increment usage: {str(e)}")

    async def get_usage_stats(self, user_id: str) -> dict:
        """Get usage statistics for a user"""
        try:
            print(f"Getting usage statistics for user {user_id}")
            result = self.supabase.table('usage').select('*').eq('user_id', user_id).execute()
            print(f"Usage stats result: {result.data if result.data else 'No data found'}")
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error getting usage stats: {str(e)}")
            import traceback
            traceback.print_exc()
            raise UsageTrackingError(f"Error getting usage stats: {str(e)}")

# Create a singleton instance
usage_service = UsageTrackingService(supabase)
