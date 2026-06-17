import pandas as pd
import numpy as np

# 请把路径换成你电脑上的实际路径
travel_path = "F:\数据可视化\数据整理交付包(1)\同学A_数据整理交付包\代码/TravelJournal.csv"
venue_path = "F:\数据可视化\数据整理交付包(1)\同学A_数据整理交付包\代码/venue_lookup.csv"

# 只读必要的列，节省内存
travel = pd.read_csv(travel_path, 
                     usecols=['participantId', 'travelStartTime', 'travelStartLocationId',
                              'travelEndTime', 'travelEndLocationId', 'purpose'])
venue = pd.read_csv(venue_path)

print("TravelJournal 行数：", len(travel))
print("venue_lookup 行数：", len(venue))

# 把 travelStartLocationId 中的 NA 和 0 替换成 -1（表示 unknown）
travel['start_clean'] = travel['travelStartLocationId'].copy()

# 处理 NA（pandas 读入后通常变成 float 的 NaN）
travel.loc[travel['start_clean'].isna(), 'start_clean'] = -1

# 处理 0
travel.loc[travel['start_clean'] == 0, 'start_clean'] = -1

# 把 -1 转成整数类型
travel['start_clean'] = travel['start_clean'].astype(int)

# 同样处理终点
travel['end_clean'] = travel['travelEndLocationId'].copy()
travel.loc[travel['end_clean'] == 0, 'end_clean'] = -1
travel['end_clean'] = travel['end_clean'].astype(int)

print("起点未知数量：", (travel['start_clean'] == -1).sum())
print("终点未知数量：", (travel['end_clean'] == -1).sum())

# 准备两个坐标字典，方便快速映射
# 只取 venueType 为实际地点的（Apartment/Workplace/Restaurant/Pub）
valid_venue = venue[venue['venueType'].isin(['Apartment', 'Workplace', 'Restaurant', 'Pub'])]

# 建立 venueId -> x, y 的字典
id_to_x = dict(zip(valid_venue['venueId'], valid_venue['x']))
id_to_y = dict(zip(valid_venue['venueId'], valid_venue['y']))

# 添加起点坐标
travel['start_x'] = travel['start_clean'].map(id_to_x)
travel['start_y'] = travel['start_clean'].map(id_to_y)

# 添加终点坐标
travel['end_x'] = travel['end_clean'].map(id_to_x)
travel['end_y'] = travel['end_clean'].map(id_to_y)

# 检查有多少成功匹配
print("起点匹配成功数：", travel['start_x'].notna().sum())
print("终点匹配成功数：", travel['end_x'].notna().sum())

# 把 travelStartTime 转为 datetime
travel['start_dt'] = pd.to_datetime(travel['travelStartTime'], format='ISO8601', errors='coerce')
travel['hour'] = travel['start_dt'].dt.hour

# 看看小时分布
print(travel['hour'].value_counts().sort_index())

# 只保留后续分析需要的列
travel_clean = travel[['participantId', 'start_clean', 'end_clean', 
                       'start_x', 'start_y', 'end_x', 'end_y', 
                       'hour', 'purpose']].copy()

# 保存到新文件
output_path = "F:\数据可视化\数据整理交付包(1)\同学A_数据整理交付包\代码/travel_clean.csv"
travel_clean.to_csv(output_path, index=False)

print("清洗完成，已保存到：", output_path)

# 修正这一行 ✅
valid_count = (travel_clean['start_x'].notna() & travel_clean['end_x'].notna()).sum()
print("有效出行记录数（起点和终点都有坐标）：", valid_count)
