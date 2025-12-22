
import json
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.chat_models.litellm import ChatLiteLLM
from dotenv import load_dotenv
import config

# Load environment variables
load_dotenv()

def generate_slide_content():
    """
    Step 1: Formulate slide content using LLM.
    Reads the content and template, then generates a structured list of slides.
    """
    print("--- Step 1: Generating Slide Content ---")
    
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    
    # 1. Load Files
    # Ensure config.INPUT_CONTENT_FILE points to "Program 8 Natural Language Processing NLP.md"
    # Ensure config.INPUT_TEMPLATE_FILE points to "Specialization Introduction Video - SprintUp.md"
    try:
        with open(config.INPUT_CONTENT_FILE, "r", encoding="utf-8") as f:
            content_text = f.read()
        with open(config.INPUT_TEMPLATE_FILE, "r", encoding="utf-8") as f:
            template_text = f.read()
    except FileNotFoundError as e:
        print(f"❌ Error loading files: {e}")
        print("Please check that config.INPUT_CONTENT_FILE and config.INPUT_TEMPLATE_FILE are set correctly.")
        return []

    # 2. Setup LLM
    llm = ChatLiteLLM(model="gemini/gemini-2.5-flash", api_key=gemini_api_key)

    # 3. Define Prompt
    # Updated to strictly enforce Template Titles + Content Details logic
    prompt = (
        "You are an expert curriculum designer and video script writer.\n"
        "Your task is to merge two inputs into a single JSON slide plan for a specialization introduction video.\n\n"

        "INPUTS:\n"
        "1. TEMPLATE: A video script structure defining the flow, section titles (e.g., 'Welcome', 'Career Outlook'), and goals.\n"
        "2. CONTENT: A technical syllabus (Program 8: Natural Language Processing) containing learning objectives, modules (NLP, Sequence Models, Transformers), and project details.\n\n"

        "TASK:\n"
        "Create a JSON array where each object represents a slide based on the TEMPLATE structure, populated with technical details from the CONTENT.\n\n"

        "MAPPING RULES (CRITICAL):\n"
        "- **Slide Titles (`main_title`)**: MUST be taken strictly from the 'TEMPLATE' file's headers .\n"
        "- **Slide Content (`sections`)**: MUST be taken strictly from the 'CONTENT' file.\n"
        "- you are allowed to rephrase the slide content to be bullet points for example or short phrases"

        "OUTPUT STRUCTURE:\n"
        "For EACH slide, generate ONE object with these exact keys:\n"
        "- \"main_title\": (String) The section title from the TEMPLATE.\n"
        "- \"sections\": (Array of Objects) List of content blocks:\n"
        "    - \"subheader\": (String) A short header for this text block.\n"
        "    - \"content\": (String) Concise technical details derived from the CONTENT file.\n"
        "- \"image_search_description\": (String) A visual description for AI image generation (e.g., 'Diagram of Transformer architecture', 'Futuristic data flow').\n"
        "- \"image_path\": (Null) Always set to null.\n\n"

        "OUTPUT FORMAT:\n"
        "- Return ONLY a valid JSON array.\n"
        "- No markdown formatting (no ```json).\n"
    )

    user_message = (
        f"TEMPLATE (Use for Structure/Titles):\n{template_text}\n\n"
        f"CONTENT (Use for Technical Details):\n{content_text}\n\n"
        f"Generate the JSON slide plan."
    )

    messages = [
        SystemMessage(content=prompt),
        HumanMessage(content=user_message)
    ]

    print("🤖 Analyzing content and mapping to template...")
    
    try:
        response = llm.invoke(messages)
        
        # Cleanup response string
        clean_content = response.content.replace("```json", "").replace("```", "").strip()
        
        # Parse JSON
        slides_data = json.loads(clean_content)
        print(f"✅ Generated content for {len(slides_data)} slides.")
        
        # Save to Output
        with open(config.OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(slides_data, f, indent=4, ensure_ascii=False)
        print(f"💾 Saved slide plan to: {config.OUTPUT_JSON_FILE}")

        return slides_data
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parsing failed: {e}")
        print("Raw Output:", response.content)
        return []
    except Exception as e:
        print(f"❌ An error occurred: {e}")
        return []

if __name__ == "__main__":
    generate_slide_content()