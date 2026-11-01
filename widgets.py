import customtkinter as ctk
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

import theme as T


def card(parent, **kw):
    opts = dict(corner_radius=16, fg_color=T.CARD, border_width=1, border_color=T.BORDER)
    opts.update(kw)
    return ctk.CTkFrame(parent, **opts)


def label(parent, text, size=14, bold=False, color=None, **kw):
    return ctk.CTkLabel(parent, text=text, font=(T.FONT, size, "bold" if bold else "normal"),
                        text_color=color or T.TEXT, **kw)


def button(parent, text, command, kind="primary", **kw):
    fg, hover, tc = {"primary": (T.accent, T.darker(T.accent), "white"),
                     "danger": (T.BAD, T.darker(T.BAD), "white"),
                     "ghost": (T.INNER, T.BORDER, T.TEXT)}[kind]
    return ctk.CTkButton(parent, text=text, command=command, fg_color=fg, hover_color=hover, text_color=tc,
                         corner_radius=10, height=38, font=(T.FONT, 13, "bold"), **kw)


def seg(parent, values, command=None):
    return ctk.CTkSegmentedButton(parent, values=values, command=command, height=36, font=(T.FONT, 13, "bold"),
                                  selected_color=T.accent, selected_hover_color=T.darker(T.accent),
                                  unselected_color=T.INNER, unselected_hover_color=T.BORDER,
                                  fg_color=T.INNER, text_color=T.TEXT)


def menu(parent, values, command=None, width=150):
    return ctk.CTkOptionMenu(parent, values=values, command=command, width=width, height=36, corner_radius=10,
                             fg_color=T.INNER, button_color=T.INNER, button_hover_color=T.BORDER,
                             text_color=T.TEXT, dropdown_fg_color=T.CARD, dropdown_text_color=T.TEXT,
                             dropdown_hover_color=T.INNER, font=(T.FONT, 13))


def entry(parent, width=240):
    return ctk.CTkEntry(parent, width=width, height=38, corner_radius=10, fg_color=T.INNER,
                        border_color=T.BORDER, text_color=T.TEXT, font=(T.FONT, 13))


class Flow(ctk.CTkFrame):
    """Responsive grid of stat cards: uses as many columns as fit the width."""

    def __init__(self, parent, min_width=210):
        super().__init__(parent, fg_color="transparent")
        self.items, self.min_width, self.cols = [], min_width, 0
        self.bind("<Configure>", lambda e: self.layout())

    def stat(self, title, icon, color):
        c = card(self)
        top = ctk.CTkFrame(c, fg_color="transparent")
        top.pack(fill="x", padx=16, pady=(14, 0))
        ctk.CTkLabel(top, text=icon, width=32, height=32, corner_radius=9, text_color=color,
                     fg_color=T.tint(color), font=(T.FONT, 15, "bold")).pack(side="left")
        label(top, title, 12, color=T.MUTED).pack(side="left", padx=10)
        value = label(c, "-", 28, True)
        value.pack(anchor="w", padx=16, pady=(6, 0))
        sub = label(c, " ", 11, color=T.MUTED)
        sub.pack(anchor="w", padx=16, pady=(0, 14))
        self.items.append(c)
        self.layout(force=True)
        return value, sub

    def layout(self, force=False):
        cols = max(1, min(len(self.items) or 1, self.winfo_width() // self.min_width))
        if cols == self.cols and not force:
            return
        self.cols = cols
        for i in range(12):
            self.grid_columnconfigure(i, weight=1 if i < cols else 0, uniform="f" if i < cols else "")
        for i, c in enumerate(self.items):
            c.grid(row=i // cols, column=i % cols, sticky="nsew", padx=6, pady=6)


class Split(ctk.CTkFrame):
    """Two side-by-side panels that stack vertically on narrow windows."""

    def __init__(self, parent, weights=(1, 1), break_at=860):
        super().__init__(parent, fg_color="transparent")
        self.left = ctk.CTkFrame(self, fg_color="transparent")
        self.right = ctk.CTkFrame(self, fg_color="transparent")
        self.weights, self.break_at, self.wide = weights, break_at, None
        self.bind("<Configure>", lambda e: self.layout())

    def layout(self):
        wide = self.winfo_width() >= self.break_at
        if wide == self.wide:
            return
        self.wide = wide
        self.grid_columnconfigure(0, weight=self.weights[0] if wide else 1, uniform="s" if wide else "")
        self.grid_columnconfigure(1, weight=self.weights[1] if wide else 0, uniform="s" if wide else "")
        if wide:
            self.left.grid(row=0, column=0, sticky="nsew", padx=(6, 6), pady=6)
            self.right.grid(row=0, column=1, sticky="nsew", padx=(6, 6), pady=6)
        else:
            self.left.grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
            self.right.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)


class Chart(ctk.CTkFrame):
    """A Matplotlib figure that follows the current light/dark theme."""

    def __init__(self, parent, height=260):
        super().__init__(parent, fg_color="transparent")
        self.fig = Figure(figsize=(5, height / 100), dpi=100, layout="constrained")
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

    def begin(self):
        bg = T.pick(T.CARD)
        self.fig.clear()
        self.fig.set_facecolor(bg)
        self.canvas.get_tk_widget().configure(bg=bg, highlightthickness=0)

    def ax(self, *pos, title="", polar=False):
        a = self.fig.add_subplot(*pos, projection="polar" if polar else None, facecolor=T.pick(T.CARD))
        a.set_title(title, color=T.pick(T.TEXT), fontsize=11, fontweight="bold", pad=10,
                    loc="center" if polar else "left")
        a.tick_params(colors=T.pick(T.MUTED), labelsize=8)
        a.grid(True, color=T.pick(T.BORDER), alpha=0.8, linewidth=0.6)
        for name, spine in a.spines.items():
            spine.set_color(T.pick(T.BORDER))
            if name in ("top", "right"):
                spine.set_visible(False)
        return a

    def empty(self, a, msg="No data yet"):
        a.text(0.5, 0.5, msg, ha="center", va="center", color=T.pick(T.MUTED), transform=a.transAxes)

    def show(self):
        self.canvas.draw_idle()


ROWS = ["1234567890-=", "qwertyuiop[]", "asdfghjkl;'", "zxcvbnm,./"]
SHIFT = {"!": "1", "@": "2", "#": "3", "$": "4", "%": "5", "^": "6", "&": "7", "*": "8", "(": "9", ")": "0",
         "_": "-", "+": "=", "{": "[", "}": "]", ":": ";", '"': "'", "<": ",", ">": ".", "?": "/"}


def key_of(ch):
    """Physical key for a typed character."""
    return SHIFT.get(ch, ch.lower())


class Keyboard(ctk.CTkFrame):
    """On-screen keyboard: highlights the next key, or shows a mistake heatmap."""

    def __init__(self, parent, key=34):
        super().__init__(parent, fg_color="transparent")
        self.keys, self.current = {}, None
        for r, row in enumerate(ROWS):
            f = ctk.CTkFrame(self, fg_color="transparent")
            f.pack(pady=2)
            if r:
                ctk.CTkFrame(f, width=r * 14, height=1, fg_color="transparent").pack(side="left")
            for ch in row:
                k = ctk.CTkLabel(f, text=ch.upper(), width=key, height=key, corner_radius=8,
                                 fg_color=T.INNER, text_color=T.MUTED, font=(T.FONT, 12, "bold"))
                k.pack(side="left", padx=2)
                self.keys[ch] = k
        space = ctk.CTkLabel(self, text="space", width=key * 7, height=key, corner_radius=8,
                             fg_color=T.INNER, text_color=T.MUTED, font=(T.FONT, 11))
        space.pack(pady=2)
        self.keys[" "] = space

    def reset(self):
        for k in self.keys.values():
            k.configure(fg_color=T.INNER, text_color=T.MUTED)
        self.current = None

    def highlight(self, ch):
        if self.current:
            self.current.configure(fg_color=T.INNER, text_color=T.MUTED)
        self.current = self.keys.get(key_of(ch)) if ch else None
        if self.current:
            self.current.configure(fg_color=T.accent, text_color="white")

    def heatmap(self, counts):
        """counts: {char: mistakes}. Redder keys = more mistakes."""
        self.reset()
        merged = {}
        for ch, n in counts.items():
            merged[key_of(ch)] = merged.get(key_of(ch), 0) + n
        top = max(merged.values(), default=0)
        for ch, n in merged.items():
            if ch in self.keys and top:
                color = T.blend(T.pick(T.INNER), T.BAD, 0.3 + 0.7 * n / top)
                self.keys[ch].configure(fg_color=color, text_color="white")
