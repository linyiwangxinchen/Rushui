import bisect
import os
import time
# from tqdm import tqdm
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


class under:
    def __init__(self):
        self.plot_pao_down_y = None
        self.plot_pao_down_x = None
        self.plot_pao_up_y = None
        self.plot_pao_up_x = None
        self.plot_zhou_y = None
        self.plot_zhou_x = None
        self.plot_dan_y = None
        self.plot_dan_x = None
        self.update_callback = None
        self.progress_callback = None
        self.min_callback_interval = 0.05
        # 添加推力时间曲线
        self.time_sequence = None
        self.thrust_sequence = None
        """初始化所有仿真参数"""
        # 上面是预制参数
        self.start_tcs = True
        self.write1 = False
        self.dan_type = 213
        self.nc = 200
        self.dt = 0.0001
        self.tend = 3.41
        self.RTD = 180 / np.pi  # 弧度到角度转换
        RTD = self.RTD
        # === 输入参量 === #
        # case11 初始条件
        self.t0 = 0.539
        self.vx = 100.96949
        self.vy = -0.01323
        self.vz = -0.95246
        self.wx = 242.955 / RTD  # 单位：度
        self.wy = -42.435 / RTD
        self.wz = 56.515 / RTD
        self.theta = 0 / RTD  # 度
        self.psi = 0 / RTD
        self.phi = 6.84184 / RTD
        self.x0 = 27.82448
        self.y0 = -3.45
        self.z0 = 0.05623
        self.DK = -2.9377 / RTD  # 空化器舵角
        self.DS = 0.94986 / RTD  # 上直舵角
        self.DX = 0.94986 / RTD  # 下直舵角
        self.dkf = -2.50238 / RTD
        self.dsf = 0.38547 / RTD
        self.dxf = 0.30266 / RTD
        self.T1 = 25080.6  # 推力
        self.T2 = 6971.4
        self.TC = self.t0  # 空泡计算时刻


        # === 弹体总体相关参数 === #
        self.L = 3.195  # 总长
        self.S = 0.0356  # 最大横截面积
        self.V = 0  # 体积
        self.m = 114.7  # 重量
        self.xc = -0.0188  # 中心距前端距离
        self.yc = -0.0017
        self.zc = 0.0008
        self.Jxx = 0.63140684  # 转动惯量
        self.Jyy = 57.06970864
        self.Jzz = 57.07143674
        self.T1 = 25080.6
        self.T2 = 6971.4

        # === 物理常数 ===

        self.RHO = 998.2  # 水密度 (kg/m³)
        self.G = 9.81  # 重力加速度 (m/s²)

        # === 仿真控制参数 ===
        self.TP = 0.0  # 控制周期时间
        self.DK = 0.0  # 空化器舵角
        self.DS = 0.0  # 上舵舵角
        self.DX = 0.0  # 下舵舵角

        # === 物理几何参数 ===
        self.LK = 1.714  # 空化器位置 (m)
        self.RK = 0.021  # 空化器半径 (m)
        self.SGM = 0.018  # 空化数
        self.LW = 0.8856  # 水平鳍位置 (m)
        self.LH = 0.1405  # 垂直鳍位置 (m)
        self.q1 = 0
        self.q2 = 0

        # === 启控时刻参数 ===
        self.YCS = -3.45  # 启控深度 (m)
        self.THETACS = -2.5086 / self.RTD  # 启控俯仰角 (rad)
        self.VYCS = -0.01323  # 启控垂向速度 (m/s)
        self.PSICS = 2.17098 / self.RTD  # 启控偏航角 (rad)
        self.ZCS = 0
        self.VZCS = 0

        # === 动态数据数组 ===
        self.AF = np.zeros((80, 6))  # 空泡延迟历史数组
        self.INDEX = 0  # 当前索引
        self.TT = 0.0  # 上次记录时间

        # === 空泡数据 ===
        self.CAV = np.zeros((self.nc, 8))  # 空泡数据数组

        # 控制律参数
        RTD = self.RTD
        self.ddmax = 10 / RTD
        self.dvmax = 5 / RTD
        self.dkmax = 0 / RTD
        self.dkmin = -4 / RTD
        self.dk0 = -2.61917 / RTD
        self.deltaymax = 10
        self.deltavymax = 10
        self.dthetamax = 5 / RTD
        self.wzmax = 30 / RTD
        self.wxmax = 300 / RTD
        self.wymax = 30 / RTD
        self.dphimax = 60 / RTD
        self.kth = 4
        self.kps = self.kth
        self.kph = 0.08
        self.kwx = 0.0016562
        self.kwz = 0.312
        self.kwy = self.kwz
        # 初始条件
        self.y1_initial = np.array(
            [self.vx, self.vy, self.vz, self.wx, self.wy, self.wz, self.theta, self.psi, self.phi, self.x0, self.y0,
             self.z0, self.dkf, self.dsf, self.dxf])
        self.t0_initial = self.t0
        # 过程条件
        self.y = []
        # 流体动力部分
        self.CxS = 0
        self.mxdd = 0
        self.mxwx = 0
        self.Cya = 0
        self.Cydc = 0
        self.Cywz = 0
        self.mza = 0
        self.mzdc = 0
        self.mzwz = 0
        self.Czb = -self.Cya
        self.Czdv = 0
        self.Czwy = -self.Cywz
        self.myb = self.mza
        self.mydv = 0
        self.mywy = self.mzwz
        self.n11 = 0
        self.n22 = 0
        self.n26 = 0
        self.n44 = 0
        self.n66 = 0
        self.fluid = np.array(
            [self.CxS, self.mxdd, self.mxwx, self.Cya, self.Cydc, self.Cywz, self.mza, self.mzdc, self.mzwz,
             self.Czb, self.Czdv, self.Czwy, self.myb, self.mydv, self.mywy, self.n11, self.n22, self.n44, self.n66,
             self.n26])
        self.ts = None
        self.dydt = None
        self.Mxw = None
        self.Mzw = None
        self.Myw = None
        self.Zw = None
        self.Yw = None
        self.Xw = None
        self.Mxv = None
        self.Mxc = None
        self.Myd = None
        self.Myu = None
        self.Zd = None
        self.Zu = None
        self.Xd = None
        self.Xu = None
        self.Mxh = None
        self.Mzr = None
        self.Mzl = None
        self.Yr = None
        self.Yl = None
        self.Xr = None
        self.Xl = None
        self.alphat = None
        self.Mzb = None
        self.Myb = None
        self.Mxb = None
        self.Zb = None
        self.Yb = None
        self.Xb = None
        self.cf = None
        self.sf = None
        self.cp = None
        self.sp = None
        self.ct = None
        self.st = None
        self.Cb0 = None
        self.vkn = None
        self.vzn = None
        self.vyn = None
        self.vxn = None
        self.Mzk = None
        self.Myk = None
        self.Mxk = None
        self.Zk = None
        self.Yk = None
        self.Xk = None
        self.t = None
        self.zb1 = None
        self.yb1 = None
        self.zb = None
        self.yb = None
        self.xb = None
        self.dk = None
        self.dx = None
        self.ds = None
        self.XT = None
        self.dJzz = None
        self.dJyy = None
        self.dJxx = None
        self.dxc = None
        self.dm = None

    def initialize_simulation(self):
        """初始化仿真环境"""
        # 清空记录文件
        files_to_delete = ['cavity.txt', 'test-ts.txt', 'rudder.txt']
        for file in files_to_delete:
            if os.path.exists(file):
                os.remove(file)

        # print("仿真环境初始化完成")

    def set_initial_conditions(self):
        """设置初始条件"""
        RTD = self.RTD

        # # case11 初始条件
        # t0 = 0.539
        # vx = 100.96949
        # vy = -0.01323
        # vz = -0.95246
        # wx = 242.955 / RTD  # 单位：度
        # wy = -42.435 / RTD
        # wz = 56.515 / RTD
        # theta = 0 / RTD  # 度
        # psi = 0 / RTD
        # phi = 6.84184 / RTD
        # x0 = 27.82448
        # y0 = -3.45
        # z0 = 0.05623
        # DK = -2.9377 / RTD  # 空化器舵角
        # DS = 0.94986 / RTD  # 上直舵角
        # DX = 0.94986 / RTD  # 下直舵角
        # dkf = -2.50238 / RTD
        # dsf = 0.38547 / RTD
        # dxf = 0.30266 / RTD
        # T1 = 25080.6  # 推力
        # T2 = 6971.4
        # TC = t0  # 空泡计算时刻
        #
        # # case11 初始条件
        # self.t0 = t0
        # self.vx = vx
        # self.vy = vy
        # self.vz = vz
        # self.wx = wx
        # self.wy = wy
        # self.wz = wz
        # self.theta = theta
        # self.psi = psi
        # self.phi = phi
        # self.x0 = x0
        # self.y0 = y0
        # self.z0 = z0
        # self.DK = DK
        # self.DS = DS
        # self.DX = DX
        # self.dkf = dkf
        # self.dsf = dsf
        # self.dxf = dxf
        # self.T1 = T1
        # self.T2 = T2
        # self.TC = TC

        # 初始状态向量
        y1 = np.array([self.vx, self.vy, self.vz, self.wx, self.wy, self.wz, self.theta, self.psi, self.phi, self.x0, self.y0, self.z0, self.dkf, self.dsf, self.dxf])
        self.y1_initial = y1
        self.t0_initial = self.t0

    def update_initial_conditions(self):
        """
        更新t0跟y1
        :return:
        """
        # 初始状态向量
        y1 = np.array(
            [self.vx, self.vy, self.vz, self.wx, self.wy, self.wz, self.theta, self.psi, self.phi, self.x0, self.y0,
             self.z0, self.dkf, self.dsf, self.dxf])
        self.y1_initial = y1
        self.t0_initial = self.t0

    def get_thrust(self, t, time_sequence, thrust_sequence, tol=1e-9):
        """
        根据时间t获取对应的推力值。

        参数:
        t (float): 需要查询的时间点
        time_sequence (list): 时间序列，必须是递增的
        thrust_sequence (list): 推力序列，与时间序列一一对应
        tol (float): 浮点数比较的容差，默认1e-9

        返回:
        float: 对应的推力值
        """
        # 检查边界：t 小于最小值或大于最大值（考虑容差）
        if t < time_sequence[0] - tol or t > time_sequence[-1] + tol:
            return 0.0

        # 调整t到有效范围[min, max]（处理浮点误差）
        if t < time_sequence[0]:
            t = time_sequence[0]
        if t > time_sequence[-1]:
            t = time_sequence[-1]

        # 使用二分查找定位t的插入位置
        index = bisect.bisect_left(time_sequence, t)

        # 检查是否精确匹配（考虑容差）
        if index < len(time_sequence) and abs(time_sequence[index] - t) < tol:
            return thrust_sequence[index]
        if index > 0 and abs(time_sequence[index - 1] - t) < tol:
            return thrust_sequence[index - 1]

        # 线性插值（index一定在1到len(time_sequence)-1之间）
        t0 = time_sequence[index - 1]
        t1 = time_sequence[index]
        f0 = thrust_sequence[index - 1]
        f1 = thrust_sequence[index]

        # 防止除零错误（理论上时间序列应严格递增）
        if abs(t1 - t0) < tol:
            return (f0 + f1) / 2.0

        # 线性插值公式
        thrust = f0 + (f1 - f0) * (t - t0) / (t1 - t0)
        return thrust

    def control_main(self):
        # 获取当前总体参数

        L = self.L
        S = self.S
        V = self.V
        m = self.m
        xc = self.xc
        yc = self.yc
        zc = self.zc
        Jxx = self.Jxx
        Jyy = self.Jyy
        Jzz = self.Jzz
        T1 = self.T1
        T2 = self.T2
        # 传入ty状态
        t = self.t
        y = self.y
        # 传入这组
        dkmin = self.dkmin
        dkmax = self.dkmax
        ddmax = self.ddmax
        deltaymax = self.deltaymax
        deltavymax = self.deltavymax
        dthetamax = self.dthetamax
        wzmax = self.wzmax
        dk0 = self.dk0
        kth = self.kth
        kwz = self.kwz
        dphimax = self.dphimax
        kwz = self.kwz
        wxmax = self.wxmax
        kph = self.kph
        kwx = self.kwx
        dvmax = self.dvmax
        RK = self.RK

        RTD = self.RTD

        # 获取当前运动参数
        vx = y[0]
        vy = y[1]
        vz = y[2]
        wx = y[3]
        wy = y[4]
        wz = y[5]
        theta = y[6]
        psi = y[7]
        phi = y[8]
        x0 = y[9]
        y0 = y[10]
        z0 = y[11]

        # 求当前速度，攻角和侧滑角
        v = np.sqrt(vx ** 2 + vy ** 2 + vz ** 2)
        alpha = np.arctan(-vy / vx) if vx != 0 else 0
        beta = np.arctan(vz / np.sqrt(vx ** 2 + vy ** 2)) if (vx ** 2 + vy ** 2) != 0 else 0

        # # 手动设置轮廓
        # xb = np.array([0, 0, 1.3, 2.6, 2.6, 3.1, 3.1, 2.6, 2.6, 1.3, 0, 0])
        # yb = np.array([0, 0.021, 0.1065, 0.1065, 0.08, 0.08, -0.08, -0.08, -0.1065, -0.1065, -0.021, 0])
        # zb = np.zeros_like(yb)
        #
        # # 俯视图轮廓
        # yb1 = np.zeros_like(yb)
        # zb1 = np.array([0, 0.021, 0.1065, 0.1065, 0.08, 0.08, -0.08, -0.08, -0.1065, -0.1065, -0.021, 0])
        # xb = 1.714 - xb

        # 解包总体参数
        # 解包个毛线

        # 变质量参数插值表
        # q = np.loadtxt('m_interp.txt')

        q = np.array([
            [0, 114.7, 1732.8, 0.63140684, 57.06970864, 57.07143674],
            [0.16, 112.9, 1731.3, 0.623028517, 56.86812779, 56.86986447],
            [0.33, 111.0, 1729.9, 0.614895781, 56.70818405, 56.70993049],
            [0.5, 109.1, 1728.3, 0.614895781, 56.70818405, 56.70993049],
            [1, 106.7, 1728.4, 0.599187271, 56.51460737, 56.51638155],
            [1.5, 105.5, 1729.2, 0.594861404, 56.51679073, 56.51857965],
            [2, 102.9, 1730.0, 0.589807777, 56.63981389, 56.64161743],
            [2.2, 102.3, 1729.9, 0.588325129, 56.6960952, 56.69789811],
            [2.32, 101.9, 1729.8, 0.587503208, 56.72565175, 56.72745457],
            [2.5, 101.8, 1730.6, 0.587415814, 56.64950294, 56.65132087],
            [3, 101.7, 1731.4, 0.587333997, 56.57321447, 56.57504787],
            [3.6, 101.6, 1732.4, 0.587238036, 56.48086209, 56.4827153],
            [3.61, 101.6, 1732.4, 0.587236388, 56.47912611, 56.48097931]
        ])
        # 插值获取当前时刻的参数
        m = np.interp(t, q[:, 0], q[:, 1])
        xc_interp = np.interp(t, q[:, 0], q[:, 2])
        xc = 1.714 - 0.001 * xc_interp
        Jxx = np.interp(t, q[:, 0], q[:, 3])
        Jyy = np.interp(t, q[:, 0], q[:, 4])
        Jzz = np.interp(t, q[:, 0], q[:, 5])

        # 计算变质量引起的导数（数值微分）
        dt = 0.1
        m_prev = np.interp(t - dt, q[:, 0], q[:, 1])
        xc_prev = 1.714 - 0.001 * np.interp(t - dt, q[:, 0], q[:, 2])
        Jxx_prev = np.interp(t - dt, q[:, 0], q[:, 3])
        Jyy_prev = np.interp(t - dt, q[:, 0], q[:, 4])
        Jzz_prev = np.interp(t - dt, q[:, 0], q[:, 5])

        dm = (m - m_prev) / dt
        dxc = 0.001 * np.interp(t, q[:, 0], q[:, 2]) / dt - 0.001 * np.interp(t - dt, q[:, 0], q[:, 2]) / dt
        dJxx = (Jxx - Jxx_prev) / dt
        dJyy = (Jyy - Jyy_prev) / dt
        dJzz = (Jzz - Jzz_prev) / dt
        if self.time_sequence is not None:
            XT = self.get_thrust(t, self.time_sequence, self.thrust_sequence, tol=1e-9)
        else:
            # 计算发动机推力
            if t < 0.56:
                XT = T1
            elif t < 100:
                XT = T2
            else:
                XT = 0

        # 控制律参数

        # 获取当前舵角
        dkf = y[12]
        dsf = y[13]
        dxf = y[14]

        # 舵角限幅
        dkf = np.clip(dkf, dkmin, dkmax)
        dsf = np.sign(dsf) * min(abs(dsf), ddmax)
        dxf = np.sign(dxf) * min(abs(dxf), ddmax)

        # 控制律
        cc = 0.001  # 控制周期
        tcs = 0.36  # 启控时间
        tcs = 0.002
        YCS = self.YCS
        VYCS = self.VYCS
        THETACS = self.THETACS
        PSICS = self.PSICS
        ZCS = self.ZCS
        VZCS = self.VZCS

        # 在启控时间之前记录初始条件
        if tcs - 0.001 <= t <= tcs:
            YCS = y0
            ZCS = z0
            THETACS = theta
            PHICS = phi
            VYCS = vy
            VZCS = vz
            PSICS = psi

        # 控制周期判断
        if (t - self.TP) >= cc and t > tcs:
            # --------------俯仰通道控制--------------
            if self.start_tcs:
                self.start_tcs = False
                self.h0_start = YCS
                self.t0_start = t

            h1 = (-2.5 - self.h0_start) / (3 - self.t0_start) * (
                        t - self.t0_start) + self.h0_start
            h0 = -2.5
            if h1 < h0:
                h0 = (h0 + h1) / 2
            else:
                h0 = h0

            # 深度偏差
            deltay = h0 + (YCS - h0) * np.exp(-(t - tcs) / 0.2) - y0
            deltay = np.sign(deltay) * min(abs(deltay), deltaymax)

            # 垂向速度偏差
            deltavy = (VYCS - 0) * np.exp(-(t - tcs) / 0.2) - vy
            deltavy = np.sign(deltavy) * min(abs(deltavy), deltavymax)

            # 俯仰角控制目标
            thetac = ((THETACS * RTD - 0.084743) * np.exp(-(t - tcs) / 0.2) + 0.084743 +
                      (0.02 * deltay + 0.003 * deltavy) * RTD) / RTD
            dtheta = theta - thetac
            dtheta = np.sign(dtheta) * min(abs(dtheta), dthetamax)

            # 俯仰角速度限幅
            wz = np.sign(wz) * min(abs(wz), wzmax)

            # 因为dk符号定义的是反的，所以式子里的符号也与控制率中的符号相反
            dk = dk0 + kth * dtheta + kwz * wz
            dk = np.clip(dk, dkmin, dkmax)

            # --------------偏航通道（简化）--------------
            h0 = 0
            # 深度偏差
            deltaz = h0 + (ZCS - h0) * np.exp(-(t - tcs) / 0.2) - z0
            deltaz = np.sign(deltaz) * min(abs(deltaz), deltaymax)

            # 垂向速度偏差
            deltavz = (VZCS - 0) * np.exp(-(t - tcs) / 0.2) - vz
            deltavz = np.sign(deltavz) * min(abs(deltavz), deltavymax)

            # 俯仰角控制目标
            psic = ((PSICS * RTD ) * np.exp(-(t - tcs) / 0.2) +
                      (0.02 * deltaz + 0.003 * deltavz) * RTD) / RTD
            psic = -psic
            dpsi = psi - psic
            dpsi = np.sign(dpsi) * min(abs(dpsi), dthetamax)

            dv = 0
            # los_psi = 0
            # dpsi = psi - los_psi
            dpsi = dpsi
            wy = np.sign(wy) * min(abs(wy), self.wymax)
            dv = self.kps * dpsi + self.kwy * wy
            # dv = dv / 2
            dv = np.sign(dv) * min(abs(dv), dvmax)

            # --------------横滚通道--------------
            if t < 1.5:
                phic = 0 / RTD
            elif t < 2:
                phic = (t - 1.5) / 0.5 * 12 * (psi - PSICS)
            else:
                phic = 12 * (psi - PSICS)

            # 横滚偏差限幅
            dphi = phi - phic
            dphi = np.sign(phi) * min(abs(dphi), dphimax)

            # 横滚角速度限幅
            wx = np.sign(wx) * min(abs(wx), wxmax)

            dd = kph * dphi + kwx * wx
            dd = np.sign(dd) * min(abs(dd), ddmax)

            # --------------舵角分配--------------
            ds = dd + dv
            dx = -dd + dv
            if abs(ds) >= dvmax or abs(dx) >= dvmax:
                ds = dd
                dx = -dd
            ds = np.sign(ds) * min(abs(ds), dvmax)
            dx = np.sign(dx) * min(abs(dx), dvmax)

            self.TP = t  # 更新时间
            if self.write1:
                # 保存舵角历史
                with open('rudder.txt', 'a') as f:
                    f.write(f'{t:8.3f} {dk * RTD:8.6f} {ds * RTD:8.6f} {dx * RTD:8.6f} '
                            f'{dkf * RTD:8.6f} {dsf * RTD:8.6f} {dxf * RTD:8.6f}\n')
                    f.close()

            y[0], y[1], y[2] = vx, vy, vz
            y[3], y[4], y[5] = wx, wy, wz
            # 获取当前舵角
            y[12], y[13], y[14] = dkf, dsf, dxf

            self.ds = ds
            self.dx = dx
            self.dk = dk
        else:
            dk = self.dk
            ds = self.ds
            dx = self.dx
        self.m = m
        self.xc = xc
        self.dm = dm
        self.dxc = dxc
        self.dJxx = dJxx
        self.dJyy = dJyy
        self.dJzz = dJzz
        self.Jxx = Jxx
        self.Jyy = Jyy
        self.Jzz = Jzz
        self.vx = vx
        self.vy = vy
        self.vz = vz
        self.wx = wx
        self.wy = wy
        self.wz = wz
        self.XT = XT
        self.dkf = dkf
        self.ds = ds
        self.dx = dx
        self.dk = dk
        # self.xb = xb
        # self.yb = yb
        # self.zb = zb
        # self.yb1 = yb1
        # self.zb1 = zb1
        self.y = y

    def initialize_cavity(self, x0: float, y0: float, z0: float, vx: float):
        """初始化空泡数据"""
        RK = self.RK
        SGM = self.SGM
        CAV = self.CAV
        LK = self.LK

        # 计算最大空泡直径和半长
        rc = RK * np.sqrt(0.82 * (1 + SGM) / SGM)
        Lc = RK / SGM * (1.92 - 3 * SGM)

        # 初始化空泡中心线
        for i in range(self.nc):
            CAV[i, 0] = x0 + LK - vx * i * 0.001  # x坐标
            CAV[i, 1] = 0 + y0  # y坐标
            CAV[i, 2] = 0 + z0  # z坐标
            CAV[i, 3] = vx  # x方向速度
            CAV[i, 4] = 0  # y方向速度
            CAV[i, 5] = 0  # z方向速度
            CAV[i, 6] = 0  # 空化器舵角
            CAV[i, 7] = RK  # 初始半径

        # 计算空泡半径分布
        for i in range(1, self.nc):
            # 计算空泡中心弧线长
            length = 0
            for j in range(1, i + 1):
                dlen = np.sqrt((CAV[j, 0] - CAV[j - 1, 0]) ** 2 +
                               (CAV[j, 1] - CAV[j - 1, 1]) ** 2 +
                               (CAV[j, 2] - CAV[j - 1, 2]) ** 2)
                length += dlen

            # 根据弧长求空泡半径
            if length < 2 * Lc:
                CAV[i, 7] = rc * np.sqrt(1 - (1 - RK ** 2 / rc ** 2) * (1 - length / Lc) ** 2)
            else:
                CAV[i, 7] = 0
        self.CAV = CAV

    def get_fluid_parameters(self):
        """获取流体动力参数"""
        self.fluid = np.array(
            [self.CxS, self.mxdd, self.mxwx, self.Cya, self.Cydc, self.Cywz, self.mza, self.mzdc, self.mzwz,
             self.Czb, self.Czdv, self.Czwy, self.myb, self.mydv, self.mywy, self.n11, self.n22, self.n44, self.n66,
             self.n26])

    # 空化器流体动力计算
    def cav_fluid_dynamics(self):
        y = self.y
        dkmin = self.dkmin
        dkmax = self.dkmax
        ddmax = self.ddmax
        RK = self.RK
        LK = self.LK
        RHO = self.RHO
        SGM = self.SGM

        vx, vy, vz = y[0], y[1], y[2]
        wx, wy, wz = y[3], y[4], y[5]
        # 获取当前舵角
        dkf, dsf, dxf = y[12], y[13], y[14]

        # 舵角限幅
        dkf = np.clip(dkf, dkmin, dkmax)
        dsf = np.sign(dsf) * min(abs(dsf), ddmax)
        dxf = np.sign(dxf) * min(abs(dxf), ddmax)

        Sk = np.pi * RK ** 2

        vxn = vx
        vyn = vy + wz * LK
        vzn = vz - wy * LK

        vkn = vxn * np.cos(dkf) + vyn * np.sin(dkf)
        Fkn = 0.5 * RHO * Sk * vkn * vkn * 0.81 * (1 + SGM)

        Xk = -Fkn * np.cos(dkf)
        Yk = -Fkn * np.sin(dkf)
        Zk = 0
        Mxk = 0
        Myk = 0
        Mzk = Yk * LK
        self.Xk = Xk
        self.Yk = Yk
        self.Zk = Zk
        self.Mxk = Mxk
        self.Myk = Myk
        self.Mzk = Mzk
        self.vxn = vxn
        self.vyn = vyn
        self.vzn = vzn
        self.vkn = vkn

    # 坐标转换矩阵Cb0
    def coordinate_transformation_matrix(self):
        y = self.y
        theta = y[6]
        psi = y[7]
        phi = y[8]

        # 求转换矩阵：弹体坐标系到地面系
        st = np.sin(theta)
        ct = np.cos(theta)
        sp = np.sin(psi)
        cp = np.cos(psi)
        sf = np.sin(phi)
        cf = np.cos(phi)

        Cb0 = np.array([
            [cp * ct, sp * sf - cp * st * cf, sp * cf + cp * st * sf],
            [st, ct * cf, -ct * sf],
            [-sp * ct, cp * sf + sp * st * cf, cp * cf - sp * st * sf]
        ])
        self.Cb0 = Cb0
        self.st = st
        self.ct = ct
        self.sp = sp
        self.cp = cp
        self.sf = sf
        self.cf = cf

    def coordinate_transformation_matrix1(self):
        y = self.y
        theta = y[6]
        psi = y[7]
        phi = y[8]
        phi = 0
        # 求转换矩阵：弹体坐标系到地面系
        st = np.sin(theta)
        ct = np.cos(theta)
        sp = np.sin(psi)
        cp = np.cos(psi)
        sf = np.sin(phi)
        cf = np.cos(phi)

        Cb0 = np.array([
            [cp * ct, sp * sf - cp * st * cf, sp * cf + cp * st * sf],
            [st, ct * cf, -ct * sf],
            [-sp * ct, cp * sf + sp * st * cf, cp * cf - sp * st * sf]
        ])
        return Cb0

    # 主体部分尾部流体动力
    def tail_fluid_dynamics(self):
        t = self.t
        y = self.y
        dk = self.dk
        xb = self.xb
        yb = self.yb
        zb = self.zb
        yb1 = self.yb1
        zb1 = self.zb1
        cav = self.CAV
        RTD = self.RTD
        AF = self.AF
        RHO = self.RHO

        x0 = y[9]
        y0 = y[10]
        z0 = y[11]

        vx, vy, vz = y[0], y[1], y[2]
        wx, wy, wz = y[3], y[4], y[5]
        # 获取当前舵角
        dkf, dsf, dxf = y[12], y[13], y[14]

        # 坐标转换矩阵
        self.coordinate_transformation_matrix()
        Cb0 = self.Cb0

        # 获取空化器计算部分的头部空化器速度
        # Xk, Yk, Zk, Mxk, Myk, Mzk, vxn, vyn, vzn, vkn = cav_fluid_dynamics(y)
        self.cav_fluid_dynamics()
        Xk = self.Xk
        Yk = self.Yk
        Zk = self.Zk
        Mxk = self.Mxk
        Myk = self.Myk
        Mzk = self.Mzk
        vxn = self.vxn
        vyn = self.vyn
        vzn = self.vzn
        vkn = self.vkn
        sgm = self.SGM
        RK = self.RK
        SGM = self.SGM
        CAV = self.CAV
        # 根据空化数sgm选择不同的数据表
        if sgm == 0.018:
            # 压心位置数据表
            LB = np.array([
                [0, -0.888715589],
                [0.2, -0.888715589],
                [0.4, -0.888715589],
                [0.6, -0.888715589],
                [0.8, -0.794879884],
                [1, -0.691390921],
                [1.2, -0.56538264],
                [1.4, -0.400689192],
                [1.6, -0.245959325],
                [1.8, -0.150503863],
                [2, -0.119468313]
            ])

            # 主体流体动力系数数据表
            body = np.array([
                [0, 0.00648664, 0.0, 0.0],
                [0.2, 0.00703303, 0.00002729, -0.00005534],
                [0.4, 0.00902638, 0.00214563, -0.00077554],
                [0.6, 0.01470039, 0.03542293, -0.00985318],
                [0.8, 0.02462379, 0.06930548, -0.01724242],
                [1, 0.03186021, 0.0862397, -0.01866208],
                [1.2, 0.02855741, 0.09014268, -0.01595152],
                [1.4, 0.02735502, 0.08726014, -0.01094341],
                [1.6, 0.02822194, 0.08664883, -0.00667045],
                [1.8, 0.03041468, 0.09212615, -0.0043397],
                [2, 0.03355466, 0.10477325, -0.00391771]
            ])

        elif sgm == 0.019:
            LB = np.array([
                [0, -0.9054127],
                [0.2, -0.9054127],
                [0.4, -0.9054127],
                [0.6, -0.7990140],
                [0.8, -0.7162796],
                [1, -0.6200311],
                [1.2, -0.5110901],
                [1.4, -0.3944276],
                [1.6, -0.2889765],
                [1.8, -0.2142775],
                [2, -0.1612079]
            ])

            body = np.array([
                [0, 0.0086270, 0.0000001, 0.0000000],
                [0.2, 0.0095434, 0.0009200, -0.0003638],
                [0.4, 0.0132049, 0.0322201, -0.0091307],
                [0.6, 0.0212162, 0.0746834, -0.0186770],
                [0.8, 0.0325073, 0.0913916, -0.0204889],
                [1, 0.0355440, 0.1014105, -0.0196800],
                [1.2, 0.0323854, 0.1057335, -0.0169137],
                [1.4, 0.0310978, 0.1061294, -0.0131018],
                [1.6, 0.0318736, 0.1080314, -0.0097711],
                [1.8, 0.0340612, 0.1142207, -0.0076604],
                [2, 0.0368472, 0.1223518, -0.0061734]
            ])

        elif sgm == 0.020:
            LB = np.array([
                [0, -0.887694983],
                [0.2, -0.887694983],
                [0.4, -0.796295977],
                [0.6, -0.709613605],
                [0.8, -0.642608025],
                [1, -0.559284638],
                [1.2, -0.464593657],
                [1.4, -0.371573007],
                [1.6, -0.288537818],
                [1.8, -0.223046325],
                [2, -0.171991758]
            ])

            body = np.array([
                [0, 0.01200363, 0.0, -0.0],
                [0.2, 0.01393804, 0.04361421, -0.01211772],
                [0.4, 0.02009684, 0.08072377, -0.02011894],
                [0.6, 0.02927145, 0.0950447, -0.02110955],
                [0.8, 0.03865464, 0.10579733, -0.02127894],
                [1, 0.03918332, 0.11291399, -0.01976559],
                [1.2, 0.03618071, 0.11757286, -0.01709659],
                [1.4, 0.03479942, 0.11986755, -0.01394039],
                [1.6, 0.03542791, 0.12299171, -0.01110728],
                [1.8, 0.0373765, 0.12851503, -0.00897177],
                [2, 0.0402012, 0.13631452, -0.00733802]
            ])

        elif sgm == 0.021:
            LB = np.array([
                [0, -0.4318652],
                [0.2, -0.4318652],
                [0.4, -0.4968312],
                [0.6, -0.5260267],
                [0.8, -0.4683127],
                [1, -0.4109909],
                [1.2, -0.3575775],
                [1.4, -0.3108350],
                [1.6, -0.2703418],
                [1.8, -0.2178498],
                [2, -0.1713181]
            ])

            body = np.array([
                [0, 0.0243732, 0.0000433, -0.0000045],
                [0.2, 0.0258971, 0.0218634, -0.0029553],
                [0.4, 0.0314730, 0.0545303, -0.0084796],
                [0.6, 0.0402960, 0.0936242, -0.0154144],
                [0.8, 0.0466153, 0.1052103, -0.0154214],
                [1, 0.0448134, 0.1144782, -0.0147260],
                [1.2, 0.0414554, 0.1222708, -0.0136843],
                [1.4, 0.0395850, 0.1294602, -0.0125949],
                [1.6, 0.0396826, 0.1365728, -0.0115560],
                [1.8, 0.0413185, 0.1425834, -0.0097220],
                [2, 0.0436638, 0.1489929, -0.0079891]
            ])

        elif sgm == 0.022:
            LB = np.array([
                [0, -0.007754],
                [0.2, -0.007754],
                [0.4, -0.0170056],
                [0.6, -0.0270397],
                [0.8, -0.0670453],
                [1, -0.1580194],
                [1.2, -0.2262599],
                [1.4, -0.1941195],
                [1.6, -0.1756203],
                [1.8, -0.1539224],
                [2, -0.1384483]
            ])

            body = np.array([
                [0, 0.0346309, 0, 0],
                [0.2, 0.0369621, 0.0122254, -0.0000297],
                [0.4, 0.0420597, 0.0263295, -0.0001401],
                [0.6, 0.0509281, 0.0411018, -0.0003479],
                [0.8, 0.0538747, 0.0599916, -0.0012589],
                [1, 0.0504538, 0.0871154, -0.0043086],
                [1.2, 0.0476519, 0.1202393, -0.008515],
                [1.4, 0.0454046, 0.1295667, -0.0078721],
                [1.6, 0.044733, 0.1389089, -0.0076354],
                [1.8, 0.0458425, 0.1481371, -0.0071367],
                [2, 0.047596, 0.1575861, -0.0068287]
            ])

        elif sgm == 0.023:
            LB = np.array([
                [0, 0.1725053],
                [0.2, 0.1725053],
                [0.4, 0.2039690],
                [0.6, 0.2392094],
                [0.8, 0.2631872],
                [1, 0.2717560],
                [1.2, 0.2569413],
                [1.4, 0.1883151],
                [1.6, 0.0094348],
                [1.8, -0.0564503],
                [2, -0.0539028]
            ])

            body = np.array([
                [0, 0.0438250, 0.0000205, 0.0000029],
                [0.2, 0.0470332, 0.0109256, 0.0005899],
                [0.4, 0.0525684, 0.0228126, 0.0014564],
                [0.6, 0.0591106, 0.0346104, 0.0025913],
                [0.8, 0.0602795, 0.0459192, 0.0037826],
                [1, 0.0568287, 0.0575654, 0.0048963],
                [1.2, 0.0537185, 0.0702885, 0.0056526],
                [1.4, 0.0515615, 0.0878303, 0.0051768],
                [1.6, 0.0505473, 0.1246099, 0.0003680],
                [1.8, 0.0512451, 0.1478025, -0.0026114],
                [2, 0.0523496, 0.1585242, -0.0026745]
            ])

        elif sgm == 0.024:
            LB = np.array([
                [0, 0.3431864],
                [0.2, 0.3431864],
                [0.4, 0.3384479],
                [0.6, 0.3904278],
                [0.8, 0.4295729],
                [1, 0.453357],
                [1.2, 0.4608763],
                [1.4, 0.4466269],
                [1.6, 0.4102494],
                [1.8, 0.3210683],
                [2, 0.1702677]
            ])

            body = np.array([
                [0, 0.0532393, 0, 0],
                [0.2, 0.0557941, 0.0105671, 0.0011351],
                [0.4, 0.0629577, 0.0216205, 0.0022903],
                [0.6, 0.0665592, 0.0321875, 0.0039333],
                [0.8, 0.066144, 0.0418096, 0.0056214],
                [1, 0.0629529, 0.0516273, 0.0073257],
                [1.2, 0.0598997, 0.0617001, 0.0089002],
                [1.4, 0.0575832, 0.0727787, 0.0101737],
                [1.6, 0.0566674, 0.0851889, 0.0109386],
                [1.8, 0.0563475, 0.1028389, 0.0103344],
                [2, 0.0570239, 0.1327563, 0.0070748]
            ])

        # 计算最大空泡直径和半长
        rc = RK * np.sqrt(0.82 * (1 + SGM) / SGM)
        Lc = RK / SGM * (1.92 - 3 * SGM)

        # 计算空化器在地面系坐标
        dlk = Cb0 @ np.array([self.LK, 0, 0])
        xn = x0 + dlk[0]
        yn = y0 + dlk[1]
        zn = z0 + dlk[2]

        # 初始化空泡轮廓数组
        cav0 = np.zeros((len(CAV), 3))  # 用来存空泡轴线坐标

        # 可能是上半部分和下半部分
        cav1 = np.zeros((len(CAV), 3))  # 前视图上面空泡的坐标
        cav2 = np.zeros((len(CAV), 3))  # 前视图下面空泡的坐标

        cav3 = np.zeros((len(CAV), 3))  # 俯视图上面空泡的坐标
        cav4 = np.zeros((len(CAV), 3))  # 俯视图下面空泡的坐标

        # 空泡计算（简化版本）
        if (t - self.TC) >= 0.001:
            # 更新空泡数组
            # 数组元素一次后移一位，相当于更新空泡的绝对状态值
            for i in range(self.nc - 1, 0, -1):
                # 上一刻的值往下移。符合独立膨胀原理的规律
                # 空泡先扩张后收缩，后部的空泡重复前端坐标空泡的扩张收缩行为
                CAV[i] = CAV[i - 1]

            # 插入新数据
            # 在数组首位插入当前空化器中心位置、速度、空泡半径
            # xn yn zn vxn vyn vzn dk(空化器舵角) rk(空化器半径)
            CAV[0, :] = [xn, yn, zn, vxn, vyn, vzn, dk, RK]

            # 更新上一步时间
            self.TC = t

            # 刷新空泡直径
            for i in range(1, self.nc):  # 相当于MATLAB的i=2:200，注意索引调整
                # 计算空泡中心弧线长
                # 最简单的两点（三维）之间求直线距离
                length = 0.0

                for j in range(1, i + 1):  # 相当于MATLAB的j=2:i，注意索引调整
                    # 计算相邻两点间的距离
                    dlen = np.sqrt(
                        (CAV[j, 0] - CAV[j - 1, 0]) ** 2 +
                        (CAV[j, 1] - CAV[j - 1, 1]) ** 2 +
                        (CAV[j, 2] - CAV[j - 1, 2]) ** 2
                    )
                    length += dlen

                # 根据弧长求空泡半径
                if length < 2 * Lc:
                    # 参考公式2.87 - Logvinovich空泡截面独立膨胀原理
                    CAV[i, 7] = rc * np.sqrt(1 - (1 - RK ** 2 / rc ** 2) * (1 - length / Lc) ** 2)
                else:
                    CAV[i, 7] = 0.0  # 空泡已闭合

            # 保存空泡数据
            if self.write1:
                with open('cavity.txt', 'a') as f:
                    f.write(f'{t:5.3f} {x0:8.3f} {y0:8.3f} {z0:8.3f} '
                            f'{xn:8.3f} {yn:8.3f} {zn:8.3f} {RK:8.3f}\n')
                    f.close()

            # 获取弹体位置 - 从弹体系转到地系
            Cb1 = self.coordinate_transformation_matrix1()
            posb = Cb1 @ np.vstack([xb, yb, zb])
            posb1 = Cb1 @ np.vstack([xb, yb1, zb1])

            # 将空泡轴线坐标转化为雷体坐标系下
            for j in range(len(CAV)):
                cav0[j, 0] = CAV[j, 0] - x0  # x坐标
                cav0[j, 1] = CAV[j, 1] - y0  # y坐标
                cav0[j, 2] = CAV[j, 2] - z0  # z坐标

            # 坐标转换：地面系 -> 弹体系
            p = Cb1.T @ cav0[:, 0:3].T
            cav0 = p.T

            # 前视图和俯视图轮廓计算
            for j in range(self.nc - 1):  # 相当于MATLAB的j=1:199
                # 前视图计算
                if j == 0:  # 第一个点
                    angle = CAV[j, 6]  # 空泡截面与弹体纵切面的夹角（舵角）
                else:
                    # 计算角度
                    dy = cav0[j, 1] - cav0[j + 1, 1]
                    dx = cav0[j, 0] - cav0[j + 1, 0]
                    angle = np.arctan2(dy, dx) if dx != 0 else 0  # 这是一整句话，防止除零错误：当dx=0时（垂直线），避免直接除法导致的错误

                # 前视图上空泡轮廓
                cav1[j, 0] = cav0[j, 0] - CAV[j, 7] * np.sin(angle)
                cav1[j, 1] = cav0[j, 1] + CAV[j, 7] * np.cos(angle) * np.cos(CAV[j, 6])
                cav1[j, 2] = 0

                # 前视图下空泡轮廓
                cav2[j, 0] = cav0[j, 0] + CAV[j, 7] * np.sin(angle)
                cav2[j, 1] = cav0[j, 1] - CAV[j, 7] * np.cos(angle) * np.cos(CAV[j, 6])
                cav2[j, 2] = 0

                # 俯视图计算
                if j == 0:  # 第一个点
                    angle_z = 0
                else:
                    # 计算俯视图角度
                    dz = cav0[j, 2] - cav0[j + 1, 2]
                    dx_z = cav0[j, 0] - cav0[j + 1, 0]
                    angle_z = np.arctan2(dz, dx_z) if dx_z != 0 else 0

                # 俯视图上空泡轮廓
                cav3[j, 0] = cav0[j, 0] + CAV[j, 7] * np.sin(angle_z)
                cav3[j, 2] = cav0[j, 2] - CAV[j, 7] * np.cos(angle_z)
                cav3[j, 1] = 0

                # 俯视图下空泡轮廓
                cav4[j, 0] = cav0[j, 0] - CAV[j, 7] * np.sin(angle_z)
                cav4[j, 2] = cav0[j, 2] + CAV[j, 7] * np.cos(angle_z)
                cav4[j, 1] = 0

            # 由弹体坐标系转回地面系
            cav0 = (Cb1 @ cav0.T).T
            cav1 = (Cb1 @ cav1.T).T
            cav2 = (Cb1 @ cav2.T).T
            cav3 = (Cb1 @ cav3.T).T
            cav4 = (Cb1 @ cav4.T).T

            # 准备绘图数据
            self.plot_dan_x = posb[0, :]
            self.plot_dan_y = posb[1, :]
            self.plot_zhou_x = cav0[:, 0]
            self.plot_zhou_y = cav0[:, 1]
            self.plot_pao_up_x = cav1[:, 0]
            self.plot_pao_up_y = cav1[:, 1]
            self.plot_pao_down_x = cav2[:, 0]
            self.plot_pao_down_y = cav2[:, 1]
            aaaa = 1



            # 创建图形
            # plt.figure(figsize=(12, 10))
            # 前视图（y-z平面投影）
            # plt.subplot(2, 1, 1)
            # 绘制弹体轮廓
            # plt.plot(posb[0, :], posb[1, :], 'b-', linewidth=2, label='Body')
            # 绘制空泡轴线
            # plt.plot(cav0[:, 0], cav0[:, 1], 'k-', linewidth=1, label='Cavity Axis')
            # 绘制空泡轮廓（上半部分）
            # plt.plot(cav1[:, 0], cav1[:, 1], 'r--', linewidth=1, label='Upper Cavity')
            # 绘制空泡轮廓（下半部分）
            # plt.plot(cav2[:, 0], cav2[:, 1], 'r--', linewidth=1, label='Lower Cavity')

            # plt.grid(True)
            # plt.axis('equal')
            # plt.xlim([-3, 3])
            # plt.ylim([-0.5, 0.5])
            # plt.xlabel('x/m')
            # plt.ylabel('y/m')
            # plt.title(f'Front View')
            # plt.legend()

            # # 俯视图（x-z平面投影）
            # plt.subplot(2, 1, 2)
            #
            # # 绘制弹体轮廓（俯视图）
            # plt.plot(posb1[0, :], posb1[2, :], 'b-', linewidth=2, label='Body')
            #
            # # 绘制空泡轴线
            # plt.plot(cav0[:, 0], cav0[:, 2], 'k-', linewidth=1, label='Cavity Axis')
            #
            # # 绘制空泡轮廓（左侧）
            # plt.plot(cav3[:, 0], cav3[:, 2], 'g--', linewidth=1, label='Left Cavity')
            #
            # # 绘制空泡轮廓（右侧）
            # plt.plot(cav4[:, 0], cav4[:, 2], 'g--', linewidth=1, label='Right Cavity')
            #
            # plt.grid(True)
            # plt.axis('equal')
            # plt.xlim([-3, 3])
            # plt.ylim([-0.5, 0.5])
            # plt.xlabel('x/m')
            # plt.ylabel('z/m')
            # plt.title('Top View')
            # plt.legend()
            #
            # # 反转y轴方向（模仿MATLAB的set(gca,'YDir','reverse')）
            # plt.gca().invert_yaxis()
            #
            # plt.tight_layout()
            # plt.show()

            # print(f"Time: {t:.3f}")

        # 将空泡轴线坐标转化到雷体坐标系下

        for j in range(len(cav)):
            cav0[j, 0] = cav[j, 0] - x0  # x坐标转换
            cav0[j, 1] = cav[j, 1] - y0  # y坐标转换
            cav0[j, 2] = cav[j, 2] - z0  # z坐标转换

        # 坐标转换：地面系 -> 雷体系
        p = Cb0.T @ cav0[:, 0:3].T
        cav0 = p.T

        # 计算总冲角（转换为角度）
        v_mag = np.sqrt(vx ** 2 + vy ** 2 + vz ** 2)
        if v_mag > 0 and vx > 0:
            alphat = np.arccos(vx / v_mag) * RTD
        else:
            alphat = 0

        # 插值求尾部流体动力压心
        if abs(alphat) > 2:
            lb = LB[-1, 1]  # 使用最后一个值
        else:
            # 压心距浮心的距离
            lb = np.interp(abs(alphat), LB[:, 0], LB[:, 1])

        # 查询尾部压心所在位置空泡轴线上的区间
        j = 1  # Python索引从0开始，所以j=1对应MATLAB的j=2
        while j < len(cav0) - 1 and cav0[j, 0] > lb:
            j += 1
            if j >= len(cav0):
                j = len(cav0) - 1
                break

        # 压心处的当地攻角（考虑旋转阻尼力）
        vx_rot = vx
        vy_rot = vy + wz * lb
        vz_rot = vz - wy * lb
        v_rot_mag = np.sqrt(vx_rot ** 2 + vy_rot ** 2 + vz_rot ** 2)

        if v_rot_mag > 0 and vx_rot > 0:
            alphat = np.arccos(vx_rot / v_rot_mag) * RTD
        else:
            alphat = 0

        alphay = alphat

        # 根据攻角插值流体动力系数
        a = np.zeros(3)
        if abs(alphay) < 2:
            a[0] = np.interp(abs(alphay), body[:, 0], body[:, 1])
            a[1] = np.interp(abs(alphay), body[:, 0], body[:, 2])
            a[2] = np.interp(abs(alphay), body[:, 0], body[:, 3])
        else:
            a[0] = body[-1, 1]
            a[1] = body[-1, 2]
            a[2] = body[-1, 3]

        # 空泡延迟算法
        if t - self.TT > 0.001:
            AF[self.INDEX, 0] = t
            AF[self.INDEX, 1] = a[0]  # cx
            AF[self.INDEX, 2] = a[1]  # cy
            AF[self.INDEX, 3] = a[2]  # mz
            AF[self.INDEX, 4] = np.sign(vy)
            AF[self.INDEX, 5] = np.sign(vz)

            self.INDEX += 1

            if self.INDEX >= 80:
                self.INDEX = 0

            self.TT = t

        # 取得t - 0.01时刻的流体动力（延迟效应）
        getindex1 = self.INDEX - 10  # cx的延时
        getindex2 = self.INDEX - 10  # cy的延时
        getindex3 = self.INDEX - 10  # mz的延时
        getindex4 = self.INDEX - 10  # vy符号
        getindex5 = self.INDEX - 10  # vz符号

        # 处理循环索引
        if getindex1 < 0:
            getindex1 += 80
        if getindex2 < 0:
            getindex2 += 80
        if getindex3 < 0:
            getindex3 += 80
        if getindex4 < 0:
            getindex4 += 80
        if getindex5 < 0:
            getindex5 += 80

        # 获取延迟的流体动力系数
        cxb = AF[getindex1, 1]
        cyb = AF[getindex2, 2]
        mzb = AF[getindex3, 3]
        vy_flag = AF[getindex4, 4]
        vz_flag = AF[getindex5, 5]

        # L, S, V, m, xc, yc, zc, Jxx, Jyy, Jzz, T1, T2 = get_total_parameters()

        L = self.L
        S = self.S
        V = self.V
        m = self.m
        xc = self.xc
        yc = self.yc
        zc = self.zc
        Jxx = self.Jxx
        Jyy = self.Jyy
        Jzz = self.Jzz
        T1 = self.T1
        T2 = self.T2

        # 计算流体动力和力矩
        q1 = 0.5 * RHO * S * (vx ** 2 + vy ** 2 + vz ** 2)
        self.q1 = q1

        q2 = q1 * L
        self.q2 = q2
        speed_2d = np.sqrt(vy ** 2 + vz ** 2)

        X = -cxb * q1
        Y = cyb * q1
        Mz = mzb * q2
        Mxb = 0
        Xb = X

        # 根据速度方向分配力和力矩
        if abs(vy) <= 0.001 and abs(vz) <= 0.001:
            Yb = 0
            Zb = 0
            Mzb = 0
            Myb = 0
        else:
            Yb = -vy_flag * Y * abs(vy) / speed_2d
            Zb = -vz_flag * Y * abs(vz) / speed_2d
            Mzb = -vy_flag * Mz * abs(vy) / speed_2d
            Myb = vz_flag * Mz * abs(vz) / speed_2d

        # 保存结果到文件
        if self.write1:
            with open('test-ts.txt', 'a') as fid:
                fid.write(f'{t:8.4f} {alphat:8.6f} {Xb:8.6f} {Yb:8.6f} {Zb:8.6f} {Myb:8.6f} {Mzb:8.6f}\n')
                fid.close()

        self.Xb = Xb
        self.Yb = Yb
        self.Zb = Zb
        self.Mxb = Mxb
        self.Myb = Myb
        self.Mzb = Mzb
        self.alphat = alphat
        self.alphay = alphay

    def fin_fluid_dynamics(self):
        y = self.y
        sgm = self.SGM
        LH = self.LH
        LW = self.LW
        RTD = self.RTD

        vx, vy, vz = y[0], y[1], y[2]
        wx, wy, wz = y[3], y[4], y[5]
        # 获取当前舵角
        dkf, dsf, dxf = y[12], y[13], y[14]
        if sgm == 0.018:
            # alpha cx cy mz
            hd = np.array([
                [0, 0.00161083, 0.0000015, -0.00000042],
                [0.2, 0.00163044, 0.00039107, -0.00010838],
                [0.4, 0.00168229, 0.00082013, -0.00022725],
                [0.6, 0.00183933, 0.00157407, -0.00043609],
                [0.8, 0.00245313, 0.00644634, -0.00178571],
                [1, 0.00249219, 0.00667577, -0.00184904],
                [1.2, 0.00254161, 0.00688571, -0.00190709],
                [1.4, 0.00254948, 0.00670023, -0.00185584],
                [1.6, 0.00239953, 0.0058042, -0.00160824],
                [1.8, 0.00222231, 0.00532342, -0.00147505],
                [2, 0.00238052, 0.00759514, -0.00210448]
            ])

        elif sgm == 0.019:
            hd = np.array([
                [0, 0.0019178, 0.0000015, -0.0000004],
                [0.2, 0.0019237, 0.0005131, -0.0001422],
                [0.4, 0.0020296, 0.0012676, -0.0003512],
                [0.6, 0.0025162, 0.0058601, -0.0016232],
                [0.8, 0.0025325, 0.0060345, -0.0016713],
                [1, 0.0025786, 0.0063310, -0.0017533],
                [1.2, 0.0025785, 0.0064949, -0.0017987],
                [1.4, 0.0025482, 0.0067833, -0.0018786],
                [1.6, 0.0025250, 0.0075009, -0.0020776],
                [1.8, 0.0025012, 0.0080730, -0.0022363],
                [2, 0.0024909, 0.0085178, -0.0023595]
            ])

        elif sgm == 0.020:
            hd = np.array([
                [0, 0.00223223, 0.00000238, -0.00000066],
                [0.2, 0.00259815, 0.00250833, -0.00069499],
                [0.4, 0.00261777, 0.00475789, -0.00131764],
                [0.6, 0.00261378, 0.00498263, -0.00137982],
                [0.8, 0.00262810, 0.00545741, -0.00151125],
                [1, 0.00263856, 0.00588964, -0.00163089],
                [1.2, 0.00260397, 0.00615421, -0.00170415],
                [1.4, 0.00255742, 0.00666578, -0.00184600],
                [1.6, 0.00253317, 0.00747779, -0.00207109],
                [1.8, 0.00251940, 0.00815456, -0.00225871],
                [2, 0.00251540, 0.00861100, -0.00238523]
            ])

        elif sgm == 0.021:
            hd = np.array([
                [0, 0.0027032, 0.0000057, -0.0000016],
                [0.2, 0.0027115, 0.0011845, -0.0003281],
                [0.4, 0.0027174, 0.0025328, -0.0007014],
                [0.6, 0.0026805, 0.0041273, -0.0011429],
                [0.8, 0.0026872, 0.0048242, -0.0013358],
                [1, 0.0026713, 0.0053396, -0.0014785],
                [1.2, 0.0026266, 0.0057998, -0.0016060],
                [1.4, 0.0025760, 0.0065188, -0.0018052],
                [1.6, 0.0025503, 0.0073286, -0.0020297],
                [1.8, 0.0025371, 0.0080756, -0.0022367],
                [2, 0.0025353, 0.0086181, -0.0023871]
            ])

        elif sgm == 0.022:
            hd = np.array([
                [0, 0.0026964, 0.0000047, -0.0000013],
                [0.2, 0.0026976, 0.0007525, -0.0002085],
                [0.4, 0.0027194, 0.001481, -0.0004102],
                [0.6, 0.0027406, 0.0022153, -0.0006135],
                [0.8, 0.002757, 0.0030744, -0.0008513],
                [1, 0.0027299, 0.004152, -0.0011497],
                [1.2, 0.0026477, 0.0054881, -0.0015197],
                [1.4, 0.0026107, 0.0062932, -0.0017426],
                [1.6, 0.0025758, 0.0071871, -0.0019904],
                [1.8, 0.0025586, 0.0079707, -0.0022076],
                [2, 0.0025543, 0.0085844, -0.0023777]
            ])

        elif sgm == 0.023:
            hd = np.array([
                [0, 0.0027057, 0.0000045, -0.0000013],
                [0.2, 0.0027053, 0.0006717, -0.0001861],
                [0.4, 0.0027259, 0.0012970, -0.0003592],
                [0.6, 0.0027435, 0.0019002, -0.0005262],
                [0.8, 0.0027473, 0.0024792, -0.0006865],
                [1, 0.0027414, 0.0031161, -0.0008628],
                [1.2, 0.0027136, 0.0038238, -0.0010588],
                [1.4, 0.0027003, 0.0047880, -0.0013258],
                [1.6, 0.0026365, 0.0066625, -0.0018449],
                [1.8, 0.0025849, 0.0077789, -0.0021544],
                [2, 0.0025711, 0.0084879, -0.0023509]
            ])

        elif sgm == 0.024:
            hd = np.array([
                [0, 0.0027153, 0.0000045, -0.0000013],
                [0.2, 0.0027211, 0.0006296, -0.0001744],
                [0.4, 0.0027319, 0.0012146, -0.0003364],
                [0.6, 0.0027422, 0.0017721, -0.0004908],
                [0.8, 0.0027376, 0.0023253, -0.0006439],
                [1, 0.0027340, 0.0028838, -0.0007986],
                [1.2, 0.0027132, 0.0035248, -0.0009760],
                [1.4, 0.0027105, 0.0042521, -0.0011774],
                [1.6, 0.0027089, 0.0050395, -0.0013954],
                [1.8, 0.0027052, 0.0060256, -0.0016685],
                [2, 0.0026410, 0.0076822, -0.0021275]
            ])

        # 计算水平鳍攻角
        alpha_w = -np.arctan((vy - wz * LW) / vx) * RTD

        # 初始化结果数组
        f1 = np.zeros(3)

        # 根据攻角插值流体动力系数
        if abs(alpha_w) > 2:
            # 超出插值范围，使用边界值
            f1[0] = hd[-1, 1]  # cx
            f1[1:3] = np.sign(alpha_w) * hd[-1, 2:4]  # cy, mz
        else:
            # 在插值范围内，使用插值
            f1[0] = np.interp(abs(alpha_w), hd[:, 0], hd[:, 1])  # cx
            cy_val = np.interp(abs(alpha_w), hd[:, 0], hd[:, 2])  # cy
            mz_val = np.interp(abs(alpha_w), hd[:, 0], hd[:, 3])  # mz
            f1[1:3] = np.sign(alpha_w) * np.array([cy_val, mz_val])

        # 提取系数
        cxl = f1[0]  # 阻力系数
        cyl = f1[1]  # 升力系数
        mzl = f1[2]  # 俯仰力矩系数

        # 计算水平鳍的力和力矩
        q1 = self.q1
        q2 = self.q2
        Xl = -cxl * q1  # x方向力（阻力）
        Yl = cyl * q1  # y方向力（升力）
        Mzl = mzl * q2  # z方向力矩（俯仰）

        # 左右对称，假设左右鳍相同
        Xr = Xl  # 右鳍x方向力
        Yr = Yl  # 右鳍y方向力
        Mzr = Mzl  # 右鳍z方向力矩

        # 计算水平鳍横滚阻尼力矩
        alpha_wx = (wx * LH / np.sqrt(vx ** 2 + vy ** 2 + vz ** 2)) * RTD

        # 插值横滚阻尼系数
        if abs(alpha_wx) < 2:
            # 在插值范围内
            cyh = np.sign(alpha_wx) * np.interp(abs(alpha_wx), hd[:, 0], hd[:, 2])
        else:
            # 超出范围，使用边界值
            cyh = np.sign(alpha_wx) * hd[-1, 2]

        # 计算横滚阻尼力和力矩
        Yh = cyh * q1  # 横滚阻尼力
        Mxh = -2 * Yh * LH  # 横滚阻尼力矩（考虑左右对称）

        self.Xl = Xl
        self.Xr = Xr
        self.Yl = Yl
        self.Yr = Yr
        self.Mzl = Mzl
        self.Mzr = Mzr
        self.Mxh = Mxh

    # 垂直舵流体动力
    def rudder_fluid_dynamics(self):
        t = self.t
        y = self.y
        alphat = self.alphat
        sgm = self.SGM
        RTD = self.RTD
        vx, vy, vz = y[0], y[1], y[2]
        wx, wy, wz = y[3], y[4], y[5]
        # 获取当前舵角
        dkf, dsf, dxf = y[12], y[13], y[14]
        # 根据空化数选择数据表
        if sgm == 0.018:
            vd = np.array([
                [0, 0.00040979, 0.00000064, 0.00000018],
                [2, 0.00045006, -0.00039732, -0.00011027],
                [4, 0.00051598, -0.00082802, -0.00022965],
                [6, 0.00060714, -0.00119779, -0.00033234],
                [8, 0.00074187, -0.00156466, -0.00043413],
                [10, 0.00089884, -0.00187144, -0.00051927],
                [12, 0.00108484, -0.00213801, -0.00059321],
                [14, 0.00129264, -0.00239678, -0.00066497]
            ])

            R = np.array([
                [-2.0, 1.0000, 0.0000],
                [-1.8, 1.0000, 0.0000],
                [-1.6, 1.0000, 0.0000],
                [-1.4, 1.0000, 0.0000],
                [-1.2, 1.0000, 0.0000],
                [-1.0, 1.0000, 0.0000],
                [-0.8, 1.0000, 0.0000],
                [-0.6, 1.0000, 0.0000],
                [-0.4, 0.9695, 0.2969],
                [-0.2, 0.7578, 0.4597],
                [0.0, 0.6694, 0.6694],
                [0.2, 0.4597, 0.7578],
                [0.4, 0.2969, 0.9896],
                [0.6, 0.0000, 1.0000],
                [0.8, 0.0000, 1.0000],
                [1.0, 0.0000, 1.0000],
                [1.2, 0.0000, 1.0000],
                [1.4, 0.0000, 1.0000],
                [1.6, 0.0000, 1.0000],
                [1.8, 0.0000, 1.0000],
                [2.0, 0.0000, 1.0000]
            ])  # 第二三列分别为上下舵的沾湿比

        elif sgm == 0.019:
            vd = np.array([
                [0, 0.00066922, -0.00000209, -0.00000058],
                [2, 0.00070412, -0.00059310, -0.00016442],
                [4, 0.00079160, -0.00123258, -0.00034167],
                [6, 0.00091293, -0.00178905, -0.00049602],
                [8, 0.00109122, -0.00238625, -0.00066167],
                [10, 0.00131018, -0.00278902, -0.00077340],
                [12, 0.00155818, -0.00312824, -0.00086743],
                [14, 0.00183668, -0.00345120, -0.00095699]
            ])

            R = np.array([
                [-2.0, 1.0000, 0.0000],
                [-1.8, 1.0000, 0.0000],
                [-1.6, 1.0000, 0.0000],
                [-1.4, 1.0000, 0.0000],
                [-1.2, 1.0000, 0.0000],
                [-1.0, 1.0000, 0.0000],
                [-0.8, 1.0000, 0.0000],
                [-0.6, 1.0000, 0.1032],
                [-0.4, 1.0000, 0.3065],
                [-0.2, 0.8968, 0.5806],
                [0.0, 0.7422, 0.7422],
                [0.2, 0.5806, 0.8968],
                [0.4, 0.3065, 1.0000],
                [0.6, 0.1032, 1.0000],
                [0.8, 0.0000, 1.0000],
                [1.0, 0.0000, 1.0000],
                [1.2, 0.0000, 1.0000],
                [1.4, 0.0000, 1.0000],
                [1.6, 0.0000, 1.0000],
                [1.8, 0.0000, 1.0000],
                [2.0, 0.0000, 1.0000]
            ])  # 第二三列分别为上下舵的沾湿比

        elif sgm == 0.020:
            vd = np.array([
                [0, 0.00095126, -0.00000182, -0.00000050],
                [2, 0.00099690, -0.00085900, -0.00023799],
                [4, 0.00111092, -0.00176325, -0.00048851],
                [6, 0.00127093, -0.00262819, -0.00072827],
                [8, 0.00151954, -0.00346207, -0.00095965],
                [10, 0.00183335, -0.00399313, -0.00110686],
                [12, 0.00218979, -0.00448420, -0.00124295],
                [14, 0.00257236, -0.00491780, -0.00136317]
            ])

            R = np.array([
                [-2.0, 1.0000, 0.0000],
                [-1.8, 1.0000, 0.0000],
                [-1.6, 1.0000, 0.0000],
                [-1.4, 1.0000, 0.0645],
                [-1.2, 1.0000, 0.1613],
                [-1.0, 1.0000, 0.2063],
                [-0.8, 1.0000, 0.3175],
                [-0.6, 1.0000, 0.4344],
                [-0.4, 1.0000, 0.6111],
                [-0.2, 1.0000, 0.7661],
                [0.0, 0.8226, 0.8226],
                [0.2, 0.7661, 1.0000],
                [0.4, 0.6111, 1.0000],
                [0.6, 0.4344, 1.0000],
                [0.8, 0.3175, 1.0000],
                [1.0, 0.2063, 1.0000],
                [1.2, 0.1613, 1.0000],
                [1.4, 0.0645, 1.0000],
                [1.6, 0.0000, 1.0000],
                [1.8, 0.0000, 1.0000],
                [2.0, 0.0000, 1.0000]
            ])  # 第二三列分别为上下舵的沾湿比

        elif sgm == 0.021:
            vd = np.array([
                [0, 0.00139009, 0.00000166, 0.00000046],
                [2, 0.00144613, -0.00136992, -0.00037938],
                [4, 0.00157663, -0.00276866, -0.00076670],
                [6, 0.00176028, -0.00427105, -0.00118323],
                [8, 0.00204629, -0.00487045, -0.00134950],
                [10, 0.00237099, -0.00529175, -0.00146625],
                [12, 0.00272686, -0.00567973, -0.00157380],
                [14, 0.00311100, -0.00602298, -0.00166901]
            ])

            R = np.array([
                [-2.0, 1.0000, 0.0000],
                [-1.8, 1.0000, 0.0000],
                [-1.6, 1.0000, 0.0000],
                [-1.4, 1.0000, 0.0000],
                [-1.2, 1.0000, 0.0000],
                [-1.0, 1.0000, 0.1048],
                [-0.8, 1.0000, 0.3871],
                [-0.6, 1.0000, 0.6290],
                [-0.4, 1.0000, 1.0000],
                [-0.2, 1.0000, 1.0000],
                [0.0, 1.0000, 1.0000],
                [0.2, 1.0000, 1.0000],
                [0.4, 1.0000, 1.0000],
                [0.6, 0.6290, 1.0000],
                [0.8, 0.3871, 1.0000],
                [1.0, 0.1048, 1.0000],
                [1.2, 0.0000, 1.0000],
                [1.4, 0.0000, 1.0000],
                [1.6, 0.0000, 1.0000],
                [1.8, 0.0000, 1.0000],
                [2.0, 0.0000, 1.0000]
            ])  # 第二三列分别为上下舵的沾湿比

        elif sgm == 0.022:
            vd = np.array([
                [0, 0.00139010, 0.00000170, 0.00000050],
                [2, 0.00144610, -0.00136990, -0.00037940],
                [4, 0.00157660, -0.00276870, -0.00076670],
                [6, 0.00176030, -0.00427110, -0.00118320],
                [8, 0.00204630, -0.00487050, -0.00134950],
                [10, 0.00237100, -0.00529180, -0.00146630],
                [12, 0.00272690, -0.00567970, -0.00157380],
                [14, 0.00311100, -0.00602300, -0.00166900]
            ])

            R = np.array([
                [-2.0, 1.0000, 0.0000],
                [-1.8, 1.0000, 0.0000],
                [-1.6, 1.0000, 0.0000],
                [-1.4, 1.0000, 0.1256],
                [-1.2, 1.0000, 0.4016],
                [-1.0, 1.0000, 1.0000],
                [-0.8, 1.0000, 1.0000],
                [-0.6, 1.0000, 1.0000],
                [-0.4, 1.0000, 1.0000],
                [-0.2, 1.0000, 1.0000],
                [0.0, 1.0000, 1.0000],
                [0.2, 1.0000, 1.0000],
                [0.4, 1.0000, 1.0000],
                [0.6, 1.0000, 1.0000],
                [0.8, 1.0000, 1.0000],
                [1.0, 1.0000, 1.0000],
                [1.2, 0.4016, 1.0000],
                [1.4, 0.1256, 1.0000],
                [1.6, 0.0000, 1.0000],
                [1.8, 0.0000, 1.0000],
                [2.0, 0.0000, 1.0000]
            ])  # 第二三列分别为上下舵的沾湿比

        elif sgm == 0.023:
            vd = np.array([
                [0, 0.00139009, 0.00000166, 0.00000046],
                [2, 0.00144613, -0.00136992, -0.00037938],
                [4, 0.00157663, -0.00276866, -0.00076670],
                [6, 0.00176028, -0.00427105, -0.00118323],
                [8, 0.00204629, -0.00487045, -0.00134950],
                [10, 0.00237099, -0.00529175, -0.00146625],
                [12, 0.00272686, -0.00567973, -0.00157380],
                [14, 0.00311100, -0.00602298, -0.00166901]
            ])

            R = np.array([
                [-2.0, 1.0000, 0.2581],
                [-1.8, 1.0000, 0.4286],
                [-1.6, 1.0000, 0.9215],
                [-1.4, 1.0000, 1.0000],
                [-1.2, 1.0000, 1.0000],
                [-1.0, 1.0000, 1.0000],
                [-0.8, 1.0000, 1.0000],
                [-0.6, 1.0000, 1.0000],
                [-0.4, 1.0000, 1.0000],
                [-0.2, 1.0000, 1.0000],
                [0.0, 1.0000, 1.0000],
                [0.2, 1.0000, 1.0000],
                [0.4, 1.0000, 1.0000],
                [0.6, 1.0000, 1.0000],
                [0.8, 1.0000, 1.0000],
                [1.0, 1.0000, 1.0000],
                [1.2, 1.0000, 1.0000],
                [1.4, 1.0000, 1.0000],
                [1.6, 0.9215, 1.0000],
                [1.8, 0.4286, 1.0000],
                [2.0, 0.2581, 1.0000]
            ])  # 第二三列分别为上下舵的沾湿比

        elif sgm == 0.024:
            vd = np.array([
                [0, 0.00095126, -0.00000182, -0.00000050],
                [2, 0.00099690, -0.00085900, -0.00023799],
                [4, 0.00111092, -0.00176325, -0.00048851],
                [6, 0.00127093, -0.00262819, -0.00072827],
                [8, 0.00151954, -0.00346207, -0.00095965],
                [10, 0.00183335, -0.00399313, -0.00110686],
                [12, 0.00218979, -0.00448420, -0.00124295],
                [14, 0.00257236, -0.00491780, -0.00136317]
            ])

            R = np.array([
                [-2.0, 1.0000, 1.0000],
                [-1.8, 1.0000, 1.0000],
                [-1.6, 1.0000, 1.0000],
                [-1.4, 1.0000, 1.0000],
                [-1.2, 1.0000, 1.0000],
                [-1.0, 1.0000, 1.0000],
                [-0.8, 1.0000, 1.0000],
                [-0.6, 1.0000, 1.0000],
                [-0.4, 1.0000, 1.0000],
                [-0.2, 1.0000, 1.0000],
                [0.0, 1.0000, 1.0000],
                [0.2, 1.0000, 1.0000],
                [0.4, 1.0000, 1.0000],
                [0.6, 1.0000, 1.0000],
                [0.8, 1.0000, 1.0000],
                [1.0, 1.0000, 1.0000],
                [1.2, 1.0000, 1.0000],
                [1.4, 1.0000, 1.0000],
                [1.6, 1.0000, 1.0000],
                [1.8, 1.0000, 1.0000],
                [2.0, 1.0000, 1.0000]
            ])  # 第二三列分别为上下舵的沾湿比

        # 插值求上舵侧向力
        lw = self.LW
        v = np.sqrt(vx ** 2 + vy ** 2 + vz ** 2)
        beta = np.arctan(vz / np.sqrt(vx ** 2 + vy ** 2))
        ds1 = (beta + dsf + wy * lw / v) * RTD

        f2 = np.zeros(3)

        if abs(ds1) < 14:
            f2[0] = np.interp(abs(ds1), vd[:, 0], vd[:, 1])  # cx
            cy_val = np.interp(abs(ds1), vd[:, 0], vd[:, 2])  # cy
            mz_val = np.interp(abs(ds1), vd[:, 0], vd[:, 3])  # mz
            f2[1:3] = np.sign(ds1) * np.array([cy_val, mz_val])
        else:
            f2[0] = vd[-1, 1]  # cx
            f2[1:3] = np.sign(ds1) * vd[-1, 2:4]  # cy, mz

        # 插值求下舵侧向力
        dx1 = (beta + dxf + wy * lw / v) * RTD

        f3 = np.zeros(3)

        if abs(dx1) < 14:
            f3[0] = np.interp(abs(dx1), vd[:, 0], vd[:, 1])  # cx
            cy_val = np.interp(abs(dx1), vd[:, 0], vd[:, 2])  # cy
            mz_val = np.interp(abs(dx1), vd[:, 0], vd[:, 3])  # mz
            f3[1:3] = np.sign(dx1) * np.array([cy_val, mz_val])
        else:
            f3[0] = vd[-1, 1]  # cx
            f3[1:3] = np.sign(dx1) * vd[-1, 2:4]  # cy, mz

        # 插值求上下舵沾湿比
        if -2 < alphat < 2:
            r = np.array([
                np.interp(alphat, R[:, 0], R[:, 1]),  # 上舵沾湿比
                np.interp(alphat, R[:, 0], R[:, 2])  # 下舵沾湿比
            ])
        elif alphat <= -2:
            r = R[0, 1:3]  # 使用第一个值
        else:
            r = R[-1, 1:3]  # 使用最后一个值

        # 提取系数
        cxu = f2[0]  # 上舵阻力系数
        czu = f2[1]  # 上舵侧向力系数
        myu = f2[2]  # 上舵俯仰力矩系数

        cxd = f3[0]  # 下舵阻力系数
        czd = f3[1]  # 下舵侧向力系数
        myd = f3[2]  # 下舵俯仰力矩系数

        ru = r[0]  # 上舵沾湿比
        rd = r[1]  # 下舵沾湿比

        # 0°攻角下的沾湿比
        r0 = R[10, 1]  # 索引10对应攻角0° (R[10]对应MATLAB的R(11,2))
        q1 = self.q1

        q2 = self.q2
        # 计算上下舵的力和力矩
        Xu = -cxu * q1 * ru / r0
        Xd = -cxd * q1 * rd / r0

        Zu = czu * q1 * ru / r0
        Zd = czd * q1 * rd / r0

        Myu = myu * q2 * ru / r0
        Myd = myd * q2 * rd / r0

        # 计算力臂
        lu = 0.213 / 2 + 0.04 * (1 - ru / 2)
        ld = 0.213 / 2 + 0.04 * (1 - rd / 2)

        # 由差动舵引起的横滚力矩
        Mxc = Zu * lu - Zd * ld

        # 直舵引起的横滚阻尼
        alpha_wx_u = (wx * lu / v) * RTD
        alpha_wx_d = (wx * ld / v) * RTD

        # 上舵横滚阻尼系数
        if abs(alpha_wx_u) < 14:
            czvu = np.sign(alpha_wx_u) * np.interp(abs(alpha_wx_u), vd[:, 0], vd[:, 2])
        else:
            czvu = np.sign(alpha_wx_u) * vd[-1, 2]

        # 下舵横滚阻尼系数
        if abs(alpha_wx_d) < 14:
            czvd = np.sign(alpha_wx_d) * np.interp(abs(alpha_wx_d), vd[:, 0], vd[:, 2])
        else:
            czvd = np.sign(alpha_wx_d) * vd[-1, 2]

        # 横滚阻尼力
        Zvu = czvu * q1 * ru / r0
        Zvd = czvd * q1 * rd / r0

        # wx引起的垂直舵横滚阻尼力矩
        Mxv = Zvu * lu + Zvd * ld

        self.Xu = Xu
        self.Xd = Xd
        self.Zu = Zu
        self.Zd = Zd
        self.Myu = Myu
        self.Myd = Myd
        self.Mxc = Mxc
        self.Mxv = Mxv

    # 总体流体动力计算
    def overall_fluid_dynamic_calculation(self):
        y = self.y
        t = self.t

        y0 = self.y.copy()
        # 状态量获取
        # m, xc, dm, dxc, dJxx, dJyy, dJzz, Jxx, Jyy, Jzz, vx, vy, vz, wx, wy, wz, XT, dkf, dkf, ds, dx, dk, xb, yb, zb, yb1, zb1, _ = control_main(            t, y)
        self.control_main()

        # 获取空化器流体动力
        # Xk, Yk, Zk, Mxk, Myk, Mzk, vxn, vyn, vzn, vkn = cav_fluid_dynamics(y)
        self.cav_fluid_dynamics()

        # 获取尾部流体动力
        # Xb, Yb, Zb, Mxb, Myb, Mzb, alphat = tail_fluid_dynamics(t, y, dk, xb, yb, zb, yb1, zb1)
        self.tail_fluid_dynamics()

        # 获取鳍流体动力
        # Xl, Xr, Yl, Yr, Mzl, Mzr, Mxh = fin_fluid_dynamics(t, y)
        self.fin_fluid_dynamics()
        # 获取其他参数
        # L, S, V, _, _, yc, zc, _, _, _, T1, T2 = get_total_parameters()

        # 获取舵流体动力
        # Xu, Xd, Zu, Zd, Myu, Myd, Mxc, Mxv = rudder_fluid_dynamics(t, y, alphat)
        self.rudder_fluid_dynamics()

        # ---------鳍舵总的位置力和阻尼力-------
        self.Xw = self.Xu + self.Xd + self.Xl + self.Xr
        self.Yw = self.Yl + self.Yr
        self.Zw = self.Zu + self.Zd

        self.Myw = self.Myu + self.Myd
        self.Mzw = self.Mzr + self.Mzl
        self.Mxw = self.Mxc + self.Mxv + self.Mxh

        self.coordinate_transformation_matrix()

        # ---------浮力和重力-------
        Cb0 = self.Cb0
        m = self.m
        g = self.G
        # 忽略浮力
        B = 0
        G = m * g  # 来自变质量插值表

        # 重力在地面系的分量
        DG_ground = np.array([0, B - G, 0])
        DG = DG_ground @ Cb0  # 转换到体轴系
        DG = DG.flatten()
        xc = self.xc
        yc = self.yc
        zc = self.zc
        # 重力矩（关于浮心）
        r_cg = np.array([xc, yc, zc])  # 质心位置向量
        Fg_ground = np.array([[0, -G, 0]])  # 重力在地面系（行向量）
        Fg_body = Fg_ground @ Cb0  # 转换到体轴系
        Fg_body = Fg_body.flatten()  # 一维数组
        MG = np.cross(r_cg, Fg_body)  # 重力矩

        # 获取流体动力参数
        # fluid = get_fluid_parameters()
        self.get_fluid_parameters()
        # 附加质量（简化处理）
        # n11, n22, n44, n66, n26 = fluid[15:20]
        n11 = self.n11
        n22 = self.n22
        n44 = self.n44
        n66 = self.n66
        n26 = self.n26
        n33 = n22
        n55 = n66
        n35 = -n26
        Jxx = self.Jxx
        Jyy = self.Jyy
        Jzz = self.Jzz
        dm = self.dm
        dxc = self.dxc
        dJxx = self.dJxx
        dJyy = self.dJyy
        dJzz = self.dJzz
        wx = self.wx
        wy = self.wy
        wz = self.wz
        vx = self.vx
        vy = self.vy
        vz = self.vz
        Xk = self.Xk
        Yk = self.Yk
        Zk = self.Zk
        Xb = self.Xb
        Yb = self.Yb
        Zb = self.Zb
        Xw = self.Xw
        Yw = self.Yw
        Zw = self.Zw
        XT = self.XT
        Mxk = self.Mxk
        Myk = self.Myk
        Mzk = self.Mzk
        Mxb = self.Mxb
        Myb = self.Myb
        Mzb = self.Mzb
        Mxw = self.Mxw
        Myw = self.Myw
        Mzw = self.Mzw
        sf = self.sf
        cf = self.cf
        st = self.st
        ct = self.ct
        RTD = self.RTD
        dk = self.dk
        ds = self.ds
        dx = self.dx


        # 惯性矩阵
        Amn = np.array([
            [m + n11, 0, 0, 0, m * zc, -m * yc],
            [0, m + n22, 0, -m * zc, 0, m * xc + n26],
            [0, 0, m + n33, m * yc, -m * xc + n35, 0],
            [0, -m * zc, m * yc, Jxx + n44, 0, 0],
            [m * zc, 0, -m * xc + n35, 0, Jyy + n55, 0],
            [-m * yc, m * xc + n26, 0, 0, 0, Jzz + n66]
        ])

        DAmn = np.array([
            [dm, 0, 0, 0, dm * zc, -dm * yc],
            [0, dm, 0, -dm * zc, 0, dm * xc + m * dxc],
            [0, 0, dm, dm * yc, -dm * xc - m * dxc, 0],
            [0, -dm * zc, dm * yc, dJxx, 0, 0],
            [dm * zc, 0, -dm * xc - m * dxc, 0, dJyy, 0],
            [-dm * yc, dm * xc + m * dxc, 0, 0, 0, dJzz]
        ])

        Am = np.array([
            [m, 0, 0, 0, m * zc, -m * yc],
            [0, m, 0, -m * zc, 0, m * xc],
            [0, 0, m, m * yc, -m * xc, 0],
            [0, -m * zc, m * yc, Jxx, 0, 0],
            [m * zc, 0, -m * xc, 0, Jyy, 0],
            [-m * yc, m * xc, 0, 0, 0, Jzz]
        ])

        # 角速度矩阵
        Avw = np.array([
            [0, -wz, wy, 0, 0, 0],
            [wz, 0, -wx, 0, 0, 0],
            [-wy, wx, 0, 0, 0, 0],
            [0, -vz, vy, 0, -wz, wy],
            [vz, 0, -vx, wz, 0, -wx],
            [-vy, vx, 0, -wy, wx, 0]
        ])

        # 总外力和力矩
        AFM = np.array([
            Xk + Xb + Xw + DG[0] + XT,
            Yk + Yb + Yw + DG[1],
            Zk + Zb + Zw + DG[2],
            Mxk + Mxb + Mxw + MG[0],
            Myk + Myb + Myw + MG[1],
            Mzk + Mzb + Mzw + MG[2]
        ])  # 坐标原点建立在浮心，所以只有重力矩没有浮力矩
        self.AFM = AFM

        # 初始化导数向量
        dydt = np.zeros(15)

        # 1. 线速度和角速度导数 (前6个状态)
        y_6 = y0[0:6]  # 提取前6个状态变量

        # 解线性方程组: Amn * dydt[0:6] = (-Avw * Am * y_6 + AFM - DAmn * y_6)
        # 等价于 MATLAB 的 Amn \ (-Avw * Am * y_6 + AFM - DAmn * y_6)
        rhs = -Avw @ Am @ y_6 + AFM - DAmn @ y_6
        dydt[0:6] = np.dot(np.linalg.inv(Amn), rhs[:, np.newaxis]).T

        # 2. 欧拉角导数 (第7-9个状态)
        # 欧拉角运动学方程
        dydt[6] = wy * sf + wz * cf  # theta 导数
        dydt[7] = (wy * cf - wz * sf) / ct  # psi 导数
        dydt[8] = wx - wy * st * cf / ct + wz * st * sf / ct  # phi 导数

        # 3. 位置导数 (第10-12个状态)
        # 速度在地面系的分量: dydt[9:12] = Cb0 * y[0:3]
        vel_body = np.array([y0[0], y0[1], y0[2]])
        vel_ground = Cb0 @ vel_body
        dydt[9:12] = vel_ground  # x0, y0, z0 的导数

        # 4. 舵角变化率 (第13-15个状态)
        # 舵机最大角速度 (转换为弧度/秒)
        wdk = 96.0 / RTD  # 空化器舵角速度
        wds = 96.0 / RTD  # 上舵舵角速度
        wdx = 96.0 / RTD  # 下舵舵角速度
        dkf, dsf, dxf = y[12], y[13], y[14]
        # 舵角一阶滞后模型
        dydt[12] = np.sign(dk - dkf) * wdk  # 空化器舵角变化率
        dydt[13] = np.sign(ds - dsf) * wds  # 上舵舵角变化率
        dydt[14] = np.sign(dx - dxf) * wdx  # 下舵舵角变化率
        aaa = dydt[:, np.newaxis]
        # print(t)
        y = y0
        self.dydt = dydt
        # return dydt

    def events1(self, t: float, y: np.ndarray, *args) -> float:
        """事件处理函数（用于终止条件）"""
        # 使用 *args 来接收额外的参数，即使不使用也要保留
        y0 = y[10]  # 深度坐标
        return y0 + 100  # 当深度小于-100米时停止

    def solve_trajectory(self):
        """求解弹道方程"""
        t0 = self.t0
        tend = self.tend
        y1 = self.y1_initial

        # 时间点
        t_eval = np.linspace(t0, tend, int((tend - t0) / self.dt) + 1)

        # # 求解微分方程
        # sol = solve_ivp(overall_fluid_dynamic_calculation, [t0, tend], y1,
        #                 t_eval=t_eval, events=events1,
        #                 rtol=1e-3, atol=1e-3, max_step=1e-3)
        # return t_eval, sol.y.T
        self.ts = []
        self.ys = []
        dt = self.dt
        y = y1.copy()
        t = t0
        self.t = t
        self.y = y.copy()
        self.t = t
        current_time = time.time()
        last_callback_time = time.time()
        for i in range(len(t_eval)):
            self.ys.append(self.y.copy())
            self.ts.append(self.t)
            y0 = self.y.copy()
            self.overall_fluid_dynamic_calculation()
            self.y = y0 + self.dydt * dt

            self.t = self.t + dt
            current_time = time.time()
            if hasattr(self, 'update_callback') and current_time - last_callback_time > self.min_callback_interval:
                last_callback_time = current_time
                # ========== 进度回调 ==========
                if self.progress_callback:
                    self.progress_callback(i, len(t_eval))

                # ========== 实时数据准备 ==========
                if self.update_callback:
                    # 准备实时数据

                    data = {
                        'motions': {
                            't': self.t,
                            'alphat': self.alphay,
                            'y': self.y
                        },
                        'points': {
                            'plot_dan_x': self.plot_dan_x,
                            'plot_dan_y': self.plot_dan_y,
                            'plot_zhou_x': self.plot_zhou_x,
                            'plot_zhou_y': self.plot_zhou_y,
                            'plot_pao_up_x': self.plot_pao_up_x,
                            'plot_pao_up_y': self.plot_pao_up_y,
                            'plot_pao_down_x': self.plot_pao_down_x,
                            'plot_pao_down_y': self.plot_pao_down_y
                        },
                        'forces': {
                            'AFM': self.AFM
                        },
                        'datas': {
                            'ts': self.ts,
                            'ys': self.ys
                        },
                        'Pi': self.P,
                        'P_list': np.array(self.P_list)
                    }
                    # 调用回调函数
                    self.update_callback(data)

        self.ys.append(self.y)
        self.ts.append(self.t)
        self.ys = np.array(self.ys)
        self.ts = np.array(self.ts)

    def plot_results(self):
        pass
        # """绘制结果图表"""
        # t = self.ts
        # y = self.ys
        # RTD = self.RTD
        #
        # vx = y[:, 0]
        # vy = y[:, 1]
        # vz = y[:, 2]
        # v = np.sqrt(vx ** 2 + vy ** 2 + vz ** 2)
        #
        # alpha = -np.arctan(vy / vx) * RTD
        # beta = np.arctan(vz / np.sqrt(vx ** 2 + vy ** 2)) * RTD
        #
        # # 图1: 速度、攻角、侧滑角
        # plt.figure(1, figsize=(10, 8))
        # plt.subplot(3, 1, 1)
        # plt.plot(t, v, 'k-', linewidth=2)
        # plt.grid(True)
        # plt.ylabel('v(m/s)')
        #
        # plt.subplot(3, 1, 2)
        # plt.plot(t, alpha, 'k-', linewidth=2)
        # plt.grid(True)
        # plt.ylabel('$\\alpha$(°)')
        #
        # plt.subplot(3, 1, 3)
        # plt.plot(t, beta, 'k-', linewidth=2)
        # plt.grid(True)
        # plt.ylabel('$\\beta$(°)')
        # plt.xlabel('t(s)')
        #
        # # 图2: 角速度
        # plt.figure(2, figsize=(10, 8))
        # for i in range(3):
        #     plt.subplot(3, 1, i + 1)
        #     plt.plot(t, y[:, 3 + i], 'k-', linewidth=2)
        #     plt.grid(True)
        #     plt.ylabel(['$\\omega_x$(°/s)', '$\\omega_y$(°/s)', '$\\omega_z$(°/s)'][i])
        # plt.xlabel('t(s)')
        #
        # plt.savefig('./000.png')
        #
        # # 更多图表可以继续添加...
        #
        # plt.show()

    def save_results(self):
        """保存结果到文件"""
        t = self.ts
        y = self.ys
        RTD = self.RTD

        vx = y[:, 0]
        vy = y[:, 1]
        vz = y[:, 2]
        v = np.sqrt(vx ** 2 + vy ** 2 + vz ** 2)
        alpha = -np.arctan(vy / vx) * RTD

        # 保存弹道数据
        trajectory_data = np.column_stack([t, y, v, alpha])
        np.savetxt('tra.txt', trajectory_data, fmt='%9.5f')

    def get_results(self):
        data = {
            'points': {
                'plot_dan_x': self.plot_dan_x,
                'plot_dan_y': self.plot_dan_y,
                'plot_zhou_x': self.plot_zhou_x,
                'plot_zhou_y': self.plot_zhou_y,
                'plot_pao_up_x': self.plot_pao_up_x,
                'plot_pao_up_y': self.plot_pao_up_y,
                'plot_pao_down_x': self.plot_pao_down_x,
                'plot_pao_down_y': self.plot_pao_down_y
            }
        }
        return data

    def main(self):
        """主程序"""
        # print("开始水下弹道仿真...")
        # self.y1_initial = y1
        # self.t0_initial = t0

        # 初始化
        self.initialize_simulation()

        # 设置初始条件
        self.set_initial_conditions()

        # 获取参数
        self.get_fluid_parameters()

        # 初始化空泡
        self.initialize_cavity(self.y1_initial[9], self.y1_initial[10], self.y1_initial[11], self.y1_initial[0])

        # 求解弹道
        # print("正在求解弹道方程...")
        self.solve_trajectory()

        # 将角速度从弧度转换回度
        self.ys[:, 3:9] = self.ys[:, 3:9] * self.RTD

        # 绘制结果
        # print("正在生成图表...")
        self.plot_results()

        # 保存结果
        # print("正在保存结果...")
        self.save_results()

        # print("仿真完成！")


if __name__ == "__main__":
    Calculate1 = under()
    Calculate1.tend = 0.6
    Calculate1.main()

    # []
    # rushui()

