import pandas as pd

# 请修改为你的实际路径
travel_clean_path = "F:/数据可视化/数据整理交付包(1)/同学A_数据整理交付包/代码/travel_clean.csv"
output_path = "F:/数据可视化/数据整理交付包(1)/同学A_数据整理交付包/代码/od_with_hour.csv"

# 读取清洗后的出行数据
df = pd.read_csv(travel_clean_path)

# 只保留起点和终点都有效的记录
valid = df[df['start_x'].notna() & df['end_x'].notna()].copy()

# 按起点、终点、小时 三列聚合
od_hour = valid.groupby(['start_clean', 'end_clean', 'hour']).size().reset_index(name='trip_count')

# 合并坐标信息（从原始数据中取一组坐标即可）
coords = valid[['start_clean', 'start_x', 'start_y']].drop_duplicates(subset=['start_clean'])
od_hour = od_hour.merge(coords, on='start_clean', how='left')

coords_end = valid[['end_clean', 'end_x', 'end_y']].drop_duplicates(subset=['end_clean'])
od_hour = od_hour.merge(coords_end, on='end_clean', how='left')

# 保存
od_hour.to_csv(output_path, index=False)
print(f"已生成带 hour 的 OD 数据：{output_path}")
print(f"共 {len(od_hour)} 行")