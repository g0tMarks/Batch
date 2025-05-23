# Fix for RLS (Row Level Security) Issue

## Problem
The database update for `output_file_url` is failing because of Row Level Security (RLS) policies in Supabase. The current code uses the anonymous key which doesn't have permission to update records that belong to authenticated users.

## Solution Options

### Option 1: Add Service Role Key (Recommended)
1. Go to your Supabase dashboard
2. Navigate to Settings > API
3. Copy the "service_role" key (NOT the anon key)
4. Add it to your .env file:
   ```
   SUPABASE_SERVICE_ROLE_KEY="your_service_role_key_here"
   ```
5. Restart your application

The updated code will automatically use the service role key which bypasses RLS for admin operations.

### Option 2: Update RLS Policies
If you prefer to keep using the anonymous key, you need to update the RLS policies on the `uploads` table:

1. Go to Supabase Dashboard > Authentication > Policies
2. Find the `uploads` table policies
3. Add or modify the UPDATE policy to allow updates:
   ```sql
   -- Allow users to update their own upload records
   CREATE POLICY "Users can update own uploads" ON uploads
   FOR UPDATE USING (auth.uid() = user_id);
   ```

### Option 3: Disable RLS (Not Recommended for Production)
1. Go to Supabase Dashboard > Table Editor
2. Select the `uploads` table
3. Click on the RLS toggle to disable it

**Warning**: This removes all security restrictions on the table.

## Current Code Changes
The code has been updated to:
1. Check for a service role key in environment variables
2. Use the service role client for database operations when available
3. Fall back to the anonymous client if no service role key is found
4. Provide better error messages when RLS blocks operations

## Testing
After implementing one of the solutions above:
1. Upload a new Excel file
2. Generate reports
3. Check that the `output_file_url` is properly set in the database
4. Verify that the download functionality works

## Recommended Next Steps
1. Add the service role key to your .env file (Option 1)
2. Test the report generation and download functionality
3. If still having issues, check the Supabase logs for more detailed error messages
