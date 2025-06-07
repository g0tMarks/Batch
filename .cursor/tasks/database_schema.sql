-- Create uploads table if it doesn't exist
CREATE TABLE IF NOT EXISTS public.uploads (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    user_id UUID REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    num_students INTEGER,
    output_file_url TEXT,
    error_message TEXT,
    status TEXT DEFAULT 'pending'
);

-- Enable Row Level Security
ALTER TABLE public.uploads ENABLE ROW LEVEL SECURITY;

-- Create policies for uploads table
CREATE POLICY "Users can view own uploads" ON public.uploads
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can insert own uploads" ON public.uploads
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own uploads" ON public.uploads
    FOR UPDATE USING (auth.uid() = user_id);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS uploads_user_id_idx ON public.uploads(user_id);
CREATE INDEX IF NOT EXISTS uploads_created_at_idx ON public.uploads(created_at); 