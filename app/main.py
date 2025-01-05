from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, status
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordBearer
from PIL import Image, ImageDraw, ImageFont
from pydantic import BaseModel
from typing import List, Optional
import io
import requests
from io import BytesIO
import os
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")

app = FastAPI()

# Bearer-Token-Validierung
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Umgebungsvariablen laden
API_TOKEN = os.getenv("API_KEY")
GCP_BUCKET_NAME = os.getenv("GCP_BUCKET_NAME")
GCP_SA_CREDENTIALS = os.getenv("GCP_SA_CREDENTIALS")

def verify_token(token: str = Depends(oauth2_scheme)):
    if token != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return token

class TextLayer(BaseModel):
    text: str
    font: str = "Allison/Allison-Regular.ttf"  # Standard-Font
    font_size: Optional[int] = None  # Optional, falls dynamisch berechnet
    color: str = "black"  # Farbe als Hex oder RGBA
    position: dict = {"x": 0, "y": 0}
    box_size: dict = {"width": 100, "height": 50}

class ImageLayer(BaseModel):
    image_url: Optional[str] = None  # URL des Overlay-Bildes
    image: Optional[UploadFile] = None  # Oder direkt hochgeladenes Bild
    position: dict = {"x": 0, "y": 0}
    size: dict = {"width": 100, "height": 100}

def calculate_font_size(draw, text, font_path, box_width, box_height):
    font_size = 1
    font = ImageFont.truetype(font_path, font_size)
    while True:
        text_width, text_height = draw.textsize(text, font=font)
        if text_width > box_width or text_height > box_height:
            break
        font_size += 1
        font = ImageFont.truetype(font_path, font_size)
    return font_size - 1  # Letzte Größe, die passt

@app.post("/process-image/")
async def process_image(
    token: str = Depends(verify_token),
    background_url: Optional[str] = None,
    background: Optional[UploadFile] = File(None),
    text_layers: List[TextLayer] = [],
    image_layers: List[ImageLayer] = []
):
    try:
        # Hintergrundbild laden
        if background_url:
            logging.debug(f"Loading background image from URL: {background_url}")
            response = requests.get(background_url)
            response.raise_for_status()
            background_image = Image.open(BytesIO(response.content)).convert("RGBA")
        elif background:
            logging.debug("Loading background image from uploaded file")
            background_image = Image.open(io.BytesIO(await background.read())).convert("RGBA")
        else:
            raise HTTPException(status_code=400, detail="No background image provided")

        # Textschichten hinzufügen
        for layer in text_layers:
            try:
                draw = ImageDraw.Draw(background_image)
                font_path = f"app/fonts/{layer.font}"
                logging.debug(f"Attempting to load font from: {font_path}")

                # Schriftgröße dynamisch berechnen, falls nicht angegeben
                if layer.font_size is None:
                    logging.debug("Calculating font size dynamically")
                    layer.font_size = calculate_font_size(draw, layer.text, font_path, layer.box_size["width"], layer.box_size["height"])

                font = ImageFont.truetype(font_path, layer.font_size)
                logging.debug(f"Loaded font: {font_path}, Size: {layer.font_size}")

                # Deckkraft prüfen und setzen
                fill_color = layer.color
                if isinstance(fill_color, str):
                    fill_color = (0, 0, 0, 255) if layer.color == "black" else (255, 255, 255, 255)

                draw.text(
                    (layer.position["x"], layer.position["y"]),
                    layer.text,
                    font=font,
                    fill=fill_color
                )
                logging.debug(f"Added text: '{layer.text}' at position ({layer.position['x']}, {layer.position['y']})")

            except Exception as e:
                logging.error(f"Error processing text layer: {e}")

        # Bild in Bytes umwandeln und zurückgeben
        img_byte_arr = io.BytesIO()
        background_image.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)
        logging.debug("Image processing completed successfully.")
        return StreamingResponse(img_byte_arr, media_type="image/png")

    except Exception as e:
        logging.error(f"Error processing image: {e}")
        raise HTTPException(status_code=500, detail=str(e))
