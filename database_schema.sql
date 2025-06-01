-- Database Schema for Additional Signup Information
-- This file contains SQL commands to set up storage for the new signup fields

-- OPTION 1: Using Supabase Auth User Metadata (RECOMMENDED)
-- The signup information is already being stored in the auth.users table's raw_user_meta_data column
-- This is automatically handled by the updated signup function in app.py
-- No additional SQL is needed for this approach.

-- To query user metadata, you can use:
-- SELECT raw_user_meta_data FROM auth.users WHERE id = 'user_id';

-- The metadata will contain:
-- {
--   "full_name": "User Name",
--   "school": "School Name", 
--   "how_did_you_hear": "Source",
--   "newsletter_signup": true/false
-- }

-- OPTION 2: Create a separate user_profiles table (ALTERNATIVE)
-- If you prefer to store this information in a separate table for easier querying:

CREATE TABLE IF NOT EXISTS public.user_profiles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE NOT NULL,
    full_name TEXT,
    school TEXT,
    how_did_you_hear TEXT,
    newsletter_signup BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Enable Row Level Security
ALTER TABLE public.user_profiles ENABLE ROW LEVEL SECURITY;

-- Create policy to allow users to only access their own profile
CREATE POLICY "Users can view own profile" ON public.user_profiles
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own profile" ON public.user_profiles
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own profile" ON public.user_profiles
    FOR UPDATE USING (auth.uid() = user_id);

-- Create an index for faster lookups
CREATE INDEX IF NOT EXISTS user_profiles_user_id_idx ON public.user_profiles(user_id);

-- Create a trigger to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION public.handle_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_user_profiles_updated_at
    BEFORE UPDATE ON public.user_profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.handle_updated_at();

-- OPTION 3: Add columns to existing uploads table (NOT RECOMMENDED)
-- This would store signup info with each upload, which is redundant
-- ALTER TABLE public.uploads ADD COLUMN school TEXT;
-- ALTER TABLE public.uploads ADD COLUMN how_did_you_hear TEXT;
-- ALTER TABLE public.uploads ADD COLUMN newsletter_signup BOOLEAN;

-- ANALYTICS QUERIES (for either approach)

-- Query to get newsletter signup statistics (using metadata approach):
-- SELECT 
--     COUNT(*) as total_users,
--     COUNT(CASE WHEN (raw_user_meta_data->>'newsletter_signup')::boolean = true THEN 1 END) as newsletter_signups,
--     ROUND(
--         COUNT(CASE WHEN (raw_user_meta_data->>'newsletter_signup')::boolean = true THEN 1 END) * 100.0 / COUNT(*), 
--         2
--     ) as newsletter_signup_percentage
-- FROM auth.users;

-- Query to get school distribution (using metadata approach):
-- SELECT 
--     raw_user_meta_data->>'school' as school,
--     COUNT(*) as user_count
-- FROM auth.users 
-- WHERE raw_user_meta_data->>'school' IS NOT NULL
-- GROUP BY raw_user_meta_data->>'school'
-- ORDER BY user_count DESC;

-- Query to get referral source distribution (using metadata approach):
-- SELECT 
--     raw_user_meta_data->>'how_did_you_hear' as referral_source,
--     COUNT(*) as user_count
-- FROM auth.users 
-- WHERE raw_user_meta_data->>'how_did_you_hear' IS NOT NULL
-- GROUP BY raw_user_meta_data->>'how_did_you_hear'
-- ORDER BY user_count DESC;

-- If using the user_profiles table approach, the analytics queries would be:
-- SELECT 
--     COUNT(*) as total_users,
--     COUNT(CASE WHEN newsletter_signup = true THEN 1 END) as newsletter_signups,
--     ROUND(
--         COUNT(CASE WHEN newsletter_signup = true THEN 1 END) * 100.0 / COUNT(*), 
--         2
--     ) as newsletter_signup_percentage
-- FROM public.user_profiles;

-- SELECT 
--     school,
--     COUNT(*) as user_count
-- FROM public.user_profiles 
-- WHERE school IS NOT NULL
-- GROUP BY school
-- ORDER BY user_count DESC;

-- SELECT 
--     how_did_you_hear as referral_source,
--     COUNT(*) as user_count
-- FROM public.user_profiles 
-- WHERE how_did_you_hear IS NOT NULL
-- GROUP BY how_did_you_hear
-- ORDER BY user_count DESC;
