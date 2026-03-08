"""
Photobooth — Ghép avatar các thành viên có role nhất định vào 1 tấm hình.
"""

import io
import math
import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ─── Hằng số thiết kế ────────────────────────────────────────────────
AVATAR_SIZE = 128          # px cho mỗi avatar
PADDING = 20               # khoảng cách giữa các avatar
BORDER = 4                 # viền tròn quanh avatar
BG_COLOR = (47, 49, 54)    # màu nền Discord-dark
BORDER_COLOR = (88, 101, 242)  # màu viền (Discord blurple)
TEXT_COLOR = (255, 255, 255)
TITLE_COLOR = (88, 101, 242)
MAX_COLS = 8               # số cột tối đa


async def fetch_avatar(session: aiohttp.ClientSession, url: str, size: int = AVATAR_SIZE) -> Image.Image:
    """Tải avatar từ URL và trả về Image đã resize."""
    async with session.get(str(url)) as resp:
        data = await resp.read()
    img = Image.open(io.BytesIO(data)).convert("RGBA")
    img = img.resize((size, size), Image.LANCZOS)
    return img


def make_circle_avatar(avatar: Image.Image, border: int = BORDER, border_color=BORDER_COLOR) -> Image.Image:
    """Tạo avatar hình tròn với viền."""
    size = avatar.size[0]
    total = size + border * 2

    # Tạo ảnh nền trong suốt
    output = Image.new("RGBA", (total, total), (0, 0, 0, 0))

    # Vẽ vòng tròn viền
    draw = ImageDraw.Draw(output)
    draw.ellipse([0, 0, total - 1, total - 1], fill=border_color)

    # Mask tròn cho avatar
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size - 1, size - 1], fill=255)

    # Paste avatar vào giữa
    output.paste(avatar, (border, border), mask)
    return output


def try_load_font(size: int):
    """Cố tải font đẹp, nếu không có thì dùng font mặc định."""
    font_paths = [
        "C:/Windows/Fonts/segoeui.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/calibri.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for fp in font_paths:
        try:
            return ImageFont.truetype(fp, size)
        except (OSError, IOError):
            continue
    return ImageFont.load_default()


async def create_group_photo(
    members: list,
    title: str = "~ Group Photo ~",
    subtitle: str | None = None,
) -> io.BytesIO:
    """
    Create a collage of member avatars.

    Parameters
    ----------
    members : list[discord.Member]
        List of members to include.
    title : str
        Title on the image.
    subtitle : str | None
        Subtitle line.

    Returns
    -------
    io.BytesIO  — PNG image buffer ready to send.
    """
    count = len(members)
    if count == 0:
        raise ValueError("No members to create photo!")

    # Tính lưới
    cols = min(count, MAX_COLS)
    rows = math.ceil(count / cols)

    cell = AVATAR_SIZE + BORDER * 2 + PADDING + 16  # extra space for name labels
    header_height = 100
    footer_height = 60

    img_w = PADDING + cols * cell
    img_h = header_height + rows * cell + footer_height

    # Tạo canvas
    canvas = Image.new("RGBA", (img_w, img_h), BG_COLOR)
    draw = ImageDraw.Draw(canvas)

    # Font
    font_title = try_load_font(28)
    font_sub = try_load_font(18)
    font_name = try_load_font(12)
    font_footer = try_load_font(14)

    # ── Draw title with cute sparkles ──
    draw.text((img_w // 2, 20), title, fill=TITLE_COLOR, font=font_title, anchor="mt")
    if subtitle:
        draw.text((img_w // 2, 55), subtitle, fill=TEXT_COLOR, font=font_sub, anchor="mt")

    # Cute sparkle dots around title
    sparkle_color = (255, 200, 100)  # golden sparkle
    for dx in [-30, 30]:
        cx = img_w // 2 + dx + (len(title) * 6 * (1 if dx > 0 else -1))
        draw.ellipse([cx - 3, 17, cx + 3, 23], fill=sparkle_color)
        draw.ellipse([cx - 1, 15, cx + 1, 25], fill=sparkle_color)

    # Decorative line under header
    line_y = header_height - 10
    draw.line([(PADDING, line_y), (img_w - PADDING, line_y)], fill=(80, 85, 95), width=2)
    # Small heart accents on the line
    heart_color = (237, 66, 100)
    for hx in [PADDING + 8, img_w - PADDING - 8]:
        draw.ellipse([hx - 4, line_y - 4, hx + 4, line_y + 4], fill=heart_color)

    # Tải & vẽ avatar
    async with aiohttp.ClientSession() as session:
        for idx, member in enumerate(members):
            row = idx // cols
            col = idx % cols

            x = PADDING + col * cell
            y = header_height + row * cell

            # Tải avatar
            avatar_url = member.display_avatar.replace(size=256, format="png")
            try:
                avatar_img = await fetch_avatar(session, avatar_url)
            except Exception:
                # Nếu lỗi, tạo avatar placeholder
                avatar_img = Image.new("RGBA", (AVATAR_SIZE, AVATAR_SIZE), (114, 137, 218, 255))
                d = ImageDraw.Draw(avatar_img)
                d.text((AVATAR_SIZE // 2, AVATAR_SIZE // 2), "?", fill="white", font=font_title, anchor="mm")

            circle_avatar = make_circle_avatar(avatar_img)
            canvas.paste(circle_avatar, (x, y), circle_avatar)

            # Tên thành viên dưới avatar
            name = member.display_name
            if len(name) > 12:
                name = name[:11] + "…"
            name_x = x + (AVATAR_SIZE + BORDER * 2) // 2
            name_y = y + AVATAR_SIZE + BORDER * 2 + 4
            draw.text((name_x, name_y), name, fill=TEXT_COLOR, font=font_name, anchor="mt")

    # ── Footer with cute icons ──
    footer_text = f"Members: {count}"
    draw.text((img_w // 2, img_h - 38), footer_text, fill=(200, 200, 210), font=font_footer, anchor="mt")
    # Small decorative dots
    dot_y = img_h - 18
    for i, color in enumerate([(237, 66, 100), (255, 200, 100), (88, 101, 242), (67, 181, 129)]):
        dx = (i - 1.5) * 14
        draw.ellipse([img_w // 2 + int(dx) - 3, dot_y - 3, img_w // 2 + int(dx) + 3, dot_y + 3], fill=color)

    # Xuất buffer
    buf = io.BytesIO()
    canvas.save(buf, format="PNG")
    buf.seek(0)
    return buf
