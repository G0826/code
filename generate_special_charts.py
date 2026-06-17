"""Generate time-activity heatmap and purpose pie + Sankey diagrams."""
import json
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.colors import ListedColormap, BoundaryNorm
import numpy as np
import plotly.graph_objects as go

BASE = Path(__file__).parent
DATA_PATH = BASE / "animation_data.json"
OUT_DIR = BASE / "travel_images"

plt.rcParams["font.sans-serif"] = ["Microsoft YaHei", "SimHei", "DejaVu Sans"]
plt.rcParams["axes.unicode_minus"] = False

PURPOSE_CN = {
    "Work/Home Commute": "通勤",
    "Eating": "用餐",
    "Recreation (Social Gathering)": "休闲",
    "Coming Back From Restaurant": "餐返",
    "Going Back to Home": "回家",
}
PURPOSE_COLORS = {
    "Work/Home Commute": "#FF6B6B",
    "Eating": "#4ECDC4",
    "Recreation (Social Gathering)": "#FFE66D",
    "Coming Back From Restaurant": "#FF9F4A",
    "Going Back to Home": "#9B5DE5",
}
PURPOSE_ORDER = list(PURPOSE_CN.keys())

LOC_CN = {
    "Apartment": "家",
    "Employer": "工作",
    "Restaurant": "餐厅",
    "Pub": "酒吧",
    "School": "学校",
}

RESIDENT = {
    "35": {"name": "居民 35", "color": "#1565C0"},
    "195": {"name": "居民 195", "color": "#C62828"},
}


def load_data():
    with open(DATA_PATH, encoding="utf-8") as f:
        return json.load(f)


def trip_hours(t):
    """Hours covered by a trip (from start to end)."""
    t0 = datetime.fromisoformat(t["startTime"].replace("Z", "+00:00"))
    t1 = datetime.fromisoformat(t["endTime"].replace("Z", "+00:00"))
    hours = set()
    cur = t0.replace(minute=0, second=0, microsecond=0)
    while cur <= t1:
        hours.add(cur.hour)
        cur += timedelta(hours=1)
    if not hours:
        hours.add(t0.hour)
    return hours


def build_day_hour_matrix(trips, dates):
    """Matrix [n_dates, 24] with purpose index; -1 = no activity."""
    date_idx = {d: i for i, d in enumerate(dates)}
    # weight[date][hour][purpose] = minutes
    weight = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    for t in trips:
        if t["date"] not in date_idx:
            continue
        dur_min = t["durationMs"] / 60000
        per_hour = dur_min / max(len(trip_hours(t)), 1)
        for h in trip_hours(t):
            weight[t["date"]][h][t["purpose"]] += per_hour

    mat = np.full((len(dates), 24), -1, dtype=int)
    for d in dates:
        i = date_idx[d]
        for h in range(24):
            if weight[d][h]:
                mat[i, h] = PURPOSE_ORDER.index(
                    max(weight[d][h].items(), key=lambda x: x[1])[0]
                )
    return mat


def build_weekday_hour_matrix(trips):
    """Aggregate by weekday (0=Mon) × hour for life pattern."""
    weight = defaultdict(lambda: defaultdict(lambda: defaultdict(float)))
    for t in trips:
        dt = datetime.strptime(t["date"], "%Y-%m-%d")
        wd = dt.weekday()
        dur_min = t["durationMs"] / 60000
        for h in trip_hours(t):
            weight[wd][h][t["purpose"]] += dur_min

    mat = np.full((7, 24), -1, dtype=int)
    for wd in range(7):
        for h in range(24):
            if weight[wd][h]:
                mat[wd, h] = PURPOSE_ORDER.index(
                    max(weight[wd][h].items(), key=lambda x: x[1])[0]
                )
    return mat


def select_dates(trips, mode="month", month="2022-03"):
    all_dates = sorted(set(t["date"] for t in trips))
    if mode == "month":
        return [d for d in all_dates if d.startswith(month)]
    if mode == "first60":
        return all_dates[:60]
    return all_dates


def plot_heatmap_panel(ax, mat, ylabels, title, show_cbar=False):
    cmap_colors = ["#EEEEEE"] + [PURPOSE_COLORS[p] for p in PURPOSE_ORDER]
    cmap = ListedColormap(cmap_colors)
    bounds = np.arange(-0.5, len(PURPOSE_ORDER) + 1.5, 1)
    norm = BoundaryNorm(bounds, len(cmap_colors))

    im = ax.imshow(mat, aspect="auto", cmap=cmap, norm=norm, interpolation="nearest")
    ax.set_title(title, fontsize=12, fontweight="bold", pad=8)
    ax.set_xlabel("时刻 (小时)", fontsize=10)
    ax.set_xticks(range(0, 24, 2))
    ax.set_xticklabels([f"{h:02d}" for h in range(0, 24, 2)], fontsize=8)
    ax.set_yticks(range(len(ylabels)))
    ax.set_yticklabels(ylabels, fontsize=7 if len(ylabels) > 15 else 9)
    ax.grid(False)
    return im


def image_time_activity_heatmap(data):
    fig = plt.figure(figsize=(22, 16), dpi=150)
    gs = fig.add_gridspec(3, 2, height_ratios=[1.2, 1, 1], hspace=0.38, wspace=0.22)

    weekday_labels = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    for col, pid in enumerate(["35", "195"]):
        trips = data["participants"][pid]["trips"]
        name = RESIDENT[pid]["name"]
        dates_march = select_dates(trips, "month", "2022-03")
        day_labels = [d[5:] for d in dates_march]  # MM-DD

        # Row 0: weekday × hour (生活规律)
        ax0 = fig.add_subplot(gs[0, col])
        wmat = build_weekday_hour_matrix(trips)
        plot_heatmap_panel(ax0, wmat, weekday_labels,
                           f"{name} · 星期×时刻 活动规律（全周期汇总）")

        # Row 1: March daily × hour
        ax1 = fig.add_subplot(gs[1, col])
        dmat = build_day_hour_matrix(trips, dates_march)
        plot_heatmap_panel(ax1, dmat, day_labels,
                           f"{name} · 2022年3月 每日×时刻")

        # Row 2: hour activity frequency bar
        ax2 = fig.add_subplot(gs[2, col])
        hour_cnt = defaultdict(lambda: defaultdict(int))
        for t in trips:
            for h in trip_hours(t):
                hour_cnt[h][t["purpose"]] += 1
        hours = range(24)
        bottom = np.zeros(24)
        for p in PURPOSE_ORDER:
            vals = [hour_cnt[h][p] for h in hours]
            ax2.bar(hours, vals, bottom=bottom, label=PURPOSE_CN[p],
                    color=PURPOSE_COLORS[p], edgecolor="white", linewidth=0.3)
            bottom += vals
        ax2.set_xlim(-0.5, 23.5)
        ax2.set_xlabel("时刻 (小时)", fontsize=10)
        ax2.set_ylabel("活动段数", fontsize=10)
        ax2.set_title(f"{name} · 各时段活动类型堆叠分布", fontsize=12, fontweight="bold")
        ax2.set_xticks(range(0, 24, 2))
        ax2.legend(fontsize=8, loc="upper right", ncol=2)

    # Shared legend
    patches = [mpatches.Patch(color=PURPOSE_COLORS[p], label=PURPOSE_CN[p]) for p in PURPOSE_ORDER]
    patches.insert(0, mpatches.Patch(color="#EEEEEE", label="无活动"))
    fig.legend(handles=patches, loc="upper center", ncol=6, fontsize=10,
               bbox_to_anchor=(0.5, 1.01), title="活动类型", title_fontsize=11)

    fig.suptitle("时间-活动热力图 · 居民 35 vs 195", fontsize=18, fontweight="bold", y=1.03)

    out = OUT_DIR / "06_时间活动热力图.png"
    fig.savefig(out, bbox_inches="tight", facecolor="white", pad_inches=0.25)
    plt.close(fig)
    return out


def purpose_counts(trips):
    cnt = defaultdict(int)
    for t in trips:
        cnt[t["purpose"]] += 1
    return cnt


def plot_pie_panel(ax, trips, pid):
    cnt = purpose_counts(trips)
    labels, sizes, colors = [], [], []
    for p in PURPOSE_ORDER:
        if cnt[p]:
            labels.append(f"{PURPOSE_CN[p]}\n{cnt[p]}段 ({100*cnt[p]/len(trips):.1f}%)")
            sizes.append(cnt[p])
            colors.append(PURPOSE_COLORS[p])
    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors, autopct="",
        startangle=90, pctdistance=0.75,
        wedgeprops=dict(edgecolor="white", linewidth=2),
    )
    for t in texts:
        t.set_fontsize(9)
    ax.set_title(f"{RESIDENT[pid]['name']}\n共 {len(trips)} 段行程",
                 fontsize=13, fontweight="bold")


def build_sankey_data(trips, pid):
    """3-layer: 起点类型 -> 出行目的 -> 终点类型"""
    flow = defaultdict(int)
    for t in trips:
        s = LOC_CN.get(t["startType"], t["startType"])
        e = LOC_CN.get(t["endType"], t["endType"])
        p = PURPOSE_CN.get(t["purpose"], t["purpose"])
        flow[(s, p)] += 1
        flow[(p, e)] += 1

    prefix = RESIDENT[pid]["name"] + "·"
    nodes = []
    node_idx = {}

    def add_node(label):
        key = prefix + label
        if key not in node_idx:
            node_idx[key] = len(nodes)
            nodes.append(label)
        return node_idx[key]

    sources = []
    targets = []
    values = []
    link_colors = []
    link_color_map = PURPOSE_CN

    for (a, b), v in flow.items():
        # determine if a is location or purpose
        if a in LOC_CN.values():
            ia = add_node(a)
        else:
            ia = add_node(a)
        ib = add_node(b)
        sources.append(ia)
        targets.append(ib)
        values.append(v)
        # color by purpose if b is purpose else by a
        if b in link_color_map.values():
            rev = {v: k for k, v in PURPOSE_CN.items()}
            pk = rev.get(b, "")
            link_colors.append(PURPOSE_COLORS.get(pk, "#cccccc"))
        elif a in link_color_map.values():
            rev = {v: k for k, v in PURPOSE_CN.items()}
            pk = rev.get(a, "")
            link_colors.append(PURPOSE_COLORS.get(pk, "#cccccc"))
        else:
            link_colors.append("#aaaaaa88")

    return nodes, sources, targets, values, link_colors


def build_sankey_figure(data):
    """Combined figure with two sankey subplots via plotly."""
    figs = []
    for pid in ["35", "195"]:
        trips = data["participants"][pid]["trips"]
        nodes, sources, targets, values, link_colors = build_sankey_data(trips, pid)
        node_colors = []
        loc_colors = {"家": "#90CAF9", "工作": "#FFCC80", "餐厅": "#EF9A9A",
                      "酒吧": "#CE93D8", "学校": "#A5D6A7"}
        for n in nodes:
            if n in loc_colors:
                node_colors.append(loc_colors[n])
            elif n in PURPOSE_CN.values():
                rev = {v: k for k, v in PURPOSE_CN.items()}
                node_colors.append(PURPOSE_COLORS.get(rev.get(n, ""), "#B0BEC5"))
            else:
                node_colors.append("#B0BEC5")

        fig = go.Figure(data=[go.Sankey(
            arrangement="snap",
            node=dict(
                pad=18, thickness=22,
                label=[f"{n}" for n in nodes],
                color=node_colors,
                line=dict(color="#333", width=0.5),
            ),
            link=dict(
                source=sources, target=targets, value=values,
                color=[c if len(c) == 9 else c + "99" for c in link_colors],
            ),
        )])
        fig.update_layout(
            title=dict(text=f"{RESIDENT[pid]['name']} · 地点—目的—地点 流量桑基图",
                       font=dict(size=16, family="Microsoft YaHei")),
            font=dict(family="Microsoft YaHei", size=11),
            width=900, height=520,
            margin=dict(l=20, r=20, t=60, b=20),
        )
        figs.append(fig)
    return figs


def image_pie_and_sankey(data):
    # --- Matplotlib pie charts ---
    fig_pie, axes = plt.subplots(1, 2, figsize=(16, 7), dpi=150)
    for ax, pid in zip(axes, ["35", "195"]):
        trips = data["participants"][pid]["trips"]
        plot_pie_panel(ax, trips, pid)
    fig_pie.suptitle("行程目的占比 · 居民 35 vs 195（全周期）",
                     fontsize=16, fontweight="bold", y=1.02)
    out_pie = OUT_DIR / "07a_行程目的占比饼图.png"
    fig_pie.savefig(out_pie, bbox_inches="tight", facecolor="white")
    plt.close(fig_pie)

    # --- Plotly Sankey combined PNG ---
    out_sankey_combined = OUT_DIR / "07b_地点流量桑基图.png"
    from plotly.subplots import make_subplots
    # Build one figure with 2 rows
    all_nodes_35, s35, t35, v35, c35 = build_sankey_data(
        data["participants"]["35"]["trips"], "35")
    all_nodes_195, s195, t195, v195, c195 = build_sankey_data(
        data["participants"]["195"]["trips"], "195")

    def node_colors_for(nodes):
        loc_colors = {"家": "#90CAF9", "工作": "#FFCC80", "餐厅": "#EF9A9A",
                      "酒吧": "#CE93D8", "学校": "#A5D6A7"}
        rev = {v: k for k, v in PURPOSE_CN.items()}
        colors = []
        for n in nodes:
            if n in loc_colors:
                colors.append(loc_colors[n])
            elif n in rev:
                colors.append(PURPOSE_COLORS[rev[n]])
            else:
                colors.append("#B0BEC5")
        return colors

    fig_combined = make_subplots(
        rows=2, cols=1,
        specs=[[{"type": "sankey"}], [{"type": "sankey"}]],
        row_heights=[0.5, 0.5],
        vertical_spacing=0.06,
        subplot_titles=("居民 35 · 起点 → 目的 → 终点 流量",
                        "居民 195 · 起点 → 目的 → 终点 流量"),
    )
    for row, (nodes, s, t, v, pid) in enumerate(
        [(all_nodes_35, s35, t35, v35, "35"), (all_nodes_195, s195, t195, v195, "195")], 1
    ):
        nc = node_colors_for(nodes)
        fig_combined.add_trace(go.Sankey(
            arrangement="snap",
            node=dict(pad=16, thickness=20, label=nodes, color=nc,
                      line=dict(color="#333", width=0.5)),
            link=dict(source=s, target=t, value=v,
                      color=["rgba(120,120,120,0.35)"] * len(v)),
        ), row=row, col=1)

    fig_combined.update_layout(
        title=dict(text="地点间出行流量桑基图（宽度 = 行程段数）",
                   font=dict(size=18, family="Microsoft YaHei")),
        font=dict(family="Microsoft YaHei", size=11),
        width=1200, height=1100,
        margin=dict(t=80, b=30),
    )
    fig_combined.write_image(str(out_sankey_combined), scale=2)

    return [out_pie, out_sankey_combined]


def main():
    OUT_DIR.mkdir(exist_ok=True)
    data = load_data()
    outputs = [
        image_time_activity_heatmap(data),
        *image_pie_and_sankey(data),
    ]
    print("Generated:")
    for p in outputs:
        print(f"  {p} ({p.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
