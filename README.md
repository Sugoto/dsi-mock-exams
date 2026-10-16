# DSI mock exams

Five practice exams for CS 6422 (Database System Implementation), in the final-exam format:

- 35 graded questions worth 50 points, followed by a zero-point Yes/No scratch-paper acknowledgement
- Questions 1–20: True/False on Modules 1–8 (1 point each)
- Questions 21–30: numeric answers (21–25 are 2 points, 26–30 are 3 points)
- Questions 31–35: True/False on Papers 1–4 (1 point each)

Open `index.html` locally or use the GitHub Pages site. Every answer is graded immediately; finishing shows the total score out of 50 and missed topics. Progress is saved in your browser's localStorage.

## Regenerating the questions

Questions live in `tools/build.py`. The numeric answer keys are computed by the simulators in `tools/sim.py` (LRU, 2Q, probing with tombstones, free lists, lock conflicts, join counts). `sim.py` asserts that those simulators reproduce the answers from the course practice sheet.

```bash
python3 tools/build.py
```

This rewrites `data/exams.js` and checks each exam's question counts, point total, True/False balance, and that no question text repeats.

These are original practice questions, not official course material.
