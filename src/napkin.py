import os
import asyncio
import httpx
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class NapkinService:
    def __init__(self):
        self.base_url = os.getenv("NAPKIN_BASE_URL", "https://api.napkin.ai/v1/visual")
        # Clean up URL just in case
        self.base_url = self.base_url.strip("'").strip('"').rstrip('/')
        self.token = os.getenv("NAPKIN_PAT")
        
        if not self.token:
            logger.warning("NAPKIN_PAT environment variable is not set.")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    async def generate_svg(
        self, 
        text: str, 
        output_path: str, 
        context: Optional[str] = None,
        no_visuals: Optional[int] = 1,
        visual_id: Optional[str] = None, 
        style_id: Optional[str] = None
    ) -> str:
        """
        Generates an SVG from text using Napkin API and saves it to output_path.
        
        Args:
            text: The content text to visualize.
            output_path: The path to save the generated SVG.
            visual_id: Optional visual_id for Napkin API.
            style_id: Optional style_id for Napkin API.
            
        Returns:
            The path where the SVG was saved.
        """
        if not self.token:
            raise ValueError("NAPKIN_PAT is not set.")

        # 1. Generate Request
        payload = {
            "format": "svg",
            "content": text,
            "context": context,
            "language": "en-US",
            "number_of_visuals": no_visuals,
            "transparent_background": True,
            "color_mode": "light",
            "width": 1920,
            "height": 1080,
            "orientation": "auto",
            "text_extraction_mode": "auto",
            "sort_strategy": "relevance"
        }
        
        if visual_id:
            payload["visual_id"] = visual_id
        if style_id:
            payload["style_id"] = style_id

        async with httpx.AsyncClient() as client:
            # Step 1: Generate
            logger.info(f"Sending generation request to Napkin API")
            try:
                response = await client.post(self.base_url, headers=self.headers, json=payload, timeout=30.0)
                response.raise_for_status()
                data = response.json()
            except httpx.HTTPStatusError as e:
                logger.error(f"Napkin API error: {e.response.text}")
                raise

            # Extract request_id. 
            request_id = data.get("id")
            
            if not request_id:
                raise ValueError(f"Could not find request_id in Napkin API response: {data}")

            logger.info(f"Generation started. Request ID: {request_id}")

            # Step 2: Poll Status
            status_url = f"{self.base_url}/{request_id}/status"
            
            max_retries = 30 # 60 seconds max
            
            for _ in range(max_retries):
                await asyncio.sleep(2)
                logger.debug("Checking status...")
                status_response = await client.get(status_url, headers=self.headers, timeout=10.0)
                status_response.raise_for_status()
                status_data = status_response.json()
                
                status = status_data.get("status")
                logger.debug(f"Status: {status}")
                
                if status == "completed":
                    # Extract file_id
                    visuals = status_data.get("visuals")
                    generated_files = status_data.get("generated_files")
                    
                    file_ids = []
                    if generated_files and isinstance(generated_files, list) and len(generated_files) > 0:
                        # Extract file_id from URL if id is not present
                        for file_obj in generated_files:
                            # URL format: .../file/<file_id>
                            file_ids.append(file_obj["url"].split("/")[-1])
                    else:
                        file_ids.append(status_data.get("visual_id"))
                        
                    if not file_ids:
                        raise ValueError(f"Completed but no file_id found in: {status_data}")
                    break
                elif status == "failed" or status == "error":
                    raise RuntimeError(f"Napkin generation failed: {status_data}")
                # else pending/processing
            
            if not file_ids:
                raise TimeoutError("Timed out waiting for Napkin generation")

            logger.info(f"Generation completed. File ID: {file_ids}")

            # Step 3: Download
            save_paths = []
            for file_id in file_ids:
                output_file_path = os.path.join(output_path, f"{file_id}.svg")
                download_url = f"{self.base_url}/{request_id}/file/{file_id}"
                download_headers = self.headers.copy()
                download_headers["Accept"] = "image/svg+xml"
                
                logger.info("Downloading SVG...")
                download_response = await client.get(download_url, headers=download_headers, timeout=30.0)
                download_response.raise_for_status()
                
                # Save to file
                os.makedirs(os.path.dirname(output_file_path), exist_ok=True)
                with open(output_file_path, "wb") as f:
                    f.write(download_response.content)
                    
                logger.info(f"SVG saved to {output_file_path}")
                save_paths.append(output_file_path.split("/")[-1])

            return save_paths