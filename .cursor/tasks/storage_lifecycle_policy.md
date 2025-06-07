# Supabase Storage Lifecycle Policy Setup

## Overview
This document provides instructions for setting up an automatic deletion policy for files in the Supabase Storage bucket. The policy will automatically delete files that are older than 24 hours.

## Steps to Set Up Lifecycle Policy

1. Log in to your Supabase Dashboard
2. Navigate to Storage > Buckets
3. Select the "uploads" bucket
4. Click on "Policies" tab
5. Click "Add Policy"
6. Configure the policy with the following settings:
   - Policy Name: "Auto-delete old files"
   - Policy Type: "Lifecycle"
   - Action: "Delete"
   - Condition: "Age > 24 hours"
   - Apply to: "All files in bucket"

## Policy Details
- Files will be automatically deleted after 24 hours
- This applies to all files in the bucket
- The policy is enforced by Supabase's storage system
- No manual intervention required

## Important Notes
1. This policy will affect all files in the bucket, including:
   - Uploaded Excel files
   - Generated report files
   - Any other files stored in the bucket

2. Make sure this aligns with your business requirements:
   - Users should download their reports within 24 hours
   - The system should not need to retain files longer than 24 hours
   - All processing should be completed within 24 hours

3. Consider the following before enabling:
   - Users may need more time to download their reports
   - Some files may need to be retained longer
   - The policy cannot be reversed once files are deleted

## Testing the Policy
1. Upload a test file
2. Wait for 24 hours
3. Verify that the file is automatically deleted
4. Check the storage logs to confirm the deletion

## Monitoring
- Monitor the storage usage to ensure files are being deleted as expected
- Check for any errors in the storage logs
- Verify that the policy is working as intended

## Troubleshooting
If files are not being deleted:
1. Check the policy configuration
2. Verify the bucket settings
3. Check the storage logs for any errors
4. Ensure the policy is enabled and active 