import pandas as pd
import numpy as np

# ============================================
# 请修改这两个路径为你的实际路径
# ============================================
travel_clean_path = "F:/数据可视化/数据整理交付包(1)/同学A_数据整理交付包/代码/travel_clean.csv"
venue_path = "F:/数据可视化/数据整理交付包(1)/同学A_数据整理交付包/代码/venue_lookup.csv"
output_folder = "F:/数据可视化/数据整理交付包(1)/同学A_数据整理交付包/"

# ============================================
# 1. 读取清洗后的数据
# ============================================
print("正在读取 travel_clean.csv ...")
travel_clean = pd.read_csv(travel_clean_path)
print(f"读取完成，共 {len(travel_clean)} 行")

# 读取 venue_lookup 获取坐标
venue = pd.read_csv(venue_path)
valid_venue = venue[venue['venueType'].isin(['Apartment', 'Workplace', 'Restaurant', 'Pub'])]
id_to_x = dict(zip(valid_venue['venueId'], valid_venue['x']))
id_to_y = dict(zip(valid_venue['venueId'], valid_venue['y']))

# ============================================
# 2. OD 聚合统计
# ============================================
print("\n正在计算 OD 聚合...")
valid_od = travel_clean[
    travel_clean['start_x'].notna() & 
    travel_clean['end_x'].notna()
].copy()

od_counts = valid_od.groupby(['start_clean', 'end_clean']).size().reset_index(name='trip_count')
od_counts_sorted = od_counts.sort_values('trip_count', ascending=False)

print("\n最热门的20条OD路径：")
print(od_counts_sorted.head(20))

od_counts_sorted.to_csv(output_folder + "od_aggregated.csv", index=False)
print(f"OD聚合结果已保存到 {output_folder}od_aggregated.csv")

# ============================================
# 3. 生成带坐标的 OD 画图数据
# ============================================
print("\n正在生成画图数据...")
od_df = od_counts_sorted.copy()
od_df['start_x'] = od_df['start_clean'].map(id_to_x)
od_df['start_y'] = od_df['start_clean'].map(id_to_y)
od_df['end_x'] = od_df['end_clean'].map(id_to_x)
od_df['end_y'] = od_df['end_clean'].map(id_to_y)

od_clean_for_map = od_df.dropna(subset=['start_x', 'start_y', 'end_x', 'end_y'])
od_clean_for_map.to_csv(output_folder + "od_for_map.csv", index=False)
print(f"OD画图数据已保存到 {output_folder}od_for_map.csv，共 {len(od_clean_for_map)} 条OD对")

# ============================================
# 4. 小时热度统计
# ============================================
print("\n正在计算小时热度...")
hourly_counts = travel_clean['hour'].value_counts().sort_index().reset_index()
hourly_counts.columns = ['hour', 'trip_count']
hourly_counts.to_csv(output_folder + "hourly_heat.csv", index=False)
print("小时热度数据已保存")

print("\n各小时出行量统计：")
print(hourly_counts)

# ============================================
# 5. 可选：按目的统计
# ============================================
print("\n按出行目的统计：")
purpose_counts = travel_clean['purpose'].value_counts()
print(purpose_counts)

# ============================================
# 完成
# ============================================
print("\n✅ 全部完成！生成的文件：")
print(f"   - {output_folder}od_aggregated.csv")
print(f"   - {output_folder}od_for_map.csv")
print(f"   - {output_folder}hourly_heat.csv")