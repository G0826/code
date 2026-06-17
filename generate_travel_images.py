"""Generate static travel visualization images on the city base map."""
import json
from collections import Counter, defaultdict
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from matplotlib.patches import FancyBboxPatch
from PIL import Image
import numpy as np

BASE = Path(__file__).parent
MAP_PATH = BASE / "debug_vector_buildings_points.png"
DATA_PATH = BASE / "animation_data.json"
OUT_DIR = BASE / "travel_images"
MAP_W, MAP_H = 1514, 1570

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

PURPOSE_CN = {
    "Work/Home Commute": "通勤上班",
    "Eating": "外出用餐",
    "Recreation (Social Gathering)": "社交娱乐",
    "Coming Back From Restaurant": "用餐返回",
    "Going Back to Home": "回家",
}
PURPOSE_COLORS = {
    "Work/Home Commute": "#FF6B6B",
    "Eating": "#4ECDC4",
    "Recreation (Social Gathering)": "#FFE66D",
    "Coming Back From Restaurant": "#FF9F4A",
    "Going Back to Home": "#9B5DE5",
}
RESIDENT_STYLE = {
    "35": {"color": "#1565C0", "name": "居民 35", "ls": "-", "lw": 3.2, "marker": "o"},
    "195": {"color": "#C62828", "name": "居民 195", "ls": "-", "lw": 3.2, "marker": "s"},
}


def load_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def load_bg():
    return np.array(Image.open(MAP_PATH))


def setup_ax(figsize=(14, 10)):
    fig, ax = plt.subplots(figsize=figsize, dpi=150)
    ax.imshow(load_bg(), extent=[0, MAP_W, MAP_H, 0], aspect="auto")
    ax.set_xlim(0, MAP_W)
    ax.set_ylim(MAP_H, 0)
    ax.axis("off")
    return fig, ax


def draw_trip(ax, trip, color, ls="-", lw=2.5, alpha=0.85, label_mid=True, trip_num=None):
    x1, y1, x2, y2 = trip["startPx"], trip["startPy"], trip["endPx"], trip["endPy"]
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-|>", color=color, lw=lw, ls=ls, alpha=alpha,
                        mutation_scale=14, shrinkA=2, shrinkB=2),
    )
    if trip_num is not None:
        ax.text(x1, y1 - 12, str(trip_num), fontsize=7, color="white", ha="center",
                bbox=dict(boxstyle="circle,pad=0.2", fc=color, ec="white", lw=0.8))
    if label_mid:
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        txt = PURPOSE_CN.get(trip["purpose"], trip["purpose"][:4])
        ax.text(mx, my, txt, fontsize=6.5, ha="center", va="center", color="#222",
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=color, lw=1, alpha=0.92))


def key_locations(trips):
    """Home = most frequent apartment start; work = most frequent employer end for commute."""
    starts = Counter()
    work_ends = Counter()
    for t in trips:
        if t["startType"] == "Apartment":
            starts[(t["startPx"], t["startPy"])] += 1
        if t["purpose"] == "Work/Home Commute" and t["endType"] == "Employer":
            work_ends[(t["endPx"], t["endPy"])] += 1
    home = starts.most_common(1)[0][0] if starts else None
    work = work_ends.most_common(1)[0][0] if work_ends else None
    return home, work


def stats_for_day(trips, date):
    day = [t for t in trips if t["date"] == date]
    purposes = Counter(PURPOSE_CN.get(t["purpose"], t["purpose"]) for t in day)
    total_min = sum(t["durationMs"] for t in day) / 60000
    hours = sorted(set(t["hour"] for t in day))
    return day, purposes, total_min, hours


def image_combined_one_day(data, date="2022-03-01"):
    fig, ax = setup_ax(figsize=(16, 11))
    fig.suptitle(f"双居民出行轨迹对比 · {date}", fontsize=16, fontweight="bold", y=0.98)

    legend_handles = []
    stats_lines = []

    for pid in ["35", "195"]:
        style = RESIDENT_STYLE[pid]
        trips = data["participants"][pid]["trips"]
        day, purposes, total_min, hours = stats_for_day(trips, date)
        home, work = key_locations(trips)

        for i, t in enumerate(day, 1):
            draw_trip(ax, t, style["color"], ls=style["ls"], lw=style["lw"],
                      trip_num=i, label_mid=True)

        if home:
            ax.scatter(*home, s=180, c=style["color"], marker="*", edgecolors="white",
                       linewidths=1.5, zorder=10)
            ax.text(home[0], home[1] - 28, f"{style['name']}\n[家]", fontsize=8,
                    ha="center", color=style["color"], fontweight="bold",
                    bbox=dict(boxstyle="round,pad=0.3", fc="white", alpha=0.9))
        if work:
            ax.scatter(*work, s=120, c=style["color"], marker="D", edgecolors="white",
                       linewidths=1.2, zorder=10)
            ax.text(work[0], work[1] + 22, "[工作]", fontsize=7, ha="center",
                    color=style["color"], bbox=dict(boxstyle="round,pad=0.2", fc="white", alpha=0.85))

        purpose_str = " · ".join(f"{k}×{v}" for k, v in purposes.most_common())
        stats_lines.append(
            f"{style['name']}: {len(day)}段 · 出行{total_min:.0f}分钟 · {purpose_str}"
        )
        legend_handles.append(
            Line2D([0], [0], color=style["color"], lw=style["lw"], label=style["name"])
        )

    # 目的图例
    for purpose, cn in PURPOSE_CN.items():
        legend_handles.append(
            mpatches.Patch(color=PURPOSE_COLORS[purpose], label=cn, alpha=0.8)
        )

    ax.legend(handles=legend_handles, loc="lower left", fontsize=8, framealpha=0.95,
              title="图例", title_fontsize=9, ncol=2)

    stats_text = "\n".join(stats_lines)
    ax.text(0.99, 0.02, stats_text, transform=ax.transAxes, fontsize=8,
            va="bottom", ha="right", color="#222",
            bbox=dict(boxstyle="round,pad=0.5", fc="#f8f8f8", ec="#888", alpha=0.95))

    out = OUT_DIR / f"01_双居民单日对比_{date}.png"
    fig.savefig(out, bbox_inches="tight", facecolor="white", pad_inches=0.15)
    plt.close(fig)
    return out


def image_timeline_panel(data, date="2022-03-01"):
    """Map + timeline strip below showing hourly activity."""
    fig = plt.figure(figsize=(16, 13), dpi=150)
    gs = fig.add_gridspec(2, 1, height_ratios=[5, 1.2], hspace=0.08)
    ax_map = fig.add_subplot(gs[0])
    ax_time = fig.add_subplot(gs[1])

    ax_map.imshow(load_bg(), extent=[0, MAP_W, MAP_H, 0], aspect="auto")
    ax_map.set_xlim(0, MAP_W)
    ax_map.set_ylim(MAP_H, 0)
    ax_map.axis("off")
    ax_map.set_title(f"出行时间轴与空间轨迹 · {date}", fontsize=15, fontweight="bold", pad=10)

    for pid in ["35", "195"]:
        style = RESIDENT_STYLE[pid]
        day = [t for t in data["participants"][pid]["trips"] if t["date"] == date]
        for t in day:
            draw_trip(ax_map, t, style["color"], lw=2.8, label_mid=False)
        home, _ = key_locations(data["participants"][pid]["trips"])
        if home:
            ax_map.scatter(*home, s=150, c=style["color"], marker="*", edgecolors="white", zorder=10)

    # Timeline
    ax_time.set_xlim(0, 24)
    ax_time.set_ylim(-0.5, 2.5)
    ax_time.set_xlabel("时刻 (小时)", fontsize=10)
    ax_time.set_yticks([0, 1])
    ax_time.set_yticklabels(["居民 35", "居民 195"], fontsize=10)
    ax_time.grid(axis="x", alpha=0.3)
    ax_time.set_xticks(range(0, 25, 2))

    purpose_colors = PURPOSE_COLORS
    for row, pid in enumerate(["35", "195"]):
        day = [t for t in data["participants"][pid]["trips"] if t["date"] == date]
        for t in day:
            h0 = t["hour"] + int(t["startTime"][14:16]) / 60
            h1 = int(t["endTime"][11:13]) + int(t["endTime"][14:16]) / 60
            if h1 < h0:
                h1 += 24
            c = purpose_colors.get(t["purpose"], "#999")
            ax_time.barh(row, max(h1 - h0, 0.08), left=h0, height=0.55,
                         color=c, alpha=0.85, edgecolor="white", linewidth=0.5)
            cn = PURPOSE_CN.get(t["purpose"], "")[:2]
            if h1 - h0 > 0.3:
                ax_time.text((h0 + h1) / 2, row, cn, ha="center", va="center",
                             fontsize=6, color="#333")

    # purpose legend on timeline
    patches = [mpatches.Patch(color=c, label=PURPOSE_CN[p]) for p, c in PURPOSE_COLORS.items()]
    ax_time.legend(handles=patches, loc="upper right", fontsize=7, ncol=5, framealpha=0.9)

    out = OUT_DIR / f"02_时间轴与轨迹_{date}.png"
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def image_full_overview(data):
    """All trips density + major routes on one map with info panel."""
    fig = plt.figure(figsize=(18, 12), dpi=150)
    gs = fig.add_gridspec(1, 5, wspace=0.02)
    ax_map = fig.add_subplot(gs[0, :4])
    ax_info = fig.add_subplot(gs[0, 4])
    ax_info.axis("off")

    ax_map.imshow(load_bg(), extent=[0, MAP_W, MAP_H, 0], aspect="auto")
    ax_map.set_xlim(0, MAP_W)
    ax_map.set_ylim(MAP_H, 0)
    ax_map.axis("off")
    ax_map.set_title("双居民全周期出行总览（按出行目的着色）", fontsize=15, fontweight="bold")

    info_blocks = []

    for pid in ["35", "195"]:
        style = RESIDENT_STYLE[pid]
        trips = data["participants"][pid]["trips"]
        purposes = Counter(PURPOSE_CN.get(t["purpose"], t["purpose"]) for t in trips)
        dates = len(set(t["date"] for t in trips))
        total_km_approx = 0  # skip real distance

        for t in trips:
            c = PURPOSE_COLORS.get(t["purpose"], "#999")
            ax_map.plot([t["startPx"], t["endPx"]], [t["startPy"], t["endPy"]],
                        color=c, alpha=0.08, lw=0.8)

        # Top routes (most repeated start-end pairs)
        route_cnt = Counter(
            (round(t["startPx"]), round(t["startPy"]), round(t["endPx"]), round(t["endPy"]), t["purpose"])
            for t in trips
        )
        top_routes = route_cnt.most_common(8)

        for (x1, y1, x2, y2, purpose), cnt in top_routes:
            if cnt < 5:
                continue
            c = PURPOSE_COLORS.get(purpose, "#999")
            ax_map.annotate("", xy=(x2, y2), xytext=(x1, y1),
                            arrowprops=dict(arrowstyle="-|>", color=style["color"],
                                            lw=1.5 + cnt / 30, alpha=0.55, mutation_scale=12))

        home, work = key_locations(trips)
        if home:
            ax_map.scatter(*home, s=200, c=style["color"], marker="*", edgecolors="white",
                           linewidths=2, zorder=10, label=f"{style['name']} 家")
        if work:
            ax_map.scatter(*work, s=130, c=style["color"], marker="D", edgecolors="white",
                           linewidths=1.5, zorder=10)

        block = f"{style['name']}\n"
        block += f"─────────\n"
        block += f"总行程: {len(trips)} 段\n"
        block += f"覆盖天数: {dates} 天\n\n"
        block += "出行目的:\n"
        for p, n in purposes.most_common():
            block += f"  · {p}: {n}\n"
        info_blocks.append(block)

    patches = [mpatches.Patch(color=c, label=PURPOSE_CN[p]) for p, c in PURPOSE_COLORS.items()]
    ax_map.legend(handles=patches, loc="lower left", fontsize=8, framealpha=0.95, title="出行目的")

    ax_info.text(0.05, 0.98, "\n\n".join(info_blocks), transform=ax_info.transAxes,
                 fontsize=9, va="top", ha="left",
                 bbox=dict(boxstyle="round,pad=0.6", fc="#fafafa", ec="#ccc"))

    out = OUT_DIR / "03_全周期出行总览.png"
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def image_week_comparison(data, start_date="2022-03-01", days=7):
    """7-day grid showing daily patterns."""
    from datetime import datetime, timedelta
    d0 = datetime.strptime(start_date, "%Y-%m-%d")
    dates = [(d0 + timedelta(days=i)).strftime("%Y-%m-%d") for i in range(days)]

    fig, axes = plt.subplots(2, 4, figsize=(20, 11), dpi=130)
    axes = axes.flatten()
    fig.suptitle(f"居民 35 vs 195 · 一周出行对比 ({start_date} 起)", fontsize=16, fontweight="bold")

    for idx, date in enumerate(dates):
        ax = axes[idx]
        ax.imshow(load_bg(), extent=[0, MAP_W, MAP_H, 0], aspect="auto")
        ax.set_xlim(0, MAP_W)
        ax.set_ylim(MAP_H, 0)
        ax.axis("off")

        counts = []
        for pid in ["35", "195"]:
            style = RESIDENT_STYLE[pid]
            day = [t for t in data["participants"][pid]["trips"] if t["date"] == date]
            counts.append(len(day))
            for t in day:
                draw_trip(ax, t, style["color"], lw=2.2, label_mid=False, alpha=0.8)

        ax.set_title(f"{date}\n35:{counts[0]}段 · 195:{counts[1]}段", fontsize=10)

    # last panel = legend + summary
    ax = axes[7]
    ax.axis("off")
    legend_items = [
        Line2D([0], [0], color=RESIDENT_STYLE["35"]["color"], lw=3, label="居民 35"),
        Line2D([0], [0], color=RESIDENT_STYLE["195"]["color"], lw=3, label="居民 195"),
    ]
    for p, c in PURPOSE_COLORS.items():
        legend_items.append(mpatches.Patch(color=c, label=PURPOSE_CN[p]))
    ax.legend(handles=legend_items, loc="center", fontsize=11, framealpha=0.95, title="图例")

    out = OUT_DIR / f"04_一周出行对比_{start_date}.png"
    fig.savefig(out, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return out


def image_infographic_rich(data, date="2022-03-01"):
    """Rich single-page infographic with map, stats, purpose pie, hour distribution."""
    fig = plt.figure(figsize=(20, 14), dpi=150)
    gs = fig.add_gridspec(3, 4, hspace=0.35, wspace=0.3,
                          height_ratios=[3, 1.2, 1.2], width_ratios=[1.5, 1.5, 1, 1])

    ax_map = fig.add_subplot(gs[0, :2])
    ax_map.imshow(load_bg(), extent=[0, MAP_W, MAP_H, 0], aspect="auto")
    ax_map.set_xlim(0, MAP_W)
    ax_map.set_ylim(MAP_H, 0)
    ax_map.axis("off")
    ax_map.set_title(f"空间轨迹 · {date}", fontsize=13, fontweight="bold")

    ax_map2 = fig.add_subplot(gs[0, 2:])
    ax_map2.imshow(load_bg(), extent=[0, MAP_W, MAP_H, 0], aspect="auto")
    ax_map2.set_xlim(0, MAP_W)
    ax_map2.set_ylim(MAP_H, 0)
    ax_map2.axis("off")
    ax_map2.set_title("标注详图（带序号与目的）", fontsize=13, fontweight="bold")

    for pid, ax in [("35", ax_map), ("195", ax_map2)]:
        style = RESIDENT_STYLE[pid]
        day = [t for t in data["participants"][pid]["trips"] if t["date"] == date]
        home, work = key_locations(data["participants"][pid]["trips"])
        for i, t in enumerate(day, 1):
            draw_trip(ax, t, style["color"], lw=3, trip_num=i, label_mid=(ax == ax_map2))
        if home:
            ax.scatter(*home, s=200, c=style["color"], marker="*", edgecolors="white", zorder=10)
            ax.text(home[0], home[1] - 30, style["name"], ha="center", fontsize=9,
                    fontweight="bold", color=style["color"],
                    bbox=dict(boxstyle="round", fc="white", alpha=0.9))
        ax.text(0.02, 0.02, style["name"], transform=ax.transAxes, fontsize=11,
                fontweight="bold", color=style["color"],
                bbox=dict(boxstyle="round", fc="white", alpha=0.9))

    # Bar charts: purpose count per resident
    for col, pid in enumerate(["35", "195"]):
        ax_bar = fig.add_subplot(gs[1, col * 2:(col + 1) * 2])
        day = [t for t in data["participants"][pid]["trips"] if t["date"] == date]
        purposes = Counter(PURPOSE_CN.get(t["purpose"], t["purpose"]) for t in day)
        labels = list(purposes.keys())
        vals = list(purposes.values())
        colors = [PURPOSE_COLORS.get(k, "#999") for k in PURPOSE_COLORS
                  if PURPOSE_CN.get(k, k) in labels]
        # match colors to labels
        bar_colors = []
        rev_purpose = {v: k for k, v in PURPOSE_CN.items()}
        for lb in labels:
            pk = rev_purpose.get(lb)
            bar_colors.append(PURPOSE_COLORS.get(pk, "#999") if pk else "#999")
        ax_bar.barh(labels, vals, color=bar_colors, edgecolor="white")
        ax_bar.set_title(f"{RESIDENT_STYLE[pid]['name']} · 出行目的分布", fontsize=11)
        ax_bar.set_xlabel("段数")
        for i, v in enumerate(vals):
            ax_bar.text(v + 0.05, i, str(v), va="center", fontsize=9)

    # Hour distribution
    for col, pid in enumerate(["35", "195"]):
        ax_h = fig.add_subplot(gs[2, col * 2:(col + 1) * 2])
        day = [t for t in data["participants"][pid]["trips"] if t["date"] == date]
        hours = Counter(t["hour"] for t in day)
        xs = range(24)
        ys = [hours.get(h, 0) for h in xs]
        ax_h.bar(xs, ys, color=RESIDENT_STYLE[pid]["color"], alpha=0.7, edgecolor="white")
        ax_h.set_xlim(-0.5, 23.5)
        ax_h.set_xlabel("出发小时")
        ax_h.set_ylabel("段数")
        ax_h.set_title(f"{RESIDENT_STYLE[pid]['name']} · 出发时间分布", fontsize=11)
        ax_h.set_xticks(range(0, 24, 3))

    fig.suptitle(f"VAST 2022 · 双居民出行信息图 · {date}", fontsize=18, fontweight="bold", y=1.01)

    out = OUT_DIR / f"05_综合信息图_{date}.png"
    fig.savefig(out, bbox_inches="tight", facecolor="white", pad_inches=0.2)
    plt.close(fig)
    return out


def main():
    OUT_DIR.mkdir(exist_ok=True)
    data = load_data()
    dates = ["2022-03-03", "2022-03-04", "2022-03-05"]

    outputs = [image_full_overview(data)]
    for date in dates:
        outputs.extend([
            image_combined_one_day(data, date),
            image_timeline_panel(data, date),
            image_infographic_rich(data, date),
        ])

    print("Generated images:")
    for p in outputs:
        print(f"  {p} ({p.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
