from core import Dan
from burn_cal import underwater_explosion_damage
import random
import numpy as np

N = 10

# 不同舰艇
# 福莱斯特
dict1 = {'ship_L': 315.7728, 'ship_M': 78000000, 'ship_B': 76.8096, 'ship_T': 10.8966}
# 萨拉托加
dict2 = {'ship_L': 324.0024, 'ship_M': 78000000, 'ship_B': 76.8096, 'ship_T': 11.2776}
# 游骑兵
dict3 = {'ship_L': 318.8208, 'ship_M': 78000000, 'ship_B': 76.0476, 'ship_T': 11.2776}
# 独立
dict4 = {'ship_L': 318.8208, 'ship_M': 78000000, 'ship_B': 76.0476, 'ship_T': 11.2776}

# 46km/h max
# 目标船只
ship_x = [100, 0, 0]

# for i in range(N):
Dani = Dan()
dicti = dict1
randomi = random.random() * 2 - 1
randomj = random.random() * 2 - 1
Dani.theta0 = Dani.theta0 * (1 + 0.05 * randomi)
Dani.v0 = Dani.v0 * (1 + 0.05 * randomj)

t0, y0, t1, y1 = Dani.main()
# 整理弹道数据
t1 = t1[:, np.newaxis]
dan_line = np.vstack([y0[:, 9:12], y1[:, 9:12]])
dan_v_list = np.vstack([y0[:, 0:3], y1[:, 0:3]])
dan_t = np.vstack([t0, t1])
dan_final = dan_line[-1, 9:12]
dan_v = dan_line[-1, 0:3]
# 通过时间序列计算导弹
# 最大加速度
a_max = 2
# 最大速度
v_max = 46 / 3.6
# 初始速度
v_ship_0 = [0, 0, 0]
# 是否被发现概率
if_find = random.random() > (1 - 0.2)
if_find = 1
if if_find:
    # 被发现了
    # 策略设置随机加速度方向进行逃窜
    dt = dan_t[1] - dan_t[0]
    x = np.array([ship_x])
    v = np.array([v_ship_0])
    ship_x_list = x
    ship_v_list = v
    for i in range(len(dan_t) - 1):
        theta = random.random() * 2 * np.pi
        # 设立随机加速度方向进行逃窜
        a = a_max * np.array([np.cos(theta), np.sin(theta), 0])
        x = x + v * dt[0]
        v = v + a * dt[0]
        if np.linalg.norm(v) > v_max:
            v = v / np.linalg.norm(v) * v_max
        ship_x_list = np.vstack((ship_x_list, x[0, :]))
        ship_v_list = np.vstack((ship_v_list, v[0, :]))
else:
    # 要不就原地不动
    ship_x_list = np.zeros((len(dan_line), 3))

# 此时寻找弹体与舰艇最近的点,先计算距离
distance = ship_x_list - dan_line
distance_final = np.sqrt(np.sum(distance * distance, axis=1))

# 取极小值
distance_min = np.min(distance_final)
# 爆照点寻找
boomi = np.argmin(distance_final)

ship_x_final = ship_x_list[boomi, :]
dan_x_final = dan_line[boomi, :]

# 为了适配burn那边模型，调换一下y跟z
ship_x_final1 = np.array([[ship_x_final[0], ship_x_final[2], ship_x_final[1]]])
dan_x_final1 = np.array([[dan_x_final[0], dan_x_final[2], dan_x_final[1]]])

# 然后是v参数

if if_find:
    ship_v = ship_v_list[boomi, :]
else:
    # 要不就原地不动
    ship_v = np.array([[0, 0, 0]])

dan_v = dan_v_list[boomi, :]

damage_results = underwater_explosion_damage(ship_x_final1[0, :], dicti['ship_L'], dicti['ship_M'], ship_v, dicti['ship_B'], dicti['ship_T'], dan_x_final1[0, :], Dani.total.m, dan_v)

P = damage_results['P_sink']
