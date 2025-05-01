import base64
from io import BytesIO

import arabic_reshaper
from PIL import Image, ImageDraw, ImageFont
from bidi.algorithm import get_display


def get_train_detail(difficulty: int):
    timing = {
        3: "إلزامي قبل مزاولة المهنة أو تجديد ترخيص العمل في المهنة",
        2: "خلال أول شهر من البدء في مزاولة المهنة أو تجديد ترخيص العمل في المهنة",
        1: "يفضل إجراءه",
        0: "غير مطلوب",
    }
    return timing.get(difficulty)

import base64
from io import BytesIO
from PIL import Image, ImageDraw, ImageFont
from bidi.algorithm import get_display
import arabic_reshaper

def generate_certificate(name="Ahmed Mohammed Shaban", lang="en") -> str:
    img = Image.open("tem.jpeg")
    draw = ImageDraw.Draw(img)

    font_path = "Cairo-Bold.ttf"
    font_size = 45
    font = ImageFont.truetype(font_path, font_size)
    text_color = (0, 102, 102)

    # Dynamically determine position based on word count
    word_count = len(name.strip().split())
    if word_count == 3:
        position = (375, 445)
    elif word_count == 2:
        position = (500, 445)
    else:
        position = (585, 445)  # fallback/default

    if lang == "ar":
        name = arabic_reshaper.reshape(name)
        name = get_display(name)

    draw.text(position, name, font=font, fill=text_color)
    # Save to BytesIO and encode to base64
    buffer = BytesIO()
    img.save(buffer, format="JPEG")
    base64_str = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return base64_str

