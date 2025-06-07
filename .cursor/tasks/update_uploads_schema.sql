-- Add error_message column to uploads table if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'uploads' 
        AND column_name = 'error_message'
    ) THEN
        ALTER TABLE public.uploads 
        ADD COLUMN error_message TEXT;
    END IF;
END $$;

-- Add status column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'uploads' 
        AND column_name = 'status'
    ) THEN
        ALTER TABLE public.uploads 
        ADD COLUMN status TEXT DEFAULT 'pending';
    END IF;
END $$; 