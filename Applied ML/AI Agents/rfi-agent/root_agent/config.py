import os
from dotenv import load_dotenv

# Load environment variables from the .env file in the root_agent directory
load_dotenv('root_agent/.env')

MODEL = os.getenv("MODEL", "gemini-2.5-pro")
