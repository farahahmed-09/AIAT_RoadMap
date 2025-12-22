
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
             <img src="SLIDE_IMAGE_PLACEHOLDER" class="img-zoomable cursor-zoom-in float-right ml-8 mb-6 w-5/12 max-w-sm rounded-lg shadow-md border {C_BORDER} hover:shadow-xl transition-shadow duration-300">
             <div class="space-y-4">
                </div>
          </div>
        """

    prompt = f"""
    You are a Content Developer.
    **Task:** Write inner HTML for a document section.
    **Context:** {content_context}
    
    **CRITICAL REQUIREMENT:**
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
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <style>
        html {{ scroll-behavior: smooth; }}
        body {{ font-family: 'Segoe UI', Roboto, sans-serif; transition: background 0.3s; }}
        
        /* --- DYNAMIC ANIMATION CSS --- */
        {custom_animation_css}

        /* --- REVEAL LOGIC --- */
        .reveal-item {{
            /* handled by custom_animation_css */
        }}
        body.reveal-disabled .reveal-item {{
            opacity: 1 !important;
            transform: none !important;
            filter: none !important;
            pointer-events: auto !important;
        }}

        /* --- LAYOUT UTILS --- */
        .sidebar-expanded {{ width: 230px; }}
        .sidebar-collapsed {{ width: 100px; }}
        
        /* --- IMAGE ZOOM STYLES --- */
        #zoom-backdrop {{
            position: fixed; inset: 0;
            /* Changed background to white with transparency */
            background: rgba(255, 255, 255, 0.75); 
            z-index: 9990;
            opacity: 0; pointer-events: none; transition: opacity 0.3s ease;
            /* Increased blur for frosted glass effect */
            backdrop-filter: blur(10px);
        }}
        #zoom-backdrop.active {{ opacity: 1; pointer-events: auto; }}
        
        /* Target ALL images inside the main card automatically */
        main img {{
            cursor: zoom-in !important;  /* Force the icon */
            position: relative;          /* Prepare for z-index */
            z-index: 10;                 /* Lift image ABOVE invisible text blocks */
            display: inline-block;       /* Solid hit-area */
            transition: transform 0.2s;
        }}
        main img:hover {{
            transform: scale(1.02);
        }}

        .img-zoomed {{
            cursor: zoom-out !important;
            z-index: 9999 !important;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5) !important;
            border-radius: 8px;
        }}

        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 4px; }}
    </style>
</head>
<body class="bg-slate-100 min-h-screen flex overflow-hidden">

    <div id="zoom-backdrop" onclick="closeAllZooms()"></div>

    <aside class="bg-gray-900 text-white flex-shrink-0 flex flex-col transition-all duration-300 z-50 shadow-2xl sidebar-expanded" id="sidebar">
        <div class="p-6 flex items-center gap-3 border-b border-gray-700 h-20">
            <div class="w-8 h-8 bg-indigo-500 rounded-lg flex items-center justify-center font-bold">AI</div>
            <span class="font-bold text-lg tracking-wide sidebar-text">Controls</span>
        </div>
        <div class="p-6 flex-1 overflow-y-auto space-y-8">
            <div>
                <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-4 sidebar-text">Layout Style</h3>
                <div class="flex flex-col gap-2">
                    <button onclick="setMode('layout', 'vertical')" id="btn-vertical" class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all border border-gray-700 hover:bg-gray-800 bg-indigo-600 border-indigo-500">
                        <i class="fas fa-scroll w-5"></i>
                        <span class="sidebar-text text-sm">Vertical Scroll</span>
                    </button>
                    <button onclick="setMode('layout', 'horizontal')" id="btn-horizontal" class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all border border-gray-700 hover:bg-gray-800 text-gray-400">
                        <i class="fas fa-tv w-5"></i>
                        <span class="sidebar-text text-sm">Slideshow</span>
                    </button>
                </div>
            </div>
            <div>
                <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-4 sidebar-text">Animation</h3>
                <div class="flex flex-col gap-2">
                    <button onclick="setMode('reveal', 'click')" id="btn-click" class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all border border-gray-700 hover:bg-gray-800 bg-indigo-600 border-indigo-500">
                        <i class="fas fa-mouse-pointer w-5"></i>
                        <span class="sidebar-text text-sm">Click to Reveal</span>
                    </button>
                    <button onclick="setMode('reveal', 'all')" id="btn-all" class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all border border-gray-700 hover:bg-gray-800 text-gray-400">
                        <i class="fas fa-eye w-5"></i>
                        <span class="sidebar-text text-sm">Show All</span>
                    </button>
                </div>
            </div>
            <div class="pt-8 border-t border-gray-800 sidebar-text">
                <div class="text-xs text-gray-500 mb-2">PROGRESS</div>
                <div class="text-2xl font-bold text-indigo-400" id="progress-pct">0%</div>
            </div>
        </div>
        <button onclick="toggleSidebar()" class="p-4 bg-gray-800 hover:bg-gray-700 border-t border-gray-700 flex justify-center">
             <i class="fas fa-bars"></i>
        </button>
    </aside>

    <div class="flex-1 relative h-screen overflow-y-auto bg-slate-100" id="main-scroll-container">
        
        <header class="bg-white/90 backdrop-blur sticky top-0 z-40 px-8 py-4 border-b border-gray-200 flex justify-between items-center shadow-sm">
            <div class="flex items-center gap-4">
                 <img src="{logo_image}" class="h-10 w-auto object-contain" alt="Logo">
                 <h1 class="text-xl font-bold text-gray-800">Course Viewer</h1>
            </div>
            <div id="slide-counter" class="text-sm font-bold text-gray-400"></div>
        </header>

        <div id="app-container" class="max-w-5xl mx-auto px-6 py-10 pb-32 min-h-full">
            </div>

        <button id="float-next-btn" onclick="handleMainAction()" class="fixed bottom-10 right-10 z-50 bg-indigo-600 text-white px-6 py-4 rounded-full font-bold shadow-2xl hover:bg-indigo-700 hover:scale-105 transition flex items-center gap-2">
            <span>Next</span> <i class="fas fa-chevron-down"></i>
        </button>

    </div>

    <script>
        const SLIDES = {js_slides_data};
        const state = {{ layout: 'vertical', reveal: 'click', currentSlideIdx: 0 }};
        const container = document.getElementById('app-container');
        const scrollContainer = document.getElementById('main-scroll-container');
        const nextBtn = document.getElementById('float-next-btn');
        const backdrop = document.getElementById('zoom-backdrop');

        window.onload = () => {{ renderApp(); updateButtonStyles(); }};

        // --- ROBUST ZOOM LOGIC ---
        // 1. Listen for clicks on ANY image inside the main container
        document.addEventListener('click', (e) => {{
            // Check if user clicked an IMG tag inside our main content
            if (e.target.tagName === 'IMG' && e.target.closest('main')) {{
                toggleZoom(e.target);
                e.stopPropagation(); // Stop the click from triggering "Next Slide"
            }}
        }});

        function toggleZoom(img) {{
            const isZoomed = img.classList.contains('img-zoomed');
            
            if (isZoomed) {{
                // ZOOM OUT
                img.classList.remove('img-zoomed');
                backdrop.classList.remove('active');
                
                const placeholder = img.previousElementSibling;
                if (placeholder && placeholder.classList.contains('zoom-placeholder')) {{
                    const rect = placeholder.getBoundingClientRect();
                    
                    // Animate back to original spot
                    img.style.transform = 'none';
                    img.style.top = rect.top + 'px';
                    img.style.left = rect.left + 'px';
                    img.style.width = rect.width + 'px';
                    img.style.height = rect.height + 'px';
                    
                    setTimeout(() => {{
                        img.style.position = '';
                        img.style.top = '';
                        img.style.left = '';
                        img.style.width = '';
                        img.style.height = '';
                        img.style.zIndex = '';
                        img.style.transition = '';
                        placeholder.remove();
                    }}, 300);
                }}
            }} else {{
                // ZOOM IN
                const rect = img.getBoundingClientRect();
                const computedStyle = window.getComputedStyle(img);
                
                // 1. Create Placeholder
                const placeholder = document.createElement('div');
                placeholder.className = 'zoom-placeholder';
                placeholder.style.width = rect.width + 'px';
                placeholder.style.height = rect.height + 'px';
                placeholder.style.float = computedStyle.float; 
                placeholder.style.marginBottom = computedStyle.marginBottom;
                placeholder.style.marginLeft = computedStyle.marginLeft;
                placeholder.style.marginRight = computedStyle.marginRight;
                
                img.parentNode.insertBefore(placeholder, img);
                
                // 2. Fix image position
                img.style.position = 'fixed';
                img.style.top = rect.top + 'px';
                img.style.left = rect.left + 'px';
                img.style.width = rect.width + 'px';
                img.style.height = rect.height + 'px';
                img.style.zIndex = '9999';
                img.style.transition = 'all 0.4s cubic-bezier(0.19, 1, 0.22, 1)';
                
                // Force Reflow
                void img.offsetWidth;
                
                // 3. Animate to Center
                img.classList.add('img-zoomed');
                img.style.top = '50%';
                img.style.left = '50%';
                img.style.transform = 'translate(-50%, -50%)';
                // Reset sizes to natural or max screen size
                img.style.width = 'auto';
                img.style.height = 'auto';
                img.style.maxWidth = '90vw';
                img.style.maxHeight = '90vh';
                img.style.margin = '0';
                
                backdrop.classList.add('active');
            }}
        }}
        
        function closeAllZooms() {{
            const zoomed = document.querySelector('.img-zoomed');
            if (zoomed) toggleZoom(zoomed);
        }}

        // --- RENDER & SETTINGS ---
        function setMode(type, value) {{
            state[type] = value;
            updateButtonStyles();
            if (type === 'layout') renderApp();
            if (type === 'reveal') toggleRevealClass();
        }}

        function updateButtonStyles() {{
            const setActive = (id, isActive) => {{
                const el = document.getElementById(id);
                if (isActive) {{
                    el.classList.add('bg-indigo-600', 'border-indigo-500', 'text-white');
                    el.classList.remove('text-gray-400');
                }} else {{
                    el.classList.remove('bg-indigo-600', 'border-indigo-500', 'text-white');
                    el.classList.add('text-gray-400');
                }}
            }};
            setActive('btn-vertical', state.layout === 'vertical');
            setActive('btn-horizontal', state.layout === 'horizontal');
            setActive('btn-click', state.reveal === 'click');
            setActive('btn-all', state.reveal === 'all');
            toggleRevealClass();
        }}

        function toggleRevealClass() {{
            if (state.reveal === 'all') {{
                document.body.classList.add('reveal-disabled');
                nextBtn.innerHTML = (state.layout === 'horizontal') ? 'Next Slide <i class="fas fa-arrow-right"></i>' : 'Scroll Down <i class="fas fa-arrow-down"></i>';
            }} else {{
                document.body.classList.remove('reveal-disabled');
                nextBtn.innerHTML = 'Next Step <i class="fas fa-chevron-down"></i>';
            }}
        }}

        function renderApp() {{
            container.innerHTML = '';
            if (state.layout === 'vertical') renderVerticalLayout();
            else renderHorizontalLayout();
        }}

        function renderVerticalLayout() {{
            const card = document.createElement('main');
            card.className = "bg-white rounded-3xl shadow-xl border border-gray-200 overflow-hidden";
            let fullHtml = '';
            SLIDES.forEach((slide, index) => {{
                const divider = index === 0 ? '' : '<hr class="my-12 border-gray-100">';
                fullHtml += `
                    <section class="p-10" id="slide-sec-${{index}}">
                        ${{divider}}
                        <div class="mb-6">
                            <span class="text-xs font-bold text-gray-400 uppercase tracking-wider">Part ${{index + 1}}</span>
                            <h2 class="text-3xl font-bold {header_color}">${{slide.title}}</h2>
                        </div>
                        <div class="prose max-w-none text-gray-600">
                            ${{slide.html}}
                        </div>
                    </section>
                `;
            }});
            card.innerHTML = fullHtml;
            container.appendChild(card);
            document.querySelectorAll('.reveal-item').forEach(el => el.classList.remove('visible'));
        }}

        function renderHorizontalLayout() {{
            const slide = SLIDES[state.currentSlideIdx];
            const card = document.createElement('main');
            card.className = "bg-white rounded-3xl shadow-2xl border border-gray-200 overflow-hidden p-12 min-h-[600px] flex flex-col animation-fade";
            card.innerHTML = `
                <div class="border-b border-gray-100 pb-6 mb-6 flex justify-between items-center">
                    <h2 class="text-3xl font-bold {header_color}">${{slide.title}}</h2>
                    <span class="bg-gray-100 text-gray-500 text-xs font-bold px-3 py-1 rounded-full">Slide ${{state.currentSlideIdx + 1}} / ${{SLIDES.length}}</span>
                </div>
                <div class="prose max-w-none text-gray-600 flex-1">
                    ${{slide.html}}
                </div>
                <div class="flex justify-between mt-8 pt-6 border-t border-gray-50">
                     <button onclick="prevSlide()" class="text-gray-400 hover:text-indigo-600 font-bold px-4 py-2 hover:bg-indigo-50 rounded-lg transition">← Back</button>
                     <div class="text-xs text-gray-300 self-center">Use Spacebar or Next Button</div>
                </div>
            `;
            container.appendChild(card);
            if (state.reveal === 'click') {{
                 card.querySelectorAll('.reveal-item').forEach(el => el.classList.remove('visible'));
            }}
        }}

        function handleMainAction() {{
            if (state.reveal === 'click') {{
                const hiddenItem = container.querySelector('.reveal-item:not(.visible)');
                if (hiddenItem) {{
                    hiddenItem.classList.add('visible');
                    hiddenItem.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    updateProgress();
                    return;
                }}
            }}
            if (state.layout === 'horizontal') nextSlide();
            else scrollContainer.scrollBy({{ top: 300, behavior: 'smooth' }});
        }}

        function nextSlide() {{
            if (state.currentSlideIdx < SLIDES.length - 1) {{
                state.currentSlideIdx++;
                renderApp();
                scrollContainer.scrollTop = 0;
            }} else {{ alert("End of Course!"); }}
        }}

        function prevSlide() {{
            if (state.currentSlideIdx > 0) {{
                state.currentSlideIdx--;
                renderApp();
                scrollContainer.scrollTop = 0;
            }}
        }}

        function updateProgress() {{
            const total = document.querySelectorAll('.reveal-item').length;
            const visible = document.querySelectorAll('.reveal-item.visible').length;
            if (total > 0) {{
                const pct = Math.round((visible / total) * 100);
                document.getElementById('progress-pct').innerText = pct + "%";
            }}
        }}

        function toggleSidebar() {{
            const sb = document.getElementById('sidebar');
            if (sb.classList.contains('sidebar-expanded')) {{
                sb.classList.remove('sidebar-expanded');
                sb.classList.add('sidebar-collapsed');
                document.querySelectorAll('.sidebar-text').forEach(el => el.classList.add('hidden'));
            }} else {{
                sb.classList.remove('sidebar-collapsed');
                sb.classList.add('sidebar-expanded');
                document.querySelectorAll('.sidebar-text').forEach(el => el.classList.remove('hidden'));
            }}
        }}

        document.addEventListener('keydown', (e) => {{
            if (e.key === "ArrowRight" || e.key === " " || e.key === "Enter") {{ e.preventDefault(); handleMainAction(); }}
            if (e.key === "ArrowLeft" && state.layout === 'horizontal') prevSlide();
            if (e.key === "Escape") closeAllZooms();
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