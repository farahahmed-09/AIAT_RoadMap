import pymupdf4llm
import pathlib
import os

# --- LangChain Imports ---
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from dotenv import load_dotenv  
from langchain_community.chat_models.litellm import ChatLiteLLM

# --- CONFIGURATION ---
load_dotenv()
INPUT_FILES = [
    r"D:\AIAT_roadmap\inputs\_AI & ML BootCamp Learning Journey .docx.pdf",
    r"D:\AIAT_roadmap\inputs\Specialization Introduction Video - SprintUp.pdf"
]

OUTPUT_DIR = r"D:\AIAT_roadmap\output_parser"
gemini_api_key = os.getenv("GEMINI_API_KEY")
llm = ChatLiteLLM(model="gemini/gemini-2.5-flash", api_key=gemini_api_key)
TARGET_SECTION_NAME = "Program 8: Natural Language Processing (NLP)"

# ---------------------

def process_batch():
    """
    Phase 1: Convert PDFs to Markdown using PyMuPDF4LLM.
    Returns the path to the converted Markdown file of the FIRST PDF.
    """
    print("--- Phase 1: Parsing PDFs ---")
    
    output_path = pathlib.Path(OUTPUT_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    
    first_md_file = None

    for index, file_path in enumerate(INPUT_FILES):
        input_p = pathlib.Path(file_path)

        if not input_p.exists():
            print(f"❌ File not found (skipped): {file_path}")
            continue

        print(f"⏳ Parsing: {input_p.name}...")

        try:
            md_text = pymupdf4llm.to_markdown(input_p)
            
            new_filename = input_p.stem + ".md"
            final_output_path = output_path / new_filename

            with open(final_output_path, "w", encoding="utf-8") as f:
                f.write(md_text)
            
            print(f"✅ Saved to: {final_output_path}")

            if index == 0:
                first_md_file = final_output_path

        except Exception as e:
            print(f"⚠️ Error processing {input_p.name}: {e}")
            
    return first_md_file

def extract_section_langchain(source_file_path, section_title):
    """
    Phase 2: Use LangChain's llm.invoke to extract specific content.
    """
    print(f"\n--- Phase 2: Extracting '{section_title}' (LangChain) ---")

    if not source_file_path or not source_file_path.exists():
        print("❌ Source file for extraction not found.")
        return


    print(f"📖 Reading source: {source_file_path.name}")
    try:
        with open(source_file_path, "r", encoding="utf-8") as f:
            full_text = f.read()

        # 2. Define Messages
        messages = [
            SystemMessage(content="You are a precise document extraction assistant."),
            HumanMessage(content=(
                f"I have a document formatted in Markdown. "
                f"Please find the section titled '{section_title}'.\n"
                f"Extract that entire section, including all subsections, bullets, and details belonging to it.\n"
                f"Stop extracting when the next major program or section begins.\n"
                f"Return ONLY the markdown content of that section.\n\n"
                f"DOCUMENT CONTENT:\n{full_text}"
            ))
        ]

        print("🤖 Invoking LLM...")
        
        # 3. INVOKE THE LLM
        response = llm.invoke(messages)
        
        # The content is in response.content
        extracted_content = response.content

        # 4. Save Output
        safe_name = "".join(x for x in section_title if x.isalnum() or x in " -_").strip()
        output_file = source_file_path.parent / f"{safe_name}.md"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(extracted_content)

        print(f"✅ Extracted section saved to: {output_file}")

    except Exception as e:
        print(f"⚠️ Error during LangChain extraction: {e}")

if __name__ == "__main__":
    # Run Phase 1
    first_pdf_path = process_batch()

    # Run Phase 2
    if first_pdf_path:
        extract_section_langchain(first_pdf_path, TARGET_SECTION_NAME)
    
    print("\nBatch processing complete.")