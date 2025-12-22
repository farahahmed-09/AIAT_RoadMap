
import os
import json
import base64
import webbrowser
from typing import List, Dict
from dotenv import load_dotenv
from langchain_community.chat_models.litellm import ChatLiteLLM
from langchain_core.messages import HumanMessage, SystemMessage

# ================= CONFIGURATION LOAD =================
load_dotenv()
gemini_api_key = os.getenv("GEMINI_API_KEY")

CONFIG_PATH = r"D:\AIAT_LearnerSlides\config.json"

if not os.path.exists(CONFIG_PATH):
    raise FileNotFoundError(f"Configuration file not found at {CONFIG_PATH}")

with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    config = json.load(f)

# Extract Paths
INPUT_JSON_PATH = r"D:\AIAT_roadmap\output_parser\slides_plan.json"
OUTPUT_DIR = config["paths"]["output_dir"]
BACKGROUND_IMAGE_PATH = config["paths"]["background_image"]
LOGO_IMAGE_PATH = config["paths"]["logo_image"]
ANIMATION_PROMPT = config.get("animation", {}).get("style_prompt", "fade") # Default to fade

# Extract Colors
c = config["branding"]["colors"]
C_HEADER = f"text-[{c['header_text']}]"
C_BODY = f"text-[{c['body_text']}]"
C_PRIMARY = f"text-[{c['primary_accent']}]"
C_BG_ACCENT = f"bg-[{c['soft_bg']}]"
C_BORDER = f"border-[{c['border']}]"

# LLM Selection
llm = ChatLiteLLM(model="gemini/gemini-2.5-flash", api_key=gemini_api_key)

# ================= HELPER FUNCTIONS =================

# def encode_image_to_base64(image_path: str) -> str:
#     if not image_path or not os.path.exists(image_path):
#         return "" 
#     try:
#         with open(image_path, "rb") as image_file:
#             encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
#         ext = os.path.splitext(image_path)[1].lower()
#         mime_type = "image/png" if ext == ".png" else "image/jpeg"
#         return f"data:{mime_type};base64,{encoded_string}"
#     except Exception as e:
#         print(f"Warning: Could not encode image at {image_path}: {e}")
#         return ""

def encode_image_to_base64(image_path: str) -> str:
    if not image_path or not os.path.exists(image_path):
        return "" 
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        
        ext = os.path.splitext(image_path)[1].lower()
        
        # --- MODIFIED SECTION START ---
        if ext == ".svg":
            mime_type = "image/svg+xml"
        elif ext == ".png":
            mime_type = "image/png"
        elif ext in [".jpg", ".jpeg"]:
            mime_type = "image/jpeg"
        else:
            # Fallback for other types like webp or gif
            mime_type = "image/octet-stream" 
        # --- MODIFIED SECTION END ---

        return f"data:{mime_type};base64,{encoded_string}"
    except Exception as e:
        print(f"Warning: Could not encode image at {image_path}: {e}")
        return ""

def determine_css_animation(prompt_text):
    """
    Decides the CSS for the 'reveal' class based on user prompt.
    """
    prompt_text = prompt_text.lower()
    
    # Default: Professional Fade
    css = """
        .reveal-item { opacity: 0; transition: opacity 0.8s ease-in-out; }
        .reveal-item.visible { opacity: 1; }
    """
    
    if "slide" in prompt_text or "up" in prompt_text:
        css = """
        .reveal-item { opacity: 0; transform: translateY(30px); transition: all 0.6s ease-out; }
        .reveal-item.visible { opacity: 1; transform: translateY(0); }
        """
    elif "bounce" in prompt_text:
        css = """
        .reveal-item { opacity: 0; transform: scale(0.8); transition: all 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); }
        .reveal-item.visible { opacity: 1; transform: scale(1); }
        """
    elif "zoom" in prompt_text:
        css = """
        .reveal-item { opacity: 0; transform: scale(1.1); filter: blur(4px); transition: all 0.7s ease; }
        .reveal-item.visible { opacity: 1; transform: scale(1); filter: blur(0); }
        """
    
    return css

# def generate_content_prompt(slide_data: Dict, has_slide_img: bool) -> str:
#     sections = slide_data.get('sections', [])
#     content_context = ""
#     for sec in sections:
#         content_context += f"Subheader: {sec.get('subheader', 'N/A')}\nContent: {sec.get('content', '')}\n\n"

#     img_instruction = ""
#     if has_slide_img:
#         img_instruction = f"""
#         - **LAYOUT:** Float the image to the right.
#         - **HTML Structure:**
#           <div class="clearfix">
#              <img src="SLIDE_IMAGE_PLACEHOLDER" class="float-right ml-6 mb-4 w-1/2 max-w-md rounded-xl shadow-lg border {C_BORDER}">
#              <div class="space-y-6">
#                 </div>
#           </div>
#         """

#     prompt = f"""
#     You are a Content Developer.
#     **Task:** Write inner HTML for a slide.
#     **Context:** {content_context}
    
#     **CRITICAL ANIMATION REQUIREMENT:**
#     The user wants to "Click to Reveal" content piece by piece.
#     1. You MUST wrap **EVERY** single Paragraph `<p>`, List Item `<li>`, or Header `<h3>` in the class `reveal-item`.
#     2. Example: `<p class="reveal-item text-lg...">Content...</p>`
#     3. Do NOT put the class on the parent container. Put it on the children so they appear one by one.
    
#     **Styling:**
#     - Headers: `text-2xl font-bold {C_HEADER} mb-3`
#     - Body: `text-lg {C_BODY} leading-relaxed mb-4`
#     - Lists: `list-disc pl-5 space-y-2`
    
#     {img_instruction}

#     **Output:** Raw HTML string only.
#     """
#     return prompt


def generate_content_prompt(slide_data: Dict, has_slide_img: bool) -> str:
    sections = slide_data.get('sections', [])
    content_context = ""
    for sec in sections:
        content_context += f"Subheader: {sec.get('subheader', 'N/A')}\nContent: {sec.get('content', '')}\n\n"

    img_instruction = ""
    if has_slide_img:
        img_instruction = f"""
        - **LAYOUT:** Float the image to the right.
        - **HTML Structure:**
          <div class="clearfix mb-8">
             <img src="SLIDE_IMAGE_PLACEHOLDER" class="float-right ml-8 mb-6 w-5/12 max-w-sm rounded-lg shadow-md border {C_BORDER}">
             <div class="space-y-4">
                </div>
          </div>
        """

    prompt = f"""
    You are a Content Developer.
    **Task:** Write inner HTML for a document section.
    **Context:** {content_context}
    
    **CRITICAL ANIMATION REQUIREMENT:**
    The user wants to "Click to Reveal" content piece by piece.
    1. You MUST wrap **EVERY** single Paragraph `<p>`, List Item `<li>`, or Header `<h3>` in the class `reveal-item`.
    2. Example: `<p class="reveal-item text-lg...">Content...</p>`
    
    **Styling:**
    - Headers: `text-2xl font-bold {C_HEADER} mb-3 mt-6`
    - Body: `text-lg {C_BODY} leading-relaxed mb-4`
    - Lists: `list-disc pl-5 space-y-2 text-lg {C_BODY}`
    
    {img_instruction}

    **Output:** Raw HTML string only.
    """
    return prompt

# ================= THE SINGLE PAGE APPLICATION SHELL =================

# HTML_PLAYER_SHELL = """
# <!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Course Slides</title>
#     <script src="https://cdn.tailwindcss.com"></script>
#     <style>
#         /* Base Transition for Slide Swapping */
#         .slide-container {{
#             display: none;
#             animation: fadeIn 0.5s ease-in-out;
#         }}
#         .slide-container.active {{
#             display: flex;
#         }}
        
#         @keyframes fadeIn {{ from {{ opacity: 0; }} to {{ opacity: 1; }} }}

#         /* Dynamic Animation from Config */
#         {custom_animation_css}

#         /* Scrollbar */
#         ::-webkit-scrollbar {{ width: 8px; }}
#         ::-webkit-scrollbar-track {{ background: #f1f1f1; }}
#         ::-webkit-scrollbar-thumb {{ background: #c7c7c7; border-radius: 4px; }}
#     </style>
# </head>
# <body class="h-screen w-screen overflow-hidden bg-gray-900 flex items-center justify-center relative select-none">

#     <div class="absolute inset-0 z-0 bg-cover bg-center" style="background-image: url('{bg_image}');">
#          <div class="absolute inset-0 bg-black/10"></div>
#     </div>

#     <div id="app" class="relative z-10 w-full h-full flex items-center justify-center p-4" onclick="handleGlobalClick(event)">
        
#         <main id="slide-card" class="w-full max-w-7xl h-[90vh] bg-white/95 backdrop-blur-xl rounded-3xl shadow-2xl overflow-hidden flex flex-col border border-white/50 transition-all duration-300">
            
#             <header class="{bg_accent} px-8 py-5 border-b {border_color} flex justify-between items-center shrink-0">
#                 <div class="flex items-center gap-6">
#                     <img src="{logo_image}" class="h-10 w-auto object-contain" alt="Logo">
#                     <div class="h-8 w-px bg-indigo-200"></div> 
#                     <h1 id="header-title" class="text-2xl font-bold {header_color}">Loading...</h1>
#                 </div>
#                 <div id="slide-counter" class="text-sm {primary_color} font-medium"></div>
#             </header>

#             <div id="content-area" class="flex-1 overflow-y-auto p-10 relative">
#                 </div>

#             <footer class="bg-white px-8 py-4 border-t border-slate-100 flex justify-between items-center shrink-0">
#                 <button onclick="prevSlide(event)" class="text-slate-400 hover:text-indigo-600 font-semibold px-4 py-2 hover:bg-slate-50 rounded transition">
#                     ← Back
#                 </button>
#                 <div class="text-xs text-slate-400">Click anywhere to continue</div>
#                 <button onclick="nextStep()" class="bg-indigo-600 text-white px-6 py-2 rounded-full font-semibold shadow-lg hover:bg-indigo-700 transition">
#                     Next →
#                 </button>
#             </footer>
#         </main>
#     </div>

#     <script>
#         // Python injects the slides array here
#         const SLIDES = {js_slides_data};
        
#         let currentSlideIdx = 0;

#         // --- INITIALIZATION ---
#         function renderSlide(index) {{
#             if (index < 0 || index >= SLIDES.length) return;
            
#             currentSlideIdx = index;
#             const slide = SLIDES[index];

#             // Update Text
#             document.getElementById('header-title').innerText = slide.title;
#             document.getElementById('slide-counter').innerText = `Slide ${{index + 1}} / ${{SLIDES.length}}`;

#             // Update HTML Content
#             const contentArea = document.getElementById('content-area');
#             contentArea.innerHTML = slide.html;
            
#             // Reset Scroll
#             contentArea.scrollTop = 0;

#             // PREPARE ANIMATIONS
#             // 1. Hide all elements marked with 'reveal-item'
#             const items = contentArea.querySelectorAll('.reveal-item');
#             items.forEach(el => {{
#                 el.classList.remove('visible');
#             }});
#         }}

#         // --- CORE INTERACTION LOGIC ---
#         function handleGlobalClick(e) {{
#             // Prevent triggering if clicking a button explicitly
#             if (e.target.tagName === 'BUTTON' || e.target.closest('button')) return;
            
#             nextStep();
#         }}

#         function nextStep() {{
#             const contentArea = document.getElementById('content-area');
            
#             // 1. Find the next hidden item
#             const hiddenItem = contentArea.querySelector('.reveal-item:not(.visible)');
            
#             if (hiddenItem) {{
#                 // Reveal it
#                 hiddenItem.classList.add('visible');
#                 // Auto-scroll if it's near the bottom
#                 hiddenItem.scrollIntoView({{ behavior: 'smooth', block: 'nearest' }});
#             }} else {{
#                 // All items visible? Go to next slide
#                 if (currentSlideIdx < SLIDES.length - 1) {{
#                     renderSlide(currentSlideIdx + 1);
#                 }} else {{
#                     alert("End of Lesson!");
#                 }}
#             }}
#         }}

#         function prevSlide(e) {{
#             e.stopPropagation(); // Don't trigger the 'next' click
#             if (currentSlideIdx > 0) {{
#                 renderSlide(currentSlideIdx - 1);
#             }}
#         }}

#         // Start
#         window.onload = () => renderSlide(0);
        
#         // Keyboard Support
#         document.addEventListener('keydown', (e) => {{
#             if (e.key === "ArrowRight" || e.key === " " || e.key === "Enter") nextStep();
#             if (e.key === "ArrowLeft") prevSlide(e);
#         }});

#     </script>
# </body>
# </html>
# """



HTML_PLAYER_SHELL = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Course Material</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        html {{ scroll-behavior: smooth; }}
        body {{ font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; }}
        
        /* Custom Animation */
        {custom_animation_css}

        /* The item is hidden but takes up space in flow? 
           Actually for 'reveal' we usually want it hidden entirely or opaque.
           Let's stick to opacity/transform so layout doesn't jump */
        .reveal-item {{
            /* Initial state handled by classes in determing_css_animation */
        }}

        /* Scrollbar */
        ::-webkit-scrollbar {{ width: 12px; }}
        ::-webkit-scrollbar-track {{ background: #f8fafc; }}
        ::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 6px; border: 3px solid #f8fafc; }}
        ::-webkit-scrollbar-thumb:hover {{ background: #94a3b8; }}
    </style>
</head>
<body class="bg-slate-100 min-h-screen">

    <header class="fixed top-0 inset-x-0 h-20 bg-white/95 backdrop-blur-md shadow-sm z-50 flex items-center justify-between px-6 border-b border-gray-200">
        <div class="flex items-center gap-4">
            <img src="{logo_image}" class="h-10 w-auto object-contain" alt="Logo">
            <div class="h-8 w-px bg-gray-300 mx-2"></div>
            <h1 class="text-lg font-semibold text-gray-700">Course Overview</h1>
        </div>
        
        <div class="flex items-center gap-4">
            <div class="text-sm font-bold text-indigo-600 bg-indigo-50 px-3 py-1 rounded-full" id="progress-indicator">
                0% Complete
            </div>
        </div>
    </header>

    <div class="w-full max-w-4xl mx-auto pt-28 pb-32 px-4">
        
        <main id="document-card" class="bg-white rounded-3xl shadow-xl border border-white/50 overflow-hidden min-h-[80vh]">
            </main>

    </div>

    <button onclick="nextStep()" class="fixed bottom-10 right-10 z-50 bg-indigo-600 hover:bg-indigo-700 text-white shadow-2xl rounded-full p-4 transition-all hover:scale-110 group flex items-center gap-2 pr-6">
        <span class="bg-white/20 rounded-full w-8 h-8 flex items-center justify-center">▼</span>
        <span class="font-bold">Next</span>
    </button>

    <script>
        const SLIDES = {js_slides_data};
        
        window.onload = function() {{
            const container = document.getElementById('document-card');
            
            SLIDES.forEach((slide, index) => {{
                // Create a Section Wrapper for each slide
                const section = document.createElement('section');
                section.className = "p-12 relative group";
                
                // Add a divider for all except the first one
                const borderHtml = index === 0 ? '' : '<hr class="my-12 border-slate-100">';
                
                // Slide Title styling
                const titleHtml = `
                    <div class="mb-8">
                        <span class="text-xs font-bold tracking-wider text-slate-400 uppercase">Part ${{index + 1}}</span>
                        <h2 class="text-3xl font-bold {header_color} mt-1">${{slide.title}}</h2>
                    </div>
                `;

                // Inject content
                section.innerHTML = borderHtml + titleHtml + slide.html;
                container.appendChild(section);
            }});

            // Initial cleanup of reveal items
            document.querySelectorAll('.reveal-item').forEach(el => el.classList.remove('visible'));
            updateProgress();
        }};

        // --- GLOBAL CLICK & SCROLL LOGIC ---
        
        function nextStep() {{
            const hiddenItem = document.querySelector('.reveal-item:not(.visible)');
            
            if (hiddenItem) {{
                hiddenItem.classList.add('visible');
                
                // Scroll logic: slightly offset so it's not hidden behind header
                const headerOffset = 100; 
                const elementPosition = hiddenItem.getBoundingClientRect().top;
                const offsetPosition = elementPosition + window.pageYOffset - headerOffset - (window.innerHeight / 3);
            
                window.scrollTo({{
                    top: offsetPosition,
                    behavior: "smooth"
                }});

                updateProgress();
            }} else {{
                // Optional: Scroll to bottom if done
                window.scrollTo({{ top: document.body.scrollHeight, behavior: 'smooth' }});
            }}
        }}

        function updateProgress() {{
            const total = document.querySelectorAll('.reveal-item').length;
            const visible = document.querySelectorAll('.reveal-item.visible').length;
            if (total === 0) return;
            const pct = Math.round((visible / total) * 100);
            document.getElementById('progress-indicator').innerText = `${{pct}}%`;
        }}

        // Click anywhere (except button) triggers next
        document.addEventListener('click', (e) => {{
            if (e.target.closest('button') || e.target.tagName === 'A') return;
            nextStep();
        }});

        // Keyboard navigation
        document.addEventListener('keydown', (e) => {{
            if (e.key === "ArrowRight" || e.key === " " || e.key === "Enter") {{
                e.preventDefault();
                nextStep();
            }}
        }});
    </script>
</body>
</html>
"""

# ================= MAIN LOGIC =================

def process_slides():
    print("🎨 Preparing Assets...")
    
    bg_b64 = encode_image_to_base64(BACKGROUND_IMAGE_PATH)
    logo_b64 = encode_image_to_base64(LOGO_IMAGE_PATH)
    
    # Generate Custom CSS based on User Prompt
    anim_css = determine_css_animation(ANIMATION_PROMPT)

    if not os.path.exists(INPUT_JSON_PATH):
        print(f"❌ Error: {INPUT_JSON_PATH} not found.")
        return

    with open(INPUT_JSON_PATH, 'r', encoding='utf-8') as f:
        slides_data = json.load(f)

    processed_slides = []
    
    print(f"🚀 Generating {len(slides_data)} slides...")

    for index, slide in enumerate(slides_data):
        slide_title = slide.get('main_title', f'Slide {index+1}')
        print(f"   Processing: {slide_title}...")
        
        # Image handling
        slide_img_raw = slide.get('image_path')
        slide_img_b64 = encode_image_to_base64(slide_img_raw)
        has_slide_img = True if slide_img_b64 else False
        
        # Generate HTML content via LLM
        prompt = generate_content_prompt(slide, has_slide_img)
        
        try:
            response = llm.invoke([
                SystemMessage(content="You are a web helper. Output valid HTML fragments only."),
                HumanMessage(content=prompt)
            ])
            
            content = response.content
            # Cleanup code blocks
            if "```html" in content: content = content.split("```html")[1].split("```")[0]
            elif "```" in content: content = content.split("```")[1].split("```")[0]

            # Inject Image Base64
            if has_slide_img and "SLIDE_IMAGE_PLACEHOLDER" in content:
                content = content.replace("SLIDE_IMAGE_PLACEHOLDER", slide_img_b64)
            
            # Store structured data
            processed_slides.append({
                "title": slide_title,
                "html": content
            })

        except Exception as e:
            print(f"   ❌ Error generating content: {e}")

    # Convert Python List to JSON string for JS injection
    js_slides_data = json.dumps(processed_slides)

    # Fill the Shell
    final_html = HTML_PLAYER_SHELL.format(
        bg_image=bg_b64,
        logo_image=logo_b64,
        js_slides_data=js_slides_data,
        custom_animation_css=anim_css,
        # Branding
        bg_accent=C_BG_ACCENT,
        header_color=C_HEADER,
        primary_color=C_PRIMARY,
        border_color=C_BORDER
    )

    # Save ONE file
    output_file = os.path.join(OUTPUT_DIR, "index.html")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"\n✅ SUCCESS! Generated Single Page Lesson: {output_file}")
    webbrowser.open('file://' + os.path.realpath(output_file))

if __name__ == "__main__":
    process_slides()