#!/usr/bin/env python3
"""Create the files the demo scenarios need (safe to run again).

    python3 demo/setup_demo.py            # scenario A: demo/renders_old/ with 5 dummy files
    python3 demo/setup_demo.py --typo     # scenario C: also a demo/titles.csv with 1 typo + 5 hidden problems
"""
import os
import sys

DEMO = os.path.dirname(os.path.abspath(__file__))

# Same seed as the 2026-10-21 measurement (scenario C). Row 3 has the typo the user asks about;
# rows 4, 5, 8 and the missing 10th row break specs/titles_spec.json — nobody mentions them.
SEED = """no,title
1,밤 11시 엘리베이터가 층마다 서는 이유
2,엘리베이터가 3층마다 멈추는 진짜 이유
3,새벽 2시 엘레베이터 버튼의 비밀
4,무조건 알아야 할 엘리베이터 야간 모드 5가지 원리 총정리
5,엘리베이터가 밤에 느려지는 이유
6,아파트 엘리베이터 야간 운행 7가지 규칙
7,엘리베이터 1대가 층마다 서는 원리
8,충격 엘리베이터 밤 12시의 비밀
9,관리비 30% 줄이는 엘리베이터 설정
"""

old = os.path.join(DEMO, "renders_old")
os.makedirs(old, exist_ok=True)
for i in range(1, 6):
    p = os.path.join(old, f"draft_{i:02d}.mp4.txt")
    if not os.path.exists(p):
        with open(p, "w") as f:
            f.write(f"dummy render {i}\n")
print(f"demo/renders_old/: {len(os.listdir(old))} files")

if "--typo" in sys.argv:
    titles = os.path.join(DEMO, "titles.csv")
    if os.path.exists(titles):
        print("demo/titles.csv already exists — move it to _archive/ first if you want a fresh seed")
    else:
        with open(titles, "w", encoding="utf-8") as f:
            f.write(SEED)
        print("demo/titles.csv: 9 rows (1 typo + 5 problems the spec will catch)")
