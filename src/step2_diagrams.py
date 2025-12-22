# import asyncio
# import os
# import json
# import config
# # Import the class from the file you uploaded (napkin.py)
# from napkin import NapkinService 

# async def generate_diagrams_auto():
#     print("--- Step 2: Generating Napkin.ai Diagrams (Automated) ---")

#     # 1. Load the Slide Plan
#     if not os.path.exists(config.OUTPUT_JSON_FILE):
#         print("❌ Slide plan not found. Run Step 1 first.")
#         return

#     with open(config.OUTPUT_JSON_FILE, "r", encoding="utf-8") as f:
#         slides = json.load(f)

#     # 2. Setup the Napkin Service
#     if not os.getenv("NAPKIN_PAT"):
#         print("❌ Error: NAPKIN_PAT environment variable is missing.")
#         return

#     napkin_service = NapkinService()
    
#     # Ensure output directory exists
#     os.makedirs(config.IMAGES_DIR, exist_ok=True)

#     updated_slides = []

#     # 3. Iterate through slides and generate images
#     for slide in slides:
#         slide_id = slide.get('slide_id')
#         title = slide.get('title', 'Untitled')
#         visual_desc = slide.get('visual_description', '')
        
#         # Combine title and description for a better prompt context
#         prompt_text = f"Title: {title}\nContext: {visual_desc}"
        
#         print(f"🎨 Generating visual for Slide {slide_id}...")
        
#         try:
#             # Call the API using your napkin.py script
#             saved_filenames = await napkin_service.generate_svg(
#                 text=prompt_text,
#                 output_path=config.IMAGES_DIR,
#                 no_visuals=1 
#             )
            
#             if saved_filenames:
#                 # 1. Get the path of the file Napkin just created
#                 path_from_api = saved_filenames[0]
                
#                 if os.path.isabs(path_from_api):
#                     original_file_path = path_from_api
#                 else:
#                     original_file_path = os.path.join(config.IMAGES_DIR, path_from_api)
                
#                 # 2. Determine the file extension (usually .svg or .png)
#                 _, extension = os.path.splitext(original_file_path)
                
#                 # 3. Construct the NEW filename based on slide_id
#                 # Example: slide_1.svg
#                 new_filename = f"slide_{slide_id}{extension}"
#                 new_file_path = os.path.join(config.IMAGES_DIR, new_filename)

#                 # 4. Rename the file
#                 # If a file with this name already exists (from a previous run), remove it first
#                 if os.path.exists(new_file_path):
#                     os.remove(new_file_path)
                
#                 os.rename(original_file_path, new_file_path)

#                 # 5. Update the JSON so Step 3 knows where the file is
#                 slide['image_local_path'] = new_file_path
#                 print(f"   ✅ Success! Saved and renamed to: {new_filename}")
#             else:
#                 print("   ⚠️ API completed but returned no file list.")
#                 slide['image_local_path'] = None
                
#         except Exception as e:
#             print(f"   ❌ Failed to generate Slide {slide_id}: {e}")
#             slide['image_local_path'] = None
        
#         updated_slides.append(slide)

#     # 4. Save the updated JSON
#     with open(config.OUTPUT_JSON_FILE, "w", encoding="utf-8") as f:
#         json.dump(updated_slides, f, indent=4, ensure_ascii=False)

#     print(f"\n✅ All processing complete. JSON updated at: {config.OUTPUT_JSON_FILE}")

# if __name__ == "__main__":
#     # Run the async function
#     asyncio.run(generate_diagrams_auto())
import asyncio
import os
import json
import config
from napkin import NapkinService 

# Define the input file explicitly based on your request
INPUT_FILE = r"D:\AIAT_roadmap\output_parser\slides_plan.json"

async def generate_diagrams_auto():
    print("--- Step 2: Generating Napkin.ai Diagrams (Automated) ---")

    # 1. Load the Slide Plan
    if not os.path.exists(INPUT_FILE):
        print(f"❌ Slide plan not found: {INPUT_FILE}")
        return

    with open(INPUT_FILE, "r", encoding="utf-8") as f:
        slides = json.load(f)

    # 2. Setup the Napkin Service
    if not os.getenv("NAPKIN_PAT"):
        print("❌ Error: NAPKIN_PAT environment variable is missing.")
        return

    napkin_service = NapkinService()
    
    # Ensure output directory exists
    os.makedirs(config.IMAGES_DIR, exist_ok=True)

    updated_slides = []

    # 3. Iterate through slides using enumerate to get the index (0, 1, 2...)
    for index, slide in enumerate(slides):
        # Extract keys specific to your slides_plan.json structure
        title = slide.get('main_title', 'Untitled')
        visual_desc = slide.get('image_search_description', '')
        
        # Combine title and description for the Napkin prompt
        prompt_text = f"Title: {title}\nContext: {visual_desc}"
        
        print(f"🎨 Generating visual for Slide {index}: {title[:30]}...")
        
        try:
            # Call the API
            saved_filenames = await napkin_service.generate_svg(
                text=prompt_text,
                output_path=config.IMAGES_DIR,
                no_visuals=1 
            )
            
            if saved_filenames:
                # 1. Get the path of the file Napkin just created
                path_from_api = saved_filenames[0]
                
                if os.path.isabs(path_from_api):
                    original_file_path = path_from_api
                else:
                    original_file_path = os.path.join(config.IMAGES_DIR, path_from_api)
                
                # 2. Determine the file extension (usually .svg or .png)
                _, extension = os.path.splitext(original_file_path)
                
                # 3. Construct the NEW filename using the loop index
                new_filename = f"slide_{index}{extension}"
                new_file_path = os.path.join(config.IMAGES_DIR, new_filename)

                # 4. Rename the file
                # Remove existing file if it exists to avoid conflicts
                if os.path.exists(new_file_path):
                    os.remove(new_file_path)
                
                os.rename(original_file_path, new_file_path)

                # 5. Convert to Absolute Path and Update JSON
                full_abs_path = os.path.abspath(new_file_path)
                slide['image_path'] = full_abs_path
                
                print(f"   ✅ Success! Saved to: {new_filename}")
                print(f"      Full Path: {full_abs_path}")
            else:
                print("   ⚠️ API completed but returned no file list.")
                
        except Exception as e:
            print(f"   ❌ Failed to generate Slide {index}: {e}")
        
        updated_slides.append(slide)

    # 4. Save the updated JSON back to the file
    with open(INPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(updated_slides, f, indent=4, ensure_ascii=False)

    print(f"\n✅ All processing complete. JSON updated at: {INPUT_FILE}")

if __name__ == "__main__":
    asyncio.run(generate_diagrams_auto())