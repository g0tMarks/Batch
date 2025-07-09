Project Title
Secure Temporary File Upload and Processing System

1. Overview
Implement a secure, scalable system for uploading Excel spreadsheets, temporarily storing them, parsing the data for report generation, and cleaning up after processing. Uploaded files will be stored in Supabase Storage, processed by the server, and deleted after use.

2. Problem Statement
Currently, user-uploaded files are stored locally on the server, which:

Risks data loss if the server restarts.

Does not scale well with increased load or multi-server architecture.

Introduces security risks due to residual user data on disk.

We need a reliable and secure method to handle user uploads, aligned with best practices for cloud applications.

3. Goals
Securely store user-uploaded files temporarily.

Ensure uploaded files are processed correctly to generate AI prompts.

Automatically clean up files after processing.

Ensure the system is scalable and supports concurrent uploads and processing.

4. Requirements
4.1 Functional Requirements
#	Requirement
F1	Users must be able to upload Excel files (.xlsx) via the web interface.
F2	Files must be stored temporarily in Supabase Storage under a bucket (e.g., uploads/).
F3	The server must download the file temporarily to RAM or a temp directory (/tmp) for processing.
F4	The server must parse the Excel file, extract valid student data (skip empty/incomplete rows).
F5	After processing, the server must delete the uploaded file from Supabase Storage.
F6	(Optional) Supabase Storage bucket must have a lifecycle policy to auto-delete files older than 24 hours.

4.2 Non-Functional Requirements
#	Requirement
NF1	The system must handle multiple concurrent uploads and processing jobs.
NF2	Uploaded files must not be permanently stored on the server.
NF3	Files must be processed securely — no public exposure of upload data.
NF4	Operations must log key events (upload, processing start/end, deletion) for traceability.
NF5	Failure in processing must not leave orphan files in storage.
NF6	Temporary files must be cleared from server memory/disk post-processing.

5. User Flow
User uploads Excel file via UI.

Server uploads file to Supabase Storage under uploads/ bucket.

Server downloads file from Supabase Storage for processing.

Server parses file, generates prompts, processes reports.

Server deletes file from Supabase Storage.

(Optional) Lifecycle rule auto-deletes any old files not manually cleaned.

6. Security Considerations
Only authenticated users can upload files.

Uploaded files are not publicly accessible.

Server limits file size to prevent abuse (e.g., 10MB max).

Server validates and sanitizes file names.

Ensure Supabase Storage has proper RLS policies (upload only accessible by uploader).

Temporary files are deleted after processing, reducing attack surface.

7. Scalability Considerations
Use Supabase Storage for durable, scalable storage.

Server should stream large files instead of loading entirely into memory.

Temporary processing should support concurrent jobs without disk contention.

8. Open Questions
#	Question
Q1	What is the maximum file size allowed for upload?
Q2	Should users be notified if a file fails validation (e.g., missing required columns)?
Q3	Should we enforce a limit on number of students parsed per upload (e.g., max 500)?
Q4	Should the system allow re-processing the same file, or one-shot processing only?

9. Milestones
Milestone	Description	Target Date
M1	Implement Supabase Storage bucket and RLS policies	[Date]
M2	Implement upload API to Supabase Storage	[Date]
M3	Implement processing logic (download, parse, generate, clean)	[Date]
M4	Implement automatic cleanup and lifecycle rules	[Date]
M5	Testing and validation	[Date]
M6	Production deployment	[Date]

10. Future Enhancements
Show upload progress/status to users.

Retry mechanism on temporary network failures during upload/download.

Audit logs for uploads and deletions.

Support other file types (CSV).

11. Risks
Risk	Mitigation
Large files may overwhelm memory	Stream processing and enforce file size limits
Files not deleted after crash	Lifecycle rules in storage as backup cleanup
RLS misconfiguration exposes data	Strict Supabase policies and access controls
