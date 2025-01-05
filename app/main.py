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

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

API_TOKEN = os.getenv("API_KEY")

def verify_token(token: str = Depends(oauth2_scheme)):
    if token != API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    return token

@app.post("/process-image/")
async def process_image(
    token: str = Depends(verify_token),
    background: Optional[UploadFile] = File(None),
):
    try:
        if background:
            background_image = Image.open(io.BytesIO(await background.read())).convert("RGBA")
            logging.debug(f"Eingabebild-Modus: {background_image.mode}")
        else:
            raise HTTPException(status_code=400, detail="No background image provided")

        # Testtext hinzufügen
        draw = ImageDraw.Draw(background_image)
        test_font_path = "app/fonts/arial.ttf"
        test_font_size = 50
        test_text = "Testtext: Funktioniert es?"
        test_position = (50, 50)

        try:
            test_font = ImageFont.truetype(test_font_path, test_font_size)
            logging.debug(f"Font '{test_font_path}' erfolgreich geladen.")
        except Exception as e:
            logging.error(f"Fehler beim Laden des Fonts '{test_font_path}': {e}")
            raise

        try:
            draw.text(test_position, test_text, font=test_font, fill="red")
            logging.debug(f"Testtext '{test_text}' erfolgreich gezeichnet.")
        except Exception as e:
            logging.error(f"Fehler beim Zeichnen des Textes: {e}")
            raise

        # Bild speichern und zurückgeben
        img_byte_arr = io.BytesIO()
        background_image.save(img_byte_arr, format="PNG")
        img_byte_arr.seek(0)

        return StreamingResponse(img_byte_arr, media_type="image/png")

    except Exception as e:
        logging.error(f"Fehler: {e}")
        raise HTTPException(status_code=500, detail=str(e))
