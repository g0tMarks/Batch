- [x] Set up Supabase Storage bucket and configure RLS policies
    - [x] 1.1 Create a new bucket (e.g., `uploads/`) in Supabase Storage
    - [x] 1.2 Define RLS policies to restrict access to authenticated users
    - [x] 1.3 Ensure only the uploader can access their files
    - [x] 1.4 Verify that files are not publicly accessible

- [x] 2.1 Add UI component for uploading Excel files (.xlsx)
    - [x] 2.2 Enforce file type restriction to `.xlsx`
    - [x] 2.3 Enforce file size restriction (e.g., max 10MB)
    - [x] 2.4 Validate and sanitize file names before upload
    - [x] 2.5 Restrict upload access to authenticated users

- [x] Implement server-side upload API to Supabase Storage
    - [x] 3.1 Create API endpoint to receive file from UI
    - [x] 3.2 Upload received file to Supabase Storage under the correct bucket
    - [x] 3.3 Log upload event for traceability

- [x] Implement file processing logic
    - [x] 4.1 Download file from Supabase Storage to server (RAM or temp directory)
    - [x] 4.2 Parse Excel file and extract valid student data
    - [x] 4.3 Skip empty or incomplete rows during parsing
    - [x] 4.4 Generate AI prompts and process reports based on parsed data
    - [x] 4.5 Log processing start and end events

- [ ] Implement cleanup and deletion logic
    - [x] 5.1 Delete uploaded file from Supabase Storage after processing
    - [x] 5.2 Delete temporary files from server memory/disk post-processing
    - [x] 5.3 Log deletion event
    - [x] 5.4 Handle processing failures to avoid orphan files in storage

- [ ] Implement (optional) Supabase Storage lifecycle policy
    - [x] 6.1 Set up automatic deletion of files older than 24 hours in the bucket
    - [ ] 6.2 Test lifecycle policy to ensure old files are deleted

- [ ] Ensure system supports concurrent uploads and processing
    - [ ] 7.1 Test multiple simultaneous uploads and processing jobs
    - [ ] 7.2 Implement file streaming for large files
    - [ ] 7.3 Validate no disk contention or memory issues during concurrent jobs

- [ ] Implement logging and monitoring
    - [ ] 8.1 Log all key events (upload, processing, deletion)
    - [ ] 8.2 Set up monitoring for failed uploads or processing jobs
    - [ ] 8.3 (Future) Provide audit logs for uploads and deletions

- [ ] Testing and validation
    - [ ] 9.1 Test user upload, processing, and cleanup flows
    - [ ] 9.2 Test security (authentication, RLS, file access)
    - [ ] 9.3 Test scalability (concurrent uploads, large files)
    - [ ] 9.4 Validate that no orphan files remain after failures

- [ ] Production deployment
    - [ ] 10.1 Deploy system to production environment
    - [ ] 10.2 Monitor for issues and validate successful operation
