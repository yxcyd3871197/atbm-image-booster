# ATBM Image Booster

Eine Bildbearbeitungs-API, die Hintergrundbilder mit Text und Overlays kombiniert.

## Verwendung

1. **API-Endpoint**: `POST /process-image/`
2. **Parameter**:
   - `background`: Das Hintergrundbild (JPEG, PNG, WEBP).
   - `text_layers`: Eine Liste von Textschichten.
   - `image_layers`: Eine Liste von Bildschichten.

## Beispiel

```bash
curl -X POST "http://your-cloud-run-url/process-image/" \
-F "background=@background.png" \
-F 'text_layers=[{"text": "Hello World", "font": "arial.ttf", "font_size": 30, "color": "white", "position": {"x": 50, "y": 50}, "box_size": {"width": 200, "height": 100}}]' \
-F "image_layers=[{\"image\": \"@overlay.png\", \"position\": {\"x\": 100, \"y\": 100}, \"size\": {\"width\": 50, \"height\": 50}}]"
