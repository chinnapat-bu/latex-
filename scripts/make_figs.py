"""Draw the Elo, xG and fatigue figures (chapter 2) and the learning curve (chapter 4).

Usage: python scripts/make_figs.py ../money-printer-research theme/fonts images
Reads, in money-printer-research: data/clean/{elo,fatigue,schedule}.csv,
data/predictions/backtest.csv and data/report/learning_curve.html (uv run clean_data,
backtest and learning_curve). The xG shot map reads scripts/data/understat_shots_26726.json,
Understat's shots for Liverpool 2-0 Manchester City on 2024-12-01
(https://understat.com/getMatchData/26726). Needs matplotlib and polars.
"""
import json
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
import polars as pl

research, fonts, out = (Path(a) for a in sys.argv[1:4])
clean, predictions = research / "data/clean", research / "data/predictions"
for f in fonts.glob("Sarabun-*.ttf"):
    font_manager.fontManager.addfont(str(f))
plt.rcParams.update({"font.family": "TH Sarabun New", "font.size": 17, "axes.spines.top": False,
                     "axes.spines.right": False, "figure.dpi": 200})

# --- Elo over time ---
elo = pl.read_csv(clean / "elo.csv", try_parse_dates=True)
teams = {"manchester city": "Manchester City", "liverpool": "Liverpool",
         "arsenal": "Arsenal", "leicester city": "Leicester City"}
long = pl.concat([
    elo.select(pl.col("match_date"), pl.col("home_team").alias("team"), pl.col("elo_home").alias("elo")),
    elo.select(pl.col("match_date"), pl.col("away_team").alias("team"), pl.col("elo_away").alias("elo")),
]).sort("match_date")
fig, ax = plt.subplots(figsize=(10, 4.8))
for key, name in teams.items():
    t = long.filter(pl.col("team") == key).with_columns(
        (pl.col("match_date").diff().dt.total_days() > 200).fill_null(False).cum_sum().alias("spell"))
    color = None
    for _, part in t.group_by("spell", maintain_order=True):  # no line across seasons outside the five leagues
        (line,) = ax.plot(part["match_date"], part["elo"], lw=1.6, color=color,
                          label=name if color is None else None)
        color = line.get_color()
ax.axhline(1500, color="grey", lw=0.8, ls="--")
lei = long.filter((pl.col("team") == "leicester city") & (pl.col("match_date").dt.year() == 2016)
                  & (pl.col("match_date").dt.month() == 5))
if lei.height:
    x, y = lei["match_date"][-1], lei["elo"][-1]
    ax.annotate("เลสเตอร์ฯ แชมป์ 2015–16", (x, y), xytext=(x, y + 120),
                arrowprops={"arrowstyle": "->", "color": "grey"}, ha="center", fontsize=15)
ax.set_ylabel("คะแนน Elo ก่อนแข่ง")
ax.set_xlabel("วันที่แข่งขัน")
ax.legend(frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, -0.22), fontsize=15)
fig.tight_layout()
fig.savefig(out / "elo_history.png")

# --- Fatigue and schedule for one team-season ---
b = pl.read_csv(predictions / "backtest.csv", try_parse_dates=True)
f = pl.read_csv(clean / "fatigue.csv")
s = pl.read_csv(clean / "schedule.csv")
j = b.join(f, on="game_id").join(s, on="game_id")
team, season = "liverpool", 2018
g = j.filter((pl.col("season_start") == season)
             & ((pl.col("home_team") == team) | (pl.col("away_team") == team)))
home = pl.col("home_team") == team
g = g.with_columns(
    pl.when(home).then(pl.col("h_fatigue")).otherwise(pl.col("a_fatigue")).alias("fatigue"),
    pl.when(home).then(pl.col("h_games_14d_all")).otherwise(pl.col("a_games_14d_all")).alias("g14"),
).sort("date")
fig, ax = plt.subplots(figsize=(10, 4.2))
ax2 = ax.twinx()
ax2.bar(g["date"], g["g14"], width=2.5, color="#cfd8e3", label="จำนวนนัดทุกรายการใน 14 วัน")
ax2.set_ylabel("จำนวนนัดใน 14 วัน")
ax2.set_ylim(0, 8)
ax2.spines["top"].set_visible(False)
ax.set_zorder(ax2.get_zorder() + 1)
ax.patch.set_visible(False)
ax.plot(g["date"], g["fatigue"], marker="o", ms=4, color="#d1495b", lw=1.6,
        label="ดัชนีความเหนื่อยล้าเฉลี่ยของ 11 ตัวจริง")
ax.set_ylabel("ดัชนีความเหนื่อยล้า (0–100)")
ax.set_ylim(0, 100)
ax.set_xlabel("วันที่แข่งขันในลีก")
h1, l1 = ax.get_legend_handles_labels()
h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, frameon=False, loc="upper left", fontsize=15)
fig.tight_layout()
fig.savefig(out / "fatigue_season.png")
print(g.height, "league games;", g["fatigue"].min(), g["fatigue"].max(), g["g14"].max())

# --- Learning curve, from the table and reference lines of learning_curve.html ---
html = (research / "data/report/learning_curve.html").read_text(encoding="utf-8")
cell = r"<td(?: class=num)?>([^<]*)</td>"
rows = re.findall(r"<tr>" + cell * 6 + r"</tr>", html)
fits = pl.DataFrame(
    [(m, int(n.replace(",", "")), float(test)) for m, n, _, _, test, _ in rows],
    schema=["model", "games", "test_log_loss"], orient="row",
)
prior = float(re.search(r"outcome shares only</tspan>.*?</tspan> ([0-9.]+)", html).group(1))
market = float(re.search(r"bookmaker</tspan>.*?</tspan> ([0-9.]+)", html).group(1))
names = {"logistic": ("Logistic Regression", "#2a78d6"), "logistic + sigmoid": ("Logistic + Sigmoid", "#eb6834"),
         "boosted trees": ("Boosted Trees", "#1baf7a"), "poisson goals": ("Poisson Goals", "#eda100")}
fig, ax = plt.subplots(figsize=(7.2, 4.4))
for key, (label, color) in names.items():
    f = fits.filter(pl.col("model") == key).sort("games")
    ax.plot(f["games"], f["test_log_loss"], marker="o", ms=4, lw=1.8, color=color, label=label)
ax.axhline(prior, color="grey", ls=":", lw=1.5)
ax.axhline(market, color="black", ls="--", lw=1.2)
ax.text(300, prior + 0.002, f"ทายจากสัดส่วนผลอย่างเดียว {prior:.4f}", color="dimgrey", fontsize=13)
ax.text(300, market - 0.007, f"ราคาเจ้ามือ {market:.4f}", fontsize=13)
ax.set_xscale("log")
ticks = [250, 500, 1000, 2000, 4000, 8000, 16000]
ax.set_xticks(ticks, [f"{t:,}" for t in ticks])
ax.set_ylim(market - 0.012, 1.12)
ax.grid(axis="y", color="#e6e6e6")
ax.set_xlabel("จำนวนนัดที่ใช้ฝึกแบบจำลอง (สเกลลอการิทึม)")
ax.set_ylabel("Log Loss บนชุดทดสอบ (ต่ำกว่าดีกว่า)")
ax.legend(frameon=False, loc="center right", bbox_to_anchor=(1, 0.45), fontsize=14)
fig.tight_layout()
fig.savefig(out / "learning_curve.png")

# --- xG shot map of one match, from Understat's shot data ---
match = json.loads((Path(__file__).parent / "data/understat_shots_26726.json").read_text())
L, W = 105, 68  # pitch in metres; Understat gives X along the pitch and Y across, both 0-1
fig, ax = plt.subplots(figsize=(9, 6.3))
pitch = {"color": "#9aa5b1", "lw": 1.2, "zorder": 0}
ax.plot([0, L, L, 0, 0], [0, 0, W, W, 0], **pitch)
ax.plot([L / 2, L / 2], [0, W], **pitch)
ax.add_patch(plt.Circle((L / 2, W / 2), 9.15, fill=False, **pitch))
for x0, d in ((0, 1), (L, -1)):
    for depth, width in ((16.5, 40.32), (5.5, 18.32)):
        ax.plot([x0, x0 + d * depth, x0 + d * depth, x0],
                [W / 2 - width / 2, W / 2 - width / 2, W / 2 + width / 2, W / 2 + width / 2], **pitch)
    ax.plot([x0, x0], [W / 2 - 3.66, W / 2 + 3.66], color="#52514e", lw=3, zorder=0)
sides = {"h": ("#c8102e", 1), "a": ("#6cabdd", -1)}  # home attacks right, away left
for side, (color, d) in sides.items():
    for shot in match["shots"][side]:
        x, y, xg = float(shot["X"]), float(shot["Y"]), float(shot["xG"])
        px = L * x if d == 1 else L * (1 - x)
        py = W * (1 - y) if d == 1 else W * y
        goal = shot["result"] == "Goal"
        ax.scatter(px, py, s=40 + 900 * xg, color=color if goal else "none", edgecolor=color,
                   lw=1.8, alpha=0.9, zorder=3)
        if goal or xg > 0.4:
            ax.annotate(f"{xg:.2f}", (px, py), xytext=(0, -14 - 12 * xg ** 0.5),
                        textcoords="offset points", ha="center", fontsize=12, zorder=4)
h, a = match["shots"]["h"], match["shots"]["a"]
total = {k: sum(float(s["xG"]) for s in v) for k, v in (("h", h), ("a", a))}
ax.text(L * 0.75, W + 3, f"Liverpool 2 (xG {total['h']:.2f}, {len(h)} ครั้ง)",
        ha="center", color=sides["h"][0], fontsize=15)
ax.text(L * 0.25, W + 3, f"Manchester City 0 (xG {total['a']:.2f}, {len(a)} ครั้ง)",
        ha="center", color="#3d7fb3", fontsize=15)
for xg in (0.05, 0.2, 0.5):
    ax.scatter([], [], s=40 + 900 * xg, color="none", edgecolor="grey", label=f"xG {xg}")
ax.scatter([], [], s=150, color="grey", label="เป็นประตู (วงทึบ)")
ax.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.5, -0.01), ncol=4,
          fontsize=13, scatterpoints=1, handletextpad=0.4, columnspacing=1.6)
ax.set_xlim(-2, L + 2)
ax.set_ylim(-2, W + 7)
ax.set_aspect("equal")
ax.axis("off")
fig.tight_layout()
fig.savefig(out / "xg_shot_map.png")
