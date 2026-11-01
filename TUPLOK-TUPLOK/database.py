import sqlite3
from datetime import datetime

DEFAULTS = {"name": "Typist", "theme": "Light", "accent": "Lilac", "duration": "60",
            "difficulty": "Medium", "font_size": "22", "keyboard": "1"}


class Database:
    def __init__(self, path="tuplok.db"):
        self.conn = sqlite3.connect(path)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS sessions(
                id INTEGER PRIMARY KEY AUTOINCREMENT, date TEXT, difficulty TEXT,
                duration INTEGER, wpm REAL, accuracy REAL, errors INTEGER,
                corrections INTEGER, avg_interval REAL, pauses INTEGER,
                consistency REAL, chars INTEGER);
            CREATE TABLE IF NOT EXISTS mistakes(
                session_id INTEGER, expected TEXT, count INTEGER);
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT);
        """)

    def add_session(self, r, mistakes):
        cur = self.conn.execute(
            "INSERT INTO sessions(date,difficulty,duration,wpm,accuracy,errors,corrections,"
            "avg_interval,pauses,consistency,chars) VALUES(?,?,?,?,?,?,?,?,?,?,?)",
            (datetime.now().strftime("%Y-%m-%d %H:%M"), r["difficulty"], r["duration"],
             r["wpm"], r["accuracy"], r["errors"], r["corrections"],
             r["avg_interval"], r["pauses"], r["consistency"], r["chars"]))
        self.conn.executemany("INSERT INTO mistakes VALUES(?,?,?)",
                              [(cur.lastrowid, ch, n) for ch, n in mistakes.items()])
        self.conn.commit()

    def sessions(self):
        """Return saved sessions."""
        return [dict(r) for r in self.conn.execute("SELECT * FROM sessions ORDER BY id")]

    def mistakes(self, limit=10):
        rows = self.conn.execute(
            "SELECT expected, SUM(count) n FROM mistakes GROUP BY expected "
            "ORDER BY n DESC LIMIT ?", (limit,))
        return [(r["expected"], r["n"]) for r in rows]

    def delete_session(self, session_id):
        self.conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
        self.conn.execute("DELETE FROM mistakes WHERE session_id=?", (session_id,))
        self.conn.commit()

    def clear(self):
        self.conn.executescript("DELETE FROM sessions; DELETE FROM mistakes;")

    def get_setting(self, key):
        row = self.conn.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row["value"] if row else DEFAULTS[key]

    def set_setting(self, key, value):
        self.conn.execute("INSERT OR REPLACE INTO settings VALUES(?,?)", (key, str(value)))
        self.conn.commit()
