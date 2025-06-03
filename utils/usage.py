import asyncio
from datetime import datetime
from typing import Optional
from supabase_config import supabase, supabase_admin
import os
from supabase import create_client

class UsageTrackingError(Exception):
    """Base exception for usage tracking operations"""
    pass

class UsageTrackingService:
    def __init__(self, supabase_client):
        self.supabase = supabase_client
        # Create a service role client for admin operations
        self.service_client = None
        service_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        supabase_url = os.getenv('SUPABASE_URL')
        
        print(f"Initializing UsageTrackingService...")
        print(f"Service key available: {bool(service_key)}")
        print(f"Supabase URL: {supabase_url}")
        
        if service_key and supabase_url:
            try:
                self.service_client = create_client(supabase_url, service_key)
                print("Service role client created successfully")
            except Exception as e:
                print(f"Failed to create service role client: {str(e)}")
        else:
            print("Service role key or URL not available")

    def _get_client_for_operation(self, user_token=None):
        """Get the appropriate Supabase client for the operation"""
        if self.service_client:
            # Use service role client which bypasses RLS
            return self.service_client
        elif user_token:
            # Create an authenticated client with user token
            client = create_client(
                os.getenv('SUPABASE_URL'),
                os.getenv('SUPABASE_ANON_KEY')
            )
            client.auth.set_session(user_token)
            return client
        else:
            # Fall back to default client
            return self.supabase

    async def update_upload_record(self, upload_id, student_count, output_url, user_token=None):
        try:
            # Log the update operation
            print(f"Updating upload record {upload_id} with output_file_url: {output_url}")
            
            # Get the appropriate client
            client = self._get_client_for_operation(user_token)
            
            # Create update data
            update_data = {
                'output_file_url': output_url,
                'num_students': student_count,
                'completed_at': datetime.utcnow().isoformat()
            }
            
            print(f"Update data: {update_data}")
            print(f"Using {'service role' if client == self.service_client else 'user authenticated' if user_token else 'anonymous'} client")
            
            # Update the record directly
            result = client.table('uploads').update(update_data).eq('id', upload_id).execute()
            
            # Log the result
            print(f"Update result: {result.data if hasattr(result, 'data') else result}")
            
            # Check for errors in the result
            if hasattr(result, 'error') and result.error:
                print(f"Update error: {result.error}")
                raise UsageTrackingError(f"Database update failed: {result.error}")
            
            # Double-check the update
            check_result = client.table('uploads').select('*').eq('id', upload_id).execute()
            if check_result.data:
                print(f"Verified update: {check_result.data[0]}")
                # Check if the output_file_url was actually set
                updated_record = check_result.data[0]
                if not updated_record.get('output_file_url'):
                    print("WARNING: output_file_url was not set in the database!")
                    # This might be an RLS issue - try with service role if available
                    if self.service_client and client != self.service_client:
                        print("Retrying with service role client...")
                        retry_result = self.service_client.table('uploads').update({
                            'output_file_url': str(output_url),
                            'num_students': student_count,
                            'completed_at': datetime.utcnow().isoformat()
                        }).eq('id', upload_id).execute()
                        print(f"Service role retry result: {retry_result.data if hasattr(retry_result, 'data') else retry_result}")
                        
                        # Check again
                        final_check = self.service_client.table('uploads').select('*').eq('id', upload_id).execute()
                        if final_check.data and final_check.data[0].get('output_file_url'):
                            print("Successfully updated with service role client")
                            return retry_result
                        else:
                            raise UsageTrackingError("Failed to update database even with service role - RLS policy may be blocking updates")
                    else:
                        raise UsageTrackingError("Database update failed - output_file_url not set. This may be due to RLS policies.")
                else:
                    print("Update successful - output_file_url was set correctly")
            
            return result
        except Exception as e:
            print(f"Error updating upload record: {str(e)}")
            import traceback
            traceback.print_exc()
            raise UsageTrackingError(f"Failed to update upload record: {str(e)}")

    async def increment_usage(self, user_id, user_token=None):
        try:
            # Get current usage directly
            print(f"Getting usage data for user {user_id}")
            
            # Get the appropriate client
            client = self._get_client_for_operation(user_token)
            
            result = client.table('usage').select('*').eq('user_id', user_id).execute()
            
            if result.data:
                current_count = result.data[0].get('report_count', 0)
                print(f"Incrementing usage count for user {user_id} from {current_count} to {current_count + 1}")
                
                # Update usage count directly
                update_data = {
                    'report_count': current_count + 1,
                    'last_used_at': datetime.utcnow().isoformat()
                }
                print(f"Update data: {update_data}")
                
                update_result = client.table('usage').update(update_data).eq('user_id', user_id).execute()
                
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
                
                insert_result = client.table('usage').insert(insert_data).execute()
                
                print(f"Usage insert result: {insert_result.data if hasattr(insert_result, 'data') else insert_result}")
                return insert_result
        except Exception as e:
            print(f"Error incrementing usage: {str(e)}")
            import traceback
            traceback.print_exc()
            raise UsageTrackingError(f"Failed to increment usage: {str(e)}")

    async def get_usage_stats(self, user_id: str, user_token=None) -> dict:
        """Get usage statistics for a user"""
        try:
            print(f"Getting usage statistics for user {user_id}")
            
            # Get the appropriate client
            client = self._get_client_for_operation(user_token)
            
            result = client.table('usage').select('*').eq('user_id', user_id).execute()
            print(f"Usage stats result: {result.data if result.data else 'No data found'}")
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error getting usage stats: {str(e)}")
            import traceback
            traceback.print_exc()
            raise UsageTrackingError(f"Error getting usage stats: {str(e)}")

# Create a singleton instance
usage_service = UsageTrackingService(supabase_admin)
