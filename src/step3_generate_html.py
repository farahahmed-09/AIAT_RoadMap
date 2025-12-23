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
OUTPUT_DIR = r"D:\AIAT_roadmap\output_html"
BACKGROUND_IMAGE_PATH = config["paths"]["background_image"]
LOGO_IMAGE_PATH = config["paths"]["logo_image"]
ANIMATION_PROMPT = config.get("animation", {}).get("style_prompt", "fade") 

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

def encode_image_to_base64(image_path: str) -> str:
    if not image_path or not os.path.exists(image_path):
        return "" 
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        ext = os.path.splitext(image_path)[1].lower()
        if ext == ".svg": mime_type = "image/svg+xml"
        elif ext == ".png": mime_type = "image/png"
        elif ext in [".jpg", ".jpeg"]: mime_type = "image/jpeg"
        else: mime_type = "image/octet-stream" 
        return f"data:{mime_type};base64,{encoded_string}"
    except Exception as e:
        print(f"Warning: Could not encode image at {image_path}: {e}")
        return ""

def determine_css_animation(prompt_text):
    prompt_text = prompt_text.lower()
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
        :root {{
            --theme-color: #4f46e5; 
        }}

        html {{ scroll-behavior: smooth; }}
        body {{ 
            font-family: 'Segoe UI', Roboto, sans-serif; 
            transition: background 0.3s, color 0.3s; 
        }}
        
        .theme-bg {{ background-color: var(--theme-color) !important; }}
        .theme-text {{ color: var(--theme-color) !important; }}
        .theme-border {{ border-color: var(--theme-color) !important; }}
        
        main h1, main h2, main h3, main h4, main strong, main b {{
            color: var(--theme-color) !important;
        }}
        main ul li::marker {{
            color: var(--theme-color) !important;
        }}

        body.dark-mode {{ background-color: #0f172a; color: #cbd5e1; }}
        body.dark-mode main {{ 
            background-color: #1e293b !important; 
            border-color: #334155 !important; 
            color: #e2e8f0 !important;
        }}
        body.dark-mode p, body.dark-mode li {{ color: #cbd5e1 !important; }}
        body.dark-mode .bg-gray-100 {{ background-color: #334155 !important; color: #cbd5e1 !important; }}
        body.dark-mode hr {{ border-color: #334155 !important; }}
        body.dark-mode #zoom-backdrop {{ background: rgba(0, 0, 0, 0.85); }}

        {custom_animation_css}

        body.reveal-disabled .reveal-item {{
            opacity: 1 !important; transform: none !important; filter: none !important; pointer-events: auto !important;
        }}

        .editing-mode {{
            border: 2px dashed var(--theme-color); padding: 10px; border-radius: 8px;
            background-color: rgba(255, 255, 255, 0.5); outline: none; cursor: text;
        }}
        body.dark-mode .editing-mode {{ background-color: rgba(0, 0, 0, 0.2); }}

        .sidebar-expanded {{ width: 220px; }}
        .sidebar-collapsed {{ width: 120px; }}
        
        #zoom-backdrop {{
            position: fixed; inset: 0; background: rgba(255, 255, 255, 0.75); z-index: 9990;
            opacity: 0; pointer-events: none; transition: opacity 0.3s ease; backdrop-filter: blur(10px);
        }}
        #zoom-backdrop.active {{ opacity: 1; pointer-events: auto; }}
        
        main img {{
            cursor: zoom-in !important; position: relative; z-index: 10; display: inline-block; 
            transition: transform 0.2s; border-radius: 8px;
        }}
        main img:hover {{ transform: scale(1.02); z-index: 20; }}
        .img-zoomed {{
            cursor: zoom-out !important; z-index: 9999 !important;
            box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5) !important;
        }}

        ::-webkit-scrollbar {{ width: 8px; }}
        ::-webkit-scrollbar-track {{ background: transparent; }}
        ::-webkit-scrollbar-thumb {{ background: #cbd5e1; border-radius: 4px; }}
        body.dark-mode ::-webkit-scrollbar-thumb {{ background: #475569; }}

        #ai-edit-modal {{
            display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
            background-color: rgba(0,0,0,0.6); z-index: 10000; align-items: center; justify-content: center; backdrop-filter: blur(4px);
        }}
        #ai-edit-modal.active {{ display: flex; }}

        .ai-modal-content {{
            background: white; width: 500px; max-width: 90%; padding: 25px; border-radius: 12px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.3); border: 1px solid #e0e0e0; font-family: sans-serif; animation: popIn 0.3s ease-out;
        }}
        body.dark-mode .ai-modal-content {{ background: #1e293b; border-color: #334155; color: #fff; }}

        @keyframes popIn {{ from {{ transform: scale(0.9); opacity: 0; }} to {{ transform: scale(1); opacity: 1; }} }}

        .ai-modal-header {{ font-size: 18px; font-weight: bold; margin-bottom: 15px; display: flex; justify-content: space-between; align-items: center; }}
        .ai-input-area {{
            width: 100%; height: 100px; padding: 12px; border: 1px solid #ccc; border-radius: 8px;
            font-size: 14px; resize: none; box-sizing: border-box; margin-bottom: 15px; transition: border 0.2s;
        }}
        body.dark-mode .ai-input-area {{ background: #0f172a; border-color: #475569; color: white; }}
        .ai-input-area:focus {{ border-color: var(--theme-color); outline: none; }}
        
        .ai-actions {{ display: flex; justify-content: flex-end; gap: 10px; }}
        .btn-ai-cancel {{ padding: 8px 16px; border: none; background: transparent; color: #666; cursor: pointer; font-weight: 600; }}
        body.dark-mode .btn-ai-cancel {{ color: #aaa; }}
        .btn-ai-generate {{
            padding: 8px 20px; border: none; background: linear-gradient(135deg, #6366f1, #8b5cf6);
            color: white; border-radius: 6px; cursor: pointer; font-weight: 600; box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            display: flex; align-items: center; gap: 8px; transition: transform 0.1s;
        }}
        .btn-ai-generate:active {{ transform: scale(0.98); }}
        .btn-ai-generate:disabled {{ opacity: 0.7; cursor: not-allowed; }}
        
        .ai-magic-btn {{
            background: linear-gradient(135deg, #f43f5e, #ec4899); color: white; border: none;
            width: 32px; height: 32px; border-radius: 50%; cursor: pointer; display: inline-flex; align-items: center; justify-content: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2); transition: transform 0.2s; margin-left: 5px;
        }}
        .ai-napkin-btn {{
             background: linear-gradient(135deg, #10b981, #34d399); color: white; border: none;
            width: 32px; height: 32px; border-radius: 50%; cursor: pointer; display: inline-flex; align-items: center; justify-content: center;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2); transition: transform 0.2s; margin-left: 5px;
        }}
        .ai-magic-btn:hover, .ai-napkin-btn:hover {{ transform: scale(1.1) rotate(10deg); }}

        .loading-spinner {{
            width: 16px; height: 16px; border: 2px solid #ffffff; border-top: 2px solid transparent; border-radius: 50%; animation: spin 1s linear infinite;
        }}
        @keyframes spin {{ 0% {{ transform: rotate(0deg); }} 100% {{ transform: rotate(360deg); }} }}
    </style>
</head>
<body class="bg-slate-100 min-h-screen flex overflow-hidden">

    <div id="zoom-backdrop" onclick="closeAllZooms()"></div>

    <div id="ai-edit-modal">
        <div class="ai-modal-content">
            <div class="ai-modal-header">
                <span id="ai-modal-title"><i class="fas fa-magic" style="margin-right:8px; color: #8b5cf6;"></i> AI Edit</span>
                <button onclick="closeAIModal()" style="background:none; border:none; cursor:pointer; font-size:20px; color:#999;">&times;</button>
            </div>
            <p id="ai-modal-desc" style="margin-bottom: 10px; font-size: 13px; opacity: 0.7;">
                Describe your changes.
            </p>
            <textarea id="ai-prompt-input" class="ai-input-area" placeholder="Enter your instructions here..."></textarea>
            <div class="ai-actions">
                <button class="btn-ai-cancel" onclick="closeAIModal()">Cancel</button>
                <button class="btn-ai-generate" onclick="handleAIModalSubmit()" id="btn-ai-submit">
                    <span>Generate</span> <i class="fas fa-wand-magic-sparkles"></i>
                </button>
            </div>
        </div>
    </div>

    <aside class="h-screen bg-gray-900 text-white flex-shrink-0 flex flex-col transition-all duration-300 z-50 shadow-2xl sidebar-expanded" id="sidebar">
        <div class="p-6 flex items-center justify-between border-b border-gray-700 h-20">
            <div class="flex items-center gap-3 overflow-hidden">
                <div class="w-8 h-8 rounded-lg flex-shrink-0 flex items-center justify-center font-bold theme-bg text-white transition-colors duration-300">AI</div>
                <span class="font-bold text-lg tracking-wide sidebar-text whitespace-nowrap opacity-100 transition-opacity">Controls</span>
            </div>
            <button onclick="toggleSidebar()" class="w-8 h-8 flex items-center justify-center rounded-full bg-gray-800 hover:bg-gray-700 text-gray-400 hover:text-white transition-all focus:outline-none">
                <i class="fas fa-chevron-left transition-transform duration-300" id="sidebar-toggle-icon"></i>
            </button>
        </div>
        <div class="p-6 flex-1 overflow-y-auto space-y-8 custom-scrollbar">
            <div>
                <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-4 sidebar-text">Appearance</h3>
                <button onclick="toggleDarkMode()" class="w-full flex items-center justify-between px-4 py-3 rounded-xl border border-gray-700 hover:bg-gray-800 transition mb-4">
                    <span class="sidebar-text text-sm flex items-center gap-2"><i class="fas fa-moon"></i> Dark Mode</span>
                    <div class="w-10 h-5 bg-gray-700 rounded-full relative" id="dm-toggle-bg">
                        <div class="w-5 h-5 bg-white rounded-full absolute left-0 transition-all duration-300" id="dm-toggle-dot"></div>
                    </div>
                </button>
                <div class="flex gap-2 justify-between sidebar-text">
                    <button onclick="setTheme('#6366f1')" data-color="#6366f1" class="theme-btn w-8 h-8 rounded-full bg-[#6366f1] border-2 border-transparent hover:scale-110 transition" title="Indigo"></button>
                    <button onclick="setTheme('#f43f5e')" data-color="#f43f5e" class="theme-btn w-8 h-8 rounded-full bg-[#f43f5e] border-2 border-transparent hover:scale-110 transition" title="Rose"></button>
                    <button onclick="setTheme('#10b981')" data-color="#10b981" class="theme-btn w-8 h-8 rounded-full bg-[#10b981] border-2 border-transparent hover:scale-110 transition" title="Emerald"></button>
                    <button onclick="setTheme('#f59e0b')" data-color="#f59e0b" class="theme-btn w-8 h-8 rounded-full bg-[#f59e0b] border-2 border-transparent hover:scale-110 transition" title="Amber"></button>
                    <button onclick="setTheme('#0ea5e9')" data-color="#0ea5e9" class="theme-btn w-8 h-8 rounded-full bg-[#0ea5e9] border-2 border-transparent hover:scale-110 transition" title="Sky"></button>
                </div>
            </div>
            <hr class="border-gray-800">
            <div>
                <h3 class="text-xs font-bold text-gray-500 uppercase tracking-wider mb-4 sidebar-text">Layout</h3>
                <div class="flex flex-col gap-2">
                    <button onclick="setMode('layout', 'vertical')" id="btn-vertical" class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all border border-gray-700 hover:bg-gray-800">
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
                    <button onclick="setMode('reveal', 'click')" id="btn-click" class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all border border-gray-700 hover:bg-gray-800">
                        <i class="fas fa-mouse-pointer w-5"></i>
                        <span class="sidebar-text text-sm">Click to Reveal</span>
                    </button>
                    <button onclick="setMode('reveal', 'all')" id="btn-all" class="flex items-center gap-3 px-4 py-3 rounded-xl transition-all border border-gray-700 hover:bg-gray-800 text-gray-400">
                        <i class="fas fa-eye w-5"></i>
                        <span class="sidebar-text text-sm">Show All</span>
                    </button>
                </div>
            </div>
             <div class="pt-4 border-t border-gray-800 sidebar-text">
                 <button onclick="resetAllEdits()" class="w-full text-left text-xs text-red-400 hover:text-red-300 transition uppercase font-bold tracking-wider">
                    <i class="fas fa-trash-alt mr-2"></i> Reset My Edits
                 </button>
            </div>
            <div class="pt-8 border-t border-gray-800 sidebar-text">
                <div class="text-xs text-gray-500 mb-2">PROGRESS</div>
                <div class="text-2xl font-bold theme-text transition-colors duration-300" id="progress-pct">0%</div>
            </div>
        </div>
    </aside>

    <div class="flex-1 relative h-screen overflow-y-auto transition-colors duration-300" id="main-scroll-container">
        <header class="bg-white/90 backdrop-blur sticky top-0 z-40 px-8 py-4 border-b border-gray-200 flex justify-between items-center shadow-sm transition-colors duration-300 dark:bg-slate-900/90 dark:border-slate-700">
            <div class="flex items-center gap-4">
                 <img src="{logo_image}" class="h-10 w-auto object-contain" alt="Logo">
                 <h1 class="text-xl font-bold text-gray-800 dark:text-white transition-colors">Course Roadmap</h1>
            </div>
            <div id="slide-counter" class="text-sm font-bold text-gray-400"></div>
        </header>

        <div id="app-container" class="max-w-5xl mx-auto px-6 py-10 pb-32 min-h-full transition-colors duration-300"></div>

        <div class="fixed bottom-10 right-10 z-50 flex gap-3">
            <button id="float-prev-btn" onclick="handleBackAction()" class="text-gray-500 bg-white/80 backdrop-blur px-6 py-4 rounded-full font-bold shadow-lg hover:bg-white hover:scale-105 transition-all flex items-center gap-2 border border-gray-200 dark:bg-slate-800/80 dark:text-gray-300 dark:border-slate-600">
                <i class="fas fa-chevron-up" id="prev-icon"></i> <span>Back</span>
            </button>
            <button id="float-next-btn" onclick="handleMainAction()" class="text-white px-6 py-4 rounded-full font-bold shadow-2xl hover:scale-105 transition-all flex items-center gap-2 theme-bg border-2 border-white dark:border-slate-700">
                <span>Next</span> <i class="fas fa-chevron-down" id="next-icon"></i>
            </button>
        </div>
    </div>

    <script>
        // --- DATA INITIALIZATION ---
        const ORIGINAL_SLIDES = {js_slides_data};
        let SLIDES = JSON.parse(JSON.stringify(ORIGINAL_SLIDES)); 
        
        const state = {{ layout: 'vertical', reveal: 'click', currentSlideIdx: 0, darkMode: false, theme: '#6366f1' }};
        const container = document.getElementById('app-container');
        const scrollContainer = document.getElementById('main-scroll-container');
        const nextBtn = document.getElementById('float-next-btn');
        const nextIcon = document.getElementById('next-icon');
        const prevBtn = document.getElementById('float-prev-btn');
        const prevIcon = document.getElementById('prev-icon');
        const backdrop = document.getElementById('zoom-backdrop');

        window.onload = () => {{ 
            loadUserEdits();
            renderApp(); 
            updateButtonStyles(); 
            setTheme(state.theme); 
        }};
        
        // --- EDITING LOGIC ---
        function loadUserEdits() {{
            const saved = localStorage.getItem('my_course_edits');
            if (saved) {{
                try {{
                    const savedSlides = JSON.parse(saved);
                    if (savedSlides.length === SLIDES.length) {{ SLIDES = savedSlides; }}
                }} catch(e) {{ console.error("Error loading edits", e); }}
            }}
        }}

        function toggleEdit(index) {{
            const contentDiv = document.getElementById(`content-${{index}}`);
            const editBtn = document.getElementById(`edit-btn-${{index}}`);
            const aiBtn = document.getElementById(`ai-btn-${{index}}`);
            const napkinBtn = document.getElementById(`napkin-btn-${{index}}`);
            const saveBtn = document.getElementById(`save-btn-${{index}}`);
            
            if (contentDiv) {{
                contentDiv.contentEditable = "true";
                contentDiv.classList.add('editing-mode');
                contentDiv.focus();
                
                if(editBtn) editBtn.classList.add('hidden');
                if(aiBtn) aiBtn.classList.add('hidden');
                if(napkinBtn) napkinBtn.classList.add('hidden');
                if(saveBtn) saveBtn.classList.remove('hidden');
                
                if (state.reveal !== 'all') {{
                    contentDiv.querySelectorAll('.reveal-item').forEach(el => el.classList.add('visible'));
                }}
            }}
        }}

        function saveSlide(index) {{
            const contentDiv = document.getElementById(`content-${{index}}`);
            const editBtn = document.getElementById(`edit-btn-${{index}}`);
            const aiBtn = document.getElementById(`ai-btn-${{index}}`);
            const napkinBtn = document.getElementById(`napkin-btn-${{index}}`);
            const saveBtn = document.getElementById(`save-btn-${{index}}`);

            if (contentDiv) {{
                const newHtml = contentDiv.innerHTML;
                SLIDES[index].html = newHtml;
                persistChanges();
                
                contentDiv.contentEditable = "false";
                contentDiv.classList.remove('editing-mode');
                
                if(editBtn) editBtn.classList.remove('hidden');
                if(aiBtn) aiBtn.classList.remove('hidden');
                if(napkinBtn) napkinBtn.classList.remove('hidden');
                if(saveBtn) saveBtn.classList.add('hidden');
            }}
        }}

        function persistChanges() {{
            localStorage.setItem('my_course_edits', JSON.stringify(SLIDES));
        }}
        
        function resetAllEdits() {{
            if(confirm("Are you sure? This will delete all your text changes and revert to the original course content.")) {{
                localStorage.removeItem('my_course_edits');
                SLIDES = JSON.parse(JSON.stringify(ORIGINAL_SLIDES));
                renderApp();
            }}
        }}

        // --- AI & NAPKIN EDITING LOGIC ---
        let currentEditingIndex = -1;
        let activeModalType = 'text'; // 'text' (Gemini) or 'image' (Napkin)

        function openAIModal(index) {{
            currentEditingIndex = index;
            activeModalType = 'text';
            
            document.getElementById('ai-modal-title').innerHTML = '<i class="fas fa-magic" style="margin-right:8px; color: #8b5cf6;"></i> AI Edit';
            document.getElementById('ai-modal-desc').innerText = 'Describe how you want to change this slide text (e.g. "Make it shorter").';
            document.getElementById('ai-prompt-input').placeholder = "Enter your instructions here...";
            
            document.getElementById('ai-edit-modal').classList.add('active');
            document.getElementById('ai-prompt-input').value = "";
            document.getElementById('ai-prompt-input').focus();
        }}

        function openNapkinModal(index) {{
            currentEditingIndex = index;
            activeModalType = 'image';

            document.getElementById('ai-modal-title').innerHTML = '<i class="fas fa-image" style="margin-right:8px; color: #10b981;"></i> Napkin Visual Gen';
            document.getElementById('ai-modal-desc').innerText = 'Enter the text you want to convert into a visual diagram.';
            document.getElementById('ai-prompt-input').placeholder = "e.g., 'A flow chart showing the process of photosynthesis'";

            document.getElementById('ai-edit-modal').classList.add('active');
            document.getElementById('ai-prompt-input').value = "";
            document.getElementById('ai-prompt-input').focus();
        }}

        function closeAIModal() {{
            document.getElementById('ai-edit-modal').classList.remove('active');
            currentEditingIndex = -1;
        }}
        
        function handleAIModalSubmit() {{
            if(activeModalType === 'text') {{
                executeAIGenerate();
            }} else {{
                executeNapkinGenerate();
            }}
        }}

        // --- GEMINI TEXT GENERATION ---
        async function executeAIGenerate() {{
            const promptText = document.getElementById('ai-prompt-input').value;
            if(!promptText) return;

            let tempKey = window.prompt("Please enter your Gemini API Key:\\n(It will be deleted from memory immediately after use)");
            if (!tempKey) return;

            const submitBtn = document.getElementById('btn-ai-submit');
            const originalBtnContent = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<div class="loading-spinner"></div> Generating...';

            try {{
                let currentHtml = SLIDES[currentEditingIndex].html;
                const imgRegex = /<img[^>]+src=["']data:image\/[^"']+["'][^>]*>/i;
                const imgMatch = currentHtml.match(imgRegex);
                let savedImgTag = null;
                
                if (imgMatch) {{
                    savedImgTag = imgMatch[0];
                    currentHtml = currentHtml.replace(imgRegex, '');
                }}
                
                const systemPrompt = `You are an expert HTML editor. Task: Update provided HTML. Rules: Maintain 'reveal-item' classes. Output raw HTML only.`;
                const userMessage = `CURRENT HTML: ${{currentHtml}}\\nUSER REQUEST: ${{promptText}}\\nOUTPUT NEW HTML:`;

                const response = await fetch(`https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key=${{tempKey}}`, {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ contents: [{{ parts: [{{ text: systemPrompt + "\\n" + userMessage }}] }}] }})
                }});

                tempKey = null; // Security wipe
                const data = await response.json();
                if (data.error) throw new Error(data.error.message);

                let newHtml = data.candidates[0].content.parts[0].text;
                newHtml = newHtml.replace(/```html/g, '').replace(/```/g, '').trim();

                if (savedImgTag) {{
                    if (!newHtml.includes('<img')) {{
                        newHtml = '<div class="clearfix mb-8">' + savedImgTag + '</div>' + newHtml;
                    }}
                }}

                SLIDES[currentEditingIndex].html = newHtml;
                persistChanges();
                refreshSlideView(currentEditingIndex);
                closeAIModal();

            }} catch (err) {{
                alert("AI Generation Failed: " + err.message);
            }} finally {{
                tempKey = null;
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnContent;
            }}
        }}

        // --- NAPKIN IMAGE GENERATION ---
        async function executeNapkinGenerate() {{
            const promptText = document.getElementById('ai-prompt-input').value;
            if(!promptText) return;

            let tempKey = window.prompt("Please enter your Napkin AI API Key:\\n(It will be deleted from memory immediately after use)");
            if (!tempKey) return;

            const submitBtn = document.getElementById('btn-ai-submit');
            const originalBtnContent = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<div class="loading-spinner"></div> Visualizing...';

            try {{
                // 1. Send Generation Request
                const genRes = await fetch("https://api.napkin.ai/v1/visual", {{
                    method: 'POST',
                    headers: {{ 'Authorization': 'Bearer ' + tempKey, 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        format: "svg",
                        content: promptText,
                        language: "en-US",
                        number_of_visuals: 1,
                        transparent_background: true,
                        color_mode: "light",
                        width: 1000,
                        height: 1000
                    }})
                }});
                
                if (!genRes.ok) throw new Error("Napkin Request Failed: " + genRes.statusText);
                const genData = await genRes.json();
                const requestId = genData.id;

                // 2. Poll for Status
                let fileId = null;
                for (let i = 0; i < 30; i++) {{ // Try 30 times
                    await new Promise(r => setTimeout(r, 2000)); // Sleep 2s
                    const statusRes = await fetch(`https://api.napkin.ai/v1/visual/${{requestId}}/status`, {{
                        headers: {{ 'Authorization': 'Bearer ' + tempKey }}
                    }});
                    const statusData = await statusRes.json();
                    
                    if (statusData.status === 'completed') {{
                        if (statusData.generated_files && statusData.generated_files.length > 0) {{
                            const url = statusData.generated_files[0].url;
                            fileId = url.substring(url.lastIndexOf('/') + 1);
                        }} else {{
                            fileId = statusData.visual_id;
                        }}
                        break;
                    }} else if (statusData.status === 'failed' || statusData.status === 'error') {{
                        throw new Error("Napkin generation failed.");
                    }}
                }}

                if(!fileId) throw new Error("Timed out waiting for Napkin.");

                // 3. Download the SVG Content
                const downloadRes = await fetch(`https://api.napkin.ai/v1/visual/${{requestId}}/file/${{fileId}}`, {{
                    headers: {{ 'Authorization': 'Bearer ' + tempKey, 'Accept': 'image/svg+xml' }}
                }});
                
                if (!downloadRes.ok) throw new Error("Failed to download image.");
                const svgBlob = await downloadRes.blob();
                
                // 4. Convert Blob to Base64
                const reader = new FileReader();
                reader.readAsDataURL(svgBlob); 
                reader.onloadend = function() {{
                    const base64data = reader.result;
                    
                    // 5. Inject into Slide
                    injectImageIntoSlide(currentEditingIndex, base64data);
                    
                    // Cleanup
                    tempKey = null;
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = originalBtnContent;
                    closeAIModal();
                }}

            }} catch (err) {{
                tempKey = null;
                alert("Napkin Error: " + err.message);
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnContent;
            }}
        }}

        function injectImageIntoSlide(index, base64Data) {{
            let html = SLIDES[index].html;
            
            // If there's an existing img with standard classes, replace it
            const parser = new DOMParser();
            const doc = parser.parseFromString(html, 'text/html');
            const existingImg = doc.querySelector('img.img-zoomable') || doc.querySelector('img.float-right');

            if (existingImg) {{
                existingImg.src = base64Data;
                SLIDES[index].html = doc.body.innerHTML;
            }} else {{
                // If no image exists, prepend standard layout
                const newImageHtml = `
                <div class="clearfix mb-8">
                     <img src="${{base64Data}}" class="img-zoomable cursor-zoom-in float-right ml-8 mb-6 w-5/12 max-w-sm rounded-lg shadow-md border hover:shadow-xl transition-shadow duration-300">
                </div>`;
                SLIDES[index].html = newImageHtml + SLIDES[index].html;
            }}
            
            persistChanges();
            refreshSlideView(index);
        }}

        function refreshSlideView(index) {{
            const contentDiv = document.getElementById(`content-${{index}}`);
            if(contentDiv) {{
                contentDiv.innerHTML = SLIDES[index].html;
                if(state.reveal !== 'click') {{
                    contentDiv.querySelectorAll('.reveal-item').forEach(el => el.classList.add('visible'));
                }}
            }}
        }}

        // --- THEME, DARK MODE, RENDER ---
        function setTheme(colorHex) {{
            state.theme = colorHex;
            document.documentElement.style.setProperty('--theme-color', colorHex);
            updateButtonStyles();
        }}
        function toggleDarkMode() {{
            state.darkMode = !state.darkMode;
            const dot = document.getElementById('dm-toggle-dot');
            const bg = document.getElementById('dm-toggle-bg');
            if (state.darkMode) {{
                document.body.classList.add('dark-mode'); dot.style.transform = 'translateX(1.25rem)';
                bg.classList.remove('bg-gray-700'); bg.classList.add('theme-bg'); bg.style.backgroundColor = state.theme;
            }} else {{
                document.body.classList.remove('dark-mode'); dot.style.transform = 'translateX(0)';
                bg.classList.add('bg-gray-700'); bg.classList.remove('theme-bg'); bg.style.backgroundColor = '';
            }}
        }}
        document.addEventListener('click', (e) => {{
            if (e.target.tagName === 'IMG' && e.target.closest('main')) {{
                toggleZoom(e.target); e.stopPropagation();
            }}
        }});
        function toggleZoom(img) {{
            const isZoomed = img.classList.contains('img-zoomed');
            if (isZoomed) {{
                img.classList.remove('img-zoomed'); backdrop.classList.remove('active');
                const placeholder = img.previousElementSibling;
                if (placeholder && placeholder.classList.contains('zoom-placeholder')) {{
                    const rect = placeholder.getBoundingClientRect();
                    img.style.transform = 'none'; img.style.top = rect.top + 'px'; img.style.left = rect.left + 'px';
                    img.style.width = rect.width + 'px'; img.style.height = rect.height + 'px';
                    setTimeout(() => {{ img.style = ''; placeholder.remove(); }}, 300);
                }}
            }} else {{
                const rect = img.getBoundingClientRect();
                const placeholder = document.createElement('div');
                placeholder.className = 'zoom-placeholder';
                placeholder.style.width = rect.width + 'px'; placeholder.style.height = rect.height + 'px';
                placeholder.style.float = window.getComputedStyle(img).float; 
                placeholder.style.marginBottom = window.getComputedStyle(img).marginBottom;
                placeholder.style.marginLeft = window.getComputedStyle(img).marginLeft;
                img.parentNode.insertBefore(placeholder, img);
                img.style.position = 'fixed'; img.style.top = rect.top + 'px'; img.style.left = rect.left + 'px';
                img.style.width = rect.width + 'px'; img.style.height = rect.height + 'px';
                img.style.zIndex = '9999'; img.style.transition = 'all 0.4s cubic-bezier(0.19, 1, 0.22, 1)';
                void img.offsetWidth;
                img.classList.add('img-zoomed'); img.style.top = '50%'; img.style.left = '50%';
                img.style.transform = 'translate(-50%, -50%)'; img.style.width = 'auto'; img.style.height = 'auto';
                img.style.maxWidth = '90vw'; img.style.maxHeight = '90vh';
                backdrop.classList.add('active');
            }}
        }}
        function closeAllZooms() {{ const z = document.querySelector('.img-zoomed'); if(z) toggleZoom(z); }}
        function setMode(type, value) {{
            state[type] = value; updateButtonStyles();
            if (type === 'layout') renderApp();
            if (type === 'reveal') toggleRevealClass();
        }}
        function updateButtonStyles() {{
            const setActive = (id, isActive) => {{
                const el = document.getElementById(id);
                if (isActive) {{
                    el.classList.add('theme-bg', 'theme-border', 'text-white'); el.classList.remove('text-gray-400');
                    el.style.backgroundColor = state.theme; el.style.borderColor = state.theme;
                }} else {{
                    el.classList.remove('theme-bg', 'theme-border', 'text-white'); el.classList.add('text-gray-400');
                    el.style.backgroundColor = ''; el.style.borderColor = '';
                }}
            }};
            setActive('btn-vertical', state.layout === 'vertical'); setActive('btn-horizontal', state.layout === 'horizontal');
            setActive('btn-click', state.reveal === 'click'); setActive('btn-all', state.reveal === 'all');
            document.querySelectorAll('.theme-btn').forEach(btn => {{
                const color = btn.getAttribute('data-color');
                if (color === state.theme) {{
                    btn.classList.add('ring-2', 'ring-offset-2', 'ring-offset-gray-900'); btn.style.setProperty('--tw-ring-color', color);
                }} else {{
                    btn.classList.remove('ring-2', 'ring-offset-2', 'ring-offset-gray-900'); btn.style.removeProperty('--tw-ring-color');
                }}
            }});
            const dmBg = document.getElementById('dm-toggle-bg');
            if (state.darkMode) dmBg.style.backgroundColor = state.theme;
            toggleRevealClass();
        }}
        function toggleRevealClass() {{
            if (state.reveal === 'all') {{
                document.body.classList.add('reveal-disabled');
                nextBtn.innerHTML = (state.layout === 'horizontal') ? 'Next Slide' : 'Scroll Down';
                prevBtn.querySelector('span').innerText = (state.layout === 'horizontal') ? 'Prev Slide' : 'Scroll Up';
                nextIcon.className = (state.layout === 'horizontal') ? "fas fa-arrow-right" : "fas fa-arrow-down";
                prevIcon.className = (state.layout === 'horizontal') ? "fas fa-arrow-left" : "fas fa-arrow-up";
            }} else {{
                document.body.classList.remove('reveal-disabled');
                nextBtn.innerHTML = 'Next Step'; prevBtn.querySelector('span').innerText = 'Back';
                nextIcon.className = "fas fa-chevron-down"; prevIcon.className = "fas fa-chevron-up";
                nextBtn.appendChild(nextIcon); 
            }}
        }}
        function renderApp() {{
            container.innerHTML = '';
            if (state.layout === 'vertical') renderVerticalLayout();
            else renderHorizontalLayout();
            updateButtonStyles(); updateProgress(); 
        }}
        function renderVerticalLayout() {{
            const card = document.createElement('main');
            card.className = "bg-white rounded-3xl shadow-xl border border-gray-200 overflow-hidden transition-colors duration-300";
            let fullHtml = '';
            SLIDES.forEach((slide, index) => {{
                const divider = index === 0 ? '' : '<hr class="my-12 border-gray-100">';
                fullHtml += `
                    <section class="p-10 relative group" id="slide-sec-${{index}}">
                        ${{divider}}
                        <div class="mb-6 flex justify-between items-start">
                            <div>
                                <span class="text-xs font-bold text-gray-400 uppercase tracking-wider">Part ${{index + 1}}</span>
                                <h2 class="text-3xl font-bold transition-colors duration-300">${{slide.title}}</h2>
                            </div>
                            <div class="opacity-0 group-hover:opacity-100 transition-opacity flex gap-2">
                                <button id="edit-btn-${{index}}" onclick="toggleEdit(${{index}})" class="text-gray-400 hover:text-indigo-600 p-2 rounded-full hover:bg-gray-100 transition" title="Edit Content">
                                    <i class="fas fa-pen"></i>
                                </button>
                                <button id="ai-btn-${{index}}" onclick="openAIModal(${{index}})" class="ai-magic-btn" title="AI Text Edit">
                                    <i class="fas fa-wand-magic-sparkles"></i>
                                </button>
                                <button id="napkin-btn-${{index}}" onclick="openNapkinModal(${{index}})" class="ai-napkin-btn" title="Napkin Image Gen">
                                    <i class="fas fa-image"></i>
                                </button>
                                <button id="save-btn-${{index}}" onclick="saveSlide(${{index}})" class="hidden text-white bg-green-500 hover:bg-green-600 p-2 px-3 rounded-full shadow-md transition" title="Save Changes">
                                    <i class="fas fa-check"></i> Save
                                </button>
                            </div>
                        </div>
                        <div id="content-${{index}}" class="prose max-w-none text-gray-600 transition-colors duration-300 p-2 rounded">
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
            const idx = state.currentSlideIdx;
            const card = document.createElement('main');
            card.className = "bg-white rounded-3xl shadow-2xl border border-gray-200 overflow-hidden p-12 min-h-[600px] flex flex-col animation-fade transition-colors duration-300 relative";
            card.innerHTML = `
                <div class="border-b border-gray-100 pb-6 mb-6 flex justify-between items-center">
                    <h2 class="text-3xl font-bold transition-colors duration-300">${{slide.title}}</h2>
                    <div class="flex items-center gap-4">
                        <button id="edit-btn-${{idx}}" onclick="toggleEdit(${{idx}})" class="text-gray-400 hover:text-indigo-600 p-2 rounded-full hover:bg-gray-100 transition" title="Edit Slide">
                            <i class="fas fa-pen"></i>
                        </button>
                        <button id="ai-btn-${{idx}}" onclick="openAIModal(${{idx}})" class="ai-magic-btn" title="AI Text Edit">
                            <i class="fas fa-wand-magic-sparkles"></i>
                        </button>
                        <button id="napkin-btn-${{idx}}" onclick="openNapkinModal(${{idx}})" class="ai-napkin-btn" title="Napkin Image Gen">
                            <i class="fas fa-image"></i>
                        </button>
                        <button id="save-btn-${{idx}}" onclick="saveSlide(${{idx}})" class="hidden text-white bg-green-500 hover:bg-green-600 p-2 px-3 rounded-full shadow-md transition" title="Save Changes">
                            <i class="fas fa-check"></i> Save
                        </button>
                        <span class="bg-gray-100 text-gray-500 text-xs font-bold px-3 py-1 rounded-full">Slide ${{idx + 1}} / ${{SLIDES.length}}</span>
                    </div>
                </div>
                <div id="content-${{idx}}" class="prose max-w-none text-gray-600 flex-1 transition-colors duration-300 p-2 rounded">
                    ${{slide.html}}
                </div>
                <div class="flex justify-between mt-8 pt-6 border-t border-gray-50">
                     <button onclick="prevSlide()" class="text-gray-400 hover:text-indigo-600 font-bold px-4 py-2 hover:bg-indigo-50 rounded-lg transition">← Slide Back</button>
                     <div class="text-xs text-gray-300 self-center">Use Arrow Keys</div>
                </div>
            `;
            container.appendChild(card);
            if (state.reveal === 'click') {{
                 card.querySelectorAll('.reveal-item').forEach(el => el.classList.remove('visible'));
            }}
        }}
        function handleMainAction() {{
            if (document.querySelector('.editing-mode')) return;
            if (document.getElementById('ai-edit-modal').classList.contains('active')) return;
            if (state.reveal === 'click') {{
                const hiddenItem = container.querySelector('.reveal-item:not(.visible)');
                if (hiddenItem) {{
                    hiddenItem.classList.add('visible'); hiddenItem.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
                    updateProgress(); return;
                }}
            }}
            if (state.layout === 'horizontal') nextSlide(); else scrollContainer.scrollBy({{ top: 300, behavior: 'smooth' }});
        }}
        function handleBackAction() {{
            if (document.querySelector('.editing-mode')) return; 
            if (document.getElementById('ai-edit-modal').classList.contains('active')) return;
            if (state.reveal === 'click') {{
                const visibleItems = Array.from(document.querySelectorAll('.reveal-item.visible'));
                if (visibleItems.length > 0) {{
                    const lastItem = visibleItems[visibleItems.length - 1]; lastItem.classList.remove('visible');
                    if (visibleItems.length > 1) {{ visibleItems[visibleItems.length - 2].scrollIntoView({{ behavior: 'smooth', block: 'center' }}); }} 
                    else {{ if(state.layout === 'horizontal') container.scrollIntoView({{behavior: 'smooth'}}); }}
                    updateProgress(); return;
                }}
            }}
            if (state.layout === 'horizontal') prevSlide(); else scrollContainer.scrollBy({{ top: -300, behavior: 'smooth' }});
        }}
        function nextSlide() {{
            if (state.currentSlideIdx < SLIDES.length - 1) {{ state.currentSlideIdx++; renderApp(); scrollContainer.scrollTop = 0; }} else {{ alert("End of Course!"); }}
        }}
        function prevSlide() {{
            if (state.currentSlideIdx > 0) {{ state.currentSlideIdx--; renderApp(); scrollContainer.scrollTop = 0; }}
        }}
        function updateProgress() {{
            if (state.layout === 'horizontal') {{
                const pct = Math.round(((state.currentSlideIdx + 1) / SLIDES.length) * 100);
                document.getElementById('progress-pct').innerText = pct + "%";
            }} else {{
                const total = document.querySelectorAll('.reveal-item').length;
                const visible = document.querySelectorAll('.reveal-item.visible').length;
                if (total > 0) {{ const pct = Math.round((visible / total) * 100); document.getElementById('progress-pct').innerText = pct + "%"; }}
            }}
        }}
        function toggleSidebar() {{
            const sb = document.getElementById('sidebar'); const icon = document.getElementById('sidebar-toggle-icon');
            if (sb.classList.contains('sidebar-expanded')) {{
                sb.classList.remove('sidebar-expanded'); sb.classList.add('sidebar-collapsed');
                document.querySelectorAll('.sidebar-text').forEach(el => el.classList.add('hidden'));
                if(icon) icon.style.transform = 'rotate(180deg)';
            }} else {{
                sb.classList.remove('sidebar-collapsed'); sb.classList.add('sidebar-expanded');
                document.querySelectorAll('.sidebar-text').forEach(el => el.classList.remove('hidden'));
                if(icon) icon.style.transform = 'rotate(0deg)';
            }}
        }}
        document.addEventListener('keydown', (e) => {{
            if (document.querySelector('.editing-mode')) return;
            if (document.getElementById('ai-edit-modal').classList.contains('active')) {{ if(e.key === "Escape") closeAIModal(); return; }}
            if (e.key === "ArrowRight" || e.key === " " || e.key === "Enter") {{ e.preventDefault(); handleMainAction(); }}
            if (e.key === "ArrowLeft") {{ e.preventDefault(); handleBackAction(); }}
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
        api_key=gemini_api_key,
        bg_accent=C_BG_ACCENT,
        header_color=C_HEADER,
        primary_color=C_PRIMARY,
        border_color=C_BORDER,
        body_color=C_BODY
    )

    # Save ONE file
    output_file = os.path.join(OUTPUT_DIR, "index.html")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(final_html)

    print(f"\n✅ SUCCESS! Generated Single Page Lesson: {output_file}")
    webbrowser.open('file://' + os.path.realpath(output_file))

if __name__ == "__main__":
    process_slides()