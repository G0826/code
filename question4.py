import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import os

# =========================
# 字体设置
# =========================
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# =========================
# 数据：后期占比 - 前期占比
# =========================
data = pd.DataFrame(
    [
        [3.65, -1.92, -1.23, -0.47, -0.04],
        [3.58, -1.07, -1.92, -0.57, -0.03],
        [3.57, -1.89, -1.12, -0.57,  0.00],
        [5.14, -3.18, -2.03,  0.09, -0.02],
        [5.30, -3.37, -1.66, -0.22, -0.04],
        [3.19, -0.78, -1.69, -0.73,  0.02]
    ],
    index=['区域A', '区域B', '区域C', '区域D', '区域E', '区域F'],
    columns=['居家', '娱乐', '出行', '工作', '餐饮']
)

# 综合变化强度 = 居家增加 + 娱乐下降绝对值 + 出行下降绝对值
strength = pd.Series(
    [6.80, 6.57, 6.58, 10.35, 10.33, 5.66],
    index=['区域A', '区域B', '区域C', '区域D', '区域E', '区域F']
).sort_values(ascending=True)

# =========================
# 柔和蓝-白-橙色盘
# =========================
cmap = LinearSegmentedColormap.from_list(
    "soft_blue_orange",
    ["#6F93B7", "#F7F7F7", "#E39A63"],
    N=256
)

# =========================
# 画布布局
# =========================
fig = plt.figure(figsize=(14, 8), facecolor="white")

# 主标题
fig.text(0.06, 0.94, "Significant Change #1", fontsize=13, fontweight="bold", color="#444444")
fig.text(0.06, 0.895, "城市活动结构整体转变", fontsize=22, fontweight="bold", color="#222222")
fig.text(0.06, 0.862, "Regional Activity Change Matrix (Late Period − Early Period)",
         fontsize=12, color="#666666")

# =========================
# 左侧热力图
# =========================
ax_heat = fig.add_axes([0.06, 0.22, 0.55, 0.55])

sns.heatmap(
    data,
    cmap=cmap,
    center=0,
    vmin=-5.5,
    vmax=5.5,
    annot=True,
    fmt=".2f",
    linewidths=0.4,
    linecolor="#EAEAEA",
    cbar=True,
    cbar_kws={
        "label": "变化百分点",
        "shrink": 0.82
    },
    ax=ax_heat
)

ax_heat.set_title("区域 × 活动变化热力图", fontsize=15, fontweight="bold", pad=12)
ax_heat.set_xlabel("活动类型", fontsize=11)
ax_heat.set_ylabel("城市区域", fontsize=11)
ax_heat.tick_params(axis='x', labelrotation=0)
ax_heat.tick_params(axis='y', labelrotation=0)

# =========================
# 右侧 Top Findings
# =========================
ax_note = fig.add_axes([0.67, 0.43, 0.28, 0.34])
ax_note.axis("off")

ax_note.text(0.00, 1.00, "Top Findings", fontsize=15, fontweight="bold", color="#222222")

findings = [
    ("01", "所有区域居家活动均增加", "居家变化均为正值，说明居家化趋势具有全局性。"),
    ("02", "区域D、E变化最显著", "区域D与区域E综合变化强度均超过10。"),
    ("03", "娱乐活动普遍下降", "六个区域娱乐活动均为负向变化。"),
    ("04", "工作与餐饮基本稳定", "两类活动变化幅度整体较小。")
]

y = 0.82
for no, title, desc in findings:
    ax_note.text(0.00, y, no, fontsize=11, fontweight="bold", color="#E39A63")
    ax_note.text(0.10, y, title, fontsize=11.5, fontweight="bold", color="#222222")
    ax_note.text(0.10, y - 0.08, desc, fontsize=9.5, color="#666666")
    y -= 0.22

# =========================
# 右下：区域变化强度排序
# =========================
ax_bar = fig.add_axes([0.67, 0.18, 0.28, 0.18])

bar_colors = ["#D8B18A" if v < 8 else "#D8783F" for v in strength.values]

ax_bar.barh(strength.index, strength.values, color=bar_colors)
ax_bar.set_title("区域综合变化强度排序", fontsize=12, fontweight="bold")
ax_bar.set_xlabel("综合变化强度", fontsize=9)
ax_bar.tick_params(axis='both', labelsize=9)

for i, v in enumerate(strength.values):
    ax_bar.text(v + 0.15, i, f"{v:.2f}", va="center", fontsize=9)

ax_bar.spines["top"].set_visible(False)
ax_bar.spines["right"].set_visible(False)
ax_bar.grid(axis="x", alpha=0.25)

# =========================
# 底部总结
# =========================
fig.text(
    0.06, 0.08,
    "核心发现：从前期到后期，城市活动结构呈现明显居家化趋势；娱乐和出行活动在多数区域下降，区域D与区域E表现出最强烈的行为变化。",
    fontsize=11,
    color="#333333"
)

# =========================
# 保存到桌面
# =========================
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
save_path = os.path.join(desktop, "图1_区域活动变化矩阵_升级版.png")

plt.savefig(save_path, dpi=300, bbox_inches="tight")
plt.show()




import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import os

# =========================
# 字体设置
# =========================
plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# =========================
# 数据：后期占比 - 前期占比
# =========================
data = pd.DataFrame(
    [
        [10.00, -6.11, -3.79],
        [8.52,  -4.61, -3.86],
        [3.51,  -1.48, -1.10],
        [1.56,  -0.68, -0.66]
    ],
    index=['晚高峰', '夜间活动时段', '白天工作时段', '早高峰'],
    columns=['居家', '娱乐', '出行']
)

# 综合变化强度 = 居家增加 + 娱乐下降绝对值 + 出行下降绝对值
strength = pd.Series(
    {
        '晚高峰': 10.00 + 6.11 + 3.79,
        '夜间活动时段': 8.52 + 4.61 + 3.86,
        '白天工作时段': 3.51 + 1.48 + 1.10,
        '早高峰': 1.56 + 0.68 + 0.66
    }
).sort_values(ascending=True)

# =========================
# 柔和蓝-白-橙色盘，和图一统一
# =========================
cmap = LinearSegmentedColormap.from_list(
    "soft_blue_orange",
    ["#6F93B7", "#F7F7F7", "#E39A63"],
    N=256
)

# =========================
# 画布
# =========================
fig = plt.figure(figsize=(14, 7), facecolor="white")

# 左侧热力图
ax1 = plt.subplot2grid((1, 4), (0, 0), colspan=3)

sns.heatmap(
    data,
    cmap=cmap,
    center=0,
    vmin=-10,
    vmax=10,
    annot=True,
    fmt=".2f",
    linewidths=0.2,
    linecolor="#EEEEEE",
    cbar_kws={"label": "变化幅度"},
    ax=ax1
)

ax1.set_title(
    "时段活动变化矩阵\nTemporal Activity Change Matrix",
    fontsize=16,
    fontweight="bold",
    pad=15
)

ax1.set_xlabel("")
ax1.set_ylabel("")
ax1.tick_params(axis="x", labelrotation=0)
ax1.tick_params(axis="y", labelrotation=0)

# 右侧强度排序图
ax2 = plt.subplot2grid((1, 4), (0, 3))

ax2.barh(
    strength.index,
    strength.values,
    color="#D98B5F"
)

ax2.set_title(
    "时段变化强度",
    fontsize=13,
    fontweight="bold"
)

for i, v in enumerate(strength.values):
    ax2.text(
        v + 0.3,
        i,
        f"{v:.2f}",
        va="center",
        fontsize=10
    )

ax2.set_xlim(0, max(strength.values) + 3)
ax2.spines["top"].set_visible(False)
ax2.spines["right"].set_visible(False)

# 总标题
plt.suptitle(
    "Significant Change #2\n城市行为变化主要集中于晚间",
    fontsize=20,
    fontweight="bold",
    y=0.98
)

plt.tight_layout()

# =========================
# 保存到桌面
# =========================
desktop = os.path.join(os.path.expanduser("~"), "Desktop")
save_path = os.path.join(desktop, "图2_时段活动变化矩阵_美化版.png")

plt.savefig(save_path, dpi=300, bbox_inches="tight")
plt.show()

print("已保存到：")
print(save_path)





import pandas as pd
import matplotlib.pyplot as plt
import os
from PIL import Image

plt.rcParams['font.sans-serif'] = ['Microsoft YaHei', 'SimHei']
plt.rcParams['axes.unicode_minus'] = False

# =========================
# 1. 读取桌面文件
# =========================
desktop = os.path.join(os.path.expanduser("~"), "Desktop")

csv_path = os.path.join(desktop, "聚类结果_地点区域映射.csv")

df = pd.read_csv(csv_path)

# 如果你的列名里有空格，先清理一下
df.columns = df.columns.str.strip()

# =========================
# 2. 区域变化强度数据
# 综合强度 = 居家增加 + 娱乐下降绝对值 + 出行下降绝对值
# =========================
strength = pd.Series({
    "区域A": 6.80,
    "区域B": 6.57,
    "区域C": 6.58,
    "区域D": 10.35,
    "区域E": 10.33,
    "区域F": 5.66
})

# =========================
# 3. 计算每个区域中心点
# =========================
centers = df.groupby("区域")[["x", "y"]].mean()
centers["变化强度"] = centers.index.map(strength)

# 按强度排序，用于右侧条形图
rank = centers["变化强度"].sort_values()

# =========================
# 4. 画布
# =========================
fig = plt.figure(figsize=(14, 8), facecolor="white")

# =========================
# 5. 左侧地图
# =========================
ax_map = plt.subplot2grid((1, 4), (0, 0), colspan=3)

# 先画全部点，作为城市底图
# 按类型区分建筑，颜色尽量淡，避免抢热点气泡
type_colors = {
    "公寓": "#D9E6F2",
    "餐厅": "#F2D8D8",
    "酒吧": "#E1D8F2",
    "学校": "#D8EAD8",
    "雇主": "#F2E6C8",
    "公司": "#F2E6C8"
}

for t, sub in df.groupby("类型"):
    ax_map.scatter(
        sub["x"], sub["y"],
        s=8,
        c=type_colors.get(t, "#DDDDDD"),
        alpha=0.65,
        label=t,
        edgecolors="none"
    )

# 热点气泡大小
bubble_sizes = (centers["变化强度"] ** 2) * 28

sc = ax_map.scatter(
    centers["x"],
    centers["y"],
    s=bubble_sizes,
    c=centers["变化强度"],
    cmap="Oranges",
    alpha=0.78,
    edgecolors="#8A3F16",
    linewidths=1.2,
    zorder=5
)

# 标注区域名和强度
for region, row in centers.iterrows():
    ax_map.text(
        row["x"],
        row["y"],
        f"{region}\n{row['变化强度']:.2f}",
        ha="center",
        va="center",
        fontsize=11,
        fontweight="bold",
        color="black",
        zorder=6
    )

ax_map.set_title(
    "区域变化强度空间分布图\nSpatial Distribution of Regional Change Intensity",
    fontsize=16,
    fontweight="bold",
    pad=15
)

ax_map.set_xlabel("X 坐标")
ax_map.set_ylabel("Y 坐标")
ax_map.grid(alpha=0.2)

# 只保留地图比例，不让图太挤
ax_map.set_aspect("equal", adjustable="box")

# 图例放小一点
ax_map.legend(
    title="地点类型",
    loc="lower right",
    fontsize=8,
    title_fontsize=9,
    frameon=True
)

# 色条
cbar = plt.colorbar(sc, ax=ax_map, fraction=0.035, pad=0.02)
cbar.set_label("变化强度")

# =========================
# 6. 右侧强度排序图
# =========================
ax_bar = plt.subplot2grid((1, 4), (0, 3))

ax_bar.barh(
    rank.index,
    rank.values,
    color="#D98B5F"
)

ax_bar.set_title(
    "区域变化强度",
    fontsize=13,
    fontweight="bold"
)

for i, v in enumerate(rank.values):
    ax_bar.text(
        v + 0.15,
        i,
        f"{v:.2f}",
        va="center",
        fontsize=10
    )

ax_bar.set_xlim(0, max(rank.values) + 2)
ax_bar.spines["top"].set_visible(False)
ax_bar.spines["right"].set_visible(False)
ax_bar.grid(axis="x", alpha=0.25)

# =========================
# 7. 总标题
# =========================
plt.suptitle(
    "Significant Change #3\n行为变化具有明显空间差异",
    fontsize=20,
    fontweight="bold",
    y=0.98
)

plt.tight_layout()

# =========================
# 8. 保存到桌面
# =========================
save_path = os.path.join(desktop, "图3_区域变化强度空间分布图.png")

plt.savefig(save_path, dpi=300, bbox_inches="tight")
plt.show()

print("已保存到：")
print(save_path)

print("图片已保存到：")
print(save_path)
