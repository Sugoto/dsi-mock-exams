# DSI practice questions

Practice questions for CS 6422 (Database System Implementation), split into three sets:

- **Modules · True/False** (100): Modules 1–8, mixed topics
- **Numeric** (50): exact whole-number answers, grouped by topic
- **Papers · True/False** (50): Codd 1970, Stonebraker 1981, Stonebraker & Pavlo 2024 and Umbra 2020, grouped by paper

Open `index.html` locally or use the GitHub Pages site. Each answer is graded as soon as you give it, with an explanation. Answers are saved in your browser's localStorage.

## Regenerating the questions

Questions live in `tools/build.py`. The numeric answer keys are computed by the simulators in `tools/sim.py` (LRU, 2Q, probing with tombstones, free lists, lock conflicts, join counts). `sim.py` asserts that those simulators reproduce the answers from the course practice sheet.

```bash
python3 tools/build.py
```

This rewrites `data/sets.js` and checks set sizes, True/False balance, and that no question text repeats.

These are original practice questions, not official course material.
