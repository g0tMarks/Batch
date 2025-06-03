import os
from supabase import create_client
from dotenv import load_dotenv
import logging

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]

# Try to get service role key for admin operations
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

# Create the main client with anonymous key (for auth operations)
supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# Create admin client with service role key if available (bypasses RLS)
if SUPABASE_SERVICE_ROLE_KEY:
    supabase_admin = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)
    logger.info("Service role key found - admin operations will bypass RLS")
else:
    supabase_admin = supabase
    logger.warning("No service role key found - using anonymous key for all operations")
    logger.warning("This may cause RLS policy violations. Add SUPABASE_SERVICE_ROLE_KEY to your environment.")
