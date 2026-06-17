import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import Polygon
from matplotlib.collections import PatchCollection
from matplotlib.colors import Normalize
from scipy.ndimage import gaussian_filter
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from shapely import wkt
import os
import warnings
warnings.filterwarnings('ignore')

plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False

# ========== 路径 ==========
ROOT_PATH  = r"C:\Users\luo\AppData\Local\Programs\Python\Python313\可视化\VAST-Challenge-2022"
ATTR_PATH  = f"{ROOT_PATH}/Datasets/Attributes"
LOG_PATH   = f"{ROOT_PATH}/Datasets/Activity Logs"
SAVE_PATH  = f"{ROOT_PATH}/images"
BASEMAP_PATH = f"{ROOT_PATH}/BaseMap.png"
os.makedirs(SAVE_PATH, exist_ok=True)

X_MIN, X_MAX = -4701.5, 2630.0
Y_MIN, Y_MAX = 22.2, 7836.5
X_SPAN = X_MAX - X_MIN
Y_SPAN = Y_MAX - Y_MIN

basemap_img = plt.imread(BASEMAP_PATH)

# ========== 清新色板 ==========
COLORS = {
    '住宅': '#C8E6FA',   # 淡天蓝
    '住宅边': '#6BAED6',
    '商业': '#FDDCAA',   # 淡暖橙
    '商业边': '#F4A460',
    '学校建筑': '#C3EDD3',
    '学校建筑边': '#52B788',
    '公寓点': '#4895EF',
    '雇主点': '#FF6B35',
    '餐厅点': '#FF3366',
    '酒吧点': '#9B5DE5',
    '学校点': '#00C49A',
}

# ========== 解析坐标 ==========
def parse_point(series):
    coords = series.str.extract(r'POINT \(([+-]?\d+\.?\d*) ([+-]?\d+\.?\d*)\)')
    return coords[0].astype(float), coords[1].astype(float)

def parse_polygon_centroid(series):
    xs, ys = [], []
    for g in series:
        try:
            geom = wkt.loads(g)
            xs.append(geom.centroid.x)
            ys.append(geom.centroid.y)
        except:
            xs.append(np.nan); ys.append(np.nan)
    return pd.Series(xs), pd.Series(ys)

def parse_polygon_patches(series):
    result = []
    for i, g in enumerate(series):
        try:
            geom = wkt.loads(g)
            coords = np.array(geom.exterior.coords)
            result.append((Polygon(coords, closed=True), i))
        except:
            pass
    return result

# ========== 加载数据 ==========
print("加载属性数据...")
buildings   = pd.read_csv(f"{ATTR_PATH}/Buildings.csv")
employers   = pd.read_csv(f"{ATTR_PATH}/Employers.csv")
pubs        = pd.read_csv(f"{ATTR_PATH}/Pubs.csv")
restaurants = pd.read_csv(f"{ATTR_PATH}/Restaurants.csv")
schools     = pd.read_csv(f"{ATTR_PATH}/Schools.csv")
apartments  = pd.read_csv(f"{ATTR_PATH}/Apartments.csv")

buildings['x'], buildings['y'] = parse_polygon_centroid(buildings['location'])
building_patch_list = parse_polygon_patches(buildings['location'])
for df in [employers, pubs, restaurants, schools, apartments]:
    df['x'], df['y'] = parse_point(df['location'])

# ========== 底图函数 ==========
def make_map(title, figwidth=13, basemap_alpha=0.92):
    ratio = Y_SPAN / X_SPAN
    fig, ax = plt.subplots(figsize=(figwidth, figwidth * ratio))
    ax.imshow(basemap_img, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
              aspect='equal', alpha=basemap_alpha, zorder=0)
    ax.set_xlim(X_MIN, X_MAX)
    ax.set_ylim(Y_MIN, Y_MAX)
    ax.set_title(title, fontsize=16, fontweight='bold', pad=14)
    ax.set_xlabel('X 坐标', fontsize=11)
    ax.set_ylabel('Y 坐标', fontsize=11)
    ax.grid(True, alpha=0.1, color='gray')
    return fig, ax

# ===================================================
# 图1修复版：白色背景+建筑颜色更实
# ===================================================
fig, ax = make_map('城市建筑与地点分布总览', basemap_alpha=0.0)  # 底图透明度设0，先不显示

# 先铺白色背景
ax.set_facecolor('white')

# 建筑按类型上色，透明度提高
type_cfg = {
    'Residental': ('#BDE0FE', '#6BAED6', '住宅建筑'),
    'Commercial': ('#FFD6A5', '#F4A460', '商业建筑'),
    'School':     ('#B7E4C7', '#52B788', '学校建筑'),
}
for btype, (face, edge, label) in type_cfg.items():
    idx_set = set(buildings[buildings['buildingType'] == btype].index)
    patches = [p for p, i in building_patch_list if i in idx_set]
    if patches:
        pc = PatchCollection(patches, facecolor=face, edgecolor=edge,
                             linewidth=0.6, alpha=0.85, zorder=1)  # alpha提高到0.85
        ax.add_collection(pc)
        ax.scatter([], [], color=face, edgecolors=edge, s=90,
                   linewidths=1.2, label=label, marker='s')

# 然后叠加底图（道路/轮廓），用multiply混合
ax.imshow(basemap_img, extent=[X_MIN, X_MAX, Y_MIN, Y_MAX],
          aspect='equal', alpha=0.45, zorder=2)  # 只保留道路线条

ax.scatter(apartments['x'],  apartments['y'],  c='#4895EF', s=5,  alpha=0.35, zorder=3, label='公寓')
ax.scatter(employers['x'],   employers['y'],   c='#FF6B35', s=40, alpha=0.85, zorder=4, label='雇主/公司')
ax.scatter(restaurants['x'], restaurants['y'], c='#FF3366', s=55, alpha=0.85, zorder=5, label='餐厅')
ax.scatter(pubs['x'],        pubs['y'],        c='#9B5DE5', s=55, alpha=0.85, zorder=5, label='酒吧')
ax.scatter(schools['x'],     schools['y'],     c='#00C49A', s=100,alpha=1.0,  zorder=6, label='学校')

ax.legend(loc='lower right', fontsize=10, framealpha=0.95,
          markerscale=1.3, borderpad=0.9)
ax.set_xlim(X_MIN, X_MAX)
ax.set_ylim(Y_MIN, Y_MAX)
plt.tight_layout()
plt.savefig(f'{SAVE_PATH}/图1_城市全貌地图.png', dpi=150, bbox_inches='tight')
plt.show()
print("图1修复完成")

# ===================================================
# 图2：昼夜活动热力图
# ===================================================
print("加载日志数据（前3个文件）...")
log_dfs = []
for i in range(1, 4):
    df = pd.read_csv(f"{LOG_PATH}/ParticipantStatusLogs{i}.csv",
                     usecols=['timestamp', 'currentLocation'])
    log_dfs.append(df)
logs = pd.concat(log_dfs, ignore_index=True)
logs['x'], logs['y'] = parse_point(logs['currentLocation'])
logs['timestamp'] = pd.to_datetime(logs['timestamp'])
logs['hour'] = logs['timestamp'].dt.hour
logs = logs.dropna(subset=['x', 'y'])

day_logs   = logs[(logs['hour'] >= 9)  & (logs['hour'] <= 17)][['x','y']]
night_logs = logs[(logs['hour'] >= 20) | (logs['hour'] <= 5)][['x','y']]

def make_smooth_rgba(x, y, cmap_name, bins=200, sigma=4, alpha_scale=0.82):
    h, _, _ = np.histogram2d(x, y, bins=bins,
                              range=[[X_MIN,X_MAX],[Y_MIN,Y_MAX]])
    h = gaussian_filter(h, sigma=sigma)
    thr = h.max() * 0.035
    cmap = plt.get_cmap(cmap_name)
    norm = Normalize(vmin=thr, vmax=h.max())
    rgba = cmap(norm(h.T))
    alpha = norm(h.T)
    rgba[..., 3] = np.where(h.T < thr, 0, alpha * alpha_scale)
    return rgba

day_rgba   = make_smooth_rgba(day_logs['x'],   day_logs['y'],   'YlOrRd')
night_rgba = make_smooth_rgba(night_logs['x'], night_logs['y'], 'PuBu')

ratio = Y_SPAN / X_SPAN
fig, axes = plt.subplots(1, 2, figsize=(24, 12 * ratio))

for ax, rgba, title, n in zip(
    axes,
    [day_rgba, night_rgba],
    ['白天活动热力图（09:00–17:00）', '夜间活动热力图（20:00–05:00）'],
    [len(day_logs), len(night_logs)]
):
    ax.imshow(basemap_img, extent=[X_MIN,X_MAX,Y_MIN,Y_MAX],
              aspect='equal', alpha=0.9, zorder=0)
    ax.imshow(rgba, extent=[X_MIN,X_MAX,Y_MIN,Y_MAX],
              origin='lower', aspect='equal', zorder=1, interpolation='bilinear')
    ax.set_xlim(X_MIN, X_MAX); ax.set_ylim(Y_MIN, Y_MAX)
    ax.set_title(title, fontsize=14, fontweight='bold', pad=12)
    ax.set_xlabel('X 坐标', fontsize=10); ax.set_ylabel('Y 坐标', fontsize=10)
    ax.grid(True, alpha=0.1)
    ax.text(0.02, 0.02, f'记录数: {n:,}', transform=ax.transAxes,
            fontsize=10, bbox=dict(boxstyle='round', facecolor='white', alpha=0.85))

plt.suptitle('城市昼夜活动对比', fontsize=18, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig(f'{SAVE_PATH}/图2_昼夜热力图.png', dpi=150, bbox_inches='tight')
plt.show()
print("图2完成")

# ===================================================
# 图3：KMeans聚类（固定6个区域，标注超大）
# ===================================================
print("绘制图3...")

all_venues = pd.concat([
    apartments[['x','y']].assign(类型='公寓'),
    employers[['x','y']].assign(类型='雇主'),
    restaurants[['x','y']].assign(类型='餐厅'),
    pubs[['x','y']].assign(类型='酒吧'),
    schools[['x','y']].assign(类型='学校'),
], ignore_index=True).dropna()

from sklearn.cluster import KMeans
kmeans = KMeans(n_clusters=6, random_state=42, n_init=10)
all_venues['cluster'] = kmeans.fit_predict(all_venues[['x','y']])
centers = kmeans.cluster_centers_

# 按Y从高到低命名，北→南
order = np.argsort(centers[:, 1])[::-1]
labels = ['区域A','区域B','区域C','区域D','区域E','区域F']
name_map = {cid: labels[rank] for rank, cid in enumerate(order)}
all_venues['区域'] = all_venues['cluster'].map(name_map)
named_centers = {name_map[cid]: centers[cid] for cid in range(6)}

AREA_COLORS = {
    '区域A': '#FF595E',
    '区域B': '#1982C4',
    '区域C': '#8AC926',
    '区域D': '#FF924C',
    '区域E': '#6A4C93',
    '区域F': '#06D6A0',
}

fig, ax = make_map('城市功能区域聚类（KMeans, k=6）', basemap_alpha=0.82)

for area in labels:
    sub = all_venues[all_venues['区域'] == area]
    ax.scatter(sub['x'], sub['y'],
               color=AREA_COLORS[area], s=22, alpha=0.7,
               edgecolors='white', linewidths=0.4,
               zorder=2, label=f'{area}（{len(sub)}）')

for area, (cx, cy) in named_centers.items():
    ax.annotate(area, (cx, cy),
                fontsize=16, fontweight='bold',
                ha='center', va='center', zorder=5,
                bbox=dict(boxstyle='round,pad=0.6',
                          facecolor='white',
                          edgecolor=AREA_COLORS[area],
                          linewidth=3,
                          alpha=0.97))

ax.legend(loc='lower right', fontsize=10, framealpha=0.95,
          markerscale=1.5, borderpad=0.9)
plt.tight_layout()
plt.savefig(f'{SAVE_PATH}/图3_KMeans聚类.png', dpi=150, bbox_inches='tight')
plt.show()
print("图3完成")

# 同步更新图4和图5用的all_venues
major_clusters = labels  # 用区域名代替cluster编号

# ===================================================
# 导出聚类结果：各类venue + buildingId → 区域映射表
# ===================================================

# 1. 公寓
apt_cluster = apartments[['apartmentId','buildingId','x','y']].copy()
apt_cluster['类型'] = '公寓'
apt_cluster['locationId'] = apt_cluster['apartmentId']
apt_cluster = apt_cluster.merge(
    all_venues[['x','y','区域']].drop_duplicates(),
    on=['x','y'], how='left'
)

# 2. 雇主
emp_cluster = employers[['employerId','buildingId','x','y']].copy()
emp_cluster['类型'] = '雇主'
emp_cluster['locationId'] = emp_cluster['employerId']
emp_cluster = emp_cluster.merge(
    all_venues[['x','y','区域']].drop_duplicates(),
    on=['x','y'], how='left'
)

# 3. 餐厅
res_cluster = restaurants[['restaurantId','buildingId','x','y']].copy()
res_cluster['类型'] = '餐厅'
res_cluster['locationId'] = res_cluster['restaurantId']
res_cluster = res_cluster.merge(
    all_venues[['x','y','区域']].drop_duplicates(),
    on=['x','y'], how='left'
)

# 4. 酒吧
pub_cluster = pubs[['pubId','buildingId','x','y']].copy()
pub_cluster['类型'] = '酒吧'
pub_cluster['locationId'] = pub_cluster['pubId']
pub_cluster = pub_cluster.merge(
    all_venues[['x','y','区域']].drop_duplicates(),
    on=['x','y'], how='left'
)

# 5. 学校
sch_cluster = schools[['schoolId','buildingId','x','y']].copy()
sch_cluster['类型'] = '学校'
sch_cluster['locationId'] = sch_cluster['schoolId']
sch_cluster = sch_cluster.merge(
    all_venues[['x','y','区域']].drop_duplicates(),
    on=['x','y'], how='left'
)

# 合并所有
result = pd.concat([
    apt_cluster[['locationId','buildingId','类型','x','y','区域']],
    emp_cluster[['locationId','buildingId','类型','x','y','区域']],
    res_cluster[['locationId','buildingId','类型','x','y','区域']],
    pub_cluster[['locationId','buildingId','类型','x','y','区域']],
    sch_cluster[['locationId','buildingId','类型','x','y','区域']],
], ignore_index=True)

# 保存
result.to_csv(f'{SAVE_PATH}/聚类结果_地点区域映射.csv', index=False, encoding='utf-8-sig')
print(f"已保存！共 {len(result)} 条记录")
print(result.head(10))
print("\n各区域数量：")
print(result['区域'].value_counts().sort_index())
# ===================================================
# 图4：雷达图（用区域名）
# ===================================================
print("绘制图4...")
type_list = ['公寓','雇主','餐厅','酒吧','学校']
angles = np.linspace(0, 2*np.pi, len(type_list), endpoint=False).tolist()
angles += angles[:1]

fig, axes = plt.subplots(2, 3, figsize=(15, 11),
                          subplot_kw=dict(polar=True))
axes = axes.flatten()

for i, area in enumerate(labels):
    ax = axes[i]
    sub = all_venues[all_venues['区域'] == area]
    total = len(sub)
    values = [len(sub[sub['类型']==t])/total*100 for t in type_list]
    values += values[:1]
    color = AREA_COLORS[area]
    ax.plot(angles, values, color=color, linewidth=2.2)
    ax.fill(angles, values, color=color, alpha=0.22)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(type_list, fontsize=11)
    ax.set_title(f'{area}（{total}个地点）',
                 fontsize=13, fontweight='bold', pad=16, color=color)
    ax.set_ylim(0, 100)
    ax.grid(True, alpha=0.3)

plt.suptitle('各区域功能构成雷达图', fontsize=17, fontweight='bold')
plt.tight_layout()
plt.savefig(f'{SAVE_PATH}/图4_功能画像雷达图.png', dpi=150, bbox_inches='tight')
plt.show()
print("图4完成")

# ===================================================
# 图5：打分表（用区域名）
# ===================================================
print("绘制图5...")

def name_area(row):
    if row['雇主%'] > 25:               return '商业就业区'
    elif row['公寓%'] > 65:             return '居住区'
    elif row['餐厅%']+row['酒吧%'] > 18: return '娱乐餐饮区'
    elif row['学校%'] > 5:              return '教育区'
    else:                               return '混合区'

rows = []
for area in labels:
    sub = all_venues[all_venues['区域'] == area]
    t = len(sub)
    rows.append({
        '区域': area,
        '地点数': t,
        '公寓%': round(len(sub[sub['类型']=='公寓'])/t*100, 1),
        '雇主%': round(len(sub[sub['类型']=='雇主'])/t*100, 1),
        '餐厅%': round(len(sub[sub['类型']=='餐厅'])/t*100, 1),
        '酒吧%': round(len(sub[sub['类型']=='酒吧'])/t*100, 1),
        '学校%': round(len(sub[sub['类型']=='学校'])/t*100, 1),
        'X中心': round(sub['x'].mean()),
        'Y中心': round(sub['y'].mean()),
    })

score_df = pd.DataFrame(rows)
score_df['区域定性'] = score_df.apply(name_area, axis=1)

fig, ax = plt.subplots(figsize=(15, len(score_df)*0.72 + 2.5))
ax.axis('off')

table = ax.table(
    cellText=score_df.values.tolist(),
    colLabels=list(score_df.columns),
    cellLoc='center', loc='center'
)
table.auto_set_font_size(False)
table.set_fontsize(11)
table.scale(1.15, 2.2)

for j in range(len(score_df.columns)):
    table[(0,j)].set_facecolor('#2C3E50')
    table[(0,j)].set_text_props(color='white', fontweight='bold')

for i in range(1, len(score_df)+1):
    bg = '#F7FBFF' if i%2==0 else 'white'
    for j in range(len(score_df.columns)):
        table[(i,j)].set_facecolor(bg)

type_clr = {'商业就业区':'#FDDCAA','居住区':'#C8E6FA',
            '娱乐餐饮区':'#FFCCD5','教育区':'#C3EDD3','混合区':'#E8D5F5'}
last = len(score_df.columns)-1
for i, v in enumerate(score_df['区域定性']):
    table[(i+1, last)].set_facecolor(type_clr.get(v,'white'))

# 第一列用区域颜色
for i, area in enumerate(labels):
    table[(i+1, 0)].set_facecolor(AREA_COLORS[area])
    table[(i+1, 0)].set_text_props(color='white', fontweight='bold')

ax.set_title('各区域功能定量分析与区域命名',
             fontsize=15, fontweight='bold', pad=20)
plt.tight_layout()
plt.savefig(f'{SAVE_PATH}/图5_区域打分表.png', dpi=150, bbox_inches='tight')
plt.show()
print("图5完成")

print(f"\n✅ 图3、4、5已更新保存到：{SAVE_PATH}")


print(result[['类型','区域']].value_counts().sort_index())
print("\n各区域中心坐标：")
for area in labels:
    sub = all_venues[all_venues['区域'] == area]
    print(f"{area}: X={sub['x'].mean():.0f}, Y={sub['y'].mean():.0f}, 总数={len(sub)}")


# ===================================================
# 补充图A：各区域venue类型构成分组柱状图
# ===================================================
print("绘制补充图A...")

type_list = ['公寓', '雇主', '餐厅', '酒吧', '学校']
type_colors_bar = {
    '公寓': '#4895EF',
    '雇主': '#FF6B35',
    '餐厅': '#FF3366',
    '酒吧': '#9B5DE5',
    '学校': '#00C49A',
}

composition = all_venues.groupby(['区域', '类型']).size().unstack(fill_value=0)
composition = composition.reindex(labels)

x_pos = np.arange(len(labels))
bar_width = 0.15

fig, ax = plt.subplots(figsize=(13, 6))
ax.set_facecolor('white')

for i, t in enumerate(type_list):
    if t in composition.columns:
        offset = (i - 2) * bar_width
        bars = ax.bar(x_pos + offset, composition[t],
                      width=bar_width, label=t,
                      color=type_colors_bar[t],
                      edgecolor='white', linewidth=0.5)
        # 柱子顶部标数值
        for bar in bars:
            h = bar.get_height()
            if h > 0:
                ax.text(bar.get_x() + bar.get_width()/2, h + 2,
                        str(int(h)), ha='center', va='bottom',
                        fontsize=8, color='#333333')

ax.set_xticks(x_pos)
ax.set_xticklabels(labels, fontsize=12)
ax.set_title('各区域地点类型构成对比', fontsize=15, fontweight='bold', pad=15)
ax.set_xlabel('区域', fontsize=12)
ax.set_ylabel('数量', fontsize=12)
ax.legend(title='地点类型', fontsize=10, title_fontsize=10,
          bbox_to_anchor=(1.02, 1), loc='upper left', framealpha=0.9)
ax.grid(axis='y', alpha=0.25, linestyle='--')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# 用区域颜色标注X轴
for i, (label, tick) in enumerate(zip(labels, ax.get_xticklabels())):
    tick.set_color(AREA_COLORS[label])
    tick.set_fontweight('bold')

plt.tight_layout()
plt.savefig(f'{SAVE_PATH}/补充图A_区域构成柱状图.png', dpi=150, bbox_inches='tight')
plt.show()
print("补充图A完成")

# ===================================================
# 补充图B：各区域建筑类型构成饼图（6个小饼）
# ===================================================
print("绘制补充图B...")

# 把buildings的buildingType和区域关联
# 通过buildingId关联各venue找到每栋建筑所在区域
building_area = pd.concat([
    apartments[['buildingId','x','y']],
    employers[['buildingId','x','y']],
    restaurants[['buildingId','x','y']],
    pubs[['buildingId','x','y']],
    schools[['buildingId','x','y']],
], ignore_index=True).dropna()

building_area = building_area.merge(
    all_venues[['x','y','区域']].drop_duplicates(),
    on=['x','y'], how='left'
).dropna(subset=['区域'])

building_area = building_area.merge(
    buildings[['buildingId','buildingType']],
    on='buildingId', how='left'
).dropna(subset=['buildingType'])

building_area = building_area.drop_duplicates(subset=['buildingId'])

btype_colors = {
    'Residental': '#BDE0FE',
    'Commercial': '#FFD6A5',
    'School':     '#B7E4C7',
}
btype_labels_cn = {
    'Residental': '住宅',
    'Commercial': '商业',
    'School':     '学校',
}

fig, axes = plt.subplots(2, 3, figsize=(15, 10))
axes = axes.flatten()

for i, area in enumerate(labels):
    ax = axes[i]
    sub = building_area[building_area['区域'] == area]
    counts = sub['buildingType'].value_counts()

    if len(counts) == 0:
        ax.set_visible(False)
        continue

    pie_labels = [btype_labels_cn.get(k, k) for k in counts.index]
    pie_colors = [btype_colors.get(k, '#DDDDDD') for k in counts.index]

    wedges, texts, autotexts = ax.pie(
        counts.values,
        labels=pie_labels,
        colors=pie_colors,
        autopct='%1.1f%%',
        startangle=90,
        wedgeprops=dict(edgecolor='white', linewidth=1.5),
        textprops={'fontsize': 11},
    )
    for at in autotexts:
        at.set_fontsize(10)
        at.set_fontweight('bold')

    ax.set_title(f'{area}\n（{len(sub)}栋建筑）',
                 fontsize=13, fontweight='bold',
                 color=AREA_COLORS[area], pad=10)

plt.suptitle('各区域建筑类型构成', fontsize=16, fontweight='bold', y=1.01)
plt.tight_layout()
plt.savefig(f'{SAVE_PATH}/补充图B_建筑类型饼图.png', dpi=150, bbox_inches='tight')
plt.show()
print("补充图B完成")

print(f"\n✅ 补充图A、B已保存到：{SAVE_PATH}")

# 打印饼图数据供报告参考
print("\n各区域建筑类型数量：")
print(building_area.groupby(['区域','buildingType']).size().unstack(fill_value=0))
