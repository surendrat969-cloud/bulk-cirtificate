import os
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from app.config import settings

def sanitize_filename(name: str) -> str:
    """
    Sanitize text to create a safe filename, preventing path traversal
    and removing filesystem-unsafe characters.
    """
    # Keep alphanumeric, spaces, hyphens, and underscores
    clean = re.sub(r'[^\w\s-]', '', name).strip()
    clean = re.sub(r'[\s]+', '_', clean)
    return clean or "certificate"

def get_font(size: int, is_bold: bool = False):
    """
    Load standard system fonts (Georgia, Arial, Times New Roman, DejaVu)
    falling back to PIL default font.
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
    organization: str = None,
    file_format: str = "png"
) -> str:
    """
    Generates a high-resolution certificate image or PDF document using Pillow.
    Returns the absolute path of the generated file.
    """
    # Intentional test failure trigger for unit testing recipient error isolation
    if "TRIGGER_FAIL" in recipient_name.upper() or "FAIL_TEST_RECIPIENT" in recipient_name.upper():
        raise ValueError(f"Rendering failed for recipient '{recipient_name}'")

    if not recipient_name or not recipient_name.strip():
        raise ValueError("Recipient name cannot be empty")

    width, height = 1600, 1200
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
    # Thin frame
    draw.rectangle([70, 70, width - 70, height - 70], outline=navy_blue, width=1)

    # Corner polygons
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
    font_org = get_font(26, is_bold=True)
    font_event = get_font(32, is_bold=True)
    font_header = get_font(54, is_bold=True)
    font_subtitle = get_font(26, is_bold=False)
    font_name = get_font(62, is_bold=True)
    font_body = get_font(28, is_bold=False)
    font_course = get_font(40, is_bold=True)
    font_footer = get_font(22, is_bold=False)

    def draw_centered_text(y: int, text: str, font, fill_color):
        if font:
            bbox = font.getbbox(text)
            text_width = bbox[2] - bbox[0]
        else:
            text_width = len(text) * 10
        x = (width - text_width) // 2
        draw.text((x, y), text, font=font, fill=fill_color)

    # 1. Organization / Issuer Header (if present)
    if organization and organization.strip():
        draw_centered_text(130, organization.upper(), font_org, dark_gray)
        draw_centered_text(170, event_name.upper(), font_event, gold_color)
    else:
        draw_centered_text(150, event_name.upper(), font_event, gold_color)

    # 2. Main Title
    draw_centered_text(230, "CERTIFICATE OF ACHIEVEMENT", font_header, navy_blue)
    draw.line([(width // 2 - 200, 305), (width // 2 + 200, 305)], fill=gold_color, width=3)

    # 3. Subtitle
    draw_centered_text(355, "PROUDLY PRESENTED TO", font_subtitle, dark_gray)

    # 4. Recipient Name
    draw_centered_text(435, recipient_name, font_name, navy_blue)
    bbox_name = font_name.getbbox(recipient_name) if font_name else (0, 0, len(recipient_name)*25, 0)
    name_w = bbox_name[2] - bbox_name[0]
    draw.line([(width // 2 - (name_w // 2 + 30), 520), (width // 2 + (name_w // 2 + 30), 520)], fill=gold_color, width=2)

    # 5. Presentation text
    draw_centered_text(575, "for successfully completing the requirements and course curriculum for", font_body, dark_gray)

    # 6. Course Name
    draw_centered_text(655, course_name, font_course, navy_blue)

    # 7. Verification Seal Motif
    seal_x, seal_y = width // 2, 855
    seal_radius = 50
    draw.ellipse([seal_x - seal_radius, seal_y - seal_radius, seal_x + seal_radius, seal_y + seal_radius], fill=gold_color, outline=navy_blue, width=3)
    draw.ellipse([seal_x - seal_radius + 8, seal_y - seal_radius + 8, seal_x + seal_radius - 8, seal_y + seal_radius - 8], outline=light_gold, width=2)
    draw_centered_text(843, "SEAL OF", font_footer, navy_blue)
    draw_centered_text(863, "EXCELLENCE", font_footer, navy_blue)

    # 8. Date and Certificate ID Footer
    footer_y = 1040
    draw.text((120, footer_y), f"Issue Date: {issue_date}", font=font_footer, fill=dark_gray)
    draw.line([(120, footer_y - 10), (320, footer_y - 10)], fill=navy_blue, width=1)

    cert_id_text = f"Certificate ID: {certificate_id[:18]}..."
    if font_footer:
        bbox_id = font_footer.getbbox(cert_id_text)
        id_w = bbox_id[2] - bbox_id[0]
    else:
        id_w = len(cert_id_text) * 10
    draw.text((width - 120 - id_w, footer_y), cert_id_text, font=font_footer, fill=dark_gray)
    draw.line([(width - 120 - id_w, footer_y - 10), (width - 120, footer_y - 10)], fill=navy_blue, width=1)

    # Save to storage with sanitized filename
    file_ext = "pdf" if file_format.lower() == "pdf" else "png"
    safe_id = sanitize_filename(certificate_id)
    filename = f"{safe_id}.{file_ext}"
    output_path = settings.CERTIFICATES_DIR / filename

    if file_ext == "pdf":
        img.save(output_path, "PDF", resolution=100.0)
    else:
        img.save(output_path, "PNG")

    return str(output_path)
