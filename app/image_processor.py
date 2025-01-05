from PIL import Image, ImageDraw, ImageFont

def add_text_to_image(image, text, font, font_size, color, position):
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(font, font_size)
    draw.text(position, text, font=font, fill=color)
    return image

def add_image_overlay(image, overlay, position, size):
    overlay = overlay.resize(size)
    image.paste(overlay, position, overlay)
    return image
