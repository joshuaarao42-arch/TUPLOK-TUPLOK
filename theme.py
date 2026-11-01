import customtkinter as ctk
from PIL import Image, ImageDraw

FONT = "Segoe UI"
BG = ("#f7f2ec", "#17141f")        
SIDEBAR = ("#fffdf9", "#1d1927")
CARD = ("#fffdfa", "#221e2e")
INNER = ("#f1e9e0", "#2d2839")
BORDER = ("#e8ddd0", "#393349")
TEXT = ("#2f2a3b", "#f1ecfa")
MUTED = ("#8b8396", "#a59db8")
GOOD, BAD, WARN = "#5fae8a", "#e0707f", "#e5b04a"  
ACCENTS = {"Lilac": "#8e7cc3", "Sage": "#6fa98d", "Apricot": "#ee9b6b", "Orchid": "#c77dba", "Lagoon": "#5fb3b3"}
accent = ACCENTS["Lilac"]   


def set_accent(name):
    global accent
    accent = ACCENTS.get(name, ACCENTS["Lilac"])


def is_dark():
    return ctk.get_appearance_mode() == "Dark"


def pick(c):
    """Resolve a (light, dark) pair to one color; plain strings pass through."""
    return (c[1] if is_dark() else c[0]) if isinstance(c, tuple) else c


def blend(a, b, t):
    """Mix hex colors a -> b by fraction t."""
    ra, rb = [[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in (a, b)]
    return "#%02x%02x%02x" % tuple(int(x + (y - x) * t) for x, y in zip(ra, rb))


def darker(h, t=0.2):
    return blend(h, "#000000", t)


def tint(color):
    """Soft background pair for an icon badge of the given color."""
    return (blend(color, "#ffffff", 0.85), blend(color, "#000000", 0.72))


def logo_image(size=44):
    """Pillow drawing: a gradient tile holding a white keyboard keycap with the letter T."""
    s = 256
    grad = Image.new("RGBA", (s, s))
    d = ImageDraw.Draw(grad)
    for y in range(s):
        d.line([(0, y), (s, y)], fill=blend(blend(accent, "#ffffff", 0.18), darker(accent, 0.35), y / s))
    mask = Image.new("L", (s, s), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, s - 1, s - 1), radius=64, fill=255)
    img = Image.new("RGBA", (s, s), (0, 0, 0, 0))
    img.paste(grad, (0, 0), mask)
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((40, 62, 216, 222), radius=34, fill=blend(accent, "#ffffff", 0.55))   
    d.rounded_rectangle((40, 44, 216, 196), radius=34, fill="#ffffff")                         
    d.rounded_rectangle((58, 60, 198, 180), radius=24, outline=blend(accent, "#ffffff", 0.8), width=5)
    d.rounded_rectangle((82, 78, 174, 108), radius=10, fill=accent)                            
    d.rounded_rectangle((113, 78, 143, 168), radius=10, fill=accent)                           
    return img.resize((size * 2, size * 2), Image.LANCZOS)


def logo(size=44):
    img = logo_image(size)
    return ctk.CTkImage(light_image=img, dark_image=img, size=(size, size))