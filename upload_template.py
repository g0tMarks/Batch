#!/usr/bin/env python3
"""
Script to upload the template file to Supabase storage
"""
import asyncio
import os
from utils.storage import storage_service

async def upload_template():
    """Upload the template file to Supabase storage"""
    template_path = os.path.join('uploads', 'template_student_data.xlsx')
    
    if not os.path.exists(template_path):
        print(f"Template file not found at {template_path}")
        return False
    
    try:
        print(f"Uploading template file: {template_path}")
        public_url = await storage_service.upload_template(template_path)
        print(f"Template uploaded successfully!")
        print(f"Public URL: {public_url}")
        return True
    except Exception as e:
        print(f"Error uploading template: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(upload_template())
    if success:
        print("Template upload completed successfully!")
    else:
        print("Template upload failed!")
