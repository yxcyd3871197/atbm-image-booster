# Text auf dem Bild hinzufügen
for layer in text_layers:
    log_text_layer(layer)  # Logge die Textschicht
    draw = ImageDraw.Draw(background_image)
    font_path = f"app/fonts/{layer.font}"
    
    # Prüfe, ob die Schriftdatei existiert
    if not os.path.isfile(font_path):
        logging.error(f"Font file not found: {font_path}")
        raise HTTPException(status_code=400, detail=f"Font file not found: {layer.font}")
    
    # Schriftgröße dynamisch berechnen, falls nicht angegeben
    if layer.font_size is None:
        layer.font_size = calculate_font_size(draw, layer.text, font_path, layer.box_size["width"], layer.box_size["height"])
    
    try:
        font = ImageFont.truetype(font_path, layer.font_size)
    except Exception as e:
        logging.error(f"Error loading font: {font_path} - {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading font: {layer.font}")
    
    # Debug: Position und Farbe
    logging.debug(f"Drawing text '{layer.text}' at position ({layer.position['x']}, {layer.position['y']}) "
                  f"with font size {layer.font_size} and color {layer.color}")
    
    # Text zeichnen
    draw.text((layer.position["x"], layer.position["y"]), layer.text, font=font, fill=layer.color)

# Bildgröße ändern (falls Parameter vorhanden)
if output_width and output_height:
    log_image_size("Before Resize", background_image)
    background_image = background_image.resize((output_width, output_height))
    log_image_size("After Resize", background_image)
