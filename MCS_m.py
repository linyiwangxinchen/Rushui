import time
from burn_cal import underwater_explosion_damage
import random
import numpy as np
from core_m import Dan


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
        self.ship_x = [500, 0, 0]
        self.v_ship_0 = [17, 0, 0]
        self.guidance_distance = 2000
        self.N_burn = 3
        self.ifship = 0
        self.ship_kind = 0
        # 最大加速度
        self.a_max = 2
        # 最大速度
        self.v_max = 46 / 3.6
        # no input
        self.dict_shipi = {'ship_L': 315.7728, 'ship_M': 78000000, 'ship_B': 76.8096, 'ship_T': 10.8966}
        self.model_data = None
        self.ifdian = None
        self.dian_L = None
        self.before_time = None
        self.before_L = None
        self.P = 0
        self.P_list = [0]
        self.point_dict = []


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
        if self.model_data is not None:
            # 设置参数
            model_data = self.model_data
            t0 = model_data['t0']
            tend = model_data['tend']
            dt = model_data['dt']
            v0 = model_data['v0']
            theta0 = model_data['theta0']
            psi0 = model_data['psi0']
            phi0 = model_data['phi0']
            alpha0 = model_data['alpha0']
            wx0 = model_data['wx0']
            wy0 = model_data['wy0']
            wz0 = model_data['wz0']
            k_wz = model_data['k_wz']
            k_theta = model_data['k_theta']
            k_ps = model_data['k_ps']
            k_ph = model_data['k_ph']
            k_wx = model_data['k_wx']
            k_wy = model_data['k_wy']
            kwz = model_data['kwz']
            ktheta = model_data['ktheta']
            tend_under = model_data['tend_under']

            # 几何与质量参数 (赋值到self.total命名空间)
            Dani.total.L = model_data['L']  # 长度 (m)
            Dani.total.S = model_data['S']  # 横截面积 (m²)
            Dani.total.V = model_data['V']  # 体积 (m³)
            Dani.total.m = model_data['m']  # 质量 (kg)
            Dani.total.xc = model_data['xc']  # 重心 x 坐标 (m)
            Dani.total.yc = model_data['yc']  # 重心 y 坐标 (m)
            Dani.total.zc = model_data['zc']  # 重心 z 坐标 (m)
            Dani.total.Jxx = model_data['Jxx']  # 转动惯量 Jxx (kg·m²)
            Dani.total.Jyy = model_data['Jyy']  # 转动惯量 Jyy (kg·m²)
            Dani.total.Jzz = model_data['Jzz']  # 转动惯量 Jzz (kg·m²)
            Dani.total.T = model_data['T']  # 推力 (N)

            # 空泡仿真参数 (直接赋值到实例)
            Dani.lk = model_data['lk']  # 空化器距重心距离 (m)
            Dani.rk = model_data['rk']  # 空化器半径 (m)
            Dani.sgm = model_data['sgm']  # 全局空化数
            Dani.dyc = model_data['dyc']  # 空泡轴线偏离 (m)

            # 水下物理几何参数 (直接赋值到实例)
            Dani.SGM = model_data['SGM']  # 水下空化数
            Dani.LW = model_data['LW']  # 水平鳍位置 (m)
            Dani.LH = model_data['LH']  # 垂直鳍位置 (m)

            # 舵机与角度限制参数 (需角度转弧度)
            RTD = Dani.RTD  # 获取弧度-角度转换因子 (180/π)

            # 角度类参数 (° -> rad)
            Dani.dkmax = model_data['dkmax'] / RTD  # 舵角上限 (rad)
            Dani.dkmin = model_data['dkmin'] / RTD  # 舵角下限 (rad)
            Dani.dk0 = model_data['dk0'] / RTD  # 舵角零位 (rad)
            Dani.ddmax = model_data['ddmax'] / RTD  # 最大深度变化率 (rad/s²)
            Dani.dvmax = model_data['dvmax'] / RTD  # 最大速度变化率 (rad/s²)
            Dani.dthetamax = model_data['dthetamax'] / RTD  # 最大俯仰角速率 (rad/s)
            Dani.wzmax = model_data['wzmax'] / RTD  # 最大偏航角速率 (rad/s)
            Dani.wxmax = model_data['wxmax'] / RTD  # 最大滚转角速率 (rad/s)
            Dani.dphimax = model_data['dphimax'] / RTD  # 最大滚转角加速度 (rad/s²)

            # 位移类参数 (直接赋值，单位m)
            Dani.deltaymax = model_data['deltaymax']  # 横向位移限制 (m)
            Dani.deltavymax = model_data['deltavymax']  # 垂向位移限制 (m)

            # 入水初始条件
            Dani.t0 = t0
            Dani.tend = tend
            Dani.dt = dt
            Dani.v0 = v0

            # ——————————入水参数—————————— (角度需转换为弧度)
            Dani.t0 = t0  # 起始时间 (s)
            Dani.tend = tend  # 终止时间 (s)
            Dani.dt = dt  # 仿真步长 (s)
            Dani.v0 = v0  # 入水速度 (m/s)
            Dani.theta0 = theta0 / RTD  # 弹道角 (rad)
            Dani.psi0 = psi0 / RTD  # 偏航角 (rad)
            Dani.phi0 = phi0 / RTD  # 横滚角 (rad)
            Dani.alpha0 = alpha0 / RTD  # 攻角 (rad)
            Dani.wx0 = wx0 / RTD  # 横滚角速度 (rad/s)
            Dani.wy0 = wy0 / RTD  # 偏航角速度 (rad/s)
            Dani.wz0 = wz0 / RTD  # 俯仰角速度 (rad/s)

            # ——————————基础控制参数—————————— (无量纲增益，直接赋值)
            # 注意：这些参数在Dan类中有独立用途
            Dani.k_wz = k_wz  # 偏航角速度增益
            Dani.k_theta = k_theta  # 俯仰角增益

            # ——————————深度控制参数—————————— (无量纲增益，直接赋值)
            # 与基础控制参数不同，这些用于水下控制律
            Dani.kps = k_ps  # 姿态同步增益 (对应kth)
            Dani.kph = k_ph  # 舵机响应增益
            Dani.kwx = k_wx  # 滚转角速度增益
            Dani.kwy = k_wy  # 垂向控制增益
            Dani.kwz = kwz  # 偏航角速度增益 (深度控制)
            Dani.kth = ktheta  # 俯仰角增益 (深度控制)

            # ——————————特殊关联参数——————————
            # Dan类中kps默认等于kth，但UI提供独立控制，此处显式同步
            Dani.kps = Dani.kth  # 确保姿态同步增益与俯仰增益一致
            Dani.tend_under = tend_under
            Dani.T1 = model_data['T1']
            Dani.T2 = model_data['T2']
            # 新增推力时间曲线
            time_str = model_data['time_sequence']
            thrust_str = model_data['thrust_sequence']
            time_data = [float(t.strip()) for t in time_str.split(',') if t.strip()]
            thrust_data = [float(t.strip()) for t in thrust_str.split(',') if t.strip()]
            Dani.time_sequence = time_data
            Dani.thrust_sequence = thrust_data

            if self.model_data['dan_type'] == 0:
                Dani.xb = np.array([0, 0, 1.3, 2.6, 2.6, 3.1, 3.1, 2.6, 2.6, 1.3, 0, 0])
                Dani.yb = np.array(
                    [0, 0.021, 0.1065, 0.1065, 0.08, 0.08, -0.08, -0.08, -0.1065, -0.1065, -0.021, 0])
                Dani.zb = Dani.yb
            elif self.model_data['dan_type'] == 1:
                Dani.xb = np.array([0, 0, 1.3, 2.6, 2.6, 3.1, 3.1, 2.6, 2.6, 1.3, 0, 0]) / 213 * 324
                Dani.yb = np.array(
                    [0, 0.021, 0.1065, 0.1065, 0.08, 0.08, -0.08, -0.08, -0.1065, -0.1065, -0.021, 0]) / 213 * 324
                Dani.zb = Dani.yb

            Dani.ship_x = self.ship_x
            Dani.v_ship_0 = self.v_ship_0
            Dani.v_max = self.v_max
            Dani.a_max = self.a_max
            Dani.guidance_distance = self.guidance_distance
            Dani._recalculate_update_input()
            Dani.update_callback = self.update_callback
        Dani.min_callback_interval = self.min_callback_interval
        dicti = self.dict_shipi
        randomi = random.random() * 2 - 1
        randomj = random.random() * 2 - 1
        Dani.theta0 = Dani.theta0 * (1 + 0.01 * randomi)
        Dani.v0 = Dani.v0 * (1 + 0.01 * randomj)
        Dani.P = self.P
        Dani.P_list = self.P_list

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
        v_ship_0 = self.v_ship_0
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

        ship_x_list = Dani.ship_x_list
        ship_v_list = Dani.ship_v_list


        self.ship_x_list = ship_x_list
        self.ship_v_list = ship_v_list
        self.dan_line = dan_line
        self.dan_v_list = dan_v_list
        self.dan_t = dan_t

        # 此时寻找弹体与舰艇最近的点,先计算距离
        distance = ship_x_list - dan_line
        distance_final = np.sqrt(np.sum(distance * distance, axis=1))

        # 取极小值
        distance_min = np.min(distance_final)
        if self.ifdian:
            if self.dian_L > distance_min:
                pos = -1  # 默认值（未找到）
                for i, val in enumerate(distance_final):
                    if val < self.dian_L:
                        pos = i
                        break  # 找到第一个后立即退出循环
                boomi = pos
            else:
                boomi = np.argmin(distance_final)
        else:
            boomi = np.argmin(distance_final)
        # 爆照点寻找

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
        # if P < 0.85:
        #     P = 0.85 + random.random() * 0.15
        return P

    def burn_two(self):

        return

    def main(self):
        N = int(self.N_burn)
        Ps = []
        last_callback_time = time.time()
        for i in range(N):
            P = self.burn_one()
            Ps.append(P)
            # print(P)
            self.P = P
            self.P_list = Ps
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
            dicti = {
                'ship_x_list': self.ship_x_list,
                'ship_v_list': self.ship_v_list,
                'dan_line': self.dan_line,
                'dan_v_list ': self.dan_v_list ,
                't_list': self.dan_t
            }
            self.point_dict.append(dicti)

if __name__ == '__main__':
    M = MSC()
    M.main()