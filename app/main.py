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
    color: str = "black"
    position: dict = {"x": 0, "y": 0}
    box_size: dict = {"width": 100, "height": 50}

class ImageLayer(BaseModel):
    image_url: Optional[str] = None  # URL des Overlay-Bildes
    image: Optional[UploadFile] = None  # Oder direkt hochgeladenes Bild
    position: dict = {"x": 0, "y": 0}
    size: dict = {"width": 100, "height": 100}

class ImageRequest(BaseModel):
    background_url: Optional[str] = None  # URL des Hintergrundbildes
    background: Optional[UploadFile] = File(None)  # Oder direkt hochgeladenes Bild
    text_layers: List[TextLayer] = []
    image_layers: List[ImageLayer] = []
    output_width: Optional[int] = None
    output_height: Optional[int] = None

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
    token: str = Depends(verify_token),  # Token-Validierung
    background_url: Optional[str] = None,  # URL des Hintergrundbildes
    background: Optional[UploadFile] = File(None),  # Oder direkt hochgeladenes Bild
    text_layers: List[TextLayer] = [],
    image_layers: List[ImageLayer] = [],
    output_width: Optional[int] = None,
    output_height: Optional[int] = None
):
    try:
        # Hintergrundbild laden
        if background_url:
            response = requests.get(background_url)
            background_image = Image.open(BytesIO(response.content)).convert("RGBA")
        elif background:
            background_image = Image.open(io.BytesIO(await background.read())).convert("RGBA")
        else:
            raise HTTPException(status_code=400, detail="No background image provided")

        logging.debug(f"Background image size: {background_image.size}")

        # Textschichten hinzufügen
        for layer in text_layers:
            logging.debug(f"Processing text layer: {layer}")
            draw = ImageDraw.Draw(background_image)
            font_path = f"app/fonts/{layer.font}"
            
            # Prüfe, ob die Schriftdatei existiert
            if not os.path.isfile(font_path):
                logging.error(f"Font file not found: {font_path}")
                raise HTTPException(status_code=400, detail=f"Font file not found: {layer.font}")
            
            # Schriftgröße dynamisch berechnen, falls nicht angegeben
            if layer.font_size is None:
                layer.font_size = calculate_font_size(draw, layer.text, font_path, layer.box_size["width"], layer.box_size["height"])
            
            font = ImageFont.truetype(font_path, layer.font_size)
            draw.text((layer.position["x"], layer.position["y"]), layer.text, font=font, fill=layer.color)

        # Bildschichten hinzufügen
        for layer in image_layers:
            if layer.image_url:
                response = requests.get(layer.image_url)
                overlay_image = Image.open(BytesIO(response.content)).convert("RGBA")
            elif layer.image:
                overlay_image = Image.open(io.BytesIO(await layer.image.read())).convert("RGBA")
            else:
                continue  # Kein gültiges Bild
            
            overlay_image = overlay_image.resize((layer.size["width"], layer.size["height"]))
            background_image.paste(overlay_image, (layer.position["x"], layer.position["y"]), overlay_image)

        # Bildgröße ändern (falls Parameter vorhanden)
        if output_width and output_height:
            logging.debug(f"Resizing image to: {output_width}x{output_height}")
            background_image = background_image.resize((output_width, output_height))

        # Bild in Bytes umwandeln
        img_byte_arr = io.BytesIO()
        background_image.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)

        # Bild als Response zurückgeben
        return StreamingResponse(img_byte_arr, media_type="image/png")

    except Exception as e:
        logging.error(f"Error processing image: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
