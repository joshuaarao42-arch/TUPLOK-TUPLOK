# Contributing to Tuplok-Tuplok

Tuplok-Tuplok is a desktop typing trainer that analyzes speed, accuracy, rhythm, hesitation, and typing behavior.

## Clone
```bash
git clone https://github.com/joshuaarao42-arch/TUPLOK-TUPLOK.git
cd TUPLOK-TUPLOK
```
Install the dependencies and run the entry point documented in the README.

## Project-specific contributions
- Typing passages, difficulty levels, timers, and live character feedback.
- Keystroke timing and session recording.
- WPM, accuracy, consistency, hesitation, and corrected-error calculations.
- Typing Fingerprint classifications and coaching tips.
- SQLite history, charts, and dashboard summaries.

## Measurement integrity
Test metrics against small, manually checked typing samples. Explain how incorrect, corrected, and skipped characters affect calculations. Handle very short sessions and zero-duration cases. Ensure coaching descriptions match the actual measured signals. Do not transmit typed content outside the local app without an explicit project decision; never commit real session databases.

Use branches such as `feature/typing-metric` or `fix/wpm-calculation`. Include sample keystroke sequences and expected results for algorithm changes.
