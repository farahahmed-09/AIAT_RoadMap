import os
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# Base URL for Napkin AI API
BASE_URL = "https://api.napkin.ai"

# Your API token (set as environment variable for security)
load_dotenv()

API_TOKEN = os.getenv("NAPKIN_API_KEY")
if not API_TOKEN:
    raise ValueError("Set your NAPKIN_API_TOKEN environment variable with your API key.")

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def create_visual_request(prompt: str, style_id: str = None, variations: int = 1, format: str = "png"):
    """
    Create a new visual generation request.
    
    :param prompt: The text description for the diagram/visual.
    :param style_id: Optional style ID (see https://api.napkin.ai/docs/styles/ for list).
    :param variations: Number of variations to generate (default 1).
    :param format: Output format: 'png', 'svg', or 'pdf'.
    :return: Request ID
    """
    payload = {
        "prompt": prompt,
        "variations": variations,
        "format": format
    }
    if style_id:
        payload["style_id"] = style_id
    
    response = requests.post(f"{BASE_URL}/v1/visuals", json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    request_id = data["id"]
    print(f"Visual request created: ID = {request_id}")
    return request_id

def get_request_status(request_id: str):
    """
    Poll the status of a visual request.
    """
    response = requests.get(f"{BASE_URL}/v1/visuals/{request_id}", headers=headers)
    response.raise_for_status()
    return response.json()

def download_file(file_url: str, output_path: Path):
    """
    Download a generated file.
    """
    response = requests.get(file_url, headers=headers)
    response.raise_for_status()
    output_path.write_bytes(response.content)
    print(f"Downloaded: {output_path}")

def generate_diagram(prompt: str, output_dir: Path = Path("napkin_outputs"), style_id: str = None, variations: int = 1, format: str = "png", poll_interval: int = 10):
    """
    Full function to generate and download visuals from a text prompt.
    """
    output_dir.mkdir(exist_ok=True)
    
    request_id = create_visual_request(prompt, style_id, variations, format)
    
    print("Waiting for generation to complete...")
    while True:
        status_data = get_request_status(request_id)
        status = status_data["status"]
        print(f"Status: {status}")
        
        if status == "completed":
            files = status_data["files"]
            for i, file_info in enumerate(files):
                file_url = file_info["url"]
                filename = file_info.get("filename", f"visual_{i}.{format}")
                output_path = output_dir / filename
                download_file(file_url, output_path)
            break
        elif status == "failed":
            raise RuntimeError(f"Generation failed: {status_data.get('error', 'Unknown error')}")
        
        time.sleep(poll_interval)  # Wait before polling again

# Example usage
if __name__ == "__main__":
    example_prompt = """
    A flowchart showing a machine learning pipeline:
    - Data ingestion from sources
    - Data cleaning and preprocessing
    - Feature engineering
    - Model training (with train/validation split)
    - Evaluation
    - Deployment
    Include arrows between steps.
    """
    
    generate_diagram(
        prompt=example_prompt,
        style_id="sketch-notes",  # Optional: replace with a valid style ID, or omit for default
        variations=2,
        format="png"
    )