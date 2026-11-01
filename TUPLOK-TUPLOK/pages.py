import csv
import math
import time
import tkinter.messagebox as mb
from datetime import datetime
from tkinter import filedialog

import customtkinter as ctk

import logic
import theme as T
from widgets import Chart, Flow, Keyboard, Split, button, card, entry, label, menu, seg


class Page(ctk.CTkFrame):
    def __init__(self, app, title, subtitle="", scroll=False):
        super().__init__(app.content, fg_color="transparent")
        self.app, self.db = app, app.db
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        head = ctk.CTkFrame(self, fg_color="transparent")
        head.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        head.grid_columnconfigure(0, weight=1)
        titles = ctk.CTkFrame(head, fg_color="transparent")
        titles.grid(row=0, column=0, sticky="w")
        self.title_lbl = label(titles, title, 28, True)
        self.title_lbl.pack(anchor="w")
        self.sub_lbl = label(titles, subtitle, 13, color=T.MUTED)
        self.sub_lbl.pack(anchor="w")
        self.actions = ctk.CTkFrame(head, fg_color="transparent", width=1, height=1)
        self.actions.grid(row=0, column=1, sticky="e")
        self.body = (ctk.CTkScrollableFrame(self, fg_color="transparent") if scroll
                     else ctk.CTkFrame(self, fg_color="transparent"))
        self.body.grid(row=1, column=0, sticky="nsew")

    def refresh(self):
        pass


# Dashboard
class DashboardPage(Page):
    def __init__(self, app):
        super().__init__(app, "Dashboard", scroll=True)
        button(self.actions, "⌨   Start Typing Test", lambda: app.show("Typing Test"), width=190).pack()
        self.flow = Flow(self.body)
        self.flow.pack(fill="x")
        spec = [("Average WPM", "⚡", T.accent), ("Average Accuracy", "◎", T.GOOD), ("Tests Completed", "✓", "#b58ae0"),
                ("Best WPM", "★", T.WARN), ("Best Accuracy", "◆", "#5fb3b3"), ("Day Streak", "✹", "#ee9b6b")]
        self.stats = [self.flow.stat(*s) for s in spec]
        split = Split(self.body, weights=(3, 2))
        split.pack(fill="x", pady=(6, 0))
        c = card(split.left)
        c.pack(fill="both", expand=True)
        label(c, "WPM Trend", 16, True).pack(anchor="w", padx=18, pady=(16, 0))
        label(c, "Your last 20 tests", 12, color=T.MUTED).pack(anchor="w", padx=18)
        self.chart = Chart(c, height=270)
        self.chart.pack(fill="both", expand=True, padx=8, pady=8)
        c2 = card(split.right)
        c2.pack(fill="both", expand=True)
        label(c2, "Recent Sessions", 16, True).pack(anchor="w", padx=18, pady=(16, 6))
        self.recent = ctk.CTkFrame(c2, fg_color="transparent")
        self.recent.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        tip = card(self.body)
        tip.pack(fill="x", padx=6, pady=(6, 0))
        label(tip, "✦  COACH TIP", 11, True, T.accent).pack(anchor="w", padx=18, pady=(14, 0))
        self.tip = label(tip, "", 14, wraplength=820, justify="left")
        self.tip.pack(anchor="w", padx=18, pady=(2, 16))

    def refresh(self):
        s = self.db.sessions()
        hour = datetime.now().hour
        greet = "Good morning" if hour < 12 else "Good afternoon" if hour < 18 else "Good evening"
        self.title_lbl.configure(text=f"{greet}, {self.db.get_setting('name')}")
        self.sub_lbl.configure(text="Here is your typing overview.")
        if s:
            bw, ba = max(s, key=lambda r: r["wpm"]), max(s, key=lambda r: r["accuracy"])
            data = [(f"{logic.avg(s, 'wpm'):.1f}", f"Last test: {s[-1]['wpm']:.1f}"),
                    (f"{logic.avg(s, 'accuracy'):.1f}%", f"Last test: {s[-1]['accuracy']:.1f}%"),
                    (str(len(s)), f"{logic.today_count(s)} today"),
                    (f"{bw['wpm']:.1f}", bw["date"][:10]), (f"{ba['accuracy']:.1f}%", ba["date"][:10]),
                    (str(logic.streak(s)), "days in a row")]
        else:
            data = [("-", "No tests yet")] * 2 + [("0", " ")] + [("-", " ")] * 2 + [("0", "days in a row")]
        for (value, sub), (v, t) in zip(self.stats, data):
            value.configure(text=v)
            sub.configure(text=t)
        ch = self.chart
        ch.begin()
        a = ch.ax(1, 1, 1)
        wpm = [r["wpm"] for r in s[-20:]]
        if wpm:
            x = list(range(1, len(wpm) + 1))
            a.plot(x, wpm, color=T.accent, marker="o", linewidth=2.2, markersize=5)
            a.fill_between(x, wpm, color=T.accent, alpha=0.15)
            a.set_ylim(bottom=0)
        else:
            ch.empty(a, "Complete a test to see your trend")
        ch.show()
        for w in self.recent.winfo_children():
            w.destroy()
        if not s:
            label(self.recent, "Nothing here yet.", 13, color=T.MUTED).pack(pady=20)
        for r in reversed(s[-6:]):
            row = ctk.CTkFrame(self.recent, fg_color=T.INNER, corner_radius=10)
            row.pack(fill="x", pady=3)
            label(row, f"{r['wpm']:.0f}", 20, True, T.accent).pack(side="left", padx=(14, 4), pady=8)
            label(row, "WPM", 11, color=T.MUTED).pack(side="left")
            label(row, f"{r['accuracy']:.0f}%", 13, True).pack(side="right", padx=14)
            label(row, f"{r['difficulty']} · {r['date'][5:]}", 12, color=T.MUTED).pack(side="right", padx=6)
        self.tip.configure(text=logic.recommendations(s, self.db.mistakes())[0][2])


# Typing test
class TypingPage(Page):
    def __init__(self, app):
        super().__init__(app, "Typing Test", "Type the text below. The timer starts on your first key.   Esc = restart")
        self.tracker, self.job, self.done = None, None, False
        self.duration, self.mode, self.drill, self.cache = 60, "Medium", None, {}
        b = self.body
        b.grid_columnconfigure(0, weight=1)
        b.grid_rowconfigure(3, weight=1, minsize=230)
        bar = ctk.CTkFrame(b, fg_color="transparent")
        bar.grid(row=0, column=0, sticky="ew")
        self.diff = seg(bar, logic.DIFFICULTIES, lambda v: self.new_test())
        self.diff.pack(side="left")
        self.dur = seg(bar, ["15s", "30s", "60s", "120s"], lambda v: self.new_test())
        self.dur.pack(side="left", padx=12)
        button(bar, "↻   Restart", self.new_test, "ghost", width=120).pack(side="right")
        chips = ctk.CTkFrame(b, fg_color="transparent")
        chips.grid(row=1, column=0, sticky="ew", pady=10)
        self.chip = {}
        for i, (key, title) in enumerate([("time", "TIME"), ("wpm", "WPM"), ("acc", "ACCURACY"), ("err", "ERRORS")]):
            chips.grid_columnconfigure(i, weight=1, uniform="c")
            c = card(chips)
            c.grid(row=0, column=i, sticky="nsew", padx=6)
            label(c, title, 11, True, T.MUTED).pack(anchor="w", padx=16, pady=(10, 0))
            self.chip[key] = label(c, "-", 26, True)
            self.chip[key].pack(anchor="w", padx=16, pady=(0, 10))
        self.progress = ctk.CTkProgressBar(b, height=6, progress_color=T.accent, fg_color=T.INNER)
        self.progress.set(0)
        self.progress.grid(row=2, column=0, sticky="ew", padx=6, pady=(0, 10))
        self.tcard = card(b)
        self.tcard.grid(row=3, column=0, sticky="nsew", padx=6)
        self.box = ctk.CTkTextbox(self.tcard, wrap="word", fg_color="transparent", text_color=T.MUTED,
                                  border_width=0, activate_scrollbars=False)
        self.box.pack(fill="both", expand=True, padx=14, pady=14)
        self.box._textbox.configure(spacing2=10, padx=10, pady=6)
        self.box.bind("<Key>", self.on_key)
        self.box.bind("<Button-1>", lambda e: (self.box.focus_set(), "break")[1])
        # results panel: replaces the text card (and keyboard) when a test ends
        self.res = card(b, border_color=T.accent, border_width=2)
        self.res.grid_columnconfigure(0, weight=1)
        self.res.grid_rowconfigure(0, weight=1)
        self.kcard = card(b)
        self.kb = Keyboard(self.kcard, key=32)
        self.kb.pack(pady=12)

    def destroy(self):
        if self.job:
            self.after_cancel(self.job)
        super().destroy()

    def set_chip(self, key, text):
        """Only touches the label when its text really changed (keeps typing smooth)."""
        if self.cache.get(key) != text:
            self.cache[key] = text
            self.chip[key].configure(text=text)

    def refresh(self):
        if self.drill:
            text, self.drill = self.drill, None
            self.new_test(text)
        elif self.tracker is None or not self.tracker.typed:
            self.diff.set(self.db.get_setting("difficulty"))
            d = self.db.get_setting("duration")
            self.dur.configure(values=[f"{v}s" for v in sorted({15, 30, 60, 120, int(d)})])
            self.dur.set(f"{d}s")
            self.new_test()
        self.box.focus_set()

    def new_test(self, custom=None):
        if self.job:
            self.after_cancel(self.job)
        self.job, self.done, self.cache = None, False, {}
        self.res.grid_remove()
        self.tcard.grid()
        self.mode = "Drill" if custom else self.diff.get()
        self.duration = int(self.dur.get()[:-1])
        text = custom or logic.build_text(self.diff.get(), self.duration)
        self.tracker = logic.TypingTracker(text)
        self.box.configure(font=("Consolas", int(self.db.get_setting("font_size"))), state="normal",
                           text_color=T.MUTED)
        self.box.tag_config("ok", foreground=T.pick(T.TEXT))
        self.box.tag_config("bad", foreground=T.BAD, background=T.pick(("#fbe3e6", "#4a2230")))
        self.box.tag_config("cur", background=T.accent, foreground="white")
        self.box.delete("1.0", "end")
        self.box.insert("1.0", text)
        self.box.configure(state="disabled")
        self.move_cursor()
        for key, v in (("time", f"{self.duration}s"), ("wpm", "0"), ("acc", "100%"), ("err", "0")):
            self.set_chip(key, v)
        self.progress.set(0)
        if self.db.get_setting("keyboard") == "1":
            self.kcard.grid(row=4, column=0, sticky="ew", padx=6, pady=(10, 0))
            self.kb.highlight(text[0])
        else:
            self.kcard.grid_remove()
        self.box.focus_set()

    def mark(self, i, tag):
        self.box.tag_add(tag, f"1.0+{i}c", f"1.0+{i + 1}c")

    def move_cursor(self):
        n = len(self.tracker.typed)
        self.box.tag_remove("cur", "1.0", "end")
        self.box.tag_add("cur", f"1.0+{n}c", f"1.0+{n + 1}c")
        self.box.see(f"1.0+{n}c")

    def on_key(self, event):
        if event.state & 0x4:           
            return None
        if event.keysym == "Escape":
            self.new_test()
            return "break"
        t = self.tracker
        if self.done:
            return "break"
        if event.keysym == "BackSpace":
            if t.typed:              
                i = len(t.typed) - 1
                t.backspace()
                for tag in ("ok", "bad"):
                    self.box.tag_remove(tag, f"1.0+{i}c", f"1.0+{i + 1}c")
        elif len(event.char) == 1 and event.char.isprintable():
            if t.start is None:
                self.job = self.after(100, self.tick)
            i = len(t.typed)
            t.press(event.char)
            self.mark(i, "ok" if event.char == t.target[i] else "bad")
        else:
            return "break"
        self.move_cursor()
        if t.finished():
            self.finish()
        else:
            self.kb.highlight(t.target[len(t.typed)])
        return "break"

    def tick(self):
        t = self.tracker
        elapsed = time.time() - t.start
        self.set_chip("time", f"{max(0, self.duration - elapsed):.0f}s")
        self.set_chip("wpm", f"{t.wpm(elapsed):.0f}")
        self.set_chip("acc", f"{100 * (t.keys - t.errors) / t.keys:.0f}%" if t.keys else "100%")
        self.set_chip("err", str(t.errors))
        self.progress.set(min(1, elapsed / self.duration))
        if elapsed >= self.duration:
            self.finish()
        else:
            self.job = self.after(100, self.tick)

    def finish(self):
        if self.done:
            return
        self.done = True
        if self.job:
            self.after_cancel(self.job)
        t = self.tracker
        r = t.results(min(time.time() - t.start, self.duration))
        r.update(difficulty=self.mode, duration=self.duration)
        best = max((s["wpm"] for s in self.db.sessions()), default=0)
        self.db.add_session(r, t.mistakes)
        for key, v in (("time", "Done"), ("wpm", f"{r['wpm']:.0f}"), ("acc", f"{r['accuracy']:.0f}%"),
                       ("err", str(r["errors"]))):
            self.set_chip(key, v)
        self.progress.set(1)
        self.kb.highlight("")
        self.show_result(r, best)
        self.app.update_footer()

    def show_result(self, r, best):
        for w in self.res.winfo_children():
            w.destroy()
        inner = ctk.CTkFrame(self.res, fg_color="transparent")
        inner.grid(row=0, column=0, pady=20)
        record = r["wpm"] > best
        label(inner, "🏆  New personal record!" if record else "Test complete", 15, True,
              T.GOOD if record else T.MUTED).pack()
        label(inner, f"{r['wpm']:.0f}", 80, True, T.accent).pack()
        label(inner, "words per minute", 13, color=T.MUTED).pack()
        row = ctk.CTkFrame(inner, fg_color="transparent")
        row.pack(pady=18)
        for i, (name, val) in enumerate([("Accuracy", f"{r['accuracy']:.1f}%"), ("Errors", str(r["errors"])),
                                         ("Consistency", f"{r['consistency']:.0f}%"),
                                         ("Key gap", f"{r['avg_interval']:.0f} ms")]):
            c = ctk.CTkFrame(row, fg_color=T.INNER, corner_radius=14)
            c.grid(row=0, column=i, padx=6)
            label(c, val, 20, True).pack(padx=20, pady=(12, 0))
            label(c, name, 11, color=T.MUTED).pack(padx=20, pady=(0, 12))
        btns = ctk.CTkFrame(inner, fg_color="transparent")
        btns.pack()
        button(btns, "Try Again  (Enter)", self.new_test, width=170).pack(side="left", padx=6)
        button(btns, "View Analytics", lambda: self.app.show("Analytics"), "ghost", width=150).pack(side="left", padx=6)
        self.tcard.grid_remove()
        self.kcard.grid_remove()
        self.res.grid(row=3, column=0, rowspan=2, sticky="nsew", padx=6)


# Behavior / fingerprint
class BehaviorPage(Page):
    def __init__(self, app):
        super().__init__(app, "Behavior Analyzer", "Your Typing Fingerprint - how you type, not just how fast.", scroll=True)
        banner = card(self.body)
        banner.pack(fill="x", padx=6)
        label(banner, "YOUR TYPING FINGERPRINT", 11, True, T.MUTED).pack(anchor="w", padx=20, pady=(16, 0))
        self.profile = label(banner, "-", 32, True, T.accent)
        self.profile.pack(anchor="w", padx=20)
        self.desc = label(banner, "", 13, color=T.MUTED, wraplength=800, justify="left")
        self.desc.pack(anchor="w", padx=20, pady=(2, 16))
        self.flow = Flow(self.body)
        self.flow.pack(fill="x", pady=(6, 0))
        spec = [("Keystroke Interval", "⏱", T.accent), ("Hesitation", "⏸", T.WARN),
                ("Consistency", "≋", T.GOOD), ("Corrected Mistakes", "⌫", T.BAD)]
        self.stats = [self.flow.stat(*s) for s in spec]
        split = Split(self.body)
        split.pack(fill="x")
        c1 = card(split.left)
        c1.pack(fill="both", expand=True)
        self.radar = Chart(c1, height=340)
        self.radar.pack(fill="both", expand=True, padx=8, pady=8)
        c2 = card(split.right)
        c2.pack(fill="both", expand=True)
        label(c2, "Mistake Heatmap", 16, True).pack(anchor="w", padx=18, pady=(16, 0))
        label(c2, "Redder keys are mistyped more often.", 12, color=T.MUTED).pack(anchor="w", padx=18, pady=(0, 14))
        self.kb = Keyboard(c2, key=30)
        self.kb.pack(pady=(0, 18))
        c3 = card(self.body)
        c3.pack(fill="x", padx=6, pady=(6, 0))
        label(c3, "Most Frequent Mistakes", 16, True).pack(anchor="w", padx=18, pady=(16, 6))
        self.rows = ctk.CTkFrame(c3, fg_color="transparent")
        self.rows.pack(fill="x", padx=18, pady=(0, 16))

    def refresh(self):
        s, m = self.db.sessions(), self.db.mistakes(60)
        f = logic.fingerprint(s, m)
        self.kb.heatmap(dict(m))
        ch = self.radar
        ch.begin()
        a = ch.ax(1, 1, 1, title="Skill Profile", polar=True)
        for w in self.rows.winfo_children():
            w.destroy()
        if not f:
            self.profile.configure(text="No fingerprint yet")
            self.desc.configure(text="Complete a typing test and your behavior profile will be built here.")
            for value, sub in self.stats:
                value.configure(text="-")
                sub.configure(text=" ")
            ch.empty(a)
            ch.show()
            label(self.rows, "No data yet.", 13, color=T.MUTED).pack(anchor="w")
            return
        self.profile.configure(text=f["profile"])
        self.desc.configure(text=logic.PROFILES[f["profile"]])
        data = [(f"{f['interval']:.0f} ms", "average gap between keys"), (f"{f['hesitation']:.1f}", "pauses per 100 keys"),
                (f"{f['consistency']:.0f}%", "rhythm steadiness"), (str(f["corrections"]), "errors you fixed")]
        for (value, sub), (v, t) in zip(self.stats, data):
            value.configure(text=v)
            sub.configure(text=t)
        scores = logic.radar_scores(f)
        names, vals = list(scores), list(scores.values())
        ang = [i * 2 * math.pi / len(vals) for i in range(len(vals))]
        a.plot(ang + ang[:1], vals + vals[:1], color=T.accent, linewidth=2)
        a.fill(ang + ang[:1], vals + vals[:1], color=T.accent, alpha=0.25)
        a.set_xticks(ang)
        a.set_xticklabels(names, color=T.pick(T.TEXT), fontsize=9)
        a.set_ylim(0, 100)
        a.set_yticks([25, 50, 75])
        a.set_yticklabels([])
        ch.show()
        top = f["top"]
        if not top:
            label(self.rows, "No mistakes recorded. Great!", 13, color=T.GOOD).pack(anchor="w")
        for c, n in top:
            row = ctk.CTkFrame(self.rows, fg_color="transparent")
            row.pack(fill="x", pady=4)
            ctk.CTkLabel(row, text=logic.char_name(c), width=60, height=32, corner_radius=8, fg_color=T.INNER,
                         font=("Consolas", 14, "bold"), text_color=T.TEXT).pack(side="left")
            bar = ctk.CTkProgressBar(row, height=10, progress_color=T.BAD, fg_color=T.INNER)
            bar.set(n / top[0][1])
            bar.pack(side="left", fill="x", expand=True, padx=12)
            label(row, f"{n} mistakes", 12, color=T.MUTED).pack(side="left")


# Analytics
class AnalyticsPage(Page):
    def __init__(self, app):
        super().__init__(app, "Analytics", "Track your progress over time.", scroll=True)
        self.range = seg(self.actions, ["Last 10", "Last 30", "All"], lambda v: self.refresh())
        self.range.set("Last 30")
        self.range.pack()
        self.flow = Flow(self.body)
        self.flow.pack(fill="x")
        spec = [("Tests in Range", "✓", T.accent), ("WPM Change", "⚡", T.GOOD),
                ("Accuracy Change", "◎", "#5fb3b3"), ("Weakest Key", "⌨", T.BAD)]
        self.stats = [self.flow.stat(*s) for s in spec]
        c = card(self.body)
        c.pack(fill="x", padx=6, pady=(6, 0))
        self.chart = Chart(c, height=660)
        self.chart.pack(fill="both", expand=True, padx=8, pady=8)

    @staticmethod
    def change(values, unit):
        if len(values) < 4:
            return "-", "needs 4+ tests"
        h = len(values) // 2
        d = sum(values[h:]) / len(values[h:]) - sum(values[:h]) / h
        return f"{d:+.1f}{unit}", "second half vs first half"

    def refresh(self):
        s = self.db.sessions()
        n = {"Last 10": 10, "Last 30": 30}.get(self.range.get(), len(s))
        s = s[-n:]
        m = self.db.mistakes(8)
        wpm, acc = [r["wpm"] for r in s], [r["accuracy"] for r in s]
        data = [(str(len(s)), self.range.get().lower()), self.change(wpm, " WPM"), self.change(acc, "%"),
                (f"'{logic.char_name(m[0][0])}'" if m else "-", f"{m[0][1]} mistakes" if m else " ")]
        for (value, sub), (v, t) in zip(self.stats, data):
            value.configure(text=v)
            sub.configure(text=t)
        ch = self.chart
        ch.begin()
        x = list(range(1, len(s) + 1))
        a1 = ch.ax(2, 2, 1, title="WPM Progression")
        a2 = ch.ax(2, 2, 2, title="Accuracy Trend (%)")
        a3 = ch.ax(2, 2, 3, title="Error Distribution")
        a4 = ch.ax(2, 2, 4, title="Performance by Difficulty")
        if s:
            a1.plot(x, wpm, color=T.accent, marker="o", linewidth=2, markersize=4, label="WPM")
            a1.fill_between(x, wpm, color=T.accent, alpha=0.12)
            a1.plot(x, logic.moving_average(wpm), color=T.WARN, linestyle="--", linewidth=1.6, label="3-test average")
            a1.legend(fontsize=8, facecolor=T.pick(T.CARD), labelcolor=T.pick(T.MUTED), edgecolor=T.pick(T.BORDER))
            a2.plot(x, acc, color=T.GOOD, marker="o", linewidth=2, markersize=4)
            a2.axhline(95, color=T.pick(T.MUTED), linestyle=":", linewidth=1)
            a2.set_ylim(max(0, min(acc) - 5), 101)
        else:
            ch.empty(a1)
            ch.empty(a2)
        if m:
            a3.barh([logic.char_name(c) for c, _ in m][::-1], [k for _, k in m][::-1], color=T.BAD)
        else:
            ch.empty(a3, "No mistakes recorded")
        by = {d: [r for r in s if r["difficulty"] == d] for d in logic.DIFFS}
        by = {d: v for d, v in by.items() if v}
        if by:
            bars = a4.bar(list(by), [logic.avg(v, "wpm") for v in by.values()], color=T.accent, width=0.5)
            a4.bar_label(bars, fmt="%.0f", color=T.pick(T.TEXT), fontsize=9, padding=2)
            a4.set_ylabel("Average WPM", color=T.pick(T.MUTED), fontsize=8)
        else:
            ch.empty(a4)
        ch.show()


# History
class HistoryPage(Page):
    COLS = [("Date", 18), ("Level", 10), ("Time", 8), ("WPM", 9), ("Accuracy", 11), ("Errors", 8),
            ("Consistency", 12), ("", 5)]

    def __init__(self, app):
        super().__init__(app, "History", "Every typing session you have completed.")
        self.fdiff = menu(self.actions, ["All"] + logic.DIFFS, lambda v: self.refresh(), 110)
        self.fdiff.pack(side="left", padx=4)
        self.sort = menu(self.actions, ["Newest", "Oldest", "Highest WPM", "Highest accuracy"],
                         lambda v: self.refresh(), 160)
        self.sort.pack(side="left", padx=4)
        button(self.actions, "⇩  Export CSV", self.export, "ghost", width=130).pack(side="left", padx=4)
        c = card(self.body)
        c.pack(fill="both", expand=True, padx=6)
        head = ctk.CTkFrame(c, fg_color="transparent")
        head.pack(fill="x", padx=16, pady=(14, 0))
        self.grid_cols(head)
        for i, (name, _) in enumerate(self.COLS):
            label(head, name.upper(), 11, True, T.MUTED).grid(row=0, column=i, sticky="w", padx=8)
        self.count = label(c, "", 12, color=T.MUTED)
        self.count.pack(side="bottom", anchor="w", padx=18, pady=(0, 12))
        self.rows = ctk.CTkScrollableFrame(c, fg_color="transparent")
        self.rows.pack(fill="both", expand=True, padx=8, pady=8)

    def grid_cols(self, frame):
        for i, (_, w) in enumerate(self.COLS):
            frame.grid_columnconfigure(i, weight=w, uniform="h")

    def filtered(self):
        s = self.db.sessions()
        if self.fdiff.get() != "All":
            s = [r for r in s if r["difficulty"] == self.fdiff.get()]
        key, rev = {"Newest": ("id", True), "Oldest": ("id", False), "Highest WPM": ("wpm", True),
                    "Highest accuracy": ("accuracy", True)}[self.sort.get()]
        return sorted(s, key=lambda r: r[key], reverse=rev)

    def refresh(self):
        for w in self.rows.winfo_children():
            w.destroy()
        s = self.filtered()
        if not s:
            label(self.rows, "No sessions to show.", 13, color=T.MUTED).pack(pady=30)
        for i, r in enumerate(s[:100]):
            row = ctk.CTkFrame(self.rows, fg_color=T.INNER if i % 2 == 0 else "transparent", corner_radius=10)
            row.pack(fill="x", pady=1)
            self.grid_cols(row)
            color = T.GOOD if r["wpm"] >= 60 else T.accent if r["wpm"] >= 35 else T.WARN
            cells = [(r["date"], T.TEXT, False), (r["difficulty"], T.MUTED, False), (f"{r['duration']}s", T.MUTED, False),
                     (f"{r['wpm']:.1f}", color, True), (f"{r['accuracy']:.1f}%", T.TEXT, False),
                     (str(r["errors"]), T.TEXT, False), (f"{r['consistency']:.0f}%", T.TEXT, False)]
            for j, (text, col, bold) in enumerate(cells):
                label(row, text, 13, bold, col).grid(row=0, column=j, sticky="w", padx=8, pady=7)
            ctk.CTkButton(row, text="✕", width=28, height=26, fg_color="transparent", hover_color=T.BAD,
                          text_color=T.MUTED, command=lambda sid=r["id"]: self.delete(sid)).grid(row=0, column=7, padx=4)
        self.count.configure(text=f"Showing {min(len(s), 100)} of {len(s)} sessions")

    def delete(self, session_id):
        if mb.askyesno("Delete session", "Delete this session permanently?"):
            self.db.delete_session(session_id)
            self.refresh()

    def export(self):
        s = self.filtered()
        if not s:
            mb.showinfo("Export", "There are no sessions to export.")
            return
        path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="tuplok_history.csv",
                                            filetypes=[("CSV file", "*.csv")])
        if path:
            try:
                with open(path, "w", newline="", encoding="utf-8") as fh:
                    w = csv.DictWriter(fh, fieldnames=list(s[0]))
                    w.writeheader()
                    w.writerows(s)
                mb.showinfo("Export", f"Saved {len(s)} sessions.")
            except OSError as e:
                mb.showerror("Export failed", str(e))


# Recommendations
class RecommendationsPage(Page):
    def __init__(self, app):
        super().__init__(app, "Recommendations", "Personalized advice based on your real results.", scroll=True)
        button(self.actions, "⚡  Practice Weak Keys", self.start_drill, width=200).pack()
        self.focus = card(self.body)
        self.focus.pack(fill="x", padx=6, pady=(0, 8))
        label(self.focus, "FOCUS KEYS", 11, True, T.MUTED).pack(anchor="w", padx=18, pady=(14, 6))
        self.chips = ctk.CTkFrame(self.focus, fg_color="transparent")
        self.chips.pack(anchor="w", padx=14, pady=(0, 14))
        self.list = ctk.CTkFrame(self.body, fg_color="transparent")
        self.list.pack(fill="x")

    def refresh(self):
        s, m = self.db.sessions(), self.db.mistakes(10)
        for w in self.chips.winfo_children():
            w.destroy()
        if not m:
            label(self.chips, "No weak keys yet - keep typing!", 13, color=T.MUTED).pack(padx=4)
        for c, n in m[:6]:
            ctk.CTkLabel(self.chips, text=f" {logic.char_name(c)} · {n} ", height=34, corner_radius=10,
                         fg_color=T.tint(T.BAD), text_color=T.BAD, font=("Consolas", 14, "bold")).pack(side="left", padx=4)
        for w in self.list.winfo_children():
            w.destroy()
        style = {"good": ("✔", T.GOOD), "warn": ("!", T.WARN), "tip": ("➤", T.accent)}
        for kind, title, text in logic.recommendations(s, m):
            icon, color = style[kind]
            c = card(self.list)
            c.pack(fill="x", padx=6, pady=5)
            ctk.CTkLabel(c, text=icon, width=44, height=44, corner_radius=12, fg_color=T.tint(color),
                         text_color=color, font=(T.FONT, 18, "bold")).pack(side="left", padx=16, pady=16, anchor="n")
            col = ctk.CTkFrame(c, fg_color="transparent")
            col.pack(side="left", fill="x", expand=True, pady=14, padx=(0, 16))
            label(col, title, 15, True).pack(anchor="w")
            label(col, text, 13, color=T.MUTED, wraplength=700, justify="left").pack(anchor="w", pady=(2, 0))

    def start_drill(self):
        m = self.db.mistakes(5)
        if not m:
            mb.showinfo("Practice weak keys", "No mistakes recorded yet. Take a few tests first.")
            return
        self.app.pages["Typing Test"].drill = logic.drill_text([c for c, _ in m], 360)
        self.app.show("Typing Test")


# Settings
class SettingsPage(Page):
    SIZES = {"Small": "18", "Medium": "22", "Large": "28"}

    def __init__(self, app):
        super().__init__(app, "Settings", "Customize Tuplok-Tuplok.", scroll=True)
        c = self.section("Profile")
        self.field(c, "Your name")
        self.name = entry(c)
        self.name.pack(anchor="w", padx=18, pady=(0, 14))
        c = self.section("Appearance")
        self.field(c, "Theme")
        self.theme = seg(c, ["Light", "Dark", "System"])
        self.theme.pack(anchor="w", padx=18, pady=(0, 8))
        self.field(c, "Accent color")
        self.accent = seg(c, list(T.ACCENTS))
        self.accent.pack(anchor="w", padx=18, pady=(0, 14))
        c = self.section("Typing")
        self.field(c, "Default difficulty")
        self.diff = seg(c, logic.DIFFICULTIES)
        self.diff.pack(anchor="w", padx=18, pady=(0, 8))
        self.field(c, "Default duration in seconds (10 - 300)")
        self.dur = entry(c, 120)
        self.dur.pack(anchor="w", padx=18, pady=(0, 8))
        self.field(c, "Text size")
        self.size = seg(c, list(self.SIZES))
        self.size.pack(anchor="w", padx=18, pady=(0, 8))
        self.kb = ctk.CTkSwitch(c, text="Show on-screen keyboard", progress_color=T.accent, font=(T.FONT, 13))
        self.kb.pack(anchor="w", padx=18, pady=(8, 16))
        row = ctk.CTkFrame(self.body, fg_color="transparent")
        row.pack(fill="x", padx=6, pady=4)
        button(row, "Save Settings", self.save, width=160).pack(side="left")
        button(row, "Clear All History", self.clear, "danger", width=160).pack(side="left", padx=10)
        self.msg = label(row, "", 13)
        self.msg.pack(side="left", padx=10)

    def section(self, title):
        c = card(self.body)
        c.pack(fill="x", padx=6, pady=(0, 12))
        label(c, title, 16, True).pack(anchor="w", padx=18, pady=(16, 4))
        return c

    def field(self, c, text):
        label(c, text, 12, color=T.MUTED).pack(anchor="w", padx=18, pady=(8, 4))

    def refresh(self):
        g = self.db.get_setting
        self.name.delete(0, "end")
        self.name.insert(0, g("name"))
        self.theme.set(g("theme"))
        self.accent.set(g("accent") if g("accent") in T.ACCENTS else "Lilac")
        self.diff.set(g("difficulty"))
        self.dur.delete(0, "end")
        self.dur.insert(0, g("duration"))
        self.size.set(next((k for k, v in self.SIZES.items() if v == g("font_size")), "Medium"))
        self.kb.select() if g("keyboard") == "1" else self.kb.deselect()
        self.msg.configure(text="")

    def save(self):
        try:
            d = int(self.dur.get())
            if not 10 <= d <= 300:
                raise ValueError
        except ValueError:
            self.msg.configure(text="Duration must be a whole number from 10 to 300.", text_color=T.BAD)
            return
        g = self.db.get_setting
        look_changed = (self.theme.get(), self.accent.get()) != (g("theme"), g("accent"))
        for k, v in {"name": self.name.get().strip()[:30] or "Typist", "theme": self.theme.get(),
                     "accent": self.accent.get(), "difficulty": self.diff.get(), "duration": d,
                     "font_size": self.SIZES[self.size.get()], "keyboard": "1" if self.kb.get() else "0"}.items():
            self.db.set_setting(k, v)
        self.app.pages["Typing Test"].tracker = None          # new typing settings apply to the next test
        if look_changed:
            self.app.build("Settings")                        # rebuild so theme and accent apply everywhere
            self.app.pages["Settings"].msg.configure(text="Settings saved.", text_color=T.GOOD)
        else:
            self.msg.configure(text="Settings saved.", text_color=T.GOOD)

    def clear(self):
        if mb.askyesno("Clear history", "Delete ALL saved typing sessions? This cannot be undone."):
            self.db.clear()
            self.app.update_footer()
            self.msg.configure(text="History cleared.", text_color=T.GOOD)