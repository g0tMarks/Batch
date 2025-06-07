-- Create a lifecycle policy for the uploads bucket
CREATE POLICY "Auto-delete old files"
ON storage.objects
FOR DELETE
USING (
  bucket_id = 'uploads' AND
  created_at < NOW() - INTERVAL '24 hours'
);

-- Enable the policy
ALTER POLICY "Auto-delete old files" ON storage.objects ENABLE;

-- Note: This policy will automatically delete files older than 24 hours
-- from the 'uploads' bucket. Make sure this aligns with your business requirements. 