"""Image processing engine for AKP153 button icons."""

import base64
import os
from io import BytesIO
from pathlib import Path

import httpx
from dotenv import load_dotenv
from PIL import Image

# Load .env file
load_dotenv()

TARGET_SIZE = (96, 96)  # AKP153 native key format
ICONS_DIR = Path("icons")
ICONS_DIR.mkdir(exist_ok=True)


def download_from_url(url: str, button_id: int) -> str:
    """Download image from URL, resize to 96x96, and save locally.

    Args:
        url: URL to image file
        button_id: Button number (1-15)

    Returns:
        Path to saved image file

    Raises:
        httpx.HTTPError: If download fails
        PIL.UnidentifiedImageError: If image cannot be opened
    """
    response = httpx.get(url, timeout=30.0)
    response.raise_for_status()

    img = Image.open(BytesIO(response.content))
    img = img.convert("RGB")
    img = img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)

    output_path = ICONS_DIR / f"{button_id}.png"
    img.save(output_path, "PNG")

    return str(output_path)


def generate_from_prompt(prompt: str, button_id: int) -> str:
    """Generate image from text prompt using Google Gemini.

    Args:
        prompt: Text description of desired image
        button_id: Button number (1-15)

    Returns:
        Path to saved image file

    Raises:
        ValueError: If GOOGLE_API_KEY is not set
        Exception: If API call fails
    """
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError(
            "GOOGLE_API_KEY not set. Add it to .env — see .env.example for details. "
            "Get a free key at https://aistudio.google.com/apikey"
        )

    import google.genai as genai

    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-3.1-flash-image-preview",
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            response_modalities=["IMAGE"],
        ),
    )

    # Extract image from response (base64-encoded)
    encoded_data = response.candidates[0].content.parts[0].inline_data.data
    image_data = base64.b64decode(encoded_data)

    img = Image.open(BytesIO(image_data))
    img = img.convert("RGB")
    img = img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)

    output_path = ICONS_DIR / f"{button_id}.png"
    img.save(output_path, "PNG")

    return str(output_path)


def process_image(source: str, button_id: int) -> str:
    """Process image from various sources (URL, prompt, local file).

    Args:
        source: Image source, one of:
            - URL: "https://..." or "http://..."
            - Prompt: "generate:description of image"
            - Local path: "path/to/image.png"
        button_id: Button number (1-15)

    Returns:
        Path to processed image file saved to icons/{button_id}.png

    Raises:
        ValueError: If source format is invalid or required config missing
        FileNotFoundError: If local file does not exist
    """
    if source.startswith(("http://", "https://")):
        return download_from_url(source, button_id)
    elif source.startswith("generate:"):
        prompt = source[9:]
        return generate_from_prompt(prompt, button_id)
    else:
        # Local file path
        source_path = Path(source)
        if not source_path.exists():
            raise FileNotFoundError(f"Image file not found: {source}")

        img = Image.open(source_path)
        img = img.convert("RGB")
        img = img.resize(TARGET_SIZE, Image.Resampling.LANCZOS)

        output_path = ICONS_DIR / f"{button_id}.png"
        img.save(output_path, "PNG")

        return str(output_path)
