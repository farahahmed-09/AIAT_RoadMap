import os
from dotenv import load_dotenv

load_dotenv()
# --- PATH CONFIGURATION ---
BASE_DIR = r"D:\AIAT_roadmap\output_parser"
INPUT_CONTENT_FILE = os.path.join(BASE_DIR, "Program 8 Natural Language Processing NLP.md")
INPUT_TEMPLATE_FILE = os.path.join(BASE_DIR, "Specialization Introduction Video - SprintUp.md")
OUTPUT_JSON_FILE = os.path.join(BASE_DIR, "slides_plan.json")
IMAGES_DIR = os.path.join(BASE_DIR, "images")

# --- API KEYS ---
# Set these in your environment variables or paste them here
GEMINI_API_KEY =os.getenv("GEMINI_API_KEY")
NAPKIN_API_KEY = gemini_api_key = os.getenv("NAPKIN_API_KEY")
NAPKIN_API_URL = "https://api.napkin.ai/v1/generate"