import json
import config
from step1_content import generate_slide_content
from step2_diagrams import generate_diagram_napkin

def run_pipeline():
    print("🚀 Starting Slides Generation Pipeline...\n")

    # --- Step 1: Get Content ---
    slides_data = generate_slide_content()
    
    if not slides_data:
        print("❌ Pipeline stopped at Step 1.")
        return

    final_slides_plan = []

    # --- Step 2: Generate Diagrams for each slide ---
    print("\n--- Step 2: Generating Visuals (Napkin AI) ---")
    
    for slide in slides_data:
        slide_id = slide.get('slide_id')
        vis_desc = slide.get('visual_description')
        
        image_path = None
        
        # Only generate if there is a visual description
        if vis_desc:
            image_path = generate_diagram_napkin(vis_desc, slide_id)
        
        # Append image path to the slide object
        slide['image_local_path'] = image_path
        final_slides_plan.append(slide)

    # --- Step 3: Output Final JSON ---
    print("\n--- Step 3: Saving Final Plan ---")
    
    try:
        with open(config.OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(final_slides_plan, f, indent=4, ensure_ascii=False)
        print(f"✅ Pipeline Success! Final plan saved to:\n   {config.OUTPUT_JSON_FILE}")
    except Exception as e:
        print(f"❌ Error saving final JSON: {e}")

if __name__ == "__main__":
    run_pipeline()