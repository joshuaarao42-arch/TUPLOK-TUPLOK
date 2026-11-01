import customtkinter as ctk

import pages as P
import theme as T
from database import Database
from widgets import card, label

NAV = [("Dashboard", "⌂", P.DashboardPage), ("Typing Test", "⌨", P.TypingPage), ("Behavior", "✦", P.BehaviorPage),
       ("Analytics", "◔", P.AnalyticsPage), ("History", "☰", P.HistoryPage),
       ("Recommendations", "➤", P.RecommendationsPage), ("Settings", "⚙", P.SettingsPage)]


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.title("Tuplok-Tuplok - Typing Behavior and Accuracy Analyzer")
        self.geometry("1200x760")
        self.minsize(900, 600)
        self.current = None
        self.after(100, self.maximize)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        for i, (name, _, _) in enumerate(NAV):                 # Ctrl+1 ... Ctrl+7
            self.bind(f"<Control-Key-{i + 1}>", lambda e, n=name: self.show(n))
        self.bind("<Return>", self.restart_key)
        self.bind("<Escape>", self.restart_key)
        self.build()

    def maximize(self):
        try:
            self.state("zoomed")                    
        except Exception:
            try:
                self.attributes("-zoomed", True)     
            except Exception:
                pass

    def restart_key(self, event):
        """Enter (after a finished test) or Esc restarts the typing test from anywhere."""
        page = self.pages.get("Typing Test")
        if self.current == "Typing Test" and (event.keysym == "Escape" or page.done):
            page.new_test()

    def build(self, start="Dashboard"):
        """(Re)creates the sidebar and every page, applying the saved theme and accent."""
        ctk.set_appearance_mode(self.db.get_setting("theme"))
        T.set_accent(self.db.get_setting("accent"))
        self.configure(fg_color=T.BG)
        for w in self.winfo_children():
            w.destroy()
        side = ctk.CTkFrame(self, width=236, corner_radius=0, fg_color=T.SIDEBAR)
        side.grid(row=0, column=0, sticky="ns")
        side.pack_propagate(False)
        brand = ctk.CTkFrame(side, fg_color="transparent")
        brand.pack(fill="x", padx=18, pady=(26, 22))
        ctk.CTkLabel(brand, image=T.logo(44), text="").pack(side="left")
        names = ctk.CTkFrame(brand, fg_color="transparent")
        names.pack(side="left", padx=10)
        label(names, "Tuplok-Tuplok", 17, True).pack(anchor="w")
        label(names, "Typing Analyzer", 11, color=T.MUTED).pack(anchor="w")
        self.nav = {}
        for name, icon, _ in NAV:
            b = ctk.CTkButton(side, text=f"  {icon}    {name}", anchor="w", height=44, corner_radius=12,
                              font=(T.FONT, 14, "bold"), fg_color="transparent", text_color=T.MUTED,
                              hover_color=T.INNER, command=lambda n=name: self.show(n))
            b.pack(fill="x", padx=14, pady=2)
            self.nav[name] = b
        foot = card(side, fg_color=T.INNER, border_width=0)
        foot.pack(side="bottom", fill="x", padx=14, pady=18)
        label(foot, "PERSONAL BEST", 10, True, T.MUTED).pack(anchor="w", padx=14, pady=(12, 0))
        self.best = label(foot, "-", 24, True, T.accent)
        self.best.pack(anchor="w", padx=14)
        label(foot, "Ctrl + 1-7 switches pages", 10, color=T.MUTED).pack(anchor="w", padx=14, pady=(0, 12))
        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.grid(row=0, column=1, sticky="nsew", padx=26, pady=22)
        self.content.grid_columnconfigure(0, weight=1)
        self.content.grid_rowconfigure(0, weight=1)
        self.pages = {}
        for name, _, cls in NAV:
            page = cls(self)
            page.grid(row=0, column=0, sticky="nsew")
            page.grid_remove()
            self.pages[name] = page
        self.show(start)

    def show(self, name):
        self.current = name
        for n, b in self.nav.items():
            on = n == name
            b.configure(fg_color=T.accent if on else "transparent", text_color="white" if on else T.MUTED,
                        hover_color=T.darker(T.accent) if on else T.INNER)
        for p in self.pages.values():
            p.grid_remove()
        self.pages[name].grid()
        self.pages[name].refresh()
        self.update_footer()

    def update_footer(self):
        s = self.db.sessions()
        self.best.configure(text=f"{max(r['wpm'] for r in s):.1f} WPM" if s else "-")