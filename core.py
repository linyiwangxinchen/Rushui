import os
import time

from tqdm import tqdm
import matplotlib.pyplot as plt
import pandas as pd

import numpy as np
from types import SimpleNamespace
import copy
from scipy.interpolate import interp1d
from scipy.linalg import solve
import matplotlib
matplotlib.use('Agg')
import math
from rushui1 import Entry
from rushui_model import under

# 设置字体和解决负号问题 # 以及相关中文乱码的问题
plt.rcParams["font.sans-serif"] = ["SimHei"]  # 使用黑体
plt.rcParams["axes.unicode_minus"] = False  # 正常显示负号

class Dan:
    def __init__(self):
        # ——————————画图参量——————————
        self.dan_type = None
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
        self.P = 0
        self.P_list = [0]
        # 写文件
        self.write1 = False

        # 入水部分参数
        # ——————————基本常量——————————
        # 不用变
        self.rtd = 180 / np.pi
        self.g = 9.8
        self.rho = 1000

        # ——————————总体参数——————————
        # 定义total属性
        self.total = SimpleNamespace()
        self.total.L = 3.195   # 长度
        self.total.S = 0.0356  # 横截面积

        self.total.V = 0     # 体积
        self.total.m = 114.7   # 重量
        self.total.xc = -0.0188    # 重心坐标，体坐标系原点位于重心所在横截面中心
        self.total.yc = -0.0017
        self.total.zc = 0.0008
        self.total.Jxx = 0.63140684  # 转动惯量，按均质假设估算
        self.total.Jyy = 57.06970864
        self.total.Jzz = 57.07143674
        self.total.T = 0

        # ——————————空泡仿真参数——————————
        self.lk = 1.714  # 空化器距重心
        self.rk = 0.021  # 空化器半径
        self.dk = -0 / self.rtd  # 空化器舵角，前端面上翻为正，产生负升力和低头力矩
        self.sgm = 0  # 全局变量空化数
        self.dyc = 0  # 全局变量空泡轴线偏离值

        # ——————————模型外形——————————
        # self.xb = np.array([0, 0, 1.3, 2.6, 2.6, 3.1, 3.1, 2.6, 2.6, 1.3, 0, 0])
        # self.yb = np.array([0, 0.021, 0.1065, 0.1065, 0.08, 0.08, -0.08, -0.08, -0.1065, -0.1065, -0.021, 0])

        self.xb = np.array([0, 0, 1.3, 2.6, 2.6, 3.1, 3.1, 2.6, 2.6, 1.3, 0, 0])/213*324
        self.yb = np.array([0, 0.021, 0.1065, 0.1065, 0.08, 0.08, -0.08, -0.08, -0.1065, -0.1065, -0.021, 0])/213*324
        self.zb = self.yb

        # ——————————入水参数——————————
        self.t0 = 0      # 仿真起始时间
        self.tend = 0.2  # 仿真终止时间
        self.tp = 0      # 全局变量：上一步仿真时间
        self.dt = 2e-4   # 仿真步长
        self.v0 = 300  # 入水速度
        self.theta0 = -10 / self.rtd  # 入水弹道角
        self.psi0 = 0 / self.rtd  # 入水偏航角
        self.phi0 = 0 / self.rtd  # 入水横滚角
        self.alpha0 = 0.03138 / self.rtd  # 入水攻角
        self.wx0 = 0 / self.rtd  # 入水横滚角速度
        self.wy0 = 0 / self.rtd  # 入水偏航角速度
        self.wz0 = 6.63 / self.rtd  # 入水俯仰角速度

        # ——————————控制参数——————————
        self.k_wz = 0.06
        self.k_theta = 0.04

        ## 水下部分参数
        self.tend_under = 1  # 水下仿真时长

        self.RTD = 180 / np.pi  # 弧度到角度转换
        RTD = self.RTD

        # === 输入参量 === #
        self.t0 = 0.539
        self.DK = -2.9377 / RTD  # 空化器舵角
        self.DS = 0.94986 / RTD  # 上直舵角
        self.DX = 0.94986 / RTD  # 下直舵角
        self.dkf = -2.50238 / RTD
        self.dsf = 0.38547 / RTD
        self.dxf = 0.30266 / RTD
        self.T1 = 25080.6  # 推力
        self.T2 = 6971.4
        self.TC = self.t0  # 空泡计算时刻
        # 在这里添加推力时间曲线输入
        self.time_sequence = None
        self.thrust_sequence = None

        # === 仿真控制参数 ===
        self.TP = 0.0  # 控制周期时间
        self.DK = 0.0  # 空化器舵角
        self.DS = 0.0  # 上舵舵角
        self.DX = 0.0  # 下舵舵角

        # === 物理几何参数 ===
        self.SGM = 0.018  # 空化数
        self.LW = 0.8856  # 水平鳍位置 (m)
        self.LH = 0.1405  # 垂直鳍位置 (m)
        self.q1 = 0
        self.q2 = 0

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
        self.dphimax = 60 / RTD
        self.kth = 4
        self.kps = self.kth
        self.kph = 0.08
        self.kwx = 0.0016562
        self.kwz = 0.312
        self.kwy = self.kwz

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
        self._recalculate_update_input()

    def _recalculate_update_input(self):
        self.fluid = np.array(
            [self.CxS, self.mxdd, self.mxwx, self.Cya, self.Cydc, self.Cywz, self.mza, self.mzdc, self.mzwz,
             self.Czb, self.Czdv, self.Czwy, self.myb, self.mydv, self.mywy, self.n11, self.n22, self.n44, self.n66,
             self.n26])

    def main(self):

        # 创建入水对象
        M = Entry()
        M.min_callback_interval = self.min_callback_interval

        # 获取界面数据，对入水对象数据进行刷新
        # ——————————总体参数——————————
        M.total.L = self.total.L # 长度
        M.total.S = self.total.S # 横截面积

        M.total.V = self.total.V # 体积
        M.total.m = self.total.m # 重量
        M.total.xc = self.total.xc # 重心坐标，体坐标系原点位于重心所在横截面中心
        M.total.yc = self.total.yc
        M.total.zc = self.total.zc
        M.total.Jxx = self.total.Jxx # 转动惯量，按均质假设估算
        M.total.Jyy = self.total.Jyy
        M.total.Jzz = self.total.Jzz
        M.total.T = self.total.T

        # ——————————空泡仿真参数——————————
        M.lk = self.lk # 空化器距重心
        M.rk = self.rk # 空化器半径
        M.dk = self.dk # 空化器舵角，前端面上翻为正，产生负升力和低头力矩
        M.sgm = self.sgm # 全局变量空化数
        M.dyc = self.dyc # 全局变量空泡轴线偏离值

        # ——————————模型外形——————————
        M.xb = self.xb
        M.yb = self.yb
        M.zb = self.zb

        # ——————————入水参数——————————
        M.t0 = self.t0 # 仿真起始时间
        M.tend = self.tend # 仿真终止时间
        M.tp = self.tp # 全局变量：上一步仿真时间
        M.dt = self.dt  # 仿真步长
        M.v0 = self.v0 # 入水速度
        M.theta0 = self.theta0 # 入水弹道角
        M.psi0 = self.psi0 # 入水偏航角
        M.phi0 = self.phi0 # 入水横滚角
        M.alpha0 = self.alpha0 # 入水攻角
        M.wx0 = self.wx0 # 入水横滚角速度
        M.wy0 = self.wy0 # 入水偏航角速度
        M.wz0 = self.wz0 # 入水俯仰角速度

        # ——————————控制参数——————————
        M.k_wz = self.k_wz
        M.k_theta = self.k_theta

        # 加入回调
        M.plot_pao_down_y = self.plot_pao_down_y
        M.plot_pao_down_x = self.plot_pao_down_x
        M.plot_pao_up_y = self.plot_pao_up_y
        M.plot_pao_up_x = self.plot_pao_up_x
        M.plot_zhou_y = self.plot_zhou_y
        M.plot_zhou_x = self.plot_zhou_x
        M.plot_dan_y = self.plot_dan_y
        M.plot_dan_x = self.plot_dan_x
        M.update_callback = self.update_callback
        M.progress_callback = self.progress_callback
        M.P = self.P
        M.P_list = self.P_list
        M.write1 = self.write1
        self.M = M

        # 获取入水过程中的时间和状态数据
        t_entry, y_entry = self.M.get_results()
        self.t_entry = t_entry
        self.y_entry = y_entry
        M = self.M
        # print("即将进入水下弹道程序")

        N = under()

        N.min_callback_interval = self.min_callback_interval
        ## 水下部分参数
        N.tend = self.tend_under  # 水下仿真时长

        # === 输入参量 === #
        N.dt = self.dt
        N.t0 = self.t0
        N.DK = self.DK   # 空化器舵角
        N.DS = self.DS   # 上直舵角
        N.DX = self.DX   # 下直舵角
        N.dkf = self.dkf
        N.dsf = self.dsf
        N.dxf = self.dxf
        N.T1 = self.T1   # 推力
        N.T2 = self.T2
        N.time_sequence = self.time_sequence
        N.thrust_sequence = self.thrust_sequence
        N.TC = 0   # 空泡计算时刻
        N.m = self.total.m

        # === 仿真控制参数 ===
        N.TP = self.TP   # 控制周期时间
        N.DK = self.DK   # 空化器舵角
        N.DS = self.DS   # 上舵舵角
        N.DX = self.DX   # 下舵舵角

        # === 物理几何参数 ===
        N.SGM = self.SGM   # 空化数
        N.LW = self.LW   # 水平鳍位置 (m)
        N.LH = self.LH   # 垂直鳍位置 (m)
        N.q1 = self.q1
        N.q2 = self.q2

        # 控制律参数
        N.ddmax = self.ddmax
        N.dvmax = self.dvmax
        N.dkmax = self.dkmax
        N.dkmin = self.dkmin
        N.dk0 = self.dk0
        N.deltaymax = self.deltaymax
        N.deltavymax = self.deltavymax
        N.dthetamax = self.dthetamax
        N.wzmax = self.wzmax
        N.wxmax = self.wxmax
        N.dphimax = self.dphimax
        N.kth = self.kth
        N.kps = self.kps
        N.kph = self.kph
        N.kwx = self.kwx
        N.kwz = self.kwz
        N.kwy = self.kwy

        # 流体动力部分
        N.CxS = self.CxS
        N.mxdd = self.mxdd
        N.mxwx = self.mxwx
        N.Cya = self.Cya
        N.Cydc = self.Cydc
        N.Cywz = self.Cywz
        N.mza = self.mza
        N.mzdc = self.mzdc
        N.mzwz = self.mzwz
        N.Czb = self.Czb
        N.Czdv = self.Czdv
        N.Czwy = self.Czwy
        N.myb = self.myb
        N.mydv = self.mydv
        N.mywy = self.mywy
        N.n11 = self.n11
        N.n22 = self.n22
        N.n26 = self.n26
        N.n44 = self.n44
        N.n66 = self.n66
        N.fluid = self.fluid

        ## 入水转平之后的初值输入给水下程序
        ## output = [vx, vy, vz, wx, wy, wz, theta, psi, phi, x0, y0, z0, dk]
        N.vx = y_entry[-1, 0]
        N.vy = y_entry[-1, 1]
        N.vz = y_entry[-1, 2]
        N.wx = y_entry[-1, 3] / N.RTD
        N.wy = y_entry[-1, 4] / N.RTD
        N.wz = y_entry[-1, 5] / N.RTD
        N.theta = y_entry[-1, 6] / N.RTD
        N.psi = y_entry[-1, 7] / N.RTD
        N.phi = y_entry[-1, 8] / N.RTD
        N.x0 = y_entry[-1, 9]
        N.y0 = y_entry[-1, 10]
        N.z0 = y_entry[-1, 11]
        N.dk = M.dk
        N.ds = self.DS
        N.dx = self.DX

        N.RK = self.rk
        # === 启控时刻参数 ===  // 需要根据入水时刻
        N.YCS = y_entry[-1, 10]  # 启控深度 (m)
        N.THETACS = y_entry[-1, 6]  # 启控俯仰角 (rad)
        N.VYCS = y_entry[-1, 1]  # 启控垂向速度 (m/s)
        N.PSICS = y_entry[-1, 7]  # 启控偏航角 (rad)

        N.plot_pao_down_y = self.plot_pao_down_y
        N.plot_pao_down_x = self.plot_pao_down_x
        N.plot_pao_up_y = self.plot_pao_up_y
        N.plot_pao_up_x = self.plot_pao_up_x
        N.plot_zhou_y = self.plot_zhou_y
        N.plot_zhou_x = self.plot_zhou_x
        N.plot_dan_y = self.plot_dan_y
        N.plot_dan_x = self.plot_dan_x
        N.update_callback = self.update_callback
        N.progress_callback = self.progress_callback
        N.xb = self.lk - self.xb
        N.yb = self.yb
        N.zb = self.zb
        N.yb1 = np.zeros_like(self.yb)
        N.zb1 = self.yb
        N.P = self.P
        N.P_list = self.P_list

        # === 弹体总体相关参数 === #
        N.L =  self.total.L
        N.S = self.total.S
        N.V = self.total.V
        N.m =  self.total.m
        N.xc =  self.total.xc
        N.yc =  self.total.yc
        N.zc =  self.total.zc
        N.Jxx = self.total.Jxx
        N.Jyy = self.total.Jyy
        N.Jzz = self.total.Jzz
        N.LK = self.lk
        N.RK = self.rk
        N.dan_type = self.dan_type
        N.write1 = self.write1

        self.N = N
        self.N.main()
        N = self.N
        return t_entry, y_entry, N.ts, N.ys

        # N = xxx
        # N.xxx = xxx


if __name__ == "__main__":
    dan = Dan()
    dan.main()
