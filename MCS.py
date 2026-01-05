import time

from core import Dan
from burn_cal import underwater_explosion_damage
import random
import numpy as np
from core import Dan


class MSC:
    def __init__(self):
        self.update_callback = None
        self.progress_callback = None
        self.min_callback_interval = 0.05
        # ship_L: float, 舰艇总长(m)
        # ship_M: float, 舰艇质量(kg)
        # ship_v: list or array - like, [vx0, vy0]
        # 舰艇速度(m / s)
        # ship_B: float, 舰宽(m)
        # ship_T: float, 吃水深度(m)
        self.ship_L = 315.7728
        self.ship_M = 78000000
        self.ship_B = 76.8096
        self.ship_T = 10.8966
        self.ship_x = [120, 0, 0]
        self.N_burn = 3
        self.ifship = 0
        self.ship_kind = 0
        # 最大加速度
        self.a_max = 2
        # 最大速度
        self.v_max = 46 / 3.6
        # no input
        self.dict_shipi = {'ship_L': 315.7728, 'ship_M': 78000000, 'ship_B': 76.8096, 'ship_T': 10.8966}

    def _change_data(self):
        dict1 = {'ship_L': 315.7728, 'ship_M': 78000000, 'ship_B': 76.8096, 'ship_T': 10.8966}
        # 萨拉托加
        dict2 = {'ship_L': 324.0024, 'ship_M': 78000000, 'ship_B': 76.8096, 'ship_T': 11.2776}
        # 游骑兵
        dict3 = {'ship_L': 318.8208, 'ship_M': 78000000, 'ship_B': 76.0476, 'ship_T': 11.2776}
        # 独立
        dict4 = {'ship_L': 318.8208, 'ship_M': 78000000, 'ship_B': 76.0476, 'ship_T': 11.2776}
        ships = [dict1, dict2, dict3, dict4]
        if self.ifship:
            self.dict_shipi = ships[self.ship_kind]
        else:
            self.dict_shipi = {'ship_L': self.ship_L, 'ship_M': self.ship_M, 'ship_B': self.ship_B, 'ship_T': self.ship_T}

    def burn_one(self):
        # for i in range(N):
        ship_x = self.ship_x
        Dani = Dan()
        dicti = self.dict_shipi
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
        a_max = self.a_max
        # 最大速度
        v_max = self.v_max
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

        damage_results = underwater_explosion_damage(ship_x_final1[0, :], dicti['ship_L'], dicti['ship_M'], ship_v,
                                                     dicti['ship_B'], dicti['ship_T'], dan_x_final1[0, :], Dani.total.m/5,
                                                     dan_v)
        P = damage_results['P_sink']
        return P

    def main(self):
        N = int(self.N_burn)
        Ps = []
        last_callback_time = time.time()
        for i in range(N):
            P = self.burn_one()
            Ps.append(P)
            print(P)
            current_time = time.time()
            if hasattr(self, 'update_callback') and current_time - last_callback_time > self.min_callback_interval:
                last_callback_time = current_time
                # ========== 进度回调 ==========
                if self.progress_callback:
                    self.progress_callback(i + 1, N)

                # ========== 实时数据准备 ==========
                if self.update_callback:
                    # 准备实时数据

                    data = {
                        'Pi': P,
                        'P_list': np.array(Ps)
                        }


                    # 调用回调函数
                    self.update_callback(data)


