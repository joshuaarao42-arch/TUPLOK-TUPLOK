import random
import statistics
import time

DIFFICULTIES = ["Easy", "Medium", "Hard"]
DIFFS = DIFFICULTIES + ["Drill"]   # "Drill" = practice on weak keys

PASSAGES = {
    "Easy": [
        "the sun is up and the dog runs in the park with a red ball",
        "we sit by the sea and eat rice and fish for lunch today",
        "my cat likes to nap on the warm bed all day long",
    ],
    "Medium": [
        "Learning to type quickly takes patience, because steady practice builds muscle memory over time.",
        "A good programmer reads error messages carefully and fixes problems one small step at a time.",
        "Rain fell softly on the roof while the students finished their projects before the deadline.",
    ],
    "Hard": [
        "In 2024, the team's system processed 1,250 requests/second; however, latency spiked (briefly) at 3:45 PM.",
        "\"Debugging,\" she said, \"is twice as hard as writing code; so don't write clever code!\" - Brian K.",
        "SELECT name, COUNT(*) FROM users WHERE age >= 18 GROUP BY name; -- returns 42 rows in 0.07s.",
    ],
}


def build_text(difficulty, duration):
    """Join random passages until there is enough text for the chosen duration."""
    text = random.choice(PASSAGES[difficulty])
    while len(text) < duration * 6:
        text += " " + random.choice(PASSAGES[difficulty])
    return text


def char_name(c):
    return "space" if c == " " else c


class TypingTracker:
    """Records every keystroke of one test."""
    PAUSE = 1.0  # a gap longer than this many seconds counts as a hesitation

    def __init__(self, target):
        self.target = target
        self.typed = ""
        self.start = None
        self.last = None
        self.intervals = []
        self.mistakes = {}      
        self.keys = 0           
        self.errors = 0         
        self.corrections = 0    
        self.pauses = 0

    def press(self, ch):
        now = time.time()
        if self.start is None:
            self.start = now
        if self.last is not None:
            gap = now - self.last
            self.intervals.append(gap)
            if gap > self.PAUSE:
                self.pauses += 1
        self.last = now
        expected = self.target[len(self.typed)]
        self.keys += 1
        if ch != expected:
            self.errors += 1
            self.mistakes[expected] = self.mistakes.get(expected, 0) + 1
        self.typed += ch

    def backspace(self):
        if self.typed:
            i = len(self.typed) - 1
            if self.typed[i] != self.target[i]:
                self.corrections += 1
            self.typed = self.typed[:-1]
            self.last = time.time()

    def finished(self):
        return len(self.typed) >= len(self.target)

    def wpm(self, elapsed):
        correct = sum(a == b for a, b in zip(self.typed, self.target))
        return (correct / 5) / (max(elapsed, 1) / 60)   # standard: 5 chars = 1 word

    def results(self, elapsed):
        accuracy = 100 * (self.keys - self.errors) / self.keys if self.keys else 0
        mean = statistics.mean(self.intervals) if self.intervals else 0
        cv = statistics.pstdev(self.intervals) / mean if mean else 1
        return {"wpm": self.wpm(elapsed), "accuracy": accuracy, "errors": self.errors,
                "corrections": self.corrections, "avg_interval": mean * 1000,
                "pauses": self.pauses, "chars": self.keys,
                "consistency": max(0, min(100, 100 - 50 * cv))}  # steadier rhythm = higher


def avg(rows, key):
    return sum(r[key] for r in rows) / len(rows) if rows else 0


def fingerprint(sessions, mistakes):
    """Summarize the user's typing behavior; returns None if there is no data."""
    if not sessions:
        return None
    f = {"top": mistakes[:5], "wpm": avg(sessions, "wpm"), "interval": avg(sessions, "avg_interval"),
         "consistency": avg(sessions, "consistency"), "accuracy": avg(sessions, "accuracy"),
         "corrections": sum(s["corrections"] for s in sessions),
         "hesitation": 100 * sum(s["pauses"] for s in sessions) / max(1, sum(s["chars"] for s in sessions))}
    if f["accuracy"] < 90:
        f["profile"] = "Fast but Error-Prone" if f["interval"] < 200 else "Struggling Starter"
    elif f["hesitation"] > 3:
        f["profile"] = "Careful Thinker"
    elif f["consistency"] < 40:
        f["profile"] = "Burst Typer"
    elif f["interval"] < 150:
        f["profile"] = "Steady Sprinter"
    else:
        f["profile"] = "Balanced Typist"
    return f


PROFILES = {
    "Fast but Error-Prone": "You type quickly but make many mistakes. Slowing down a little will raise your real speed.",
    "Struggling Starter": "Your keystrokes are slow and often wrong. Focus on the home row and accuracy first.",
    "Careful Thinker": "You pause often, as if checking each word. Reading ahead will smooth your flow.",
    "Burst Typer": "You type in quick bursts followed by slow spots. Aim for an even, steady rhythm.",
    "Steady Sprinter": "Fast, even keystrokes with few errors. This is a strong, efficient typing style.",
    "Balanced Typist": "Speed, accuracy and rhythm are well balanced. Keep practicing to push all three up.",
}

WORDS = ("quick brown fox jumps over lazy dog keyboard practice finger rhythm speed accuracy typing random "
         "letters pattern balance steady smooth focus window yellow zebra quiet wizard jazz extra expert fix "
         "vex quartz puzzle maximum project system python screen number winter garden market bridge flower "
         "memory mountain pocket reason simple travel village").split()


def clamp(v):
    return max(0, min(100, v))


def radar_scores(f):
    """Five 0-100 scores for the fingerprint radar chart."""
    return {"Speed": clamp(f["wpm"] / 80 * 100), "Accuracy": clamp(f["accuracy"]),
            "Consistency": clamp(f["consistency"]), "Fluency": clamp(100 - f["hesitation"] * 12),
            "Rhythm": clamp(130 - f["interval"] / 3)}


def streak(sessions):
    """Number of consecutive days (ending today or yesterday) with at least one test."""
    from datetime import date, timedelta
    days = {s["date"][:10] for s in sessions}
    d, n = date.today(), 0
    if d.isoformat() not in days:
        d -= timedelta(days=1)
    while d.isoformat() in days:
        n += 1
        d -= timedelta(days=1)
    return n


def today_count(sessions):
    from datetime import date
    return sum(s["date"].startswith(date.today().isoformat()) for s in sessions)


def moving_average(values, n=3):
    return [sum(values[max(0, i - n + 1):i + 1]) / len(values[max(0, i - n + 1):i + 1]) for i in range(len(values))]


def drill_text(chars, length=300):
    """Practice text built from words that contain the user's weakest keys."""
    chars = [c.lower() for c in chars if c.strip()] or list("etaoin")
    pool = [w for w in WORDS if any(c in w for c in chars)]
    if len(pool) < 8:
        pool += ["".join(random.choice(chars + list("aeiou")) for _ in range(random.randint(3, 5))) for _ in range(12)]
    text = random.choice(pool)
    while len(text) < length:
        text += " " + random.choice(pool)
    return text


def recommendations(sessions, mistakes):
    """Returns a list of (kind, title, text). kind is 'good', 'warn' or 'tip'."""
    if not sessions:
        return [("tip", "Take your first test", "Complete a few typing tests and personalized advice will appear here.")]
    f, tips = fingerprint(sessions, mistakes), []
    if f["accuracy"] < 90:
        tips.append(("warn", "Accuracy needs work", f"Your accuracy is {f['accuracy']:.1f}%. Slow down until you reach 95% - speed follows accuracy."))
    elif f["accuracy"] >= 97:
        tips.append(("good", "Excellent accuracy", f"{f['accuracy']:.1f}% accuracy is great. You can safely push your speed now."))
    if f["top"]:
        chars = ", ".join(f"'{char_name(c)}'" for c, _ in f["top"][:3])
        tips.append(("warn", "Weak keys detected", f"Your most mistyped keys are {chars}. Use the practice drill to train them."))
    if f["interval"] > 250:
        tips.append(("tip", "Speed up your keystrokes", f"Your average gap between keys is {f['interval']:.0f} ms. Home-row drills will tighten it."))
    if f["hesitation"] > 3:
        tips.append(("warn", "Frequent hesitation", "You pause often. Try reading a few words ahead of what you are typing."))
    if f["consistency"] < 40:
        tips.append(("warn", "Uneven rhythm", "Your keystroke timing varies a lot. Type at a steady pace, even if it feels slow."))
    elif f["consistency"] >= 70:
        tips.append(("good", "Steady rhythm", f"Consistency of {f['consistency']:.0f}% shows a smooth, even typing rhythm."))
    if f["wpm"] < 30:
        tips.append(("tip", "Build the basics", "Under 30 WPM: keep your fingers on the home row and avoid looking at the keyboard."))
    if f["wpm"] > 50 and f["accuracy"] > 95 and sessions[-1]["difficulty"] != "Hard":
        tips.append(("good", "Ready for a challenge", "Your speed and accuracy are strong. Try the Hard difficulty."))
    if len(sessions) >= 6:
        recent, before = avg(sessions[-3:], "wpm"), avg(sessions[:-3][-3:], "wpm")
        if recent > before:
            tips.append(("good", "You are improving", f"Recent average {recent:.1f} WPM vs {before:.1f} WPM before."))
        else:
            tips.append(("tip", "Progress has stalled", "Short daily sessions work better than long ones. Try 10 minutes a day."))
    return tips or [("good", "Well balanced", "Your results look balanced. Keep practicing regularly!")]
