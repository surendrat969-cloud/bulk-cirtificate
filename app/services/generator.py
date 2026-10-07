import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from app.config import settings

def get_font(size: int, is_bold: bool = False):
    """
    Attempts to load standard system fonts (Arial, Times New Roman, DejaVuSans)
    falling back to PIL default font if none are available.
    """
    font_names = []
    if os.name == 'nt':
        font_names = [
            "georgiab.ttf" if is_bold else "georgia.ttf",
            "arialbd.ttf" if is_bold else "arial.ttf",
            "timesbd.ttf" if is_bold else "times.ttf",
        ]
    else:
        font_names = [
            "DejaVuSerif-Bold.ttf" if is_bold else "DejaVuSerif.ttf",
            "DejaVuSans-Bold.ttf" if is_bold else "DejaVuSans.ttf",
        ]
    
    for name in font_names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
            
    try:
        return ImageFont.load_default()
    except Exception:
        return None

def generate_certificate_file(
    certificate_id: str,
    recipient_name: str,
    event_name: str,
    course_name: str,
    issue_date: str,
    file_format: str = "png"
) -> str:
    """
    Generates a high-quality certificate image/PDF using Pillow.
    Returns the absolute file path of the saved certificate.
    """
    # Intentional failure trigger for unit testing individual recipient failure
    if "TRIGGER_FAIL" in recipient_name.upper() or "FAIL_TEST_RECIPIENT" in recipient_name.upper():
        raise ValueError(f"Simulated rendering failure for recipient '{recipient_name}'")

    if not recipient_name or not recipient_name.strip():
        raise ValueError("Recipient name cannot be empty")

    width, height = 1600, 1200
    # Create background (soft cream/off-white)
    bg_color = (252, 251, 247)
    img = Image.new("RGB", (width, height), bg_color)
    draw = ImageDraw.Draw(img)

    # Colors
    navy_blue = (27, 54, 93)      # #1B365D
    gold_color = (212, 175, 55)    # #D4AF37
    dark_gray = (60, 64, 67)      # #3C4043
    light_gold = (244, 226, 163)   # #F4E2A3

    # Outer border (Navy)
    draw.rectangle([40, 40, width - 40, height - 40], outline=navy_blue, width=10)
    # Inner border (Gold)
    draw.rectangle([56, 56, width - 56, height - 56], outline=gold_color, width=4)
    # Decorative inner thin frame
    draw.rectangle([70, 70, width - 70, height - 70], outline=navy_blue, width=1)

    # Corner decorations
    corner_size = 40
    corners = [
        [(70, 70), (70 + corner_size, 70), (70, 70 + corner_size)],
        [(width - 70, 70), (width - 70 - corner_size, 70), (width - 70, 70 + corner_size)],
        [(70, height - 70), (70 + corner_size, height - 70), (70, height - 70 - corner_size)],
        [(width - 70, height - 70), (width - 70 - corner_size, height - 70), (width - 70, height - 70 - corner_size)]
    ]
    for c in corners:
        draw.polygon(c, fill=gold_color)

    # Load fonts
    font_event = get_font(32, is_bold=True)
    font_header = get_font(56, is_bold=True)
    font_subtitle = get_font(28, is_bold=False)
    font_name = get_font(64, is_bold=True)
    font_body = get_font(30, is_bold=False)
    font_course = get_font(42, is_bold=True)
    font_footer = get_font(22, is_bold=False)

    # Helper function to center text horizontally
    def draw_centered_text(y: int, text: str, font, fill_color):
        if font:
            bbox = font.getbbox(text)
            text_width = bbox[2] - bbox[0]
        else:
            text_width = len(text) * 10
        x = (width - text_width) // 2
        draw.text((x, y), text, font=font, fill=fill_color)

    # 1. Event / Organization Header
    draw_centered_text(150, event_name.upper(), font_event, gold_color)

    # 2. Main Certificate Title
    draw_centered_text(230, "CERTIFICATE OF ACHIEVEMENT", font_header, navy_blue)

    # Decorative underline for main header
    draw.line([(width // 2 - 200, 310), (width // 2 + 200, 310)], fill=gold_color, width=3)

    # 3. Subtitle / Presentation line
    draw_centered_text(360, "PROUDLY PRESENTED TO", font_subtitle, dark_gray)

    # 4. Recipient Name (Prominent)
    draw_centered_text(440, recipient_name, font_name, navy_blue)

    # Recipient Underline
    bbox_name = font_name.getbbox(recipient_name) if font_name else (0, 0, len(recipient_name)*25, 0)
    name_w = bbox_name[2] - bbox_name[0]
    draw.line([(width // 2 - (name_w // 2 + 30), 525), (width // 2 + (name_w // 2 + 30), 525)], fill=gold_color, width=2)

    # 5. Presentation Reason / Course
    draw_centered_text(580, "for successfully completing the requirements and course curriculum for", font_body, dark_gray)

    # 6. Course Name
    draw_centered_text(660, course_name, font_course, navy_blue)

    # 7. Decorative Gold Ribbon / Seal at Bottom Center
    seal_x, seal_y = width // 2, 860
    seal_radius = 50
    draw.ellipse([seal_x - seal_radius, seal_y - seal_radius, seal_x + seal_radius, seal_y + seal_radius], fill=gold_color, outline=navy_blue, width=3)
    draw.ellipse([seal_x - seal_radius + 8, seal_y - seal_radius + 8, seal_x + seal_radius - 8, seal_y + seal_radius - 8], outline=light_gold, width=2)
    draw_centered_text(848, "SEAL OF", font_footer, navy_blue)
    draw_centered_text(868, "EXCELLENCE", font_footer, navy_blue)

    # 8. Date and Certificate ID Footer
    footer_y = 1040
    # Left side: Date
    draw.text((120, footer_y), f"Issue Date: {issue_date}", font=font_footer, fill=dark_gray)
    draw.line([(120, footer_y - 10), (320, footer_y - 10)], fill=navy_blue, width=1)

    # Right side: Certificate ID / Verification
    cert_id_text = f"Certificate ID: {certificate_id[:18]}..."
    if font_footer:
        bbox_id = font_footer.getbbox(cert_id_text)
        id_w = bbox_id[2] - bbox_id[0]
    else:
        id_w = len(cert_id_text) * 10
    draw.text((width - 120 - id_w, footer_y), cert_id_text, font=font_footer, fill=dark_gray)
    draw.line([(width - 120 - id_w, footer_y - 10), (width - 120, footer_y - 10)], fill=navy_blue, width=1)

    # Save to storage
    file_ext = "pdf" if file_format.lower() == "pdf" else "png"
    filename = f"{certificate_id}.{file_ext}"
    output_path = settings.CERTIFICATES_DIR / filename

    if file_ext == "pdf":
        img.save(output_path, "PDF", resolution=100.0)
    else:
        img.save(output_path, "PNG")

    return str(output_path)
