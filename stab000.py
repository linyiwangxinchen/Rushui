import os
import time
import cv2
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# 设置字体和解决负号问题
plt.rcParams["font.sans-serif"] = ["SimHei"]  # 使用黑体
plt.rcParams["axes.unicode_minus"] = False  # 正常显示负号


class Stab:
    def __init__(self):
        #########################################需要输入的参量
        # DPI点数分辨率
        # 不知道为啥原模型中都是用的定数100，这里设个接口是了

        self.SwShow = 0
        self.DPI = 100
        self.dpi = 100
        # 舵长度
        self.dcd = 0
        # 舵位置，是位于弹体的几分之几。
        self.dwz = 0
        # 脉冲扰动的时间常数，单位为ms(CalcPerturbation需要)
        self.Timp = 0.1047
        # 初始速度？应该是，但是为啥是水的？
        self.V0 = 600
        # 脉冲扰动的最大压力？(CalcPerturbation需要)
        self.PmaxImp = 8.72
        # 冲击扰动的中心位置？(CalcPerturbation需要)
        self.XpImp = 0.15
        # 周期扰动的振幅(CalcPerturbation需要)
        self.AmPer = 0.005
        # 周期扰动的波数(CalcPerturbation需要)
        self.ShPer = 7.5
        # 用户定义的扰动(CalcPerturbation需要)
        self.Xuser = []
        # 用户定义的扰动的点数
        self.Np = 0
        # % 用户定义扰动的压力分布（数组，单位：MPa）
        self.Pw_User = []
        # 缩放比例
        self.Scale = 1
        # 入水时初始扰动角速度
        self.Omega0dive = 0
        # 初始扰动角速度
        self.Omega0 = 0

        ########################################模型相关的参量
        # 空化器的锥角，单位为度
        self.Beta = 1
        # 模型长度，单位米(CalcParameters)
        self.Lm = 1
        # 模型总长度，单位毫米(CalcParameters)
        self.Lmm = 1
        # 空化器角度（弧度）(CalcParameters)
        self.BetaRad = 0
        # 模型节数
        self.Ncon = 1
        # 顶点的无量纲位置
        self.Top0 = 0
        # 空化器直径
        self.Dnmm = 1.5
        # 空化器半径，单位毫米(CalcParameters)
        self.Rnmm = 1
        # 模型前体（Forebody）的长度
        self.Lf = 1
        # 模型腔体长度，单位毫米
        self.Lh = 1
        # 模型腔体左端直径，单位毫米
        self.DLh = 1
        # 模型腔体右端直径
        self.DRh = 1
        # 模型前体（Forebody）部分的材料密度（kg/m^3）
        self.Rhof = 1
        # Rhoa (float): 后体材料密度（kg/m^3）。
        self.Rhoa = 1
        # Rhoh (float): 腔体材料密度（kg/m^3）。
        self.Rhoh = 1
        # 总质量(CalcModel)
        self.TMkg = 1
        # 模型总质量(CalcModel)
        self.TMg = 1
        # 模型质心转动惯量(CalcModel)
        self.Ic = 1
        # 模型总转动惯量(CalcModel)
        self.Io = 1
        # 质心的X坐标(CalcModel定义)
        self.Xc = 0
        # Xp 在 CalcModel 中代表了模型的中段截面的相对位置
        # 不知道是否共享了啊(CalcModel定义)
        self.Xp = 1
        # 模型平均密度(CalcModel)
        self.Rho = 1
        # 描述部件位置的数组，每节的无量纲长度(CalcParameters)
        self.Part = []
        # 每一节长度，单位毫米
        self.ConeLen = []
        # 每一节末端直径
        self.BaseDiam = []
        # 一个全局变量？应该是中段截面位置(CalcModel)
        self.Imid = 0
        # 前体末端锥体编号(CalcModel)
        self.Nf = 1
        # 前体多边形节点个数(CalcModel)
        self.NPf = 1
        # 后体多边形节点个数(CalcModel)
        self.NPa = 1
        # 存储了模型在不同位置的无量纲半径值(ModelRadii)
        self.Rmstr = []
        # 每一节末端的无量纲半径(CalcParameters)
        self.BaseR = []
        # # 模型肋（Rib）处的切线斜率模型各节的切线斜率，用于描述模型的几何形状(CalcParameters)
        self.RibTan = []
        # 模型各节的切线角度（弧度），用于描述模型的几何形状(CalcParameters)
        self.RibAng = []
        # 模型轮廓点的x坐标，用于绘制模型的几何轮廓(CalcParameters)
        self.X0mod = []
        # 模型轮廓点的y坐标，用于绘制模型的几何轮廓(CalcParameters)
        self.Y0mod = []
        # 模型肋骨轮廓点的x坐标，用于绘制模型的肋骨几何轮廓(CalcParameters)
        self.X0rib = []
        # 模型肋轮廓点的y坐标，用于绘制模型的肋骨几何轮廓(CalcParameters)
        self.Y0rib = []
        # 腔体轮廓点的x坐标，用于描述腔体的几何形状(CalcParameters)
        self.X0cham = []
        # 腔体轮廓点的y坐标，用于描述腔体的几何形状(CalcParameters)
        self.Y0cham = []
        # 模型半径分布的x坐标，用于描述模型的半径变化(CalcParameters)
        self.Xmstr = []
        # 模型半径分布的横截面积，用于描述模型的几何特性(CalcParameters)
        self.Sm = []
        # 终点位置与模型长度的比值，用于描述模型的运动范围(CalcParameters)
        self.gXfin = 1
        # 拍摄起始点与模型长度的比值，用于描述模型的运动范围(CalcParameters)
        self.gXfilm = 1
        # 观察开始位置与模型长度的比值，用于描述模型的运动范围(CalcParameters)
        self.gXbeg = 1
        # 观察结束位置与模型长度的比值，用于描述模型的运动范围(CalcParameters)
        self.gXend = 1
        # 观察范围的长度，用于描述模型的运动范围(CalcParameters)
        self.Basa = 0
        # 空化器面积# 空化器面积（m²）(CalcParameters)
        self.Sn = 1
        # Xmod (numpy.ndarray): 旋转后的模型轮廓x坐标数组。(CalcTurnModel)
        self.Xmod = []
        # Ymod (numpy.ndarray): 旋转后的模型轮廓y坐标数组。(CalcTurnModel)
        self.Ymod = []
        # Xrib (numpy.ndarray): 旋转后的模型肋骨x坐标数组。(CalcTurnModel)
        self.Xrib = []
        # Yrib (numpy.ndarray): 旋转后的模型肋骨y坐标数组。(CalcTurnModel)
        self.Yrib = []
        # XGmod (numpy.ndarray): 旋转后的模型轮廓x坐标数组。(TurnModelOnGamma)
        self.XGmod = []
        # YGmod (numpy.ndarray): 旋转后的模型轮廓y坐标数组。(TurnModelOnGamma)
        self.YGmod = []
        # XGrib (numpy.ndarray): 旋转后的模型肋骨x坐标数组。(TurnModelOnGamma)
        self.XGrib = []
        # YGrib (numpy.ndarray): 旋转后的模型肋骨y坐标数组。(TurnModelOnGamma)
        self.YGrib = []
        # 归一化空间坐标的起始点(CalcModelFrequency需要)
        self.Xmin = 0
        # 归一化空间坐标的终点(CalcModelFrequency需要)
        self.Xmax = 0

        #########################################预定义的参量

        # 计算步长
        self.HX = 0.1
        # 圆周率
        self.PI = np.pi
        # 三分之一的值
        self.ONETHIRD = 1 / 3
        # “拍摄”模式专用步长
        self.HXfilm = 0.05
        # “潜水”模式专用步长
        self.HXdive = 0.02

        #########################################输入数据预处理参量
        # 空化器的面积（无量纲）
        self.B2 = 1
        # 空化器的无量纲半径(CalcParameters)
        self.Rn = 1
        # 计算步长，这里HX0就是可视化界面中的HX/L
        self.HX0 = 0.01

        #########################################后续传入更改的数据
        # 力系数
        # 升力系数
        self.Cl = 0
        # 阻力系数
        self.Cd = 0
        # 表面摩擦系数
        self.Cf = 0

        #########################################标志参量/信号参量
        # 当前计算到的位置
        self.Jend = 0
        # 是否入水的标记
        self.FlagDive = 0
        # FlagPath -- 是否为路径计算标志
        self.FlagPath = 1
        # 是否成功计算频率的标志。(CalcModelFrequency)
        self.FlagFrequency = 0
        # 控制显示设置
        self.SwDisp = 1
        # 是否接触的标识
        self.SwCont = 0
        # 计算进度标识
        self.FlagProgress = 0
        # 模型类型，用于区分不同的模型，好像0就是real model
        self.SwModel = 0
        # 下部第一次接触标识(CalcForces)
        self.FlagCont1 = False
        # 上部第一次接触表示(CalcForces)
        self.FlagCont2 = False
        # 声音标识
        self.SwSound = 0
        # 扰动标识，默认为4没有压强扰动
        self.SwPert = 4
        # 应力计算标志，这一版的好像就是false
        self.FlagStress = False
        # 截面应力计算标识
        self.FlagStress_section = False
        # FlagAhead -- 是否模型前端超出质心的标志CalcClearances
        self.FlagAhead = False
        self.SwCheckStress = 1
        self.FlagFirst = True

        ########################################记录参量
        # 速度记录参量
        self.V = []
        # 攻角记录参量
        self.Alpha = []
        # 空化数存储合集？（会在Dynamic中定义）
        self.SG = []
        # 记录最后一个有效空泡轮廓的索引(CalcSteadyCavity)
        self.Ipr = 0
        # 模型在 x 方向上的速度历史数据。(CalcModelFrequency需要)
        self.Vx = []
        # 模型位置的历史数据，单位为 m。(CalcModelFrequency需要)
        self.Xhis = []
        # 模型的 'Psi' 角历史数据，单位为 弧度。(CalcModelFrequency需要)
        self.Phis = []
        # 历史数据点数。(CalcModelFrequency需要)
        self.Khis = []
        # T -- 时间数组
        self.T = []

        #######################################现有状态参量
        # 姿态角参量
        # 攻角?应该是俯仰角吧，角度，但是里面注释说的是攻角？说PSIO是俯仰角？
        self.Gamma = 0
        # gamma弧度(CalcParameters)
        self.GammaRad = 0
        # 俯仰角的正弦值(CalcParameters)
        self.SIN_G = 0
        # 俯仰角的余弦值(CalcParameters)
        self.COS_G = 0
        # 空化器倾角角度
        self.Delta = 0
        # 空化器倾角弧度(CalcParameters)
        self.DeltaRad = 0
        # Delta的正弦(CalcParameters)
        self.SIN_D = 0
        # delta余弦(CalcParameters)
        self.COS_D = 0
        # 当前模型的x坐标
        self.Xn = 0
        # 当前无量纲位置
        self.x = 0
        # 舵偏角
        self.dpj = 0
        # 舵表穿透面积
        self.dbctmj = 0
        # 穿刺长度。
        self.cccd = 0
        # 接触次数
        self.Ncont = 0
        # 绝对纵向速度
        self.VyAbs = 0
        # 角速度
        self.Omega = 0
        # 水压扰动参数(CalcPerturbation)
        self.P1n = 0.0
        # P1w -- 水压力扰动数组
        self.P1w = []
        # 马赫数(CalcParameters)
        self.Mach = 0
        # 俯仰角？旋转角度？弧度
        self.Psi = 0
        # -- 估计的'Psi'振荡频率（CalcModelFrequency）
        self.mFpsi = 0

        #######################################潜水时的参量
        # GammaDive (float): 潜水时的攻角（度）。
        self.GammaDive = 0
        # Psi0dive (float): 潜水时的俯仰角（度）。
        self.Psi0dive = 0

        #######################################初始状态参量
        # 初始俯仰角，角度
        self.Psi0 = 0
        # 初始俯仰角，弧度(CalcParameters)
        self.Psi0Rad = 0
        # 初始俯仰角（Psi0）的正弦值，用于计算相关动力学参数(CalcParameters)
        self.SIN_P = 0
        # 初始俯仰角（Psi0）的余弦值，用于计算相关动力学参数(CalcParameters)
        self.COS_P = 0
        # H0 (float): 初始水头？不对，Head0是初始水头，这个从外部给定是个啥东东啊（m）。
        # 应该是模型在水中的初始深度，是一个直接的几何参数。
        self.H0 = 0
        # 初始水头（会在CalcParameters定义） Head0 = 5D02 * V0**2
        # 这部分是速度部分的水头，感觉是分两部分了(CalcParameters)
        self.Head0 = 0
        # 初始空化数(CalcParameters)
        self.SG0 = 0
        # Pc (float): 初始压力（Pa）。
        self.Pc = 0
        # # 弗劳德数(用于显示)(CalcParameters)
        self.Fr = 0
        # 初始弗劳德数的平方，给DerivDyn的(CalcParameters)
        self.Fr2 = 0
        # xs0 (float): 空穴中心的初始x偏移。会被定义
        self.xs0 = 0
        # ys0 (float): 空穴中心的初始y偏移。会被定义
        self.ys0 = 0

        ######################################终点/拍摄，状态参量
        # Xfin(float): 终点位置（m）。
        self.Xfin = 0
        # Xfilm (float): 拍摄起始点（m）。
        self.Xfilm = 0
        # Xbeg (float): 观察开始位置（m）。
        self.Xbeg = 0
        # Xend (float): 观察结束位置（m）。
        self.Xend = 0

        #######################################受力/力矩相关参量（平面力分量）
        # 滑行力系数

        # 最大法向阻力系数（MaxLoad定义）
        self.CnMax = 0
        # 空化数为0时的阻力系数，对圆盘去0.8275(DragForce)
        self.Cx0 = 0
        # 'f2y'的修正因子(CalcForces)
        self.AK = 0
        # 切向/法向力/力矩系数(CalcForces)
        self.Cnx = 0
        self.Cny = 0
        self.Cnm = 0
        self.Csx = 0
        self.Csy = 0
        self.Csm = 0
        # 轴向内力（与SCAV相同）(CalcStress)
        self.Nx = []
        # 由轴向力Fn引起的正应力(CalcStress)
        self.SGx1 = []
        # 剪切内力？横向剪切力？(CalcStress)
        self.Qy = []
        # 剪切应力(CalcStress)
        self.TAUy = []
        # 弯矩(CalcStress)
        self.Mz = []
        # 计算由横向力Fs引起的正应力(CalcStress)
        self.SGx2 = []
        # 总应力(CalcStress)
        self.SGx = []
        # 最大正应力(CalcStress)
        self.SGmax = 0
        # 最大正应力位置(CalcStress)
        self.X_SGmax = 0
        # 最大切应力(CalcStress)
        self.TAUmax = 0
        # 最大切应力位置(CalcStress)
        self.X_TAUmax = 0
        # 用户指定界面剪切力(CalcStress)
        self.Q_X1str = []
        # 用户指定界面剪切应力(CalcStress)
        self.TAU_X1str = []
        # 指定截面的弯矩(CalcStress)
        self.M_X1str = []
        # 指定界面的正应力(CalcStress)
        self.SG_X1str = []
        # 下面这个好像是从SG过来的，
        # SGstr(Istr) = SG(Jend)
        # SG_X2str = SGstr(1)（这里是插值）
        # 应力定义相关，感觉用不到
        self.SG_X2str = 0
        # 运动应力相关，感觉用不到
        self.Cn_X2str = 0
        # 运动应力相关，感觉用不到
        self.Cs_X2str = 0
        # # 应力集中定义参量
        # 前体开始间隔
        self.CoBeg1 = 58
        # 前体结束间隔
        self.CoEnd1 = 59
        # 前体增益系数
        self.CoFact1 = 2
        # 后体开始间隔，单位毫米
        self.CoBeg2 = 129
        # 后体结束间隔
        self.CoEnd2 = 130
        # 后体增益系数
        self.CoFact2 = 2
        # 应力计算参量，想放弃Cnx
        self.X1str = 0
        # 力归一化系数，由 Dynamics 初始化
        self.B3 = 0.0
        # 力矩归一化系数
        self.B4 = 0.0
        # 推力系数比例（C_prop / Cx0）
        self.Cpr = 0.0
        # 推力作用时间（ms）
        self.Tpr = 0.0
        # 当前绝对时间（s）
        self.Tabs = 0.0

        ####################################视图相关参量

        # 根据缩放比例和步长计算视图中的步数(CalcSteadyCavity)
        self.Nview = 1

        ###################################空泡相关参量
        # 空腔半径
        self.RR = 0
        # 模型与空泡的下壁面间隙(CalcClearances)(CalcForces)
        self.fh1 = 0
        # 模型与空泡的上壁面间隙(CalcForces)(CalcClearances)
        self.fh2 = 0
        # 下部浸湿面积(CalcClearances)
        self.Sw1 = 0
        # 上部浸湿面积(CalcClearances)
        self.Sw2 = 0
        # 下部间隙
        self.Cl1 = []
        # 上部间隙
        self.Cl2 = []
        # 下部接触索引
        self.Jc1 = []
        # 上部接触索引
        self.Jc2 = []
        # 初始空轴线位置
        self.Yax0 = []
        # 空泡变形量/空腔截面的膨胀速度
        self.DS = []
        # 空腔半径数组（记得替换为array）
        self.Rcav = []
        # 下间隙最小值对应的肋编号(CalcClearances)
        self.Imin1 = 0
        # 上间隙最小值对应的肋编号(CalcClearances)
        self.Imin2 = 0
        # 沾湿面中心/下部浸湿部分长度(CalcClearances)
        self.fdl1 = 0
        # 沾湿面重心/上部浸湿部分长度？(CalcClearances)
        self.fdl2 = 0
        # 轴对称空腔前缘的无量纲长度，用于描述空腔形状,空泡增长系数。(CalcParameters)
        self.Xagr = 1
        # 轴对称空腔前缘的无量纲半径，用于描述空腔形状(CalcParameters)
        self.Ragr = 1
        # 轴对称空腔前缘的无量纲面积，用于描述空腔形状(CalcParameters)
        self.Sagr = 1
        # 轴对称空腔前缘的起始点位置，用于描述空腔形状(CalcParameters)
        self.XcBeg = 1
        # 轴对称空腔前缘的起始点半径，用于描述空腔形状(CalcParameters)
        self.RcBeg = 1
        # 经验常数，用于描述空腔形状(CalcParameters)
        self.AA = 1
        # 空腔形状计算中的常数，用于描述空腔形状，空泡面积相关(CalcParameters)
        self.AK1 = 1
        # 空腔形状计算中的中间变量，用于描述空腔形状，空泡宽度相关(CalcParameters)
        self.w2 = 1
        # 空腔形状计算中的经验常数，用于描述空腔形状(CalcParameters)
        self.Kappa = 1
        # 轴对称空腔中段的无量纲半径，用于描述空腔形状(CalcParameters)
        self.Rc0 = 1
        # 轴对称空腔的无量纲长度，用于描述空腔形状，空泡长度(CalcParameters)
        self.Lc0 = 1
        # 空泡间隙计算
        # 空泡轮廓的x坐标数组(CalcSteadyCavity)
        self.Xpr = []
        # 空泡轮廓的半径数组(CalcSteadyCavity)
        self.Rpr = []
        # 空泡轮廓的下边界y坐标数组(CalcSteadyCavity)
        self.Ypr1 = []
        # 空泡轮廓的上边界y坐标数组(CalcSteadyCavity)
        self.Ypr2 = []
        # 下间隙数组(CalcSteadyCavity)
        self.H1 = []
        # 上间隙数组(CalcSteadyCavity)
        self.H2 = []
        # 模型轮廓的下边界y坐标数组(CalcSteadyCavity)
        self.Ymod1 = []
        # 模型轮廓的上边界y坐标数组(CalcSteadyCavity)
        self.Ymod2 = []
        # 模型后部的上间隙(CalcSteadyCavity)
        self.H2t = 1
        # 模型后部的下间隙(CalcSteadyCavity)
        self.H1t = 1
        #########################################奇奇怪怪的参量
        self.KS = None
        ##########################################ModelStrength补充
        # FOREBODY：
        # 极限法向应力，Mpa
        self.SGf = 800
        # ultimate shearing stress, MPa
        self.TAUf = 300
        # AFTBODY：
        self.SGa = 500
        self.TAUa = 200
        ########STRESS CONCENTRATION：

        #########################################循环CalcSODE

        # 状态数组（长度 >= Jend + 1）
        self.Vx1 = np.zeros(self.Nview)
        self.Vy1 = np.zeros(self.Nview)
        self.V = np.zeros(self.Nview)
        self.Alpha = np.zeros(self.Nview)
        self.T = np.zeros(self.Nview)

        # 标量状态
        self.Omega = 0.0
        self.PsiPre = 0.0  # 上一步的 Psi
        self.Psi = 0.0  # 当前步的 Psi
        self.Yabs = 0.0
        self.Jend = 1  # 初始步为 1，CalcSODE 从 Jend=2 开始调用
        self.Xn = 0.0
        self.HX = 0.1
        #########################################AI补充
        # ========== 补充初始化：确保 Dynamics 可运行 ==========

        # --- 模式标志 ---
        self.FlagDynamics = 1  # 默认启用动力学模式（与 FlagPath/FlagDive 互斥）
        # 注意：实际使用时应确保三者仅一个为 True

        # --- 数值积分控制 ---
        self.HXfilm = 0.05  # “拍摄/路径”模式专用步长
        self.HXdive = 0.02  # “潜水”模式专用步长
        self.Khis = 10  # 历史数据保存间隔（每 Khis 步存一次）

        # --- 动力学状态数组（需预分配足够长度，或动态分配）---
        # 初始 Nview 估计（后续 Dynamics 会重新分配）
        init_Nview = max(100, int(self.Scale * 1.1 / self.HX) + 2)

        self.Vx1 = np.zeros(init_Nview)
        self.Vy1 = np.zeros(init_Nview)
        self.V = np.zeros(init_Nview)
        self.Alpha = np.zeros(init_Nview)
        self.T = np.zeros(init_Nview)
        self.Ycc = np.zeros(init_Nview)
        self.Yax0 = np.zeros(init_Nview)
        self.SG = np.zeros(init_Nview)
        self.P1w = np.zeros(init_Nview)
        self.DS = np.zeros(init_Nview)

        # --- 空泡相关数组 ---
        self.Rcav = np.zeros((init_Nview, init_Nview))
        self.Xpr = np.zeros(init_Nview)
        self.Ypr1 = np.zeros(init_Nview)
        self.Ypr2 = np.zeros(init_Nview)
        self.Rpr = np.zeros(init_Nview)

        # --- 间隙计算所需数组（CalcClearances）---
        self.Cl1 = np.zeros(self.Ncon)  # 下间隙
        self.Cl2 = np.zeros(self.Ncon)  # 上间隙
        self.Jc1 = np.zeros(self.Ncon, dtype=int)  # 下接触索引
        self.Jc2 = np.zeros(self.Ncon, dtype=int)  # 上接触索引

        # --- 标量状态（关键！）---
        self.Jend = 1  # 当前有效步（1-based 语义）
        self.PsiPre = 0.0  # 上一步俯仰角
        self.Psi = 0.0  # 当前俯仰角
        self.Omega = 0.0  # 角速度
        self.Yabs = 0.0  # 质心绝对 y 坐标
        self.Xn = 0.0  # 当前鼻锥无量纲位置
        self.Tabs = 0.0  # 当前绝对时间

        # --- 力/力矩系数（避免 CalcForces 前未定义）---
        self.Cnx = 0.0
        self.Cny = 0.0
        self.Cnm = 0.0
        self.Csx = 0.0
        self.Csy = 0.0
        self.Csm = 0.0

        # --- 间隙与浸润状态 ---
        self.fh1 = -1e-9  # 初始为负（无接触）
        self.fh2 = -1e-9
        self.fdl1 = 0.0
        self.fdl2 = 0.0
        self.Sw1 = 0.0
        self.Sw2 = 0.0
        self.Imin1 = self.Ncon - 1  # Python 索引
        self.Imin2 = self.Ncon - 1

        # --- 标志位 ---
        self.FlagCont1 = False
        self.FlagCont2 = False
        self.FlagAhead = False
        self.FlagSurface = False
        self.FlagWashed = False
        self.FlagBroken = False
        self.FlagFinish = False
        self.FlagCav = True
        # 添加回调函数
        self.update_callback = None
        self.progress_callback = None
        # 是否手动输入Nview
        self.input_Nview = False

        # --- 历史数组（简化初始化）---
        self.Xhis = np.zeros(1000)
        self.Yhis = np.zeros(1000)
        self.Phis = np.zeros(1000)
        self.Vx = np.zeros(1000)
        self.Vy = np.zeros(1000)

        # --- 应力相关（避免 CalcStress 报错）---
        self.SGx = np.zeros(201)
        self.SGmax = 0.0
        self.TAUmax = 0.0
        #########################################end
        #########################################集中数据初始化
        # ========== 基础物理参数 ==========
        self.V0 = 600  # 初始速度 (m/s)
        self.H0 = 30  # 初始水深 (m)
        self.Pc = 2350  # 环境压力 (Pa)
        self.Lm = 0.5  # 模型长度 (m)
        self.Lmm = 500.0  # 模型长度 (mm)
        self.Dnmm = 1.5  # 空化器直径 (mm)
        self.Beta = 180.0  # 空化器锥角 (deg)，180=圆盘
        self.BetaRad = self.Beta / 180 * np.pi
        self.Delta = 0.0  # 空化器倾角 (deg)
        self.Psi0 = 0.0  # 初始俯仰角 (deg)
        self.Gamma = 0.0  # 攻角/发射角 (deg)
        self.Omega0 = 1  # 初始角速度 (rad/s)
        self.Omega0dive = 0.0  # 入水模式初始角速度

        # ========== 模型几何（3节示例） ==========
        self.Ncon = 3
        self.ConeLen = [24, 35, 90]  # 各节长度 (mm)
        self.BaseDiam = [6, 9.5, 15]  # len=4, 有效索引1~3
        self.BaseDiam = np.array(self.BaseDiam)
        self.Lf = 59  # 前体长度 (mm)
        self.Lh = 20  # 腔体长度 (mm)
        self.DLh = 6  # 腔体左直径
        self.DRh = 6  # 腔体右直径
        self.Rhof = 17.6  # 前体密度 (kg/m³)
        self.Rhoa = 4.5  # 后体密度
        self.Rhoh = 0.0  # 腔体密度

        # ========== 计算控制 ==========
        self.Xfin = 100.0  # 终点距离 (m)
        self.HX = 0.05  # 主步长 (无量纲)
        self.HXfilm = 0.05  # 拍摄模式步长
        self.HXdive = 0.02  # 潜水模式步长
        self.Khis = 10  # 历史数据保存间隔
        self.Scale = 1.0  # 可视化缩放

        # ========== 模式与标志 ==========
        self.FlagPath = False
        self.FlagDive = False
        self.FlagDynamics = True
        self.SwModel = 0  # 0=实模型
        self.SwPert = 4  # 4=无扰动
        self.SwDisp = 0  # 0=连续运行
        self.SwSound = 0  # 0=启用提示音（Python中忽略）
        self.SwCont = 0  # 0=不暂停于接触

        # ========== 推力参数 ==========
        self.Cpr = 1.5  # 推力系数比例
        self.Tpr = 0.0  # 推力作用时间 (ms)

        # ========== 应力集中（可选） ==========
        self.CoBeg1 = 58.0
        self.CoEnd1 = 59.0
        self.CoFact1 = 2.0
        self.CoBeg2 = 129.0
        self.CoEnd2 = 130.0
        self.CoFact2 = 2.0
        self.FlagStress = False

        # ==========水压扰动重新================Impulse
        # 冲击扰动的中心位置？(CalcPerturbation需要)
        self.XpImp = 0.15
        # 脉冲扰动的时间常数，单位为ms(CalcPerturbation需要)
        self.Timp = 0.1047
        # 脉冲扰动的最大压力？(CalcPerturbation需要)
        self.PmaxImp = 8.72
        # ======================Periodoc=======
        # 周期扰动的振幅(CalcPerturbation需要)
        self.AmPer = 0.005
        # 周期扰动的波数(CalcPerturbation需要)
        self.ShPer = 7.5

        # ========== 预分配数组（避免 AttributeError） ==========
        self._init_arrays()

    def _init_arrays(self):
        """预分配空数组，避免 Dynamics 中报错"""
        # N需要动态调整
        N = int(np.ceil(self.Xfin / min(self.HX, self.HXfilm))) + 10
        self.V = np.zeros(N)
        self.Alpha = np.zeros(N)
        self.SG = np.zeros(N)
        self.T = np.zeros(N)
        self.Vx1 = np.zeros(N)
        self.Vy1 = np.zeros(N)
        self.Ycc = np.zeros(N)
        self.Yax0 = np.zeros(N)
        self.P1w = np.zeros(N)
        self.DS = np.zeros(N)
        self.Rcav = np.zeros((N, N))
        self.Xpr = np.zeros(N)
        self.Ypr1 = np.zeros(N)
        self.Ypr2 = np.zeros(N)
        self.Rpr = np.zeros(N)
        self.Cl1 = np.zeros(self.Ncon)
        self.Cl2 = np.zeros(self.Ncon)
        self.Jc1 = np.zeros(self.Ncon, dtype=int)
        self.Jc2 = np.zeros(self.Ncon, dtype=int)

        # 历史数据
        self.Xhis = np.zeros(N)
        self.Yhis = np.zeros(N)
        self.Phis = np.zeros(N)
        self.Vx = np.zeros(N)
        self.Vy = np.zeros(N)
        self.Cn = np.zeros(N)
        self.Cs = np.zeros(N)
        self.Rcav = np.zeros((N, N))  # 或根据 Nview 动态分配
        self.Ypr1 = np.zeros(N)
        self.Ypr2 = np.zeros(N)

        # 新增历史数据存储
        self.VxAbs_list = np.zeros(N)

    def _init_Nview(self):
        # 比较懒，把Dynamics那部分初始化直接复制过来了
        # 保存原始 HX
        work0 = self.HX

        # ========== Step 1: 模式切换与步长设置 ==========
        if self.FlagPath:
            self.HX = self.HXfilm
            Wwidth = 2.4 * self.Scale
            if self.SwPert in (1, 3, 4):
                work = self.Lc0 * self.Rn
            else:  # SwPert == 2
                work = self.Lc0 * self.Rn + 1.25
            self.Nview = int(Wwidth / self.HX) + 2 if work <= Wwidth else int(work / self.HX) + 2

        elif self.FlagDive:
            self.HX = self.HXdive
            if self.GammaDive <= -45.0:
                self.Nview = int(-(1.0 + self.Scale) / (self.HX * self.SIN_G)) + 2
            else:
                self.Nview = int((1.0 + self.Scale) / (self.HX * self.COS_G)) + 2

        else:  # FlagDynamics
            self.Nview = int(self.Scale * 1.1 / self.HX) + 2

        # self.Nview = 1000
        self.Nview = int(self.gXfin / self.HX) + 1

    def _init_arrays_dynamics(self):

        if self.input_Nview:
            aa = 1
        else:
            self._init_Nview()

        # self.Nview = 100
        Nview = self.Nview
        HX = self.HX
        # ========== Step 2: 数组动态分配 ==========
        self.Xpr = np.zeros(Nview)
        self.Ypr1 = np.zeros(Nview)
        self.Ypr2 = np.zeros(Nview)
        self.Rpr = np.zeros(Nview)
        self.SG = np.zeros(Nview)
        self.Vx1 = np.zeros(Nview)
        self.Vy1 = np.zeros(Nview)
        self.V = np.zeros(Nview)
        self.T = np.zeros(Nview)
        self.Ycc = np.zeros(Nview)
        self.Yax0 = np.zeros(Nview)
        self.Alpha = np.zeros(Nview)
        self.P1w = np.zeros(Nview)
        self.DS = np.zeros(Nview)
        self.Rcav = np.zeros((Nview, Nview))

    def DragCone(self):
        # 计算空化器的阻力系数
        # 输入为
        # Beta: 锥形空化器的锥角，单位为deg
        # 输出为Cx0
        # Cx0: 空化器的阻力系数（无量纲）
        # beta角度转弧度
        Beta = self.Beta
        miu = Beta / 180
        # 根据beta的范围计算阻力系数
        if Beta < 30:
            # 阻力系数
            Cx0 = miu / 2 * (0.915 + 9.5 / 2 * miu)
        elif 30 <= Beta <= 180:
            Cx0 = 0.5 + 1.81 * (miu / 2 - 0.25) - 2 * (miu / 2 - 0.25) ** 2
        else:
            Cx0 = 0.8275 + 0.00225 * (miu * 180 - 180) - 0.000007176 * (miu * 180 - 180) ** 2
        self.Cx0 = Cx0

    def CalcForces(self):
        """
        计算空化器上的力和力矩以及模型与空腔壁相互作用产生的力
        (在机体坐标系中)
        """
        # 从self获取需要的参数
        PI = self.PI
        Jend = self.Jend
        HX = self.HX
        B2 = self.B2
        SwSound = self.SwSound
        Rn = self.Rn
        FlagDive = self.FlagDive
        Gamma = self.Gamma
        Delta = self.Delta
        Psi0 = self.Psi0
        SwDisp = self.SwDisp
        SwCont = self.SwCont
        FlagProgress = self.FlagProgress
        SwModel = self.SwModel
        fh1 = self.fh1
        fh2 = self.fh2
        Cl1 = np.array(self.Cl1)
        Cl2 = np.array(self.Cl2)
        Imin1 = self.Imin1
        Imin2 = self.Imin2
        FlagCont1 = self.FlagCont1
        FlagCont2 = self.FlagCont2
        Ncont = self.Ncont
        Sw1 = self.Sw1
        Sw2 = self.Sw2
        Xn = self.Xn
        SIN_G = self.SIN_G
        COS_G = self.COS_G
        CnMax = self.CnMax
        Cx0 = self.Cx0
        Alpha = self.Alpha
        DeltaRad = self.DeltaRad
        COS_D = self.COS_D
        SIN_D = self.SIN_D
        Xc = self.Xc
        V = self.V
        Yax0 = self.Yax0
        Jc1 = np.array(self.Jc1)
        Jc2 = np.array(self.Jc2)
        DS = self.DS
        Rcav = self.Rcav
        RibTan = np.array(self.RibTan)
        BaseR = np.array(self.BaseR)
        Part = np.array(self.Part)
        Omega = self.Omega
        VyAbs = self.VyAbs
        fdl1 = self.fdl1
        fdl2 = self.fdl2

        # 常量定义
        Cf = 1e-2  # 表面摩擦阻力系数
        AK = 10.0  # 'f2y'的修正因子

        # 局部变量初始化
        Csx1 = 0.0
        Csy1 = 0.0
        Csm1 = 0.0
        Csx2 = 0.0
        Csy2 = 0.0
        Csm2 = 0.0

        # --- 空化器上的力和力矩分量 ---
        if FlagDive:  # 潜水模式
            if abs(Gamma + Delta + Psi0 + 90.0) < 1e-6:  # 直接冲击
                s1 = Xn / Rn
                if s1 <= 3.0:
                    CnEntry = CnMax + (Cx0 - CnMax) * s1 / 3.0
                else:
                    CnEntry = Cx0
            else:  # 倾斜入水
                s2 = -Xn * SIN_G / (COS_G * 2.0 * Rn)
                if s2 <= 0.65:
                    CnEntry = CnMax * s2 / 0.65
                elif s2 <= 1.4:
                    CnEntry = ((Cx0 - CnMax) * s2 + 1.4 * CnMax - 0.65 * Cx0) / 0.75
                else:
                    CnEntry = Cx0
        else:  # 动力学和路径模式
            s1 = Xn / Rn
            if s1 <= 3.0:
                CnEntry = CnMax + (Cx0 - CnMax) * s1 / 3.0
            else:
                CnEntry = Cx0

        # 计算力和力矩系数
        Cnx = CnEntry * np.cos(Alpha[Jend] + DeltaRad) * COS_D
        Cny = -CnEntry * np.cos(Alpha[Jend] + DeltaRad) * SIN_D
        Cnm = Xc * Cny

        # --- 平面力和力矩分量 ---
        if SwModel == 0:  # 实模型
            # === 下空腔壁 ===
            if fh1 > 0.0:  # 与下空腔壁接触
                if not FlagCont1:  # 首次接触
                    if SwSound == 0:
                        # beep(55, 5)  # Python中可能需要替代实现
                        pass
                    Ncont += 1
                    FlagCont1 = True
                    if not FlagProgress and (SwCont == 1 or SwDisp == 1):
                        # CALL Message(3)  # 暂不实现消息功能
                        pass

                Csx1 = Cf * Sw1 / B2
                # 确保Imin1是有效的索引
                if Imin1 < len(Cl2):
                    fh2 = Cl2[Imin1]
                else:
                    fh2 = 0.0

                # 计算hs，避免分母为零
                denominator = fh1 + fh2
                if abs(denominator) < 1e-12:
                    denominator = 1e-12
                hs = -2.0 * fh1 / denominator

                f1y = hs * (2.0 + hs) / (1.0 + hs) ** 2
                f2y = 2.0 * hs / (1.0 + AK * hs)

                Vp = V[Jend]
                # 确保索引在有效范围内
                idx1 = max(0, min(Jend - int(Jc1[Imin1]), len(Yax0) - 1))
                idx2 = max(0, min(Jend - int(Jc1[Imin1]) - 1, len(Yax0) - 1))
                # 序列错误，增加-1
                Vyc = Vp * (Yax0[idx1 - 1] - Yax0[idx2 - 1]) / HX

                V1 = -VyAbs + Omega * (Part[Imin1] - Xc) + Vyc

                # 确保索引在有效范围内
                cav_idx = max(0, min(int(Jc1[Imin1]), Rcav.shape[1] - 1))
                if Rcav[Jend, cav_idx] < 1e-12:
                    Rcav[Jend, cav_idx] = 1e-12

                # 将Jend改为Jend-1，咱也不知道为啥，改完结果就对                了
                V2 = -DS[int(Jc1[Imin1]) + 1] / (2.0 * PI * Rcav[Jend - 1, cav_idx]) + Vp * RibTan[Imin1]

                # 确保BaseR和Rn不为零
                ratio = BaseR[Imin1] / Rn if Rn != 0 else 0.0
                Csy1 = 2.0 * ratio ** 2 * Vp * (V1 * f1y + V2 * f2y) / (V[Jend] ** 2 if V[Jend] != 0 else 1e-12)

                # 防止"吸力"
                if Csy1 < 0.0:
                    Csy1 = 0.0

                # 计算力矩
                Arm1 = Part[Imin1] - Xc - 0.5 * fdl1
                Csm1 = -Arm1 * Csy1
            else:  # 无接触
                FlagCont1 = False
                Arm1 = 0.0
                Csx1 = 0.0
                Csy1 = 0.0
                Csm1 = 0.0

            # === 上空腔壁 ===
            if fh2 > 0.0:  # 与上空腔壁接触
                if not FlagCont2:  # 首次接触
                    if SwSound == 0:
                        # beep(55, 5)  # Python中可能需要替代实现
                        pass
                    Ncont += 1
                    FlagCont2 = True
                    if not FlagProgress and (SwCont == 1 or SwDisp == 1):
                        # CALL Message(3)  # 暂不实现消息功能
                        pass

                Csx2 = Cf * Sw2 / B2
                # 确保Imin2是有效的索引
                if Imin2 < len(Cl1):
                    fh1 = Cl1[Imin2]
                else:
                    fh1 = 0.0

                # 计算hs，避免分母为零
                denominator = fh1 + fh2
                if abs(denominator) < 1e-12:
                    denominator = 1e-12
                hs = -2.0 * fh2 / denominator

                f1y = hs * (2.0 + hs) / (1.0 + hs) ** 2
                f2y = 2.0 * hs / (1.0 + AK * hs)

                Vp = V[Jend]
                # 确保索引在有效范围内
                idx1 = max(0, min(Jend - int(Jc2[Imin2]), len(Yax0) - 1))
                idx2 = max(0, min(Jend - int(Jc2[Imin2]) - 1, len(Yax0) - 1))
                # 同步修改
                Vyc = Vp * (Yax0[idx1 - 1] - Yax0[idx2 - 1]) / HX

                V1 = -VyAbs + Omega * (Part[Imin2] - Xc) + Vyc

                # 确保索引在有效范围内
                cav_idx = max(0, min(int(Jc2[Imin2]), Rcav.shape[1] - 1))
                if Rcav[Jend, cav_idx] < 1e-12:
                    Rcav[Jend, cav_idx] = 1e-12

                # 同步修改
                V2 = DS[int(Jc2[Imin2]) + 1] / (2.0 * PI * Rcav[Jend - 1, cav_idx]) - Vp * RibTan[Imin2]

                # 确保BaseR和Rn不为零
                ratio = BaseR[Imin2] / Rn if Rn != 0 else 0.0
                Csy2 = 2.0 * ratio ** 2 * Vp * (V1 * f1y + V2 * f2y) / (V[Jend] ** 2 if V[Jend] != 0 else 1e-12)

                # 防止"吸力"
                if Csy2 > 0.0:
                    Csy2 = 0.0

                # 计算力矩
                Arm2 = Part[Imin2] - Xc - 0.5 * fdl2
                Csm2 = -Arm2 * Csy2
            else:  # 无接触
                FlagCont2 = False
                Arm2 = 0.0
                Csx2 = 0.0
                Csy2 = 0.0
                Csm2 = 0.0

        # 汇总力和力矩
        Csx = Csx1 + Csx2
        Csy = Csy1 + Csy2
        Csm = Csm1 + Csm2

        # 更新self属性
        self.Cnx = Cnx
        self.Cny = Cny
        self.Cnm = Cnm
        self.Csx = Csx
        self.Csy = Csy
        self.Csm = Csm
        self.fh1 = fh1
        self.fh2 = fh2
        self.FlagCont1 = FlagCont1
        self.FlagCont2 = FlagCont2
        self.Ncont = Ncont

    def CalcPerturbation(self):
        """
        Calculate the ambient water pressure perturbation.

        Parameters:
        x (float): Coordinate of the model nose related to the model length.
        SwPert (int): Type of perturbation (1: Impulse, 2: Periodic, 3: User, 4: No perturbation).
        Lm (float): Length of the model.
        Timp (float): Time constant for impulse perturbation.
        V0 (float): Initial velocity.
        PmaxImp (float): Maximum pressure for impulse perturbation.
        Head0 (float): Initial water head.
        XpImp (float): Position of the impulse perturbation.
        AmPer (float): Amplitude of the periodic perturbation.
        ShPer (float): Spatial frequency of the periodic perturbation.
        Xuser (list of float): User-defined positions for user perturbation.
        Pw_User (list of float): User-defined pressures for user perturbation.
        Np (int): Number of user-defined points for user perturbation.

        Returns:
        P1n (float): Calculated pressure perturbation.
        """
        # 计算环境水压扰动
        # def calc_perturbation(x, SwPert, Lm, Timp, V0, PmaxImp, Head0, XpImp, AmPer, ShPer, Xuser, Pw_User, Np):
        # 扰动标识，默认为4没有压强扰动
        SwPert = self.SwPert
        # 脉冲扰动的时间常数，单位为ms
        Timp = self.Timp
        # 模型长度
        Lm = self.Lm
        # 模型初速度
        V0 = self.V0
        # 脉冲扰动的最大压力。
        PmaxImp = self.PmaxImp
        # 初始水头
        Head0 = self.Head0
        # 冲击扰动的中心位置？
        XpImp = self.XpImp
        # 当前无量纲位置
        x = self.x
        # 周期性扰动的振幅
        AmPer = self.AmPer
        # 周期性扰动的波数
        ShPer = self.ShPer
        # 用户定义的扰动
        Xuser = self.Xuser
        # 用户定义的扰动的点数
        Np = self.Np
        # 用户定义扰动的压力分布（数组，单位：MPa）
        Pw_User = self.Pw_User

        # Initialize pressure perturbation to zero
        P1n = 0.0
        # 强迫
        # Impulse
        if SwPert == 1:
            St = 2.0 * np.pi * Lm * 1e3 / (Timp * V0)
            Aka = PmaxImp * 1e6 / Head0
            Xmp = XpImp / Lm
            if x <= Xmp - np.pi / St or x >= Xmp + np.pi / St:
                P1n = 0.0
            else:
                P1n = Aka * (1.0 + np.cos(St * (x - Xmp))) / 2.0
        # Periodic
        # 周期性
        elif SwPert == 2:
            P1n = AmPer * np.sin(ShPer * x)
        # 用户定义，摒弃？
        elif SwPert == 3:  # User
            if x < Xuser[0] / Lm or x > Xuser[Np - 1] / Lm:
                P1n = 0.0
            else:
                # Interpolate user-defined pressure values
                Xuser_norm = np.array(Xuser) / Lm
                Pw_User_norm = np.array(Pw_User) * 1e6 / Head0
                P1n = np.interp(x, Xuser_norm, Pw_User_norm)

        elif SwPert == 4:  # No perturbation
            P1n = 0.0

        self.P1n = P1n

    def MaxLoad(self):
        # , PI, V0, Gamma, Delta, Psi0, FlagDive, BetaRad, DeltaRad, Psi0Rad, GammaRad, SIN_G, Mach
        """
        估计模型入水时的最大力系数。

        参数:
        PI (float): 圆周率。
        V0 (float): 初始速度。
        Gamma (float): 俯仰角（度）。
        Delta (float): 空化器倾角（度）。
        Psi0 (float): 初始俯仰角（度）。
        FlagDive (bool): 是否为入水模式。
        BetaRad (float): 空化器角度（弧度）。
        DeltaRad (float): 空化器倾角（弧度）。
        Psi0Rad (float): 初始俯仰角（弧度）。
        GammaRad (float): 俯仰角（弧度）。
        SIN_G (float): 俯仰角的正弦值。
        Mach (float): 马赫数。

        返回:
        CnMax (float): 最大力系数。
        """
        # 圆周率没啥好说的
        PI = self.PI
        # 初始速度
        V0 = self.V0
        # 空化器角度
        BetaRad = self.BetaRad
        # 入水状态判定
        FlagDive = self.FlagDive
        # 俯仰角？攻角？
        Gamma = self.Gamma
        # gamma的正弦值
        SIN_G = self.SIN_G
        # gamma弧度
        GammaRad = self.GammaRad
        # 空化器倾角
        Delta = self.Delta
        # 空化器倾角弧度
        DeltaRad = self.DeltaRad
        # 初始俯仰角
        Psi0 = self.Psi0
        # 初始俯仰角弧度
        Psi0Rad = self.Psi0Rad
        # 马赫数
        Mach = self.Mach
        # 空化器补角的一半
        Alpha1 = (PI - BetaRad) / 2.0

        if FlagDive:  # 如果是入水
            if Alpha1 < 1e-3:  # 如果空化器补角的一半小于0.001，当作圆盘空化器处理
                if Gamma + Delta + Psi0 == -90:  # 如果是垂直入水（正碰）
                    CnMax = 1.87 + 2.13 / Mach  # 圆盘空化器垂直入水的阻力系数
                else:  # 斜入水
                    work = DeltaRad + Psi0Rad
                    CnMax = 0.8 * np.cos(work) * (1.0 - SIN_G / np.cos(work + GammaRad))  # 圆盘空化器斜入水的阻力系数
            else:  # 锥形空化器
                KAlpha = 1.0 - np.tan(Alpha1) * ((4.0 + PI ** 2) / 8.0 + np.log(4.0 / np.tan(Alpha1))) / 4.0
                CXmax0 = 32.0 * KAlpha / (PI ** 2 * np.tan(Alpha1))
                A = 2.13 / (CXmax0 - 1.87)
                CnMax = 1.87 + 2.13 / (Mach + A)  # 锥形空化器直接入水的力系数
        else:  # 如果不是入水
            if Alpha1 < 1e-3:  # 圆盘空化器
                CnMax = 1.87 + 2.13 / Mach  # 正碰
            else:  # 锥形空化器
                KAlpha = 1.0 - np.tan(Alpha1) * ((4.0 + PI ** 2) / 8.0 + np.log(4.0 / np.tan(Alpha1))) / 4.0
                CXmax0 = 32.0 * KAlpha / (PI ** 2 * np.tan(Alpha1))
                A = 2.13 / (CXmax0 - 1.87)
                CnMax = 1.87 + 2.13 / (Mach + A)

        self.CnMax = CnMax

    def CalcModel(self):
        # PI, Lmm, Top0, Rnmm, Ncon, Part, Lf, ConeLen, BaseDiam, Lh, DLh, DRh, Rhof, Rhoa, Rhoh
        """
        计算模型的体积、质量、质心位置和转动惯量。

        参数:
        PI (float): 圆周率。
        Lmm (float): 模型总长度（mm）。
        Top0 (float): 顶点位置的无量纲量。
        Rnmm (float): 空化器半径（mm）。
        Ncon (int): 模型节数。
        Part (list of float): 每节的无量纲长度。
        Lf (float): 前体长度（mm）。
        ConeLen (list of float): 每节的长度（mm）。
        BaseDiam (list of float): 每节的末端直径（mm）。
        Lh (float): 腔体长度（mm）。
        DLh (float): 腔体左直径（mm）。
        DRh (float): 腔体右直径（mm）。
        Rhof (float): 前体材料密度（kg/m^3）。
        Rhoa (float): 后体材料密度（kg/m^3）。
        Rhoh (float): 腔体材料密度（kg/m^3）。

        返回:
        TMkg (float): 模型总质量（kg）。
        Xc (float): 质心位置（与模型长度相关）。
        Ic (float): 转动惯量（与质心相关，kg*mm^2）。
        """
        # 取回变量
        # 点集分辨率
        DPI = self.DPI
        # 模型的节数
        Ncon = self.Ncon
        # 圆周率，瞎注释啊哈哈哈哈
        PI = self.PI
        # 顶点的无量纲位置(CalcParameters)
        Top0 = self.Top0
        # 模型总长度
        Lmm = self.Lmm
        # 空化器半径，单位毫米
        Rnmm = self.Rnmm
        # 美节的无量纲长度
        Part = self.Part
        # 模型前体（Forebody）的长度
        Lf = self.Lf
        # 每节长度，单位毫米
        ConeLen = self.ConeLen
        # 每节末端直径
        BaseDiam = self.BaseDiam
        # 模型腔体长度，单位毫米
        Lh = self.Lh
        # 模型腔体左端直径
        DLh = self.DLh
        # 模型腔体右端直径
        DRh = self.DRh
        # 模型前体（Forebody）部分的材料密度 (float): 前体材料密度（kg/m^3）。
        Rhof = self.Rhof
        # Rhoa (float): 后体材料密度（kg/m^3）。
        Rhoa = self.Rhoa
        # Rhoh (float): 腔体材料密度（kg/m^3）。
        Rhoh = self.Rhoh
        # 空化器直径
        Dnmm = self.Dnmm
        # 空化器锥角
        Beta = self.Beta
        # 初始化局部变量
        SumLen = np.zeros(100)
        R = np.zeros(100)
        Qfw = np.zeros(100)
        Qaw = np.zeros(100)
        Mfw = np.zeros(100)
        Maw = np.zeros(100)
        Xci = np.zeros(100)

        # 基础几何计算
        Top = Top0 * Lmm  # mm
        Qn = PI * Rnmm ** 2 * Top / 3.0  # 空化器体积，mm³

        # 计算各节末端绝对长度
        for i in range(Ncon):
            SumLen[i] = Part[i] * Lmm

        # 计算各节末端半径
        for i in range(Ncon):
            R[i] = BaseDiam[i] / 2.0

        # 找到前体末端所在锥段
        i = 0
        while i < Ncon and Lf > SumLen[i]:
            i += 1
        Nf = i  # Nf 从0开始，Python索引

        # 计算多边形节点数
        NPf = 2 * (Nf + 1) + 4  # 调整为Python索引
        NPa = 2 * Ncon - NPf + 8

        # 腔体参数
        RLh = DLh / 2.0  # 腔体左半径，mm
        RRh = DRh / 2.0  # 腔体右半径，mm
        Lhx = Lmm - Lh  # 无腔体部分长度，mm

        # 前体末端空心半径
        Rfh = 0.0
        if Lf > Lhx:
            Rfh = RLh + (Lf - Lhx) * (RRh - RLh) / Lh

        # ==================== 各段体积计算 ====================
        Rf = 0.0  # 前体末端半径

        if Lf <= ConeLen[0]:
            # 前体位于第一节内
            Rf = Rnmm + Lf * (R[0] - Rnmm) / ConeLen[0]
            Qfw[0] = PI * Lf * (Rf ** 2 + Rnmm ** 2 + Rf * Rnmm) / 3.0
            Qaw[0] = PI * (ConeLen[0] - Lf) * (R[0] ** 2 + Rf ** 2 + R[0] * Rf) / 3.0

            for i in range(1, Ncon):
                Qfw[i] = 0.0
                Qaw[i] = PI * ConeLen[i] * (R[i] ** 2 + R[i - 1] ** 2 + R[i] * R[i - 1]) / 3.0
        else:
            # 前体跨多个锥段
            found = False
            for j in range(1, Ncon):
                if not found and Lf <= SumLen[j]:
                    Rf = R[j - 1] + (Lf - SumLen[j - 1]) * (R[j] - R[j - 1]) / ConeLen[j]

                    # 第一节全为前体
                    Qfw[0] = PI * ConeLen[0] * (R[0] ** 2 + Rnmm ** 2 + R[0] * Rnmm) / 3.0
                    Qaw[0] = 0.0

                    # 中间完整锥段
                    for i in range(1, j):
                        Qfw[i] = PI * ConeLen[i] * (R[i] ** 2 + R[i - 1] ** 2 + R[i] * R[i - 1]) / 3.0
                        Qaw[i] = 0.0

                    # 截断的第j节
                    Qfw[j] = PI * (Lf - SumLen[j - 1]) * (Rf ** 2 + R[j - 1] ** 2 + Rf * R[j - 1]) / 3.0
                    if j < Ncon:
                        Qaw[j] = PI * (SumLen[j] - Lf) * (R[j] ** 2 + Rf ** 2 + Rf * R[j]) / 3.0

                    # 后体部分
                    for i in range(j + 1, Ncon):
                        Qfw[i] = 0.0
                        Qaw[i] = PI * ConeLen[i] * (R[i] ** 2 + R[i - 1] ** 2 + R[i] * R[i - 1]) / 3.0

                    found = True
                    break

        # ==================== 各段质量 ====================
        for i in range(Ncon):
            Mfw[i] = Rhof * Qfw[i] / 1000.0
            Maw[i] = Rhoa * Qaw[i] / 1000.0

        # 总体积
        Qf = np.sum(Qfw[:Ncon])
        Qa = np.sum(Qaw[:Ncon])
        Q = Qf + Qa + Qn

        # 腔体体积
        Qh = PI * Lh * (RLh ** 2 + RLh * RRh + RRh ** 2) / 3.0

        # ==================== 模型质量计算 ====================
        if Lf != 0.0:
            Mn = Rhof * Qn / 1000.0
            Mf = Rhof * Qf / 1000.0
            Ma = Rhoa * Qa / 1000.0
        else:
            Mn = Rhoa * Qn / 1000.0
            Mf = 0.0
            Ma = Rhoa * Qa / 1000.0

        Mh = Rhoh * Qh / 1000.0

        # 总质量（先不计腔体）
        TMg = Mn + Mf + Ma

        # 考虑腔体对质量的影响
        if Lf <= Lhx:
            if Rhoh == 0.0:
                TMg = TMg - Qh * Rhoa / 1000.0
            else:
                TMg = TMg - Qh * Rhoa / 1000.0 + Mh
        else:
            # 计算前体和后体腔体部分体积
            Qhf = PI * (Lf - Lhx) * (RLh ** 2 + Rfh * RLh + Rfh ** 2) / 3.0
            Qha = PI * (Lmm - Lf) * (Rfh ** 2 + Rfh * RRh + RRh ** 2) / 3.0

            if Rhoh == 0.0:
                TMg = TMg - (Qha * Rhoa / 1000.0) - (Qhf * Rhof / 1000.0)
            else:
                TMg = TMg - (Qha * Rhoa / 1000.0) - (Qhf * Rhof / 1000.0) + Mh

        # 平均密度
        Rho = 1000.0 * TMg / Q if Q > 0 else 0.0

        # ==================== 确定中段截面 Imid ====================
        Imid = 0
        for i in range(1, Ncon):
            if BaseDiam[i] > BaseDiam[i - 1]:
                Imid = i

        # 计算 Xp（中段截面相对位置）
        Xp = 0.0
        if Imid == Ncon - 1:
            Xp = 1.0 - 4.0 * Q / (PI * Lmm * BaseDiam[Ncon - 1] ** 2)
        elif BaseDiam[Imid] > BaseDiam[Ncon - 1] and (1.0 - Part[Imid]) < 0.2:
            Lu = 1.0 / Part[Imid]
            Xp = (0.67 - 0.75 * Lu + 0.2 * Lu ** 2) / (1.0 - Lu + 0.25 * Lu ** 2)
        elif BaseDiam[Imid] == BaseDiam[Ncon - 1]:
            Lu = 1.0 / Part[Imid]
            work = 0.5 * (BaseDiam[0] - Dnmm) / ConeLen[0]
            La = Lmm * Part[Imid] / BaseDiam[Imid]
            Xp = (0.73 + 0.67 * La * (Lu ** 2 - 1.0)) / (Lu * (1.57 + 1.33 * La * (Lu ** 2 - 1.0)))

        # ==================== 质心计算 ====================
        # ---- 前体质心 ----
        if Nf > 0:
            if BaseDiam[0] == Dnmm:
                Xci[0] = ConeLen[0] / 2.0
            else:
                hi = R[0] * ConeLen[0] / (R[0] - Rnmm)
                xc1 = SumLen[0] - hi / 4.0
                xc2 = -(hi - ConeLen[0]) / 4.0
                Q1 = PI * R[0] ** 2 * hi / 3.0
                Q2 = PI * Rnmm ** 2 * (hi - ConeLen[0]) / 3.0
                Xci[0] = (Q1 * xc1 - Q2 * xc2) / (Q1 - Q2) if (Q1 - Q2) != 0 else 0.0

            for i in range(1, Nf):
                if BaseDiam[i] == BaseDiam[i - 1]:
                    Xci[i] = SumLen[i] - ConeLen[i] / 2.0
                else:
                    hi = R[i] * ConeLen[i] / (R[i] - R[i - 1])
                    xc1 = SumLen[i] - hi / 4.0
                    xc2 = SumLen[i] - ConeLen[i] - (hi - ConeLen[i]) / 4.0
                    Q1 = PI * R[i] ** 2 * hi / 3.0
                    Q2 = PI * R[i - 1] ** 2 * (hi - ConeLen[i]) / 3.0
                    Xci[i] = (Q1 * xc1 - Q2 * xc2) / (Q1 - Q2) if (Q1 - Q2) != 0 else 0.0

            if 2.0 * Rf == BaseDiam[Nf - 1]:
                if Nf - 1 >= 0:
                    Xci[Nf] = Lf - (Lf - SumLen[Nf - 1]) / 2.0
            else:
                prev_idx = max(0, Nf - 1)
                hi = Rf * (Lf - SumLen[prev_idx]) / (Rf - R[prev_idx])
                xc1 = Lf - hi / 4.0
                xc2 = Lf - (Lf - SumLen[prev_idx]) - (hi - (Lf - SumLen[prev_idx])) / 4.0
                Q1 = PI * Rf ** 2 * hi / 3.0
                Q2 = PI * R[prev_idx] ** 2 * (hi - (Lf - SumLen[prev_idx])) / 3.0
                Xci[Nf] = (Q1 * xc1 - Q2 * xc2) / (Q1 - Q2) if (Q1 - Q2) != 0 else 0.0
        else:
            if 2.0 * Rf == Dnmm:
                Xci[0] = Lf / 2.0
            else:
                hi = Rf * Lf / (Rf - Rnmm)
                xc1 = Lf - hi / 4.0
                xc2 = -(hi - Lf) / 4.0
                Q1 = PI * Rf ** 2 * hi / 3.0
                Q2 = PI * Rnmm ** 2 * (hi - Lf) / 3.0
                Xci[0] = (Q1 * xc1 - Q2 * xc2) / (Q1 - Q2) if (Q1 - Q2) != 0 else 0.0

        work1 = -Mn * Top / 4.0
        for i in range(Nf + 1):
            work1 += Mfw[i] * Xci[i]

        Xcf = work1 / (Mf + Mn) if (Mf + Mn) != 0 else 0.0

        # ---- 后体质心 ----
        if Nf < Ncon:
            if BaseDiam[Nf] == 2.0 * Rf:
                Xci[Nf] = SumLen[Nf] - (SumLen[Nf] - Lf) / 2.0
            else:
                hi = R[Nf] * (SumLen[Nf] - Lf) / (R[Nf] - Rf)
                xc1 = SumLen[Nf] - hi / 4.0
                xc2 = SumLen[Nf] - (SumLen[Nf] - Lf) - (hi - (SumLen[Nf] - Lf)) / 4.0
                Q1 = PI * R[Nf] ** 2 * hi / 3.0
                Q2 = PI * Rf ** 2 * (hi - (SumLen[Nf] - Lf)) / 3.0
                Xci[Nf] = (Q1 * xc1 - Q2 * xc2) / (Q1 - Q2) if (Q1 - Q2) != 0 else 0.0

            for i in range(Nf + 1, Ncon):
                if BaseDiam[i] == BaseDiam[i - 1]:
                    Xci[i] = SumLen[i] - ConeLen[i] / 2.0
                else:
                    hi = R[i] * ConeLen[i] / (R[i] - R[i - 1])
                    xc1 = SumLen[i] - hi / 4.0
                    xc2 = SumLen[i] - ConeLen[i] - (hi - ConeLen[i]) / 4.0
                    Q1 = PI * R[i] ** 2 * hi / 3.0
                    Q2 = PI * R[i - 1] ** 2 * (hi - ConeLen[i]) / 3.0
                    Xci[i] = (Q1 * xc1 - Q2 * xc2) / (Q1 - Q2) if (Q1 - Q2) != 0 else 0.0

            work1 = 0.0
            for i in range(Nf, Ncon):
                work1 += Maw[i] * Xci[i]

            Xca = work1 / Ma if Ma != 0 else 0.0
        else:
            Xca = 0.0

        # ---- 腔体质心 ----
        if RLh == RRh:
            Xch = Lmm - Lh / 2.0
        else:
            hh = RRh * Lh / (RRh - RLh)
            xc1h = Lmm - hh / 4.0
            xc2h = Lmm - Lh - (hh - Lh) / 4.0
            Q1h = PI * RRh ** 2 * hh / 3.0
            Q2h = PI * RLh ** 2 * (hh - Lh) / 3.0
            Xch = (Q1h * xc1h - Q2h * xc2h) / (Q1h - Q2h) if (Q1h - Q2h) != 0 else 0.0

        # ---- 总质心（未计腔体）----
        if Lf == 0.0:
            Xc = Xca
        elif Lf == Lmm:
            Xc = Xcf
        else:
            Xc = (Xcf * (Mf + Mn) + Xca * Ma) / (Mf + Mn + Ma) if (Mf + Mn + Ma) != 0 else 0.0

        # ---- 考虑腔体后修正质心 ----
        if (Lh > 0.0 and RLh >= 0.0 and RRh > 0.0) or (Lh > 0.0 and RLh > 0.0 and RRh >= 0.0):
            if Lf <= Lhx:
                denom = Mn + Mf + Ma - (Qh * Rhoa / 1000.0)
                if denom != 0:
                    Xc = (Xc * (Mf + Ma + Mn) - Xch * (Qh * Rhoa / 1000.0)) / denom
            elif Lf == Lmm:
                denom = Mn + Mf - (Qh * Rhof / 1000.0)
                if denom != 0:
                    Xc = (Xcf * (Mf + Mn) - Xch * (Qh * Rhof / 1000.0)) / denom
            else:
                if DLh == DRh:
                    Xcha = Lmm - (Lmm - Lf) / 2.0
                    Xchf = Lf - (Lf - Lhx) / 2.0
                else:
                    # 前体腔体部分质心
                    hhf = Rfh * (Lf - Lhx) / (Rfh - RLh) if (Rfh - RLh) != 0 else 0.0
                    xc1hf = Lf - hhf / 4.0
                    xc2hf = Lf - (Lf - Lhx) - (hhf - (Lf - Lhx)) / 4.0
                    Q1hf = PI * Rfh ** 2 * hhf / 3.0
                    Q2hf = PI * RLh ** 2 * (hhf - (Lf - Lhx)) / 3.0
                    Xchf = (Q1hf * xc1hf - Q2hf * xc2hf) / (Q1hf - Q2hf) if (Q1hf - Q2hf) != 0 else 0.0

                    # 后体腔体部分质心
                    hha = RRh * (Lmm - Lf) / (RRh - Rfh) if (RRh - Rfh) != 0 else 0.0
                    xc1ha = Lmm - hha / 4.0
                    xc2ha = Lmm - (Lmm - Lf) - (hha - (Lmm - Lf)) / 4.0
                    Q1ha = PI * RRh ** 2 * hha / 3.0
                    Q2ha = PI * Rfh ** 2 * (hha - (Lmm - Lf)) / 3.0
                    Xcha = (Q1ha * xc1ha - Q2ha * xc2ha) / (Q1ha - Q2ha) if (Q1ha - Q2ha) != 0 else 0.0

                denom = (Mf + Ma + Mn - (Qha * Rhoa / 1000.0) - (Qhf * Rhof / 1000.0))
                numerator = (Xcf * (Mf + Mn) + Xca * Ma - Xcha * (Qha * Rhoa / 1000.0) - Xchf * (Qhf * Rhof / 1000.0))
                if denom != 0:
                    Xc = numerator / denom

        Xc = Xc / Lmm  # 无量纲化

        # ==================== 转动惯量计算 ====================
        if Beta == 180.0:
            Iof = 0.0
        else:
            Iof = Rnmm ** 2 * Top ** 3 * (0.2 * Rnmm ** 2 / Top ** 2 + 2.0 / 15.0)

        # ---- 前体转动惯量 ----
        if Nf > 0:
            if BaseDiam[0] == Dnmm:
                Iof += Rnmm ** 2 * ConeLen[0] * (Rnmm ** 2 + 4.0 * ConeLen[0] ** 2 / 3.0)
            else:
                work2 = 0.5 * (BaseDiam[0] - Dnmm) / ConeLen[0]
                work3 = Rnmm
                work4 = (work3 ** 2 * Lmm ** 3 * Part[0] ** 3 / 3.0 +
                         work3 * work2 * Lmm ** 4 * Part[0] ** 4 / 2.0 +
                         work2 ** 2 * Lmm ** 5 * Part[0] ** 5 / 5.0)
                if work2 != 0:
                    Iof += 0.2 * ((work3 + work2 * ConeLen[0]) ** 5 - work3 ** 5) / work2 + 4.0 * work4

            for i in range(1, Nf):
                if BaseDiam[i] == BaseDiam[i - 1]:
                    Iof += (0.5 * BaseDiam[i]) ** 2 * ((0.5 * BaseDiam[i]) ** 2 * ConeLen[i] +
                                                       4.0 * (SumLen[i] ** 3 - SumLen[i - 1] ** 3) / 3.0)
                else:
                    work2 = 0.5 * (BaseDiam[i] - BaseDiam[i - 1]) / ConeLen[i]
                    work3 = 0.5 * BaseDiam[i - 1] - SumLen[i - 1] * work2
                    work4 = (work3 ** 2 * (SumLen[i] ** 3 - SumLen[i - 1] ** 3) / 3.0 +
                             work3 * work2 * (SumLen[i] ** 4 - SumLen[i - 1] ** 4) / 2.0 +
                             work2 ** 2 * (SumLen[i] ** 5 - SumLen[i - 1] ** 5) / 5.0)
                    if work2 != 0:
                        Iof += 0.2 * ((work3 + work2 * SumLen[i]) ** 5 - (
                                work3 + work2 * SumLen[i - 1]) ** 5) / work2 + 4.0 * work4

            if Nf < Ncon and 2.0 * Rf == BaseDiam[Nf - 1]:
                Iof += (Rf) ** 2 * (Rf ** 2 * (Lf - SumLen[Nf - 1]) + 4.0 * (Lf ** 3 - SumLen[Nf - 1] ** 3) / 3.0)
            elif Nf < Ncon:
                work2 = 0.5 * (2.0 * Rf - BaseDiam[Nf - 1]) / (Lf - SumLen[Nf - 1])
                work3 = 0.5 * BaseDiam[Nf - 1] - SumLen[Nf - 1] * work2
                work4 = (work3 ** 2 * (Lf ** 3 - SumLen[Nf - 1] ** 3) / 3.0 +
                         work3 * work2 * (Lf ** 4 - SumLen[Nf - 1] ** 4) / 2.0 +
                         work2 ** 2 * (Lf ** 5 - SumLen[Nf - 1] ** 5) / 5.0)
                if work2 != 0:
                    Iof += 0.2 * (
                            (work3 + work2 * Lf) ** 5 - (work3 + work2 * SumLen[Nf - 1]) ** 5) / work2 + 4.0 * work4
        else:
            if 2.0 * Rf == Dnmm:
                Iof += Rnmm ** 2 * Lf * (Rnmm ** 2 + 4.0 * Lf ** 2 / 3.0)
            else:
                work2 = 0.5 * (2.0 * Rf - Dnmm) / Lf
                work3 = Rnmm
                work4 = (work3 ** 2 * Lf ** 3 / 3.0 +
                         work3 * work2 * Lf ** 4 / 2.0 +
                         work2 ** 2 * Lf ** 5 / 5.0)
                if work2 != 0:
                    Iof += 0.2 * ((work3 + work2 * Lf) ** 5 - work3 ** 5) / work2 + 4.0 * work4

        Iof = Iof * PI * Rhof / 4e12  # kg·m²

        # ---- 后体转动惯量 ----
        Ioa = 0.0
        if Lf == 0.0:
            if Beta == 180.0:
                Ioa = 0.0
            else:
                Ioa = Rnmm ** 2 * Top ** 3 * (0.2 * Rnmm ** 2 / Top ** 2 + 2.0 / 15.0)

        if Nf < Ncon:
            if BaseDiam[Nf] == 2.0 * Rf:
                Ioa += (0.5 * BaseDiam[Nf]) ** 2 * ((0.5 * BaseDiam[Nf]) ** 2 * (SumLen[Nf] - Lf) +
                                                    4.0 * (SumLen[Nf] ** 3 - Lf ** 3) / 3.0)
            else:
                work2 = 0.5 * (BaseDiam[Nf] - 2.0 * Rf) / (SumLen[Nf] - Lf)
                work3 = Rf - Lf * work2
                work4 = (work3 ** 2 * (SumLen[Nf] ** 3 - Lf ** 3) / 3.0 +
                         work3 * work2 * (SumLen[Nf] ** 4 - Lf ** 4) / 2.0 +
                         work2 ** 2 * (SumLen[Nf] ** 5 - Lf ** 5) / 5.0)
                if work2 != 0:
                    Ioa += 0.2 * ((work3 + work2 * SumLen[Nf]) ** 5 - (work3 + work2 * Lf) ** 5) / work2 + 4.0 * work4

            for i in range(Nf + 1, Ncon):
                if BaseDiam[i] == BaseDiam[i - 1]:
                    Ioa += (0.5 * BaseDiam[i]) ** 2 * ((0.5 * BaseDiam[i]) ** 2 * ConeLen[i] +
                                                       4.0 * (SumLen[i] ** 3 - SumLen[i - 1] ** 3) / 3.0)
                else:
                    work2 = 0.5 * (BaseDiam[i] - BaseDiam[i - 1]) / ConeLen[i]
                    work3 = 0.5 * BaseDiam[i - 1] - SumLen[i - 1] * work2
                    work4 = (work3 ** 2 * (SumLen[i] ** 3 - SumLen[i - 1] ** 3) / 3.0 +
                             work3 * work2 * (SumLen[i] ** 4 - SumLen[i - 1] ** 4) / 2.0 +
                             work2 ** 2 * (SumLen[i] ** 5 - SumLen[i - 1] ** 5) / 5.0)
                    if work2 != 0:
                        Ioa += 0.2 * ((work3 + work2 * SumLen[i]) ** 5 - (
                                work3 + work2 * SumLen[i - 1]) ** 5) / work2 + 4.0 * work4

        Ioa = Ioa * PI * Rhoa / 4e12

        # 总转动惯量（不计腔体）
        Io = Iof + Ioa
        if Lf == 0.0:
            Io = Ioa
        elif Lf == Lmm:
            Io = Iof

        # ---- 腔体对转动惯量的影响 ----
        if (Lh > 0.0 and RLh >= 0.0 and RRh > 0.0) or (Lh > 0.0 and RLh > 0.0 and RRh >= 0.0):
            if RRh == RLh:
                Iohw = (0.5 * DLh) ** 2 * ((0.5 * DRh) ** 2 * Lh + 4.0 * (Lmm ** 3 - Lhx ** 3) / 3.0)
            else:
                work2 = 0.5 * (DRh - DLh) / Lh
                work3 = 0.5 * DLh - Lhx * work2
                work4 = (work3 ** 2 * (Lmm ** 3 - Lhx ** 3) / 3.0 +
                         work3 * work2 * (Lmm ** 4 - Lhx ** 4) / 2.0 +
                         work2 ** 2 * (Lmm ** 5 - Lhx ** 5) / 5.0)
                if work2 != 0:
                    Iohw = 0.2 * ((work3 + work2 * Lmm) ** 5 - (work3 + work2 * Lhx) ** 5) / work2 + 4.0 * work4
                else:
                    Iohw = 0.0

            if Lf <= Lhx:
                Ioh = Iohw * PI * Rhoa / 4e12
            else:
                # 前体腔体部分
                if RRh == RLh:
                    Iohf = (0.5 * DLh) ** 2 * ((0.5 * DLh) ** 2 * (Lf - Lhx) + 4.0 * (Lf ** 3 - Lhx ** 3) / 3.0)
                else:
                    work2 = 0.5 * (2.0 * Rfh - DLh) / (Lf - Lhx)
                    work3 = 0.5 * DLh - Lhx * work2
                    work4 = (work3 ** 2 * (Lf ** 3 - Lhx ** 3) / 3.0 +
                             work3 * work2 * (Lf ** 4 - Lhx ** 4) / 2.0 +
                             work2 ** 2 * (Lf ** 5 - Lhx ** 5) / 5.0)
                    if work2 != 0:
                        Iohf = 0.2 * ((work3 + work2 * Lf) ** 5 - (work3 + work2 * Lhx) ** 5) / work2 + 4.0 * work4
                    else:
                        Iohf = 0.0
                Iohf = Iohf * PI * Rhof / 4e12

                # 后体腔体部分
                if RRh == RLh:
                    Ioha = (0.5 * DLh) ** 2 * ((0.5 * DLh) ** 2 * (Lmm - Lf) + 4.0 * (Lmm ** 3 - Lf ** 3) / 3.0)
                else:
                    work2 = 0.5 * (DRh - 2.0 * Rfh) / (Lmm - Lf)
                    work3 = Rfh - Lf * work2
                    work4 = (work3 ** 2 * (Lmm ** 3 - Lf ** 3) / 3.0 +
                             work3 * work2 * (Lmm ** 4 - Lf ** 4) / 2.0 +
                             work2 ** 2 * (Lmm ** 5 - Lf ** 5) / 5.0)
                    if work2 != 0:
                        Ioha = 0.2 * ((work3 + work2 * Lmm) ** 5 - (work3 + work2 * Lf) ** 5) / work2 + 4.0 * work4
                    else:
                        Ioha = 0.0
                Ioha = Ioha * PI * Rhoa / 4e12

                Ioh = Iohf + Ioha

            # 考虑腔体材料
            if Rhoh == 0.0:
                Io -= Ioh
            else:
                Io = Io - Ioh + Iohw * PI * Rhoh / 4e12

        # ==================== 输出结果 ====================
        TMkg = TMg / 1000.0  # kg
        Ic = Io - TMkg * (Xc * (Lmm / 1000.0)) ** 2  # kg·m²

        # 更新 self 属性
        self.Imid = Imid
        self.TMkg = TMkg
        self.Xc = Xc
        self.Xp = Xp
        self.Ic = Ic
        self.TMg = TMg
        self.Rho = Rho
        self.Io = Io
        self.Nf = Nf  # Python索引
        self.NPf = NPf
        self.NPa = NPa

    def ModelRadii(self):
        # Lmm, Rnmm, Part, BaseR, Ncon
        """
        计算模型半径，步长 HX / L = 0.005。

        参数:
        Lmm (float): 模型总长度（mm）。
        Rnmm (float): 空化器半径（mm）。
        Part (list of float): 每节的无量纲长度。
        BaseR (list of float): 每节末端半径的无量纲数。
        Ncon (int): 模型节数。

        返回:
        Rmstr (list of float): 模型半径数组（无量纲）。
        """
        # 模型总长
        Lmm = self.Lmm
        # 空化器半径
        Rnmm = self.Rnmm
        # 描述部件位置的数组，每节的无量纲长度
        Part = self.Part
        # 每一节末端的无量纲半径
        BaseR = self.BaseR
        # 模型节数
        Ncon = self.Ncon

        # 初始化模型半径数组
        # 这里不知道为啥要分成200份，有啥说法喵？
        # 喵喵不解，喵喵麻木，喵喵默默记录
        Rmstr = np.zeros(201)
        work = Lmm / Rnmm  # 模型总长除以空化器半径
        Rmstr[0] = 1
        # 计算每一步的模型半径
        for i in range(1, 201):
            xi = (i) * 0.005  # 步长为0.005
            if xi <= Part[0] + 0.0025:
                # 第一节锥形部分
                Rmstr[i] = 1.0 + xi * (BaseR[0] * work - 1.0) / Part[0]
            else:
                # 其他节部分
                for j in range(1, Ncon):
                    if xi <= Part[j] + 0.0025:
                        Rmstr[i] = BaseR[j - 1] * work + (xi - Part[j - 1]) * (BaseR[j] - BaseR[j - 1]) * work / (
                                Part[j] - Part[j - 1])
                        break
        # 返回无量纲半径
        self.Rmstr = Rmstr

    def CalcParameters(self):
        """
        计算模型参数和空腔参数
        """
        PI = self.PI
        ONETHIRD = self.ONETHIRD

        # 根据模式设置角度参数
        if self.FlagDive:
            self.GammaRad = PI * self.GammaDive / 180.0
            self.Psi0Rad = PI * self.Psi0dive / 180.0
        else:
            self.GammaRad = PI * self.Gamma / 180.0
            self.Psi0Rad = PI * self.Psi0 / 180.0

        # 计算三角函数值
        self.SIN_G = np.sin(self.GammaRad)
        self.COS_G = np.cos(self.GammaRad)
        self.BetaRad = PI * self.Beta / 180.0
        self.DeltaRad = PI * self.Delta / 180.0
        self.SIN_D = np.sin(self.DeltaRad)
        self.COS_D = np.cos(self.DeltaRad)
        self.SIN_P = np.sin(self.Psi0Rad)
        self.COS_P = np.cos(self.Psi0Rad)

        # 计算模型总长度（mm）和米制单位
        self.Lmm = sum(self.ConeLen[:self.Ncon])
        self.Lm = self.Lmm / 1000.0  # 转换为米

        # 计算阻力系数
        self.DragCone()

        # 计算水力参数
        self.Head0 = 500.0 * self.V0 ** 2
        self.SG0 = (19.61 * (10.0 + self.H0) - self.Pc / 500.0) / self.V0 ** 2

        # 计算相似参数
        self.Mach = self.V0 / 1460.0
        self.Fr = int(self.V0 / np.sqrt(9.81 * self.Dnmm / 1000.0))
        self.Fr2 = self.V0 ** 2 / (9.81 * self.Lm)

        # 计算空化器几何参数
        self.Rnmm = self.Dnmm / 2.0  # 空化器半径（mm）
        self.Rn = self.Rnmm / self.Lmm  # 无量纲半径

        # 顶点位置的无量纲量
        if abs(self.Beta - 180.0) < 1e-6:
            self.Top0 = 0.0
        else:
            self.Top0 = self.Rn / np.tan(self.BetaRad / 2.0)

        # 计算模型各节切线角度
        self.RibTan = np.zeros(self.Ncon)
        self.RibAng = np.zeros(self.Ncon)

        # 第一节
        self.RibTan[0] = 0.5 * (self.BaseDiam[0] - self.Dnmm) / self.ConeLen[0]
        self.RibAng[0] = np.arctan(self.RibTan[0])

        # 其他节
        for i in range(1, self.Ncon):
            self.RibTan[i] = 0.5 * (self.BaseDiam[i] - self.BaseDiam[i - 1]) / self.ConeLen[i]
            self.RibAng[i] = np.arctan(self.RibTan[i])

        # 计算各节无量纲位置
        self.Part = np.zeros(self.Ncon)
        self.Part[0] = self.ConeLen[0] / self.Lmm
        for i in range(1, self.Ncon):
            self.Part[i] = self.Part[i - 1] + self.ConeLen[i] / self.Lmm

        # 计算各节末端无量纲半径
        self.BaseR = np.zeros(self.Ncon)
        for i in range(self.Ncon):
            self.BaseR[i] = 0.5 * self.BaseDiam[i] / self.Lmm

        # 初始化模型轮廓点
        n_points = 2 * self.Ncon + 4
        self.X0mod = np.zeros(n_points)
        self.Y0mod = np.zeros(n_points)

        # 空化器轮廓点
        self.X0mod[0] = -self.Top0 * self.COS_D
        self.Y0mod[0] = self.Top0 * self.SIN_D
        self.X0mod[1] = self.Rn * self.SIN_D
        self.Y0mod[1] = self.Rn * self.COS_D
        self.X0mod[n_points - 2] = -self.X0mod[1]
        self.Y0mod[n_points - 2] = -self.Y0mod[1]
        self.X0mod[n_points - 1] = self.X0mod[0]
        self.Y0mod[n_points - 1] = self.Y0mod[0]

        # 模型主体轮廓点
        for i in range(2, self.Ncon + 2):
            self.X0mod[i] = self.Part[i - 2]
            self.Y0mod[i] = self.BaseR[i - 2]
            self.X0mod[n_points - 1 - i] = self.Part[i - 2]
            self.Y0mod[n_points - 1 - i] = -self.BaseR[i - 2]

        # 初始化模型肋骨点
        n_rib_points = 2 * (self.Ncon - 1)
        self.X0rib = np.zeros(n_rib_points)
        self.Y0rib = np.zeros(n_rib_points)

        for i in range(self.Ncon - 1):
            self.X0rib[2 * i] = self.Part[i]
            self.Y0rib[2 * i] = self.BaseR[i]
            self.X0rib[2 * i + 1] = self.Part[i]
            self.Y0rib[2 * i + 1] = -self.BaseR[i]

        # 腔体轮廓点
        self.X0cham = np.zeros(5)
        self.Y0cham = np.zeros(5)
        self.X0cham[0] = 1.0 - self.Lh / self.Lmm
        self.Y0cham[0] = 0.5 * self.DLh / self.Lmm
        self.X0cham[1] = 1.0
        self.Y0cham[1] = 0.5 * self.DRh / self.Lmm
        self.X0cham[2] = self.X0cham[1]
        self.Y0cham[2] = -self.Y0cham[1]
        self.X0cham[3] = self.X0cham[0]
        self.Y0cham[3] = -self.Y0cham[0]
        self.X0cham[4] = self.X0cham[0]
        self.Y0cham[4] = self.Y0cham[0]

        # 空化器面积 (m²)
        self.Sn = 1e-6 * PI * self.Dnmm ** 2 / 4.0

        # 计算模型半径分布
        self.ModelRadii()

        # 初始化横截面积数组
        self.Xmstr = np.zeros(201)
        self.Sm = np.zeros(201)

        for i in range(201):
            self.Xmstr[i] = 0.005 * (i - 1)
            self.Sm[i] = 1e-6 * PI * (self.Rmstr[i] * self.Rnmm) ** 2  # m²

        # 无量纲距离参数
        self.gXfin = self.Xfin / self.Lm
        self.gXfilm = self.Xfilm / self.Lm
        self.gXbeg = self.Xbeg / self.Lm
        self.gXend = self.Xend / self.Lm
        self.Basa = self.gXend - self.gXbeg

        # 空腔参数 ("1/3定律")
        self.Xagr = 2.0
        self.Ragr = (1.0 + 3.0 * self.Xagr) ** ONETHIRD
        self.Sagr = PI * (self.Rn * self.Ragr) ** 2

        # 轴对称空腔前缘
        self.XcBeg = np.zeros(4)
        self.RcBeg = np.zeros(4)
        self.XcBeg[0] = 0.0
        self.RcBeg[0] = self.Rn

        for i in range(1, 4):
            self.XcBeg[i] = self.XcBeg[i - 1] + self.Rn * self.Xagr / 3.0
            self.RcBeg[i] = self.Rn * (1.0 + 3.0 * self.XcBeg[i] / self.Rn) ** ONETHIRD

        # 经验常数
        self.AA = 2.0
        self.AK1 = 4.0 * PI / self.AA ** 2
        self.w2 = self.Rn * self.AA * np.sqrt(self.Cx0)
        self.Kappa = 0.93

        # 轴对称空腔中段半径和长度
        self.Rc0 = np.sqrt(self.Cx0 * (1.0 + self.SG0) / (self.Kappa * self.SG0))
        self.Lc0 = 2.0 * (self.Xagr + self.AA * np.sqrt(self.Cx0) / self.SG0)

        # 计算最大入水力系数
        self.MaxLoad()
        a = 1

    def CalcStress(self, Vcur):
        """
        计算模型截面的弹性应力，步长为 HX / L = 0.005

        参数:
        Vcur (float): 当前速度
        """
        # 从self中提取变量
        # 应力计算标志，这一版的好像就是false
        FlagStress = self.FlagStress
        # 运动应力菜单对应的参数
        SG_X2str = self.SG_X2str
        Cn_X2str = self.Cn_X2str
        Cs_X2str = self.Cs_X2str
        # 空化数存储合集
        SG = self.SG
        # 当前计算位置
        Jend = self.Jend
        # 法向力系数和切向力系数
        Cnx = self.Cnx
        Csy = self.Csy
        # 初始速度
        V0 = self.V0
        # 空化器面积
        Sn = self.Sn
        # 总质量
        TMkg = self.TMkg
        # 前体材料密度
        Rhof = self.Rhof
        # 后体材料密度
        Rhoa = self.Rhoa
        # 模型半径分布的x坐标
        Xmstr = self.Xmstr
        # 模型总长度（毫米）
        Lmm = self.Lmm
        # 模型前体长度
        Lf = self.Lf
        # 模型长度（米）
        Lm = self.Lm
        # 模型半径分布的横截面积
        Sm = self.Sm
        # 质心的X坐标
        Xc = self.Xc
        # 模型质心转动惯量
        Ic = self.Ic
        # 存储了模型在不同位置的无量纲半径值
        Rmstr = self.Rmstr
        # 空化器半径（毫米）
        Rnmm = self.Rnmm
        # 应力集中定义参量
        CoBeg1 = self.CoBeg1
        CoEnd1 = self.CoEnd1
        CoFact1 = self.CoFact1
        CoBeg2 = self.CoBeg2
        CoEnd2 = self.CoEnd2
        CoFact2 = self.CoFact2
        # 应力计算参量
        X1str = self.X1str
        # 截面应力计算标识
        FlagStress_section = self.FlagStress_section
        # 圆周率
        PI = self.PI

        # 初始化局部变量
        SGcur = 0.0
        Cncur = 0.0
        Cscur = 0.0
        Ax = 0.0
        Ay = 0.0
        work = 0.0
        work1 = 0.0
        work2 = 0.0
        Rmm = 0.0
        Fs = 0.0
        Jz = 0.0
        Int1 = 0.0
        Int2 = 0.0
        Int3 = 0.0
        Rho1 = 0.0
        Rho2 = 0.0

        # 判断是否执行"运动/应力"菜单功能
        if FlagStress:
            # 如果是"运动/应力"菜单功能，则使用特定的应力参数
            SGcur = SG_X2str
            Cncur = Cn_X2str
            Cscur = abs(Cs_X2str)
        else:
            # 否则使用动态计算中的当前值
            SGcur = SG[Jend]
            Cncur = Cnx
            Cscur = abs(Csy)

        # --- 轴向内力（与SCAV相同） ---
        # 初始化轴向内力数组
        Nx = np.zeros(201)
        # 第一个点的轴向内力（单位：牛顿）
        Nx[0] = 1e3 * (Vcur * V0) ** 2 * Sn * Cncur * (1.0 + SGcur) / 2.0
        # 模型纵向加速度，单位：m/s^2
        Ax = Nx[0] / TMkg

        # 计算其他点的轴向内力
        for i in range(1, 201):
            # 确定密度值
            if Xmstr[i - 1] * Lmm < Lf:
                Rho1 = Rhof
            else:
                Rho1 = Rhoa
            if Xmstr[i] * Lmm < Lf:
                Rho2 = Rhof
            else:
                Rho2 = Rhoa
            # 梯形积分法
            work = 0.5 * 0.005 * Lm * (Rho1 * Sm[i - 1] + Rho2 * Sm[i])
            Nx[i] = Nx[i - 1] - 1e3 * Ax * work

        # --- 由轴向力Fn引起的正应力 ---
        SGx1 = np.zeros(201)
        for i in range(201):
            SGx1[i] = 1e-6 * Nx[i] / Sm[i]  # 单位：MPa

        # --- 剪切内力Qy ---
        # 计算剪切力（单位：牛顿）
        Fs = 1e3 * (Vcur * V0) ** 2 * Sn * Cscur / 2.0
        # 初始化剪切内力数组
        Qy = np.zeros(201)
        Qy[0] = 0.0
        # 模型横向加速度，单位：m/s^2
        Ay = Fs / TMkg
        Int1 = 0.0

        # 计算剪切内力
        for i in range(1, 201):
            # 确定密度值
            if Xmstr[i - 1] * Lmm < Lf:
                Rho1 = Rhof
            else:
                Rho1 = Rhoa
            if Xmstr[i] * Lmm < Lf:
                Rho2 = Rhof
            else:
                Rho2 = Rhoa
            # 梯形积分法
            Int1 = Int1 + 0.5 * 0.005 * Lm * (Rho1 * Sm[i - 1] + Rho2 * Sm[i])
            Qy[i] = 1e3 * Ay * Int1

        # --- 剪切应力 ---
        TAUy = np.zeros(201)
        for i in range(201):
            TAUy[i] = 1e-6 * 4.0 * Qy[i] / (3.0 * Sm[i])  # 单位：MPa

        # --- 弯矩Mz ---
        # 初始化弯矩数组
        Mz = np.zeros(201)
        Mz[0] = 0.0
        Int2 = 0.0
        Int3 = 0.0
        work1 = Fs * Lm * (1.0 - Xc) / Ic

        # 计算弯矩
        for i in range(1, 201):
            # 确定密度值
            if Xmstr[i - 1] * Lmm < Lf:
                Rho1 = Rhof
            else:
                Rho1 = Rhoa
            if Xmstr[i] * Lmm < Lf:
                Rho2 = Rhof
            else:
                Rho2 = Rhoa

            # --- 梯形积分法 ---
            Int2 = Int2 + 0.5 * 0.005 * Lm ** 2 * (Rho1 * Xmstr[i - 1] * Sm[i - 1] +
                                                   Rho2 * Xmstr[i] * Sm[i])
            Int3 = Int3 + 0.5 * 0.005 * Lm ** 3 * (Rho1 * Xmstr[i - 1] ** 2 * Sm[i - 1] +
                                                   Rho2 * Xmstr[i] ** 2 * Sm[i])
            Mz[i] = Xmstr[i] * Lm * Qy[i] - (Ay - work1 * Xc * Lm) * 1e3 * Int2 - work1 * 1e3 * Int3

        # --- 由横向力Fs引起的正应力 ---
        SGx2 = np.zeros(201)
        for i in range(201):
            Rmm = Rmstr[i] * Rnmm / 1e3  # 单位：米
            Jz = PI * Rmm ** 4 / 4.0
            SGx2[i] = 1e-6 * Mz[i] * Rmm / Jz  # 单位：MPa

        # --- 总正应力 ---
        SGx = np.zeros(201)
        for i in range(201):
            SGx[i] = SGx1[i] + SGx2[i]  # 单位：MPa

        # --- 应力集中处理 ---
        for i in range(201):
            if CoBeg1 < Xmstr[i] * Lmm < CoEnd1:
                SGx[i] = CoFact1 * SGx[i]
            elif CoBeg2 < Xmstr[i] * Lmm < CoEnd2:
                SGx[i] = CoFact2 * SGx[i]

        # --- 最大正应力 ---
        SGmax = SGx[0]
        X_SGmax = 0.0
        for i in range(1, 201):
            if SGx[i] > SGmax:
                SGmax = SGx[i]
                X_SGmax = Xmstr[i]

        # --- 最大剪切应力 ---
        TAUmax = abs(TAUy[0])
        X_TAUmax = 0.0
        for i in range(1, 201):
            if abs(TAUy[i]) > TAUmax:
                TAUmax = abs(TAUy[i])
                X_TAUmax = Xmstr[i]

        # --- 模型截面X1str处的剪切力和应力 ---
        if FlagStress_section:
            # 使用插值方法计算指定截面的值
            Q_X1str = self.Interpol1(201, Xmstr, Qy, X1str)
            TAU_X1str = self.Interpol1(201, Xmstr, TAUy, X1str)
            M_X1str = self.Interpol1(201, Xmstr, Mz, X1str)
            SG_X1str = self.Interpol1(201, Xmstr, SGx, X1str)
        else:
            Q_X1str = 0.0
            TAU_X1str = 0.0
            M_X1str = 0.0
            SG_X1str = 0.0

        # 将计算结果写回self
        # 轴向内力（与SCAV相同）
        self.Nx = Nx
        # 由轴向力Fn引起的正应力
        self.SGx1 = SGx1
        # 剪切内力
        self.Qy = Qy
        # 剪切应力
        self.TAUy = TAUy
        # 弯矩
        self.Mz = Mz
        # 由横向力Fs引起的正应力
        self.SGx2 = SGx2
        # 总正应力
        self.SGx = SGx
        # 最大正应力
        self.SGmax = SGmax
        # 最大正应力位置
        self.X_SGmax = X_SGmax
        # 最大剪切应力
        self.TAUmax = TAUmax
        # 最大剪切应力位置
        self.X_TAUmax = X_TAUmax
        # 用户指定界面剪切力
        self.Q_X1str = Q_X1str
        # 用户指定界面剪切应力
        self.TAU_X1str = TAU_X1str
        # 指定截面的弯矩
        self.M_X1str = M_X1str
        # 指定界面的正应力
        self.SG_X1str = SG_X1str

    # def CalcStress(self, Vcur):
    #     # , Vcur, V0, Sn, Cn_X2str, Cs_X2str, SG_X2str, SG, Cnx, Csy, FlagStress, Jend,
    #     #                     Xmstr, Lmm, Lf, Rhof, Rhoa, Sm, TMkg, Xc, Ic, Rmstr, Rnmm, CoBeg1, CoEnd1, CoFact1,
    #     #                     CoBeg2, CoEnd2, CoFact2, FlagStress_section, X1str
    #     """
    #     从当前速度计算模型截面的弹性应力。
    #     参数：
    #     - Vcur: 当前速度
    #     - V0: 初始速度
    #     - Sn: 截面面积
    #     - Cn_X2str, Cs_X2str, SG_X2str: 应力相关参数
    #     - SG: 空化数数组
    #     - Cnx, Csy: 力系数
    #     - FlagStress: 应力计算标志
    #     - Jend: 应力计算结束索引
    #     - Xmstr: 截面位置
    #     - Lmm: 模型长度
    #     - Lf: 前体长度
    #     - Rhof, Rhoa: 流体和空气密度
    #     - Sm: 截面面积
    #     - TMkg: 模型总质量
    #     - Xc: 质心位置
    #     - Ic: 惯性矩
    #     - Rmstr: 截面半径
    #     - Rnmm: 归一化半径
    #     - CoBeg1, CoEnd1, CoFact1: 应力集中因子
    #     - CoBeg2, CoEnd2, CoFact2: 应力集中因子
    #     - FlagStress_section: 截面应力计算标志
    #     - X1str: 特定截面位置
    #     """
    #     # 应力计算标志，这一版的好像就是false
    #     FlagStress = self.FlagStress
    #     # 运动应力菜单对应的，这里好像是交叉引用了
    #     # 好像是从SG过来的，
    #     # SGstr(Istr) = SG(Jend)
    #     # SG_X2str = SGstr(1)（这里是插值）
    #     SG_X2str = self.SG_X2str
    #     Cn_X2str = self.Cn_X2str
    #     Cs_X2str = self.Cs_X2str
    #     # 空化数存储合集？（会在Dynamic中定义）
    #     SG = self.SG
    #     # 当前计算位置
    #     Jend = self.Jend
    #     # 几个力矩系数
    #     Cnx = self.Cnx
    #     Csy = self.Csy
    #     # 初始速度
    #     V0 = self.V0
    #     # 空化器面积
    #     Sn = self.Sn
    #     # 总质量
    #     TMkg = self.TMkg
    #     # 模型前体（Forebody）部分的材料密度（kg/m^3）
    #     Rhof = self.Rhof
    #     # 模型半径分布的x坐标，用于描述模型的半径变化
    #     Xmstr = self.Xmstr
    #     # 模型总长度，单位毫米(CalcParameters)
    #     Lmm = self.Lmm
    #     # 模型前体（Forebody）的长度
    #     Lf = self.Lf
    #     # 模型长度，单位米(CalcParameters)
    #     Lm = self.Lm
    #     # Rhoa (float): 后体材料密度（kg/m^3）。
    #     Rhoa = self.Rhoa
    #     # 模型半径分布的横截面积，用于描述模型的几何特性(CalcParameters)
    #     Sm = self.Sm
    #     # 质心的X坐标(CalcModel定义)
    #     Xc = self.Xc
    #     # 模型质心转动惯量(CalcModel)
    #     Ic = self.Ic
    #     # 存储了模型在不同位置的无量纲半径值(ModelRadii)
    #     Rmstr = self.Rmstr
    #     # 空化器半径，单位毫米(CalcParameters)
    #     Rnmm = self.Rnmm
    #     # # 应力集中定义参量
    #     # 前体开始间隔
    #     CoBeg1 = self.CoBeg1
    #     # 前体结束间隔
    #     CoEnd1 = self.CoEnd1
    #     # 前体增益系数
    #     CoFact1 = self.CoFact1
    #     # 后体开始间隔，单位毫米
    #     CoBeg2 = self.CoBeg2
    #     # 后体结束间隔
    #     CoEnd2 = self.CoEnd2
    #     # 后体增益系数
    #     CoFact2 = self.CoFact2
    #     # 应力计算参量，想放弃
    #     X1str = self.X1str
    #     # 截面应力计算标识
    #     FlagStress_section = self.FlagStress_section
    #
    #     if FlagStress:
    #         # 如果是“运动/应力”菜单功能，则使用特定的应力参数
    #         SGcur = SG_X2str
    #         Cncur = Cn_X2str
    #         Cscur = abs(Cs_X2str)
    #     else:
    #         # 否则使用动态计算中的当前值
    #         SGcur = SG[Jend]
    #         Cncur = Cnx
    #         Cscur = abs(Csy)
    #
    #     # 计算轴向内力（与SCAV相同）
    #     Nx = np.zeros(201)
    #     Nx[0] = 1e3 * (Vcur * V0) ** 2 * Sn * Cncur * (1 + SGcur) / 2  # 单位：牛顿
    #     Ax = Nx[0] / TMkg  # 模型纵向加速度，单位：m/s^2
    #
    #     for i in range(1, 201):
    #         Rho1 = Rhof if Xmstr[i - 1] * Lmm < Lf else Rhoa
    #         Rho2 = Rhof if Xmstr[i] * Lmm < Lf else Rhoa
    #         work = 0.5 * 0.005 * Lm * (Rho1 * Sm[i - 1] + Rho2 * Sm[i])  # 梯形积分法
    #         Nx[i] = Nx[i - 1] - 1e3 * Ax * work
    #
    #     # 计算由轴向力Fn引起的正应力
    #     SGx1 = 1e-6 * Nx / Sm  # 单位：MPa
    #
    #     # 计算剪切内力Qy
    #     Fs = 1e3 * (Vcur * V0) ** 2 * Sn * Cscur / 2  # 单位：牛顿
    #
    #     Qy = np.zeros(201)
    #     Ay = Fs / TMkg  # 模型横向加速度，单位：m/s^2
    #     Int1 = 0.0
    #
    #     for i in range(1, 201):
    #         Rho1 = Rhof if Xmstr[i - 1] * Lmm < Lf else Rhoa
    #         Rho2 = Rhof if Xmstr[i] * Lmm < Lf else Rhoa
    #         Int1 += 0.5 * 0.005 * Lm * (Rho1 * Sm[i - 1] + Rho2 * Sm[i])  # 梯形积分法
    #         Qy[i] = 1e3 * Ay * Int1
    #
    #     # 计算剪切应力
    #     TAUy = 1e-6 * 4 * Qy / (3 * Sm)  # 单位：MPa
    #
    #     # 计算弯矩Mz
    #     Mz = np.zeros(201)
    #     Int2 = 0.0
    #     Int3 = 0.0
    #     work1 = Fs * Lm * (1 - Xc) / Ic
    #
    #     for i in range(1, 201):
    #         Rho1 = Rhof if Xmstr[i - 1] * Lmm < Lf else Rhoa
    #         Rho2 = Rhof if Xmstr[i] * Lmm < Lf else Rhoa
    #         Int2 += 0.5 * 0.005 * Lm ** 2 * (Rho1 * Xmstr[i - 1] * Sm[i - 1] + Rho2 * Xmstr[i] * Sm[i])
    #         Int3 += 0.5 * 0.005 * Lm ** 3 * (Rho1 * Xmstr[i - 1] ** 2 * Sm[i - 1] + Rho2 * Xmstr[i] ** 2 * Sm[i])
    #         Mz[i] = Xmstr[i] * Lm * Qy[i] - (Ay - work1 * Xc * Lm) * 1e3 * Int2 - work1 * 1e3 * Int3
    #
    #     # 计算由横向力Fs引起的正应力
    #     SGx2 = np.zeros(201)
    #     for i in range(201):
    #         Rmm = Rmstr[i] * Rnmm / 1e3  # 单位：米
    #         Jz = np.pi * Rmm ** 4 / 4
    #         SGx2[i] = 1e-6 * Mz[i] * Rmm / Jz  # 单位：MPa
    #
    #     # 计算总正应力
    #     SGx = SGx1 + SGx2  # 单位：MPa
    #
    #     # 应力集中处理
    #     for i in range(201):
    #         if CoBeg1 < Xmstr[i] * Lmm < CoEnd1:
    #             SGx[i] *= CoFact1
    #         elif CoBeg2 < Xmstr[i] * Lmm < CoEnd2:
    #             SGx[i] *= CoFact2
    #
    #     # 计算最大正应力
    #     SGmax = np.max(SGx)
    #     X_SGmax = Xmstr[np.argmax(SGx)]
    #
    #     # 计算最大剪切应力
    #     TAUmax = np.max(np.abs(TAUy))
    #     X_TAUmax = Xmstr[np.argmax(np.abs(TAUy))]
    #
    #     # 如果需要，计算特定截面的应力值
    #     if FlagStress_section:
    #         Q_X1str = np.interp(X1str, Xmstr, Qy)
    #         TAU_X1str = np.interp(X1str, Xmstr, TAUy)
    #         M_X1str = np.interp(X1str, Xmstr, Mz)
    #         SG_X1str = np.interp(X1str, Xmstr, SGx)
    #     else:
    #         Q_X1str = []
    #         TAU_X1str = []
    #         M_X1str = []
    #         SG_X1str = []
    #
    #     # 返回参量
    #     # 轴向内力（与SCAV相同）
    #     self.Nx = Nx
    #     # 计算由轴向力Fn引起的正应力
    #     self.SGx1 = SGx1
    #     # 剪切内力？横向剪切力？
    #     self.Qy = Qy
    #     # 剪切应力
    #     self.TAUy = TAUy
    #     # 弯矩
    #     self.Mz = Mz
    #     # 计算由横向力Fs引起的正应力
    #     self.SGx2 = SGx2
    #     # 总应力
    #     self.SGx = SGx
    #     # 最大正应力
    #     self.SGmax = SGmax
    #     # 最大正应力位置
    #     self.X_SGmax = X_SGmax
    #     # 最大切应力
    #     self.TAUmax = TAUmax
    #     # 最大切应力位置
    #     self.X_TAUmax = X_TAUmax
    #     # 用户指定界面剪切力
    #     self.Q_X1str = Q_X1str
    #     # 用户指定界面剪切应力
    #     self.TAU_X1str = TAU_X1str
    #     # 指定截面的弯矩
    #     self.M_X1str = M_X1str
    #     # 指定界面的正应力
    #     self.SG_X1str = SG_X1str

    # """
    # 初始化CalcSteadyCavity类。
    #
    # 参数:
    # self.Xpr = None  # 存储空泡轮廓的x坐标
    # self.Rpr = None  # 存储空泡轮廓的半径
    # self.Ypr1 = None  # 存储空泡轮廓的下边界y坐标
    # self.Ypr2 = None  # 存储空泡轮廓的上边界y坐标
    # self.H1 = None  # 存储下间隙
    # self.H2 = None  # 存储上间隙
    # self.Ymod1 = None  # 存储模型轮廓的下边界y坐标
    # self.Ymod2 = None  # 存储模型轮廓的上边界y坐标
    # self.Ipr = None  # 记录最后一个有效空泡轮廓的索引
    # self.H2t = None  # 模型后部的上间隙
    # self.H1t = None  # 模型后部的下间隙

    def CalcSteadyCavity(self):
        # HX0, Scale, Rn, Xagr, ONETHIRD, Sagr, AK1, w2, SG0, Lc0, Cx0, DeltaRad
        # Psi0Rad, SIN_P, COS_P, Ncon, Part, BaseR, Lmm, Psi0
        """
        计算稳态空泡形状和间隙分布。

        参数:
        HX0: 计算步长。
        Scale: 缩放比例。
        Rn: 空化器半径。
        Xagr: 空泡增长系数。
        ONETHIRD: 1/3的值，用于计算。
        Sagr: 空泡面积增长系数。
        AK1: 空泡面积系数。
        w2: 空泡宽度系数。
        SG0: 初始空化数。
        Lc0: 空泡长度系数。
        Cx0: 轴向力系数。
        DeltaRad: 偏航角（弧度）。
        Psi0Rad: 初始攻角（弧度）。
        SIN_P: 初始攻角的正弦值。
        COS_P: 初始攻角的余弦值。
        Ncon: 模型锥段数量。
        Part: 模型各锥段的相对位置。
        BaseR: 模型各锥段的半径。
        Lmm: 模型长度（毫米）。
        Psi0: 初始攻角（度）。
        """
        # 缩放比例
        Scale = self.Scale
        # 计算步长，这里HX0就是可视化界面中的HX/L
        HX0 = self.HX0
        # 空化器半径
        Rn = self.Rn
        # 轴对称空腔前缘的无量纲长度，用于描述空腔形状，空泡增长系数。
        Xagr = self.Xagr
        # 1/3的值
        ONETHIRD = self.ONETHIRD
        # 轴对称空腔前缘的无量纲面积，用于描述空腔形状，空泡面积增长系数
        Sagr = self.Sagr
        # 空腔形状计算中的常数，用于描述空腔形状
        AK1 = self.AK1
        # 空腔形状计算中的中间变量，用于描述空腔形状
        w2 = self.w2
        # 初始空化数
        SG0 = self.SG0
        # 轴向力系数
        Cx0 = self.Cx0
        # 偏航角（弧度）
        DeltaRad = self.DeltaRad
        # 初始攻角
        Psi0Rad = self.Psi0Rad
        # 初始攻角正弦
        SIN_P = self.SIN_P
        # 初始攻角余弦
        COS_P = self.COS_P
        # 模型锥段数量
        Ncon = self.Ncon
        # 模型各锥段的相对位置。
        Part = self.Part
        # 各锥段半径
        BaseR = self.BaseR
        # 模型长度毫米
        Lmm = self.Lmm
        # 初始攻角
        Psi0 = self.Psi0
        # 空泡长度系数
        Lc0 = self.Lc0

        # 分配内存
        if Scale >= 0.72:
            Nview = int(1.4 * Scale / HX0) + 2  # 根据缩放比例和步长计算视图中的步数
        else:
            Nview = int(1.4 / HX0) + 2

        # 初始化空泡轮廓的x坐标数组
        self.Xpr = np.zeros(Nview)
        # 初始化空泡轮廓的半径数组
        self.Rpr = np.zeros(Nview)
        # 初始化空泡轮廓的下边界y坐标数组
        self.Ypr1 = np.zeros(Nview)
        # 初始化空泡轮廓的上边界y坐标数组
        self.Ypr2 = np.zeros(Nview)
        # 初始化下间隙数组
        self.H1 = np.zeros(Nview)
        # 初始化上间隙数组
        self.H2 = np.zeros(Nview)
        # 初始化模型轮廓的下边界y坐标数组
        self.Ymod1 = np.zeros(Nview)
        # 初始化模型轮廓的上边界y坐标数组
        self.Ymod2 = np.zeros(Nview)

        Nmod = int(1 / HX0) + 1  # 计算模型上的步数
        self.Ymod1 = np.zeros(Nmod)  # 初始化模型轮廓的下边界y坐标数组
        self.Ymod2 = np.zeros(Nmod)  # 初始化模型轮廓的上边界y坐标数组

        # 初始化常量值
        self.Xpr[0] = 0.0
        self.Rpr[0] = Rn
        self.Ymod2[0] = Rn
        self.Ymod1[0] = -Rn
        self.Ypr2[0] = Rn
        self.Ypr1[0] = -Rn
        self.H1[0] = 0.0
        self.H2[0] = 0.0

        # 计算轴对称空泡的主要部分
        for i in range(1, Nview):
            self.Xpr[i] = (i - 1) * HX0  # 计算当前步长的x坐标
            if self.Xpr[i] <= Rn * Xagr:
                # 如果在空泡增长区域内，使用幂律关系计算空泡面积
                S = np.pi * (Rn * (1 + 3 * self.Xpr[i] / Rn) ** ONETHIRD) ** 2
            else:
                # 如果超出空泡增长区域，使用线性关系计算空泡面积
                work = (self.Xpr[i] - Rn * Xagr) / 2
                S = Sagr + AK1 * work * (w2 - work * SG0)
            if S >= 0:
                self.Rpr[i] = np.sqrt(S / np.pi)  # 计算空泡半径
                self.Ipr = i  # 记录最后一个有效空泡轮廓的索引

        # 计算实际空泡轮廓和间隙
        Cy = -0.5 * Cx0 * np.sin(2 * (DeltaRad + Psi0Rad))  # 流向坐标系中的升力系数
        for i in range(1, Nview):
            # 计算空泡轴的弯曲，由于空化器上的侧向力
            hfi = -Cy * Rn * (0.46 - SG0 + 2 * self.Xpr[i] / (Lc0 * Rn))
            # 计算实际空泡轮廓（不考虑空化器的垂直位移）
            self.Ypr2[i] = self.Rpr[i] + hfi
            self.Ypr1[i] = -self.Rpr[i] + hfi

            if self.Xpr[i] <= Part[0] + 5e-4:
                # 如果在模型的第一个锥段内
                self.Ymod2[i] = Rn + self.Xpr[i] * (BaseR[0] - Rn) / Part[0]
                self.Ymod1[i] = -self.Ymod2[i]
                if Psi0 != 0:
                    # 如果有初始攻角，旋转模型轮廓
                    self.Ymod2[i] = -self.Xpr[i] * SIN_P + self.Ymod2[i] * COS_P
                    self.Ymod1[i] = -self.Xpr[i] * SIN_P + self.Ymod1[i] * COS_P
                self.H2[i] = (self.Ypr2[i] - self.Ymod2[i]) * Lmm  # 计算上间隙
                self.H1[i] = (-self.Ypr1[i] + self.Ymod1[i]) * Lmm  # 计算下间隙
            else:
                for j in range(1, Ncon):
                    if self.Xpr[i] <= Part[j] + 5e-4:
                        # 如果在模型的其他锥段内
                        self.Ymod2[i] = BaseR[j - 1] + (self.Xpr[i] - Part[j - 1]) * (BaseR[j] - BaseR[j - 1]) / (
                                Part[j] - Part[j - 1])
                        self.Ymod1[i] = -self.Ymod2[i]
                        if Psi0 != 0:
                            # 如果有初始攻角，旋转模型轮廓
                            self.Ymod2[i] = -self.Xpr[i] * SIN_P + self.Ymod2[i] * COS_P
                            self.Ymod1[i] = -self.Xpr[i] * SIN_P + self.Ymod1[i] * COS_P
                        self.H2[i] = (self.Ypr2[i] - self.Ymod2[i]) * Lmm  # 计算上间隙
                        self.H1[i] = (-self.Ypr1[i] + self.Ymod1[i]) * Lmm  # 计算下间隙
                        break

        # 绘制稳态空泡形状
        # self.plot_steady_cavity()

        # 计算模型后部的间隙
        if self.Xpr[self.Ipr] >= 1.0005:
            self.H2t = self.Ypr2[-1] - self.Ymod2[-1]  # 模型后部的上间隙
            self.H1t = -self.Ypr1[-1] + self.Ymod1[-1]  # 模型后部的下间隙

    def CalcTurnModel(self):
        # Xc, Psi, X0mod, Y0mod, X0rib, Y0rib, Ncon
        """
        计算模型轮廓围绕质心旋转后的坐标。

        参数:
        Xc (float): 质心的x坐标。
        Psi (float): 旋转角度（弧度）。
        X0mod (numpy.ndarray): 模型轮廓的初始x坐标数组。
        Y0mod (numpy.ndarray): 模型轮廓的初始y坐标数组。
        X0rib (numpy.ndarray): 模型肋骨的初始x坐标数组。
        Y0rib (numpy.ndarray): 模型肋骨的初始y坐标数组。
        Ncon (int): 模型锥段数量。
        返回:
        Xmod (numpy.ndarray): 旋转后的模型轮廓x坐标数组。
        Ymod (numpy.ndarray): 旋转后的模型轮廓y坐标数组。
        Xrib (numpy.ndarray): 旋转后的模型肋骨x坐标数组。
        Yrib (numpy.ndarray): 旋转后的模型肋骨y坐标数组。
        """
        # Xc (float): 质心的x坐标。
        Xc = self.Xc
        # Psi (float): 旋转角度（弧度）。
        Psi = self.Psi
        # X0mod (numpy.ndarray): 模型轮廓的初始x坐标数组。
        X0mod = self.X0mod
        # Y0mod (numpy.ndarray): 模型轮廓的初始y坐标数组。
        Y0mod = self.Y0mod
        # X0rib (numpy.ndarray): 模型肋骨的初始x坐标数组。
        X0rib = self.X0rib
        # Y0rib (numpy.ndarray): 模型肋骨的初始y坐标数组。
        Y0rib = self.Y0rib
        # Ncon (int): 模型锥段数量。
        Ncon = self.Ncon

        # 初始化旋转后的模型轮廓坐标
        Xmod = np.zeros(2 * Ncon + 4)
        Ymod = np.zeros(2 * Ncon + 4)

        # 初始化旋转后的模型肋骨坐标
        Xrib = np.zeros(2 * (Ncon - 1))
        Yrib = np.zeros(2 * (Ncon - 1))

        # 计算模型轮廓的旋转
        for i in range(2 * Ncon + 4):
            Xmod[i] = Xc - (Xc - X0mod[i]) * np.cos(Psi) + Y0mod[i] * np.sin(Psi)
            Ymod[i] = (Xc - X0mod[i]) * np.sin(Psi) + Y0mod[i] * np.cos(Psi)

        # 计算模型肋骨的旋转
        for i in range(2 * (Ncon - 1)):
            Xrib[i] = Xc - (Xc - X0rib[i]) * np.cos(Psi) + Y0rib[i] * np.sin(Psi)
            Yrib[i] = (Xc - X0rib[i]) * np.sin(Psi) + Y0rib[i] * np.cos(Psi)

        # 返回:
        # Xmod (numpy.ndarray): 旋转后的模型轮廓x坐标数组。(CalcTurnModel)
        self.Xmod = Xmod
        # Ymod (numpy.ndarray): 旋转后的模型轮廓y坐标数组。(CalcTurnModel)
        self.Ymod = Ymod
        # Xrib (numpy.ndarray): 旋转后的模型肋骨x坐标数组。(CalcTurnModel)
        self.Xrib = Xrib
        # Yrib (numpy.ndarray): 旋转后的模型肋骨y坐标数组。(CalcTurnModel)
        self.Yrib = Yrib

    def TurnPointOnGamma(self, x0, y0):
        # 把x0,y0转换到xt,yt
        """
        在“拍摄/潜水”的空穴中心的伽玛角上旋转任何点坐标。

        参数:
        x0 (float): 初始x坐标。
        y0 (float): 初始y坐标。
        COS_G (float): 旋转角度的余弦值。
        SIN_G (float): 旋转角度的正弦值。

        返回:
        xt (float): 旋转后的x坐标。
        yt (float): 旋转后的y坐标。
        """
        # xs0 (float): 空穴中心的初始x偏移。
        xs0 = self.xs0
        # ys0 (float): 空穴中心的初始y偏移。
        ys0 = self.ys0

        COS_G = self.COS_G
        SIN_G = self.SIN_G
        # 计算旋转后的坐标
        xt = xs0 + x0 * COS_G + y0 * SIN_G
        yt = ys0 - x0 * SIN_G + y0 * COS_G
        # 这里感觉和Fortune略有不同，Fortune的括号里是传入和传出，python不是
        return xt, yt

    def TurnModelOnGamma(self):
        # xs0, ys0, COS_G, SIN_G, Xmod, Ymod, Xrib, Yrib, Ncon
        """
        在“拍摄/潜水”模式下，围绕空穴中心以角度 Gamma 旋转模型轮廓。

        参数:
        xs0 (float): 空穴中心的初始x偏移。
        ys0 (float): 空穴中心的初始y偏移。
        COS_G (float): 旋转角度 Gamma 的余弦值。
        SIN_G (float): 旋转角度 Gamma 的正弦值。
        Xmod (numpy.ndarray): 模型轮廓的初始x坐标数组。
        Ymod (numpy.ndarray): 模型轮廓的初始y坐标数组。
        Xrib (numpy.ndarray): 模型肋骨的初始x坐标数组。
        Yrib (numpy.ndarray): 模型肋骨的初始y坐标数组。
        Ncon (int): 模型锥段数量。

        返回:
        XGmod (numpy.ndarray): 旋转后的模型轮廓x坐标数组。
        YGmod (numpy.ndarray): 旋转后的模型轮廓y坐标数组。
        XGrib (numpy.ndarray): 旋转后的模型肋骨x坐标数组。
        YGrib (numpy.ndarray): 旋转后的模型肋骨y坐标数组。
        """
        if len(self.Xmod) == 0:
            self.CalcParameters()
            self.CalcModel()
        # Ncon (int): 模型锥段数量。
        Ncon = self.Ncon
        # COS_G (float): 旋转角度 Gamma 的余弦值。
        COS_G = self.COS_G
        # SIN_G (float): 旋转角度 Gamma 的正弦值。
        SIN_G = self.SIN_G
        # xs0 (float): 空穴中心的初始x偏移。
        xs0 = self.xs0
        # ys0 (float): 空穴中心的初始y偏移。
        ys0 = self.ys0
        # Xmod (numpy.ndarray): 模型轮廓的初始x坐标数组。
        Xmod = self.Xmod
        # Ymod (numpy.ndarray): 模型轮廓的初始y坐标数组。
        Ymod = self.Ymod
        # Xrib (numpy.ndarray): 模型肋骨的初始x坐标数组。
        Xrib = self.Xrib
        # Yrib (numpy.ndarray): 模型肋骨的初始y坐标数组。
        Yrib = self.Yrib


        # 初始化旋转后的模型轮廓坐标
        XGmod = np.zeros(2 * Ncon + 4)
        YGmod = np.zeros(2 * Ncon + 4)

        # 初始化旋转后的模型肋骨坐标
        XGrib = np.zeros(2 * (Ncon - 1))
        YGrib = np.zeros(2 * (Ncon - 1))
        # 计算模型轮廓的旋转
        for i in range(2 * Ncon + 4):
            XGmod[i] = xs0 + Xmod[i] * COS_G + Ymod[i] * SIN_G
            YGmod[i] = ys0 - Xmod[i] * SIN_G + Ymod[i] * COS_G

        # 计算模型肋骨的旋转
        for i in range(2 * (Ncon - 1)):
            XGrib[i] = xs0 + Xrib[i] * COS_G + Yrib[i] * SIN_G
            YGrib[i] = ys0 - Xrib[i] * SIN_G + Yrib[i] * COS_G

        # XGmod (numpy.ndarray): 旋转后的模型轮廓x坐标数组。(TurnModelOnGamma)
        self.XGmod = XGmod
        # YGmod (numpy.ndarray): 旋转后的模型轮廓y坐标数组。(TurnModelOnGamma)
        self.YGmod = YGmod
        # XGrib (numpy.ndarray): 旋转后的模型肋骨x坐标数组。(TurnModelOnGamma)
        self.XGrib = XGrib
        # YGrib (numpy.ndarray): 旋转后的模型肋骨y坐标数组。(TurnModelOnGamma)
        self.YGrib = YGrib

    def CalcModelFrequency(self):
        """
        估计模型的'Psi'振荡频率

        参数:
        V0 -- 模型的速度
        Xmin -- 分析区间的最小X值
        Xmax -- 分析区间的最大X值
        Khis -- 历史数据的采样间隔系数
        HX -- 计算步长
        Lm -- 模型的长度
        Xhis -- 历史数据中的X坐标数组
        Phis -- 历史数据中的角度Psi数组
        Vx -- 历史数据中的X方向速度数组

        返回:
        mFpsi -- 估计的'Psi'振荡频率
        FlagFrequency -- 是否成功估计频率的标志
        """
        # V0, Xmin, Xmax, Khis, HX, Lm, Vx, Xhis, Phis
        # 归一化空间坐标的起始点
        Xmin = self.Xmin
        # 归一化空间坐标的终点
        Xmax = self.Xmax
        # 初始速度
        V0 = self.V0
        # 位置步长与模型长度 Lm 的比值。
        HX = self.HX
        # 模型长度，单位为 m。
        Lm = self.Lm
        # 模型在 x 方向上的速度历史数据。
        Vx = self.Vx
        # 模型位置的历史数据，单位为 m。
        Xhis = self.Xhis
        # 模型的 'Psi' 角历史数据，单位为 弧度。
        Phis = self.Phis
        # 历史数据点数。
        Khis = self.Khis

        # 初始化变量
        Ibeg = int(Xmin / (Khis * HX * Lm)) + 1  # 起始索引
        Iend = int(Xmax / (Khis * HX * Lm)) + 1  # 结束索引
        Xnul = np.zeros(100)  # 用于存储零点交叉的X坐标
        Vnul = np.zeros(100)  # 用于存储零点交叉对应的速度
        Fpsi = np.zeros(100)  # 用于存储计算的频率
        j = 0  # 零点交叉计数器

        # 遍历历史数据，找到零点交叉点
        for i in range(Ibeg, Iend - 1):
            if Phis[i] * Phis[i + 1] <= 0.0:
                j += 1
                Xnul[j] = Xhis[i] * Lm
                Vnul[j] = Vx[i]

        # 计算频率
        work = 0.001 * 0.5 * V0 / Lm
        for i in range(1, j):
            Fpsi[i] = work * Vnul[i] / (Xnul[i + 1] - Xnul[i])  # 单位：KHz

        # 判断是否成功估计频率
        if j < 2:
            FlagFrequency = False
            mFpsi = 0.0
        elif j == 2:
            FlagFrequency = True
            mFpsi = Fpsi[1]
        else:
            FlagFrequency = True
            mFpsi = np.sum(Fpsi[1:j]) / (j - 2)

        self.FlagFrequency = FlagFrequency
        self.mFpsi = mFpsi

    def CalcClearances(self):
        """
        计算模型肋处间隙fh1、fh2和沾湿长度fdl1、fdl2
        fh1 < 0 -- 间隙
        fh1 > 0 -- 沉没深度
        """
        # 从self获取需要的参数
        Nview = self.Nview
        Ncon = self.Ncon
        HX = self.HX
        Xpr = np.array(self.Xpr)
        Ypr1 = np.array(self.Ypr1)
        Ypr2 = np.array(self.Ypr2)
        Xmod = np.array(self.Xmod)
        Ymod = np.array(self.Ymod)
        RibTan = np.array(self.RibTan)
        Part = np.array(self.Part)
        Xc = self.Xc
        BaseR = np.array(self.BaseR)

        # 初始化局部变量
        Cl1 = np.zeros(Ncon)
        Cl2 = np.zeros(Ncon)
        Jc1 = np.zeros(Ncon, dtype=int)
        Jc2 = np.zeros(Ncon, dtype=int)
        fh1 = -999.0
        fh2 = -999.0
        fdl1 = 0.0
        fdl2 = 0.0
        Sw1 = 0.0
        Sw2 = 0.0
        Imin1 = Ncon - 1  # Python 0-based indexing
        Imin2 = Ncon - 1
        FlagAhead = False

        # === 所有模型肋部的下间隙 ===
        for k in range(Ncon):  # k = 0 to Ncon-1 (对应Fortran k=1 to Ncon)
            found = False
            Y1ri = 0
            # 在腔体轮廓上寻找与模型肋相交的点
            for i in range(1, Nview):  # i = 1 to Nview-1 (对应Fortran i=2 to Nview)
                # Fortran: Xmod(2*Ncon+3-k) -> Python: 2*Ncon+3-k-1 = 2*Ncon+2-k
                # 但根据您的逻辑应该是: 2*Ncon+3-(k+1)-1 = 2*Ncon+1-k
                rib_x = Xmod[2 * Ncon + 1 - k]

                if Xpr[i] >= rib_x + 5e-4:
                    # 线性插值
                    work1 = (rib_x - Xpr[i - 1]) / HX
                    Y1ri = Ypr1[i - 1] + work1 * (Ypr1[i] - Ypr1[i - 1])
                    Jc1[k] = i - 1  # 0-based index
                    found = True
                    break

            if found:
                # Fortran: Ymod(2*Ncon+3-k) -> Python: Ymod[2*Ncon+1-k]
                Cl1[k] = Y1ri - Ymod[2 * Ncon + 1 - k]
            else:
                Cl1[k] = -999.0  # 未找到

        # --- 如果有接触，则下部浸湿部分的长度为"fdl1" ---
        contact_lower = False
        for k in range(Ncon - 1):  # k = 0 to Ncon-2 (对应Fortran k=1 to Ncon-1)
            if Cl1[k] > 0.0 and RibTan[k] > RibTan[k + 1]:  # 有接触
                if Part[k] < Xc:
                    FlagAhead = True

                Imin1 = k
                fh1 = Cl1[k]
                # 计算模型轮廓的斜率
                # Fortran: Xmod(2*Ncon+3-k) -> Python: Xmod[2*Ncon+1-k]
                # Fortran: Xmod(2*Ncon+4-k) -> Python: Xmod[2*Ncon+2-k]
                x1 = Xmod[2 * Ncon + 1 - k]
                x2 = Xmod[2 * Ncon + 2 - k]
                y1 = Ymod[2 * Ncon + 1 - k]
                y2 = Ymod[2 * Ncon + 2 - k]

                # 避免除零
                if abs(x1 - x2) < 1e-12:
                    work2 = 0.0
                else:
                    work2 = (y1 - y2) / (x1 - x2)

                # 从接触点向后搜索交点
                for i in range(Jc1[k], 1, -1):  # i from Jc1[k] down to 2
                    # 计算模型轮廓在Xpr[i]处的y值
                    yi = y2 + work2 * (Xpr[i] - x2)
                    if yi > Ypr1[i] + 1e-12:  # 考虑浮点误差
                        fdl1 = x1 - Xpr[i]
                        # 计算沾湿面积
                        if 2.0 * BaseR[k] * fh1 > 0:
                            Sw1 = fdl1 * np.sqrt(2.0 * BaseR[k] * fh1)
                        else:
                            Sw1 = 0.0
                        contact_lower = True
                        break

                if contact_lower:
                    break
            else:  # 无接触
                fdl1 = 0.0
                Sw1 = 0.0

        if not contact_lower:
            if Cl1[Ncon - 1] > 0.0:  # 尾部接触 (0-based index)
                Imin1 = Ncon - 1
                fh1 = Cl1[Ncon - 1]
                # 尾部轮廓斜率
                # Fortran: Xmod(Ncon+3) -> Python: Ncon+3-1 = Ncon+2
                # Fortran: Xmod(Ncon+4) -> Python: Ncon+4-1 = Ncon+3
                x1 = Xmod[Ncon + 2]
                x2 = Xmod[Ncon + 3]
                y1 = Ymod[Ncon + 2]
                y2 = Ymod[Ncon + 3]

                if abs(x1 - x2) < 1e-12:
                    work2 = 0.0
                else:
                    work2 = (y1 - y2) / (x1 - x2)

                for i in range(Jc1[Ncon - 1], 1, -1):  # i from Jc1[Ncon-1] down to 2
                    yi = y2 + work2 * (Xpr[i] - x2)
                    if yi > Ypr1[i] + 1e-12:
                        fdl1 = x1 - Xpr[i]
                        if 2.0 * BaseR[Ncon - 1] * fh1 > 0:
                            Sw1 = fdl1 * np.sqrt(2.0 * BaseR[Ncon - 1] * fh1)
                        else:
                            Sw1 = 0.0
                        contact_lower = True
                        break
            # 如果没有接触，找出最大间隙值
            if not contact_lower:
                fh1 = -999.0
                for k in range(Ncon):
                    if Cl1[k] > fh1:
                        fh1 = Cl1[k]
                        Imin1 = k

        # === 所有模型肋部的上间隙 ===
        for k in range(Ncon):  # k = 0 to Ncon-1 (对应Fortran k=1 to Ncon)
            found = False
            for i in range(1, Nview):  # i = 1 to Nview-1 (对应Fortran i=2 to Nview)
                # Fortran: Xmod(k+2) -> Python: (k+1)+2-1 = k+2
                rib_x = Xmod[k + 2]
                if Xpr[i] >= rib_x + 5e-4:
                    # 线性插值
                    work3 = (rib_x - Xpr[i - 1]) / HX
                    Y2ri = Ypr2[i - 1] + work3 * (Ypr2[i] - Ypr2[i - 1])
                    Jc2[k] = i - 1  # 0-based index
                    found = True
                    break

            if found:
                # Fortran: Ymod(k+2) -> Python: Ymod[k+2]
                Cl2[k] = Ymod[k + 2] - Y2ri
            else:
                Cl2[k] = -999.0  # 未找到

        # --- 如果有接触，则上部浸湿部分的长度为"fdl2" ---
        contact_upper = False
        for k in range(Ncon - 1):  # k = 0 to Ncon-2 (对应Fortran k=1 to Ncon-1)
            if Cl2[k] > 0.0 and RibTan[k] > RibTan[k + 1]:  # 有接触
                if Part[k] < Xc:
                    FlagAhead = True

                Imin2 = k
                fh2 = Cl2[k]
                # 计算模型轮廓的斜率
                # Fortran: Xmod(k+2) -> Python: Xmod[k+2]
                # Fortran: Xmod(k+1) -> Python: Xmod[k+1]
                x1 = Xmod[k + 2]
                x2 = Xmod[k + 1]
                y1 = Ymod[k + 2]
                y2 = Ymod[k + 1]

                # 避免除零
                if abs(x1 - x2) < 1e-12:
                    work4 = 0.0
                else:
                    work4 = (y1 - y2) / (x1 - x2)

                # 从接触点向后搜索交点
                for i in range(Jc2[k], 1, -1):  # i from Jc2[k] down to 2
                    # 计算模型轮廓在Xpr[i]处的y值
                    yi = y2 + work4 * (Xpr[i] - x2)
                    if yi < Ypr2[i] - 1e-12:  # 考虑浮点误差
                        fdl2 = x1 - Xpr[i]
                        # 计算沾湿面积
                        if 2.0 * BaseR[k] * fh2 > 0:
                            Sw2 = fdl2 * np.sqrt(2.0 * BaseR[k] * fh2)
                        else:
                            Sw2 = 0.0
                        contact_upper = True
                        break

                if contact_upper:
                    break
            else:  # 无接触
                fdl2 = 0.0
                Sw2 = 0.0

        if not contact_upper:
            if Cl2[Ncon - 1] > 0.0:  # 尾部接触 (0-based index)
                Imin2 = Ncon - 1
                fh2 = Cl2[Ncon - 1]
                # 尾部轮廓斜率
                # Fortran: Xmod(Ncon+2) -> Python: Ncon+2-1 = Ncon+1
                # Fortran: Xmod(Ncon+1) -> Python: Ncon+1-1 = Ncon
                x1 = Xmod[Ncon + 1]
                x2 = Xmod[Ncon]
                y1 = Ymod[Ncon + 1]
                y2 = Ymod[Ncon]

                if abs(x1 - x2) < 1e-12:
                    work4 = 0.0
                else:
                    work4 = (y1 - y2) / (x1 - x2)

                for i in range(Jc2[Ncon - 1], 1, -1):  # i from Jc2[Ncon-1] down to 2
                    yi = y2 + work4 * (Xpr[i] - x2)
                    if yi < Ypr2[i] - 1e-12:
                        fdl2 = x1 - Xpr[i]
                        if 2.0 * BaseR[Ncon - 1] * fh2 > 0:
                            Sw2 = fdl2 * np.sqrt(2.0 * BaseR[Ncon - 1] * fh2)
                        else:
                            Sw2 = 0.0
                        contact_upper = True
                        break
            # 如果没有接触，找出最大间隙值
            if not contact_upper:
                fh2 = -999.0
                for k in range(Ncon):
                    if Cl2[k] > fh2:
                        fh2 = Cl2[k]
                        Imin2 = k

        # 将计算结果更新回self
        self.Cl1 = Cl1
        self.Cl2 = Cl2
        self.Jc1 = Jc1
        self.Jc2 = Jc2
        self.fh1 = fh1
        self.fh2 = fh2
        self.fdl1 = fdl1
        self.fdl2 = fdl2
        self.Sw1 = Sw1
        self.Sw2 = Sw2
        self.Imin1 = Imin1
        self.Imin2 = Imin2
        self.FlagAhead = FlagAhead
        # return fh1, fh2, fdl1, fdl2, Sw1, Sw2, Imin1, Imin2, FlagAhead

    def CalcUnsteadyCavity(self):
        """
        计算非定常轴对称空腔形状和空腔轴线弯曲
        """
        # 从self获取需要的参数
        PI = self.PI
        Rn = self.Rn
        HX = self.HX
        Jend = self.Jend
        V0 = self.V0
        FlagPath = self.FlagPath

        # 从stabmod2获取变量
        T = np.array(self.T)
        XcBeg = np.array(self.XcBeg)
        V = np.array(self.V)
        SG = np.array(self.SG)
        Sagr = self.Sagr
        AK1 = self.AK1
        w2 = self.w2
        P1w = np.array(self.P1w)
        DS = np.array(self.DS)
        Cx0 = self.Cx0
        Alpha = np.array(self.Alpha)
        DeltaRad = self.DeltaRad
        Lc0 = self.Lc0
        Yax0 = np.array(self.Yax0)
        Rcav = np.array(self.Rcav)

        # 获取数组维度
        max_dim = Rcav.shape[0]

        # 初始化局部变量
        Si = 0.0
        work1 = 0.0
        work2 = 0.0
        DSP1 = 0.0
        DDSP1 = 0.0
        hfi = 0.0
        xi = 0.0
        Cy = 0.0
        Ipr = 0

        # 创建新的Rcav数组副本以避免修改原始数据
        Rcav_new = np.zeros_like(Rcav)
        Rcav_new[:, :] = Rcav[:, :]

        # --- Renumbering the array elements Rcav(j,i) ---
        for j in range(2, Jend + 2):  # Jend+1 for inclusive range
            start_idx = max(1, Jend - j + 1)
            end_idx = Jend - 1
            for i in range(start_idx, end_idx + 1):  # +1 for inclusive range
                if j - 1 < max_dim and i < max_dim:
                    Rcav_new[j - 1, i - 1] = Rcav[j - 2, i - 1]  # Adjusting for 0-based indexing

        DSP1 = 0.0
        DDSP1 = 0.0

        # ===== Inverse (internal) cycle along the cavity starts here ========
        for i in range(2, Jend + 2):  # i = 2 to Jend inclusive
            # Safely access array elements with bounds checking
            idx1 = Jend - i + 1
            idx2 = Jend - i + 2

            if idx1 < 0:
                idx1 = 0
            if idx2 < 0:
                idx2 = 0

            # Protect against division by zero or invalid values
            V_val = V[Jend] if V[Jend] != 0 else 1e-12

            work1 = 0.5 * (T[Jend] - XcBeg[3] / V_val - T[idx1])

            # Safely access V and SG arrays
            V_idx1 = V[idx1] if idx1 < len(V) else V[Jend]
            SG_idx1 = SG[idx1] if idx1 < len(SG) else SG[Jend]

            Si = Sagr + AK1 * work1 * (w2 * V_idx1 - SG_idx1 * work1)

            # --- Cavity deformation due to water pressure perturbation ---
            P1w_idx1 = P1w[idx1] if idx1 < len(P1w) else 0.0
            P1w_idx2 = P1w[idx2] if idx2 < len(P1w) else 0.0

            # Protect against negative time differences
            time_diff1 = max(0.0, T[Jend] - T[idx1])
            time_diff2 = max(0.0, T[Jend] - T[idx2])

            DSP1 = DSP1 + time_diff1 * P1w_idx1 + time_diff2 * P1w_idx2
            Si = Si - AK1 * HX * DSP1 / 4.0

            # --- Velocity of the cavity section expansion ---
            DS_val = AK1 * (0.5 * w2 * V_idx1 - work1 * SG_idx1)

            # --- Deformation term due to water pressure perturbation ---
            DDSP1 = DDSP1 + P1w_idx1 + P1w_idx2
            DS_val = DS_val - AK1 * HX * DDSP1 / 4.0

            # Update DS array
            if i < len(DS):
                DS[i] = DS_val

            # Store cavity radius
            if Si < 0.0:
                if Jend - 1 < Rcav_new.shape[0] and i - 1 < Rcav_new.shape[1]:
                    Rcav_new[Jend - 1, i - 1] = 0.0
                Ipr = i - 1
            else:
                radius = np.sqrt(Si / PI)
                if Jend - 1 < Rcav_new.shape[0] and i - 1 < Rcav_new.shape[1]:
                    Rcav_new[Jend - 1, i - 1] = radius
                Ipr = i - 1

        # --- Cavity axis bending due to both the lateral force on the cavitator
        #     and the cavitator displacement in the semi-body coordinate system ---
        Ypr1 = np.zeros(max_dim)
        Ypr2 = np.zeros(max_dim)

        for i in range(2, Jend + 2):
            xi = (i - 1) * HX

            # Safely access Alpha array
            alpha_idx = Jend - i + 1
            if alpha_idx < 0:
                alpha_idx = 0
            if alpha_idx >= len(Alpha):
                alpha_idx = len(Alpha) - 1

            Cy = -0.5 * Cx0 * np.sin(2.0 * (Alpha[alpha_idx] + DeltaRad))

            # Safely access SG and V arrays
            SG_idx = SG[alpha_idx] if alpha_idx < len(SG) else SG[0]
            V_idx = V[alpha_idx] if alpha_idx < len(V) and V[alpha_idx] != 0 else 1e-12

            hfi = -Cy * Rn * (0.46 - SG_idx / (V_idx ** 2) + 2.0 * xi / (Lc0 * Rn))

            # Safely access Yax0 array
            yax0_idx = alpha_idx
            if yax0_idx >= len(Yax0):
                yax0_idx = len(Yax0) - 1

            # Safely access Rcav array
            rcav_val = Rcav_new[Jend - 1, i - 1] if Jend - 1 < Rcav_new.shape[0] and i - 1 < Rcav_new.shape[1] else 0.0

            if i < max_dim:
                Ypr2[i - 1] = Yax0[yax0_idx] + hfi + rcav_val
                Ypr1[i - 1] = Yax0[yax0_idx] + hfi - rcav_val

        # 将计算结果推送回self
        self.Rcav = Rcav_new
        self.DS = DS
        self.Ypr1 = Ypr1
        self.Ypr2 = Ypr2
        self.Ipr = Ipr

    ##################################################################################################

    def ExtraUpperCav(self, x):
        """
        近水面上空腔轮廓的外推

        使用二次多项式拟合上空腔轮廓的最后三个点，
        然后外推到指定x坐标位置

        参数:
        x (float): 需要外推的点的x坐标

        返回:
        y (float): 外推得到的y坐标
        """
        # 获取需要的类属性
        Xpr = self.Xpr  # 空泡轮廓的x坐标数组
        Ypr2 = self.Ypr2  # 上空腔轮廓的y坐标数组
        Ipr = self.Ipr  # 最后一个有效空泡轮廓的索引

        # 构建线性方程组 A * coeff = B
        # 使用最后三个点拟合二次多项式 y = a*x² + b*x + c

        # 构建系数矩阵 A
        A = np.zeros((3, 3))
        A[0, 0] = Xpr[Ipr - 2] ** 2
        A[1, 0] = Xpr[Ipr - 1] ** 2
        A[2, 0] = Xpr[Ipr] ** 2
        A[0, 1] = Xpr[Ipr - 2]
        A[1, 1] = Xpr[Ipr - 1]
        A[2, 1] = Xpr[Ipr]
        A[0, 2] = 1.0
        A[1, 2] = 1.0
        A[2, 2] = 1.0

        # 构建右端向量 B
        B = np.zeros(3)
        B[0] = Ypr2[Ipr - 2]
        B[1] = Ypr2[Ipr - 1]
        B[2] = Ypr2[Ipr]

        # 求解线性方程组得到多项式系数
        try:
            coeff = np.linalg.solve(A, B)
            # 计算外推点的y坐标: y = a*x² + b*x + c
            y = coeff[0] * x ** 2 + coeff[1] * x + coeff[2]
            return y
        except np.linalg.LinAlgError:
            # 如果矩阵奇异，使用线性插值作为备选方案
            print("警告: 矩阵奇异，使用线性插值代替二次拟合")
            # 使用最后两个点进行线性插值
            y = Ypr2[Ipr - 1] + (x - Xpr[Ipr - 1]) * (Ypr2[Ipr] - Ypr2[Ipr - 1]) / (Xpr[Ipr] - Xpr[Ipr - 1])
            return y

    def ExtraLowerCav(self, x):
        """
        下空腔轮廓的外推

        使用二次多项式拟合下空腔轮廓的最后三个点，
        然后外推到指定x坐标位置

        参数:
        x (float): 需要外推的点的x坐标

        返回:
        y (float): 外推得到的y坐标
        """
        # 获取需要的类属性
        Xpr = self.Xpr  # 空泡轮廓的x坐标数组
        Ypr1 = self.Ypr1  # 下空腔轮廓的y坐标数组
        Ipr = self.Ipr  # 最后一个有效空泡轮廓的索引

        # 构建线性方程组 A * coeff = B
        # 使用最后三个点拟合二次多项式 y = a*x² + b*x + c

        # 构建系数矩阵 A
        A = np.zeros((3, 3))
        A[0, 0] = Xpr[Ipr - 2] ** 2
        A[1, 0] = Xpr[Ipr - 1] ** 2
        A[2, 0] = Xpr[Ipr] ** 2
        A[0, 1] = Xpr[Ipr - 2]
        A[1, 1] = Xpr[Ipr - 1]
        A[2, 1] = Xpr[Ipr]
        A[0, 2] = 1.0
        A[1, 2] = 1.0
        A[2, 2] = 1.0

        # 构建右端向量 B
        B = np.zeros(3)
        B[0] = Ypr1[Ipr - 2]
        B[1] = Ypr1[Ipr - 1]
        B[2] = Ypr1[Ipr]

        # 求解线性方程组得到多项式系数
        try:
            coeff = np.linalg.solve(A, B)
            # 计算外推点的y坐标: y = a*x² + b*x + c
            y = coeff[0] * x ** 2 + coeff[1] * x + coeff[2]
            return y
        except np.linalg.LinAlgError:
            # 如果矩阵奇异，使用线性插值作为备选方案
            print("警告: 矩阵奇异，使用线性插值代替二次拟合")
            # 使用最后两个点进行线性插值
            y = Ypr1[Ipr - 1] + (x - Xpr[Ipr - 1]) * (Ypr1[Ipr] - Ypr1[Ipr - 1]) / (Xpr[Ipr] - Xpr[Ipr - 1])
            return y

    def Interpol1(self, n, x, f, x1):
        """
        函数f(x)的线性插值

        参数:
        n (int): 数组x和f的长度
        x (numpy.ndarray): 自变量数组
        f (numpy.ndarray): 函数值数组
        x1 (float): 需要插值的点

        返回:
        f1 (float): 在x1处的插值结果
        """
        for i in range(1, n):
            if x1 >= x[i - 1] and x1 <= x[i]:
                f1 = f[i - 1] + (x1 - x[i - 1]) * (f[i] - f[i - 1]) / (x[i] - x[i - 1])
                return f1

        # 如果x1不在x的范围内，返回0
        f1 = 0.0
        return f1

    def DSIMQ(self, A, B, N):
        """
        求解线性方程组 AX = B

        参数:
        A (numpy.ndarray): 系数矩阵，按列存储的一维数组，大小为N*N
        B (numpy.ndarray): 常数向量，长度为N，求解后将被解向量X替换
        N (int): 方程个数和变量数

        返回:
        KS (int): 输出标志
            0 表示正常解
            1 表示方程组奇异
        """

        # 从self中提取需要的参数（如果有的话）
        # 这里主要使用传入的参数

        # 初始化局部变量
        TOL = 0.0
        KS = 0
        JJ = -N

        # 创建A和B的副本，避免修改原始数据
        A_work = A.copy()
        B_work = B.copy()

        # --- FORWARD SOLUTION --- 前向消元
        for J in range(N):
            JY = J + 1
            JJ = JJ + N + 1
            BIGA = 0.0
            IT = JJ - J
            IMAX = J

            # --- SEARCH FOR MAXIMUM COEFFICIENT IN COLUMN --- 在列中搜索最大系数
            for I in range(J, N):
                IJ = IT + I
                if abs(BIGA) - abs(A_work[IJ]) < 0.0:
                    BIGA = A_work[IJ]
                    IMAX = I

            # --- TEST FOR PIVOT LESS THAN TOLERANCE (SINGULAR MATRIX) --- 测试主元是否小于容差（奇异矩阵）
            if abs(BIGA) - TOL <= 0.0:
                KS = 1
                # 将结果写回self
                self.KS = KS
                return KS

            # --- INTERCHANGE ROWS IF NECESSARY --- 必要时交换行
            I1 = J + N * (J - 2)
            IT = IMAX - J

            for K in range(J, N):
                I1 = I1 + N
                I2 = I1 + IT
                SAVE1 = A_work[I1]
                A_work[I1] = A_work[I2]
                A_work[I2] = SAVE1

                # --- DIVIDE EQUATION BY LEADING COEFFICIENT --- 用主系数除方程
                A_work[I1] = A_work[I1] / BIGA

            SAVE1 = B_work[IMAX]
            B_work[IMAX] = B_work[J]
            B_work[J] = SAVE1 / BIGA

            # --- ELIMINATE NEXT VARIABLE --- 消去下一个变量
            if J != N - 1:  # 注意：Python索引从0开始，所以是N-1
                IQS = N * (J - 1)

                for IX in range(JY, N):
                    IXJ = IQS + IX
                    IT = J - IX

                    for JX in range(JY, N):
                        IXJX = N * (JX - 1) + IX
                        JJX = IXJX + IT
                        A_work[IXJX] = A_work[IXJX] - A_work[IXJ] * A_work[JJX]

                    B_work[IX] = B_work[IX] - B_work[J] * A_work[IXJ]

        # --- BACK SOLUTION --- 回代
        NY = N - 1
        IT = N * N

        for J in range(NY):
            IA = IT - J - 1  # 注意：Python索引从0开始
            IB = N - J - 2  # 注意：Python索引从0开始
            IC = N - 1  # 注意：Python索引从0开始

            for K in range(J + 1):
                B_work[IB] = B_work[IB] - A_work[IA] * B_work[IC]
                IA = IA - N
                IC = IC - 1

        # 将结果写回self和输入参数
        # 注意：根据Fortran代码，B被解向量X替换
        for i in range(N):
            B[i] = B_work[i]

        # 将输出标志写回self
        self.KS = KS

        return KS

    def RK4(self, Y, DYDX, N, X, H, DERIVS):
        """
        使用经典四阶龙格-库塔法（RK4）执行一步积分：
            从 x = X 积分到 x = X + H，
            初始状态为 Y，初始导数为 DYDX，
            微分方程由 DERIVS 定义。

        参数说明：
        ----------
        Y : array-like, shape (N,)
            当前状态向量 y(X)。
        DYDX : array-like, shape (N,)
            当前导数向量 dy/dx(X)，即 DERIVS(X, Y)。
        N : int
            状态变量个数（微分方程个数）。
        X : float
            当前自变量（积分起点）。
        H : float
            积分步长（必须为标量）。
        DERIVS : callable
            导数函数，签名为：DERIVS(x, y) -> dydx（返回 shape=(N,) 的数组）。

        返回值：
        -------
        YOUT : np.ndarray, shape (N,)
            积分后状态 y(X + H)。

        数值公式（经典 RK4）：
        --------------------
        k1 = f(x_n, y_n)
        k2 = f(x_n + h/2, y_n + h/2 * k1)
        k3 = f(x_n + h/2, y_n + h/2 * k2)
        k4 = f(x_n + h,   y_n + h   * k3)
        y_{n+1} = y_n + (h/6) * (k1 + 2*k2 + 2*k3 + k4)
        """
        import numpy as np

        # 转换为 NumPy 数组，确保数值稳定性
        Y = np.asarray(Y, dtype=float)
        DYDX = np.asarray(DYDX, dtype=float)

        # 预计算常用量
        HH = 0.5 * H  # h/2
        H6 = H / 6.0  # h/6
        XH = X + HH  # x + h/2

        # ---- 计算 k1（已由 DYDX 给出）----
        K1 = DYDX

        # ---- 计算 k2 ----
        YT = Y + HH * K1
        K2 = DERIVS(XH, YT)

        # ---- 计算 k3 ----
        YT = Y + HH * K2
        K3 = DERIVS(XH, YT)

        # ---- 计算 k4 ----
        YT = Y + H * K3
        K4 = DERIVS(X + H, YT)

        # ---- 组合四阶 RK 公式 ----
        YOUT = Y + H6 * (K1 + 2.0 * K2 + 2.0 * K3 + K4)

        return YOUT

    def RKDUMB(self, Y1, N, X1, X2, NSTEP, DERIVS):
        """
        使用 RK4 在区间 [X1, X2] 上积分 N 个一阶常微分方程。

        参数:
            Y1 (array-like): 初值 y(X1)，长度为 N。
            N (int): 方程个数。
            X1 (float): 积分起点。
            X2 (float): 积分终点。
            NSTEP (int): 积分步数。
            DERIVS (callable): 导数函数，签名为 DERIVS(x, y, f)。

        返回:
            Y2 (np.ndarray): y(X2) 的值。
        """
        Y = np.array(Y1, dtype=float)
        X = X1
        H = (X2 - X1) / NSTEP

        for _ in range(NSTEP):
            # 计算当前导数
            DY = np.zeros(N)
            DY = DERIVS(X, Y)
            # 执行一步 RK4
            Y = self.RK4(Y, DY, N, X, H, DERIVS)
            X += H

        return Y

    def DerivDyn(self, x, Y):
        """
        计算超空泡航行体动力学常微分方程组（SODE）右侧导数项 F(5)。

        该函数对应 Fortran 子程序 DerivDyn，用于 RK4/RKDUMB 积分器中。

        参数说明：
        - x (float): 当前无量纲位置（积分自变量，本例中未显式使用，但保留以兼容通用接口）。
        - Y (list or ndarray): 当前状态向量，长度为5，依次为：
            Y[0] = Vx1: 贴体坐标系中质心x方向速度分量（无量纲）
            Y[1] = Vy1: 贴体坐标系中质心y方向速度分量（无量纲）
            Y[2] = Omega: 无量纲角速度（实际角速度 * Lm / V0）
            Y[3] = Psi: 当前俯仰角（弧度）
            Y[4] = Yabs: 质心绝对y坐标（无量纲）
        - F (list or ndarray): 输出导数数组，长度为5，函数内部**就地修改** F[i]。

        注意：
        - 所有物理量均为无量纲（基于 Lm 和 V0 归一化）。
        - 推力、冲击力、滑行力等均已在 CalcForces 中计算并存储于 self。
        """
        # 从 self 中提取所需参数（这些应在 Dynamics 主循环前初始化）
        PI = self.PI
        Rn = self.Rn  # 空化器半径，单位毫米(CalcParameters)
        B3 = self.B3  # 力系数归一化因子：B3 = B2 * 500 * Lm^3 / TMkg
        B4 = self.B4  # 力矩系数归一化因子：B4 = B2 * 500 * Lm^5 / Ic
        Cpr = self.Cpr  # 推力系数比例（界面输入，Cpr = C_prop / Cx0）
        Tpr = self.Tpr  # 推力作用时间阈值（ms）
        V0 = self.V0  # 初始速度（m/s）
        Lm = self.Lm  # 模型长度（m）
        Tabs = self.Tabs  # 当前绝对时间（s）
        Cx0 = self.Cx0  # 空化数为0时的阻力系数（圆盘取0.8275）
        DeltaRad = self.DeltaRad  # 空化器倾角（弧度）
        COS_D = self.COS_D  # cos(Delta)
        SIN_D = self.SIN_D  # sin(Delta)
        GammaRad = self.GammaRad  # 攻角（弧度）
        Fr2 = self.Fr2  # 初始弗劳德数平方
        Csx = self.Csx  # 轴向滑行力系数
        Csy = self.Csy  # 横向滑行力系数
        Cnm = self.Cnm  # 空化器力矩系数
        Csm = self.Csm  # 滑行力矩系数
        Xc = self.Xc  # 质心无量纲位置
        fh1 = self.fh1  # 下壁面间隙（正值表示浸湿）
        fh2 = self.fh2  # 上壁面间隙
        BaseR = self.BaseR  # 各节末端无量纲半径
        Ncon = self.Ncon  # 模型节数

        # 状态变量解包（Python 索引从 0 开始）
        Vx1 = Y[0]
        Vy1 = Y[1]
        Omega = Y[2]
        Psi = Y[3]
        Yabs = Y[4]

        # 1. 计算当前攻角 Alpha（弧度）
        # 注意：使用 arctan2 更安全，但为保持与 Fortran 一致，此处仍用 -arctan(Vy1/Vx1)
        if abs(Vx1) < 1e-12:
            Vx1 = 1e-12  # 避免除零
        Alphi = -np.arctan2(Vy1, Vx1)

        # 2. 计算当前无量纲速度大小
        Vi = np.sqrt(Vx1 ** 2 + Vy1 ** 2)
        if Vi < 1e-12:
            Vi = 1e-12  # 避免除零

        # 3. 计算辅助因子 work = 1 / (Vi * cos(Psi - Alpha))
        delta_psi_alpha = Psi - Alphi
        cos_term = np.cos(delta_psi_alpha)
        if abs(cos_term) < 1e-12:
            cos_term = 1e-12
        work = 1.0 / (Vi * cos_term)

        # 4. 空化器法向力系数（贴体坐标系）
        work1 = np.cos(Alphi + DeltaRad)
        Cnxi = Cx0 * work1 * COS_D  # x方向法向力系数
        Cnyi = -Cx0 * work1 * SIN_D  # y方向法向力系数

        # 5. 推力系数 Cpri（仅在推力开启时间内有效）
        # Tabs 单位为秒，Tpr 单位为毫秒，需统一
        if Tabs * 1000.0 * Lm / V0 <= Tpr:
            Cpri = Cx0 * Cpr * np.cos(Alphi)  # 推力开启
        else:
            Cpri = 0.0  # 推力关闭

        # 6. 冲击力模型（模拟模型与空泡壁接触产生的附加力）
        KKK = 1.5  # 冲击力强度系数（相对于重力）
        # 下壁面冲击（fh1 > 0 且 角速度 > 0）
        KK1 = KKK if (fh1 >= 0.05 * BaseR[Ncon - 1] and Omega > 0) else 0.0
        # 上壁面冲击（fh2 > 0 且 角速度 < 0）
        KK2 = -KKK if (fh2 >= 0.05 * BaseR[Ncon - 1] and Omega < 0) else 0.0
        KK = KK1 + KK2  # 总冲击力系数（无量纲）

        # 7. 冲击力矩模型
        PZWZ = 0.90  # 冲击力作用位置（无量纲，距头部0.9L）
        Armcj = PZWZ - Xc  # 冲击力臂（相对于质心）
        Ccjm = -Armcj * KK  # 冲击力矩系数（与 Csm 符号规则一致）

        # 8. 重力项角度（固定坐标系中的总倾角）
        work2 = Psi + GammaRad

        # 9. 构造导数向量 F
        F = np.empty(5)
        # F[0] = d(Vx1)/dx
        F[0] = work * (Omega * Vy1 + B3 * Vi ** 2 * (Cpri - Csx - Cnxi) - np.sin(work2) / Fr2)

        # F[1] = d(Vy1)/dx
        # 注意：冲击力项 KK / Vi**2 是为了保持无量纲一致性
        # 这里为了保持一致性，先改为原版，看看结果到底是不是不一样
        # F[1] = work * (-Omega * Vx1 + B3 * Vi ** 2 * (Cnyi + Csy + KK / (Vi ** 2)) - np.cos(work2) / Fr2)
        F[1] = work * (-Omega * Vx1 + B3 * Vi ** 2 * (Cnyi + Csy) - np.cos(work2) / Fr2)

        # F[2] = d(Omega)/dx
        # 这里为了保持一致性，先改为原版，看看结果到底是不是不一样
        # F[2] = work * B4 * Vi ** 2 * (Cnm + Csm + Ccjm / (Vi ** 2))
        F[2] = work * B4 * Vi ** 2 * (Cnm + Csm)

        # F[3] = d(Psi)/dx
        F[3] = work * Omega

        # F[4] = d(Yabs)/dx = tan(Psi - Alpha)
        F[4] = np.tan(Y[3] - Alphi)

        return F

    def CalcSODE(self):
        """
        积分超空泡模型动力学的常微分方程组（SODE）。

        该函数对应 Fortran 子程序 CalcSODE，用于从当前步（Jend-1）推进到下一步（Jend）。

        输入状态（来自上一步）：
            self.Vx1[Jend-1], self.Vy1[Jend-1], self.Omega, self.PsiPre, self.Yabs

        输出状态（更新为当前步）：
            self.Vx1[Jend], self.Vy1[Jend], self.Omega, self.Psi, self.Yabs
            同时更新：self.V[Jend], self.Alpha[Jend], self.T[Jend]

        使用 RKDUMB 进行单步（NSTEP=1）积分，步长为 self.HX。
        """

        # 从 self 提取当前状态（上一步结果）
        Jend = self.Jend
        HX = self.HX
        Xn = self.Xn

        # 构造初值向量 Y1 = [Vx1, Vy1, Omega, PsiPre, Yabs]
        Y1 = np.array([
            self.Vx1[Jend - 1],
            self.Vy1[Jend - 1],
            self.Omega,
            self.PsiPre,
            self.Yabs
        ])

        # 调用 RKDUMB 进行单步积分（从 Xn - HX 到 Xn，1 步）
        # 注意：DerivDyn 是返回型函数，签名为 f(x, y) -> dydx
        Y2 = self.RKDUMB(Y1, 5, Xn - HX, Xn, 1, self.DerivDyn)

        # 更新当前状态
        self.Vx1[Jend] = Y2[0]
        self.Vy1[Jend] = Y2[1]
        self.Omega = Y2[2]
        self.Psi = Y2[3]
        self.Yabs = Y2[4]

        # 计算当前绝对速度大小
        self.V[Jend] = np.sqrt(self.Vx1[Jend] ** 2 + self.Vy1[Jend] ** 2)

        # 计算当前攻角 Alpha（弧度）
        # 注意：当 Vx1 接近 0 时，使用 arctan2 更安全，但为保持与 Fortran 一致，此处仍用 -arctan(Vy1/Vx1)
        Vx = self.Vx1[Jend]
        Vy = self.Vy1[Jend]
        if abs(Vx) < 1e-12:
            Vx = 1e-12
        self.Alpha[Jend] = -np.arctan(Vy / Vx)

        # 计算当前时间 T(Jend)（使用梯形法积分 dt = dx / (Vx * cos(Psi - Alpha))）
        # 上一步的时间导数项
        delta_psi_alpha_prev = self.PsiPre - self.Alpha[Jend - 1]
        cos_prev = np.cos(delta_psi_alpha_prev)
        if abs(cos_prev) < 1e-12:
            cos_prev = 1e-12
        work1 = 1.0 / (self.Vx1[Jend - 1] * cos_prev)

        # 当前步的时间导数项
        delta_psi_alpha_curr = self.Psi - self.Alpha[Jend]
        cos_curr = np.cos(delta_psi_alpha_curr)
        if abs(cos_curr) < 1e-12:
            cos_curr = 1e-12
        work2 = 1.0 / (self.Vx1[Jend] * cos_curr)

        # 梯形积分：T(Jend) = T(Jend-1) + (HX/2) * (work1 + work2)
        self.T[Jend] = self.T[Jend - 1] + 0.5 * HX * (work1 + work2)

        # 更新 PsiPre 为当前 Psi，供下一步使用
        self.PsiPre = self.Psi

    def plot_dynamics(self, show_plot=False, save_plot=False, plot_filename="dynamics_plot.png"):
        """
        绘制模型和空腔轮廓，适用于不同攻角和俯仰角条件下的超空泡模型。

        参数:
        show_plot (bool): 是否显示图形
        save_plot (bool): 是否保存图形
        plot_filename (str): 保存图形的文件名
        """

        # 设置图形
        plt.figure(figsize=(12, 8))

        # === 绘制水区域 ===
        if self.Jend < self.Nview:
            ax = plt.gca()
            # 水区域（左侧）
            water_x1 = [-0.02 * self.Scale, -0.02 * self.Scale, self.Xpr[self.Jend - 1], self.Xpr[self.Jend - 1]]
            water_y1 = [-0.199 * self.Scale, 0.198 * self.Scale, 0.198 * self.Scale, -0.199 * self.Scale]
            ax.fill(water_x1, water_y1, color='lightblue', alpha=0.7)

            # 水外区域（右侧）
            water_x2 = [self.Xpr[self.Jend - 1], self.Xpr[self.Jend - 1], 1.1 * self.Scale, 1.1 * self.Scale]
            water_y2 = [-0.199 * self.Scale, 0.198 * self.Scale, 0.198 * self.Scale, -0.199 * self.Scale]
            ax.fill(water_x2, water_y2, color='white', alpha=0.9)
        else:
            ax = plt.gca()
            # 绘制整个水区域
            water_x = [-0.02 * self.Scale, -0.02 * self.Scale, 1.1 * self.Scale, 1.1 * self.Scale]
            water_y = [-0.199 * self.Scale, 0.198 * self.Scale, 0.198 * self.Scale, -0.199 * self.Scale]
            ax.fill(water_x, water_y, color='lightblue', alpha=0.7)

        # === 绘制模型主体 ===
        # if (self.SwDisp == 1 or self.FlagFirst or self.FlagPause or self.FlagStop or
        #         self.FlagWashed or self.FlagSurface or self.FlagBroken or self.FlagFinish):
        # 创建多边形表示模型
        model_polygon = plt.Polygon(list(zip(self.Xmod, self.Ymod)), color='green', alpha=0.8)
        ax.add_patch(model_polygon)

        # === 绘制网格 ===
        plt.grid(True, linestyle='--', alpha=0.7)

        # === 绘制移动水面 ===
        if self.Jend < self.Nview and self.Jend - 1 < len(self.Xpr):
            if self.Xpr[self.Jend - 1] < 1.1 * self.Scale:
                plt.plot([self.Xpr[self.Jend - 1], self.Xpr[self.Jend - 1]],
                         [-0.2 * self.Scale, 0.2 * self.Scale], 'b-', linewidth=2)
            else:
                plt.plot([self.Xpr[self.Jend - 1], self.Xpr[self.Jend - 1]],
                         [-0.2 * self.Scale, 0.2 * self.Scale], 'lightblue', linewidth=2)

        # === 绘制模型轮廓和肋条 ===
        # 模型轮廓
        plt.plot(self.Xmod, self.Ymod, 'k-', linewidth=2)

        # 肋条
        if hasattr(self, 'Xrib') and hasattr(self, 'Yrib') and self.Ncon > 1:
            for i in range(self.Ncon - 1):
                idx1 = 2 * i
                idx2 = 2 * i + 1
                if idx2 < len(self.Xrib):
                    plt.plot([self.Xrib[idx1], self.Xrib[idx2]],
                             [self.Yrib[idx1], self.Yrib[idx2]], 'k-', linewidth=1)

        # === 绘制质心 ===
        plt.plot(self.Xc, 0, 'ko', markersize=5)

        # === 绘制断裂线（如果模型断裂） ===
        if self.FlagBroken and hasattr(self, 'X_SGmax'):
            # 计算断裂线位置
            if hasattr(self, 'BaseR') and len(self.BaseR) > 0:
                # 获取最后一节的半径
                last_radius = self.BaseR[-1] if len(self.BaseR) > 0 else 0.1
                y0break1 = -last_radius - 0.05
                y0break2 = last_radius + 0.05
            else:
                y0break1 = -0.1
                y0break2 = 0.1

            # 修正：当Psi非0时，确保断裂线与模型轴线垂直
            if abs(self.Psi) > 1e-12:  # Psi非0
                # 计算断裂线中点（在旋转坐标系中）
                x_mid = self.X_SGmax
                y_mid = 0.0

                # 断裂线长度（垂直于模型轴线）
                length = abs(y0break2 - y0break1)

                # 计算断裂线两个端点在全局坐标系中的位置
                # 由于模型旋转了Psi角度，断裂线需要与之垂直，所以用Psi + pi/2计算方向
                half_length = length / 2.0

                # 端点1
                xbreak1 = x_mid - half_length * np.sin(self.Psi)
                ybreak1 = y_mid + half_length * np.cos(self.Psi)

                # 端点2
                xbreak2 = x_mid + half_length * np.sin(self.Psi)
                ybreak2 = y_mid - half_length * np.cos(self.Psi)
            else:  # Psi为0，直接使用垂直线
                xbreak1 = self.X_SGmax
                ybreak1 = y0break1
                xbreak2 = self.X_SGmax
                ybreak2 = y0break2

            # 绘制断裂线
            plt.plot([xbreak1, xbreak2], [ybreak1, ybreak2], 'r-', linewidth=3)

            # 添加断裂线图例
            legend_x = 0.81 * self.Scale
            legend_y = 0.17 * self.Scale
            plt.plot([legend_x, legend_x + 0.08 * self.Scale], [legend_y, legend_y], 'r-', linewidth=2)
            plt.text(0.92 * self.Scale, 0.187 * self.Scale, 'break line', fontsize=8)

        # === 绘制空腔轮廓 ===
        if hasattr(self, 'FlagCav') and self.FlagCav and not self.FlagFirst:

            # 修正：获取当前空泡轴线的y偏移
            current_Yax0 = self.Yax0[self.Jend] if hasattr(self, 'Yax0') else 0.0

            # --- 上部空腔轮廓 ---
            # 从上分离点开始
            if len(self.Xmod) > 1 and len(self.Ymod) > 1:
                # 准备上部轮廓点的列表
                upper_x = [self.Xmod[1]]  # 上分离点x
                upper_y = [self.Ymod[1]]  # 上分离点y

                # 计算并添加其他点
                for i in range(2, self.Ipr + 1):
                    if i - 1 < len(self.Xpr):
                        x_point = self.Xpr[i - 1]
                        if x_point < self.XcBeg[1]:  # 区域1
                            RcBegX = self.Rn * (1.0 + 3.0 * x_point / self.Rn) ** (1 / 3)
                            y_point = RcBegX + current_Yax0
                        elif x_point < self.XcBeg[2]:  # 区域2
                            if i == 2:  # 第一个点需要特殊处理
                                RcBegX1 = self.Rn * (1.0 + 3.0 * self.XcBeg[1] / self.Rn) ** (1 / 3)
                                upper_x.append(self.XcBeg[1])
                                upper_y.append(RcBegX1 + current_Yax0)
                            RcBegX = self.Rn * (1.0 + 3.0 * x_point / self.Rn) ** (1 / 3)
                            y_point = RcBegX + current_Yax0
                        elif x_point < self.XcBeg[3]:  # 区域3
                            if i == 2:  # 第一个点需要特殊处理
                                RcBegX1 = self.Rn * (1.0 + 3.0 * self.XcBeg[1] / self.Rn) ** (1 / 3)
                                RcBegX2 = self.Rn * (1.0 + 3.0 * self.XcBeg[2] / self.Rn) ** (1 / 3)
                                upper_x.append(self.XcBeg[1])
                                upper_y.append(RcBegX1 + current_Yax0)
                                upper_x.append(self.XcBeg[2])
                                upper_y.append(RcBegX2 + current_Yax0)
                            RcBegX = self.Rn * (1.0 + 3.0 * x_point / self.Rn) ** (1 / 3)
                            y_point = RcBegX + current_Yax0
                        else:  # 区域4
                            if i == 2:  # 第一个点需要特殊处理
                                upper_x.append(self.XcBeg[1])
                                upper_y.append(self.RcBeg[1] + current_Yax0)
                                upper_x.append(self.XcBeg[2])
                                upper_y.append(self.RcBeg[2] + current_Yax0)
                                upper_x.append(self.XcBeg[3])
                                upper_y.append(self.RcBeg[3] + current_Yax0)
                            if hasattr(self, 'Ypr2') and i - 1 < len(self.Ypr2):
                                y_point = self.Ypr2[i - 1]
                            else:
                                y_point = 0.0
                        upper_x.append(x_point)
                        upper_y.append(y_point)

                # 绘制上部空腔轮廓
                plt.plot(upper_x, upper_y, 'b-', linewidth=2)

            # --- 下部空腔轮廓 ---
            # 从下分离点开始
            if len(self.Xmod) > 2 * self.Ncon + 2 and len(self.Ymod) > 2 * self.Ncon + 2:
                # 准备下部轮廓点的列表
                lower_x = [self.Xmod[2 * self.Ncon + 2]]  # 下分离点x
                lower_y = [self.Ymod[2 * self.Ncon + 2]]  # 下分离点y

                # 计算并添加其他点
                for i in range(2, self.Ipr + 1):
                    if i - 1 < len(self.Xpr):
                        x_point = self.Xpr[i - 1]
                        if x_point < self.XcBeg[1]:  # 区域1
                            RcBegX = self.Rn * (1.0 + 3.0 * x_point / self.Rn) ** (1 / 3)
                            y_point = -RcBegX + current_Yax0
                        elif x_point < self.XcBeg[2]:  # 区域2
                            if i == 2:  # 第一个点需要特殊处理
                                RcBegX1 = self.Rn * (1.0 + 3.0 * self.XcBeg[1] / self.Rn) ** (1 / 3)
                                lower_x.append(self.XcBeg[1])
                                lower_y.append(-RcBegX1 + current_Yax0)
                            RcBegX = self.Rn * (1.0 + 3.0 * x_point / self.Rn) ** (1 / 3)
                            y_point = -RcBegX + current_Yax0
                        elif x_point < self.XcBeg[3]:  # 区域3
                            if i == 2:  # 第一个点需要特殊处理
                                RcBegX1 = self.Rn * (1.0 + 3.0 * self.XcBeg[1] / self.Rn) ** (1 / 3)
                                RcBegX2 = self.Rn * (1.0 + 3.0 * self.XcBeg[2] / self.Rn) ** (1 / 3)
                                lower_x.append(self.XcBeg[1])
                                lower_y.append(-RcBegX1 + current_Yax0)
                                lower_x.append(self.XcBeg[2])
                                lower_y.append(-RcBegX2 + current_Yax0)
                            RcBegX = self.Rn * (1.0 + 3.0 * x_point / self.Rn) ** (1 / 3)
                            y_point = -RcBegX + current_Yax0
                        else:  # 区域4
                            if i == 2:  # 第一个点需要特殊处理
                                lower_x.append(self.XcBeg[1])
                                lower_y.append(-self.RcBeg[1] + current_Yax0)
                                lower_x.append(self.XcBeg[2])
                                lower_y.append(-self.RcBeg[2] + current_Yax0)
                                lower_x.append(self.XcBeg[3])
                                lower_y.append(-self.RcBeg[3] + current_Yax0)
                            if hasattr(self, 'Ypr1') and i - 1 < len(self.Ypr1):
                                y_point = self.Ypr1[i - 1]
                            else:
                                y_point = 0.0
                        lower_x.append(x_point)
                        lower_y.append(y_point)

                # 绘制下部空腔轮廓
                plt.plot(lower_x, lower_y, 'b-', linewidth=2)

        # === 比例尺图例 ===
        if (self.SwShow == 0 and (self.SwDisp == 1 or self.FlagFirst or self.FlagPause or self.FlagStop or
                                  self.FlagWashed or self.FlagSurface or self.FlagBroken or self.FlagFinish)):
            plt.text(0.05 * self.Scale, 0.2 * self.Scale, f'Scale = {self.Scale:.2f}', fontsize=9)
            if self.FlagFirst:
                self.FlagFirst = False

        # === 设置坐标轴范围 ===
        plt.xlim(-0.1 * self.Scale, 1.1 * self.Scale)
        plt.ylim(-0.2 * self.Scale, 0.2 * self.Scale)

        # === 设置标题 ===
        plt.title('DYNAMICS OF SUPERCAVITATING MODEL', fontsize=14)
        plt.xlabel('x / L', fontsize=10)
        plt.ylabel('y / L', fontsize=10)

        # === 显示当前运动参数 ===
        param_text = f"""
        Current Motion Parameters:
        t = {self.Tabs * self.Lm * 1000 / self.V0:.4f} ms
        x = {self.Xabs * self.Lm:.4f} m
        y = {self.Yabs * self.Lm * 100:.4f} cm
        Vx/V0 = {self.VxAbs:.4f}
        Vy = {self.VyAbs * self.V0:.4f} m/s
        Psi = {self.Psi:.5f} rad
        Alpha = {self.AlphaCur:.5f} rad
        Omega = {self.Omega * self.V0 / self.Lm:.5f} rad/s
        """
        plt.figtext(0.2, 0.1, param_text, fontsize=9, family='monospace')

        # === 显示接触次数 ===
        contact_text = f"N contacts = {self.Ncont}"
        plt.figtext(0.15, 0.2, contact_text, fontsize=10)

        # === 显示水压扰动 ===
        if hasattr(self, 'Head0') and hasattr(self, 'P1n'):
            pressure_text = f"Pw = {self.Head0 * self.P1n / 1e6:.4f} MPa"
            plt.figtext(0.45, 0.2, pressure_text, fontsize=10)

        # === 显示最小间隙和湿润长度 ===
        if hasattr(self, 'FlagPenetr') and self.FlagPenetr:
            if hasattr(self, 'fh1') and hasattr(self, 'fh2') and hasattr(self, 'fdl1') and hasattr(self, 'fdl2'):
                if hasattr(self, 'Imin1') and hasattr(self, 'Imin2') and hasattr(self, 'BaseR'):
                    clearance_text = f"""
                    MINIMAL CLEARANCES:
                    h2 = {-self.fh2 * self.Lmm:.4f} mm (rib {self.Imin2})
                    h1 = {-self.fh1 * self.Lmm:.4f} mm (rib {self.Imin1})
                    WETTED LENGTHS:
                    l2 = {self.fdl2 * self.Lmm:.4f} mm
                    l1 = {self.fdl1 * self.Lmm:.4f} mm
                    """
                    plt.figtext(0.32, 0.7, clearance_text, fontsize=9, family='monospace')

        # === 显示力系数 ===
        force_text = f"""
        FORCE COEFFICIENTS:
        Cpr = {self.Cpr if hasattr(self, 'Tpr') and self.Tabs * 1000 * self.Lm / self.V0 <= self.Tpr else 0:.4f}
        Cnx = {-self.Cnx:.4f}
        Cny = {self.Cny:.4f}
        Cnm = {self.Cnm:.4f}
        Csx = {-self.Csx:.4f}
        Csy = {self.Csy:.4f}
        Csm = {self.Csm:.4f}
        """
        plt.figtext(0.55, 0.1, force_text, fontsize=9, family='monospace')

        # === 显示最大应力 ===
        if hasattr(self, 'SGmax') and hasattr(self, 'TAUmax'):
            stress_text = f"""
            MAXIMAL STRESSES:
            Sigma_max = {self.SGmax:.2f} MPa
            Tau_max = {self.TAUmax:.2f} MPa
            """
            plt.figtext(0.65, 0.15, stress_text, fontsize=9, family='monospace')
        plt.axis('equal')
        plt.xlim(-0.1 * self.Scale, 1.1 * self.Scale)
        plt.ylim(-0.2 * self.Scale, 0.2 * self.Scale)

        # === 保存或显示图形 ===
        if save_plot:
            plt.savefig(plot_filename, dpi=100)

        if show_plot:
            plt.show()
        else:
            plt.close()

    def Dynamics(self):
        """
        超空泡模型动力学主计算循环。
        完整重写自 Fortran Dynamics 子程序。
        """

        # 保存原始 HX
        work0 = self.HX
        #
        # # ========== Step 1: 模式切换与步长设置 ==========
        # if self.FlagPath:
        #     self.HX = self.HXfilm
        #     Wwidth = 2.4 * self.Scale
        #     if self.SwPert in (1, 3, 4):
        #         work = self.Lc0 * self.Rn
        #     else:  # SwPert == 2
        #         work = self.Lc0 * self.Rn + 1.25
        #     self.Nview = int(Wwidth / self.HX) + 2 if work <= Wwidth else int(work / self.HX) + 2
        #
        # elif self.FlagDive:
        #     self.HX = self.HXdive
        #     if self.GammaDive <= -45.0:
        #         self.Nview = int(-(1.0 + self.Scale) / (self.HX * self.SIN_G)) + 2
        #     else:
        #         self.Nview = int((1.0 + self.Scale) / (self.HX * self.COS_G)) + 2
        #
        # else:  # FlagDynamics
        #     self.Nview = int(self.Scale * 1.1 / self.HX) + 2
        #
        # # self.Nview = 1000
        # self.Nview = int(self.gXfin / self.HX) + 1
        # # self.Nview = 100

        #
        # # ========== Step 2: 数组动态分配 ==========
        # self.Xpr = np.zeros(Nview)
        # self.Ypr1 = np.zeros(Nview)
        # self.Ypr2 = np.zeros(Nview)
        # self.Rpr = np.zeros(Nview)
        # self.SG = np.zeros(Nview)
        # self.Vx1 = np.zeros(Nview)
        # self.Vy1 = np.zeros(Nview)
        # self.V = np.zeros(Nview)
        # self.T = np.zeros(Nview)
        # self.Ycc = np.zeros(Nview)
        # self.Yax0 = np.zeros(Nview)
        # self.Alpha = np.zeros(Nview)
        # self.P1w = np.zeros(Nview)
        # self.DS = np.zeros(Nview)
        # self.Rcav = np.zeros((Nview, Nview))

        self._init_arrays_dynamics()

        Nview = self.Nview
        HX = self.HX
        # 历史数据数组
        NH = int(self.gXfin / (self.Khis * HX)) + 3
        NHstr = int(self.gXfin / HX) + 5
        NH = NHstr
        self.Xhis = np.zeros(NH)
        self.Yhis = np.zeros(NH)
        self.Phis = np.zeros(NH)
        self.Vx = np.zeros(NHstr)
        self.Vy = np.zeros(NHstr)
        self.Tstr = np.zeros(NHstr)
        self.Vstr = np.zeros(NHstr)
        self.SGstr = np.zeros(NHstr)
        self.Xstr = np.zeros(NHstr)
        self.Cn = np.zeros(NHstr)
        self.Cs = np.zeros(NHstr)
        self.This = np.zeros(NHstr)
        self.Ohis = np.zeros(NHstr)

        # ========== Step 3: 初始化计算参数 ==========
        self.CalcParameters()
        self.CalcModel()

        # 空腔截面x坐标
        for i in range(Nview):
            self.Xpr[i] = i * HX

        # 数组清零
        self.Ypr1[:] = 0.0
        self.Ypr2[:] = 0.0
        self.Cl1 = np.zeros(self.Ncon)
        self.Cl2 = np.zeros(self.Ncon)
        self.T[:] = 0.0
        self.Vx1[:] = 0.0
        self.Vy1[:] = 0.0
        self.V[:] = 0.0
        self.Alpha[:] = 0.0
        self.Ycc[:] = 0.0
        self.Yax0[:] = 0.0
        self.SG[:] = 0.0
        self.P1w[:] = 0.0
        self.Rcav[:, :] = 0.0
        self.Rcav[:, 0] = self.Rn

        # 工作变量
        self.Nmod = int(1.0 / HX)
        B2 = self.PI * self.Rn ** 2
        self.B2 = B2
        self.B3 = B2 * 500 * self.Lm ** 3 / self.TMkg
        self.B4 = B2 * 500 * self.Lm ** 5 / self.Ic

        # ========== Step 4: 标志与计数器初始化 ==========
        self.FlagProgress = False
        self.FlagWashed = False
        self.FlagBroken = False
        self.FlagPause = False
        self.FlagStop = False
        self.FlagEsc = False
        self.FlagPenetr = False
        self.FlagFinish = False
        self.FlagCont1 = False
        self.FlagCont2 = False
        self.FlagAhead = False

        self.Nhis = -1
        self.Ihis = 1
        self.Istr = 1
        self.Isave = 0
        self.Ncont = 0
        self.Imin1 = self.Ncon - 1  # Python索引
        self.Imin2 = self.Ncon - 1

        # ========== Step 5: 初始状态设置 ==========
        self.PsiPre = self.Psi0Rad
        if self.FlagDive:
            self.Omega = self.Omega0dive * self.Lm / self.V0
        else:
            self.Omega = self.Omega0 * self.Lm / self.V0

        self.Alpha[0] = self.Psi0Rad
        self.Vx1[0] = self.COS_P
        self.Vy1[0] = -self.SIN_P
        self.V[0] = 1.0
        self.T[0] = 0.0
        self.Ycc[0] = self.Xc * self.SIN_P
        self.Yax0[0] = self.Xc * self.SIN_P
        self.SG[0] = self.SG0
        self.P1w[0] = 0.0
        self.fh1 = -1e-9
        self.fh2 = -1e-9
        self.fdl1 = 0.0
        self.fdl2 = 0.0

        self.Xstr[0] = 0.0
        self.Vstr[0] = 1.0
        self.SGstr[0] = self.SG0
        self.This[0] = 0.0
        self.Xhis[0] = 0.0
        self.Yhis[0] = 0.0
        self.Vx[0] = 1.0
        self.Vy[0] = 0.0
        self.Phis[0] = self.Psi0Rad
        self.Ohis[0] = self.Omega

        # 初始力系数
        if self.FlagDive:
            if self.GammaDive + self.Delta + self.Psi0 == -90.0:
                self.Cnx = self.CnMax
            else:
                self.Cnx = 0.0
            self.Cny = 0.0
        else:
            self.Cnx = self.CnMax * np.cos(self.Psi0Rad + self.DeltaRad) * self.COS_D
            self.Cny = -self.CnMax * np.cos(self.Psi0Rad + self.DeltaRad) * self.SIN_D
        self.Cnm = self.Cny * self.Xc
        self.Csx = 0.0
        self.Csy = 0.0
        self.Csm = 0.0
        self.Cs[0] = self.Csy
        self.Cn[0] = self.Cnx

        # ========== Step 6: 初始绘图与应力 ==========
        self.Jend = 0  # Fortran 1-based -> Python 0-based, 但数组从0开始
        self.Tabs = 0.0
        self.xs1 = 0.0
        self.Xabs = -self.Xc * self.COS_P
        self.Yabs = -self.Xc * self.SIN_P
        self.VxAbs = 1.0
        self.VyAbs = 0.0
        self.Psi = self.Psi0Rad
        self.AlphaCur = self.Psi0Rad
        self.P1n = 0.0

        self.CalcTurnModel()
        self.CalcStress(1.0)

        # ========== Step 7: 主循环 ==========
        Ndist = int(self.gXfin / HX) + 1
        j = 0
        last_callback_time = 0
        min_callback_interval = 0.05
        for j in range(1, Ndist + 1):  # j = 1 to Ndist (0-based index for step j)
            Xn = j * HX
            self.Xn = Xn

            # 检查出水
            Hj = self.H0 - (Xn * self.SIN_G + self.Ycc[self.Jend] * self.COS_G) * self.Lm
            self.FlagSurface = (Hj <= 0.0)
            if self.FlagSurface:
                print("WARNING: The model is out of water. Calculation stopped.")
                break

            # 更新 Jend
            if j < Nview:
                self.Jend = j
            else:
                self.Jend = Nview - 1  # Python 0-based
                # 数组前移
                self.T[:Nview - 1] = self.T[1:Nview]
                self.Vx1[:Nview - 1] = self.Vx1[1:Nview]
                self.Vy1[:Nview - 1] = self.Vy1[1:Nview]
                self.V[:Nview - 1] = self.V[1:Nview]
                self.Alpha[:Nview - 1] = self.Alpha[1:Nview]
                self.Yax0[:Nview - 1] = self.Yax0[1:Nview]
                self.Ycc[:Nview - 1] = self.Ycc[1:Nview]
                self.SG[:Nview - 1] = self.SG[1:Nview]
                self.P1w[:Nview - 1] = self.P1w[1:Nview]
                ## 继续添加

            # self.Jend = j
            # 积分 SODE
            self.CalcSODE()

            # 更新全局状态
            self.Tabs = self.T[self.Jend]
            self.Xabs = Xn - self.Xc * np.cos(self.Psi)
            self.AlphaCur = self.Alpha[self.Jend]
            self.VxAbs = self.V[self.Jend] * np.cos(self.Psi - self.AlphaCur)
            self.VyAbs = self.V[self.Jend] * np.sin(self.Psi - self.AlphaCur)
            self.Ycc[self.Jend] = self.Yabs + self.Xc * np.sin(self.Psi)

            # 更新空化数
            self.SG[self.Jend] = (19.61 * (10.0 + Hj) - self.Pc / 500.0) / (self.V0 ** 2)

            # 更新模型姿态
            self.CalcTurnModel()

            # 计算扰动
            self.CalcPerturbation()
            self.P1w[self.Jend] = self.P1n

            # 更新非定常空泡
            self.CalcUnsteadyCavity()
            self.Yax0[self.Jend] = self.Xc * np.sin(self.Psi)

            # ========== 保存历史数据（用于 PlotHistory / 结果输出）==========
            self.Nhis += 1
            if self.Nhis % self.Khis == 0 or j == 1 or j == Ndist:
                if self.Ihis < len(self.Xhis):
                    self.Xhis[self.Ihis] = self.Xabs
                    self.Yhis[self.Ihis] = self.Yabs
                    self.Phis[self.Ihis] = self.Psi
                    self.Ihis += 1

            # ========== 模型浸润检查（仅实模型） ==========
            if self.SwModel == 0:
                # 模型轮廓坐标（简化）
                if self.Jend < self.Nmod:
                    Ym2 = 0.0
                    Ym1 = 0.0
                    if Xn <= self.Part[0] + 2.5e-3:
                        Ym2 = self.Rn + Xn * (self.BaseR[0] - self.Rn) / self.Part[0]
                        Ym1 = -Ym2
                        if self.Psi != 0.0:
                            Ym2 = (self.Xc - Xn) * np.sin(self.Psi) + Ym2 * np.cos(self.Psi)
                            Ym1 = (self.Xc - Xn) * np.sin(self.Psi) + Ym1 * np.cos(self.Psi)
                    else:
                        for k in range(1, self.Ncon):
                            if Xn <= self.Part[k] + 2.5e-3:
                                Ym2 = self.BaseR[k - 1] + (Xn - self.Part[k - 1]) * (
                                        self.BaseR[k] - self.BaseR[k - 1]) / (self.Part[k] - self.Part[k - 1])
                                Ym1 = -Ym2
                                if self.Psi != 0.0:
                                    Ym2 = (self.Xc - Xn) * np.sin(self.Psi) + Ym2 * np.cos(self.Psi)
                                    Ym1 = (self.Xc - Xn) * np.sin(self.Psi) + Ym1 * np.cos(self.Psi)
                                break

                    # 空腔轮廓
                    if Xn < self.Xagr * self.Rn:
                        Yc2 = self.Rn * (1.0 + 3.0 * Xn / self.Rn) ** (1 / 3) + self.Yax0[self.Jend]
                        Yc1 = -Yc2 + 2 * self.Yax0[self.Jend]
                    else:
                        Yc2 = self.Ypr2[self.Jend]
                        Yc1 = self.Ypr1[self.Jend]

                    # 检查是否浸润
                    if Yc2 < Ym2 or Yc1 > Ym1:
                        self.FlagWashed = True
                        print("WARNING: The model washed during water entry. Calculation stopped.")
                        break

                # 计算间隙分布
                if self.Jend >= self.Nmod and self.Ipr > self.Nmod:
                    self.FlagPenetr = True
                    self.CalcClearances()

                    # 检查浸入深度是否过大
                    if (self.fh1 > 0.5 * self.BaseR[self.Imin1] or
                            self.fh2 > 0.5 * self.BaseR[self.Imin2] or
                            (self.RibTan[self.Ncon - 1] >= 0.0 and
                             (self.Cl1[self.Ncon - 1] > self.BaseR[self.Ncon - 1] or
                              self.Cl2[self.Ncon - 1] > self.BaseR[self.Ncon - 1]))):
                        self.FlagWashed = True
                        print("WARNING: The model immersion is too big. Calculation stopped.")
                        break

                    # 检查环形浸润
                    if self.fh1 > 0.0 and self.fh2 > 0.0:
                        self.FlagWashed = True
                        print("WARNING: Ring washing of the model. Calculation stopped.")
                        break

            # ========== 计算下一步的力和力矩 ==========
            self.CalcForces()

            # ========== 计算应力并校核强度 ==========
            if self.SwModel == 0:
                self.CalcStress(self.V[self.Jend])
                # 强度校核（简化）
                if self.SwCheckStress == 0:
                    X_SGmax = self.X_SGmax
                    X_TAUmax = self.X_TAUmax
                    SGlim = self.SGf if X_SGmax * self.Lmm < self.Lf else self.SGa
                    TAUlim = self.TAUf if X_TAUmax * self.Lmm < self.Lf else self.TAUa
                    if abs(self.SGmax) > SGlim or abs(self.TAUmax) > TAUlim:
                        self.FlagBroken = True
                        print("WARNING: Ultimate stress exceeded. Calculation stopped.")
                        break

            # ========== 检查是否到达终点 ==========
            # self.T[:Nview - 1] = self.T[1:Nview]
            # self.Vx1[:Nview - 1] = self.Vx1[1:Nview]
            # self.Vy1[:Nview - 1] = self.Vy1[1:Nview]
            # self.V[:Nview - 1] = self.V[1:Nview]
            # self.Alpha[:Nview - 1] = self.Alpha[1:Nview]
            # self.Yax0[:Nview - 1] = self.Yax0[1:Nview]
            # self.Ycc[:Nview - 1] = self.Ycc[1:Nview]
            # self.SG[:Nview - 1] = self.SG[1:Nview]
            # self.P1w[:Nview - 1] = self.P1w[1:Nview]
            T_ = self.T[self.Jend]
            Vx1_ = self.Vx1[self.Jend]
            Vy1_ = self.Vy1[self.Jend]
            V_ = self.V[self.Jend]
            Alpha_ = self.Alpha[self.Jend]
            Yax0_ = self.Yax0[self.Jend]
            Ycc_ = self.Ycc[self.Jend]
            SG_ = self.SG[self.Jend]
            P1w_ = self.P1w[self.Jend]
            Psi_ = self.Psi
            Jend1 = self.Jend + 1
            Omega_ = self.Omega
            if Jend1 == 120:
                Jend2 = Jend1

            ############### 增加存储变量，从这里开始
            self.Ohis[self.Jend] = self.Omega
            # ======================== 插入绘制图像在这里！ ============================
            # plt.figure()

            # self.plot_dynamics(show_plot=False, save_plot=True,
            #                    plot_filename=f"./fig/dynamics_step_{str(j).rjust(6, '0')}.png")

            # ======================== 插入收集实时数据在这里！ ============================
            # 收集实时数据
            current_time = time.time()
            if hasattr(self, 'update_callback') and current_time - last_callback_time > min_callback_interval:
                # ========== 进度回调 ==========
                if self.progress_callback:
                    self.progress_callback(j, Ndist + 1)

                # ========== 实时数据准备 ==========
                if self.update_callback:
                    # 准备实时数据
                    data = {
                        'motion': {
                            't': self.Tabs,
                            'x': self.Xabs,
                            'y': self.Yabs,
                            'vx': self.VxAbs,
                            'vy': self.VyAbs,
                            'psi': self.Psi,
                            'alpha': self.AlphaCur,
                            'omega': self.Omega
                        },
                        'forces': {
                            'cpr': self.Cpr if hasattr(self,
                                                       'Tpr') and self.Tabs * 1000 * self.Lm / self.V0 <= self.Tpr else 0,
                            'cnx': -self.Cnx,
                            'cny': self.Cny,
                            'cnm': self.Cnm,
                            'csx': -self.Csx,
                            'csy': self.Csy,
                            'csm': self.Csm
                        },
                        'contact': {
                            'n_contacts': self.Ncont,
                            'pressure': self.Head0 * self.P1n / 1e6 if hasattr(self, 'Head0') else 0
                        }
                    }

                    # 添加间隙信息
                    if hasattr(self, 'FlagPenetr') and self.FlagPenetr:
                        data['contact']['h2'] = -self.fh2 * self.Lmm
                        data['contact']['h1'] = -self.fh1 * self.Lmm

                    # 添加应力信息
                    if hasattr(self, 'SGmax') and hasattr(self, 'TAUmax'):
                        data['stress'] = {
                            'sigma_max': self.SGmax,
                            'tau_max': self.TAUmax
                        }

                    # 调用回调函数
                    self.update_callback(data)

                    last_callback_time = current_time
                    # 检查是否需要停止
                    if hasattr(self, 'is_running') and not self.is_running:
                        break

                    if self.FlagFinish:
                        break

            if j == Ndist:
                self.FlagFinish = True
                print("INFO: The model flew the desired distance.")

        # ========== 循环结束 ==========
        self.Xstop = self.Xn * self.Lm
        self.FlagFinish = True

        if self.FlagPath or self.FlagDive:
            self.HX = work0
        # 合成视频
        # self.picvideo('./fig/', (1200, 800))

        # 清理（Python自动管理）
        # del self.Xpr, self.Ypr1, self.Ypr2, self.Rpr
        # del self.SG, self.Vx1, self.Vy1, self.V, self.T, self.Ycc, self.Yax0, self.Alpha
        # del self.P1w, self.DS, self.Rcav

    def get_results(self):
        """
        返回仿真结果字典，便于后续分析或绘图。
        """
        self.Ihis = getattr(self, 'Ihis', 0)
        self.Xhis = getattr(self, 'Xhis', np.zeros(100))
        self.Yhis = getattr(self, 'Yhis', np.zeros(100))
        self.Phis = getattr(self, 'Phis', np.zeros(100))
        self.Alpha = getattr(self, 'Alpha', np.zeros(100))
        self.V = getattr(self, 'V', np.zeros(100))
        self.Vx = getattr(self, 'Vx', np.zeros(100))
        self.T = getattr(self, 'T', np.zeros(100))
        self.SG = getattr(self, 'SG', np.zeros(100))

        J = self.Jend
        re = {
            'x': np.array([self.Xhis[i] * self.Lm for i in range(min(J, self.Ihis))]),
            'y': np.array([self.Yhis[i] * self.Lm for i in range(min(J, self.Ihis))]),
            'psi': np.array([self.Phis[i] for i in range(min(J, self.Ihis))]),
            'alpha': np.array([self.Alpha[:J].copy()[i] for i in range(min(J, self.Ihis))]),
            'V': np.array([(self.V[:J] * self.V0)[i] for i in range(min(J, self.Ihis))]),
            'Vx': np.array([(self.Vx[:J] * self.V0)[i] for i in range(min(J, self.Ihis))]),
            't': np.array([(self.T[:J] * self.Lm / self.V0)[i] for i in range(min(J, self.Ihis))]),
            'SG': np.array([(self.SG[:J])[i] for i in range(min(J, self.Ihis))]),
            'status': {
                'FlagSurface': self.FlagSurface,
                'FlagWashed': self.FlagWashed,
                'FlagBroken': self.FlagBroken,
                'FlagFinish': self.FlagFinish,
            }
        }
        return re

    def save_to_csv(self, filename='stab_results.csv'):
        """将结果保存为 CSV 文件"""
        res = self.get_results()
        df = pd.DataFrame({
            'x_m': res['x'],
            'y_m': res['y'],
            'psi_rad': res['psi'],
            'alpha_rad': res['alpha'][:len(res['x'])],
            'V_m_s': res['V'][:len(res['x'])],
            't_s': res['t'][:len(res['x'])],
            'SG': res['SG'][:len(res['x'])],
        })
        df.to_csv(filename, index=False)
        print(f"Results saved to {filename}")

    def plot_trajectory(self, ax=None):
        """绘制质心轨迹"""
        import matplotlib.pyplot as plt
        res = self.get_results()
        if ax is None:
            fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(res['y'][1:], res['x'][1:], 'b-', linewidth=2)
        ax.set_xlabel('Y (m)')
        ax.set_ylabel('X (m)')
        ax.set_title('Model Trajectory')
        ax.grid(True)
        return ax

    def plot_alpha_velocity(self, axs=None):
        """绘制攻角和速度"""
        res = self.get_results()
        if axs is None:
            fig, axs = plt.subplots(2, 1, figsize=(10, 6), sharex=True)

        # 攻角
        x = res['x']
        alpha = np.degrees(res['alpha'])

        axs[0].plot(x[1:], alpha[1:], 'r-')
        axs[0].set_ylabel('Alpha (deg)')
        axs[0].grid(True)

        # 速度
        V = res['V']
        axs[1].plot(x[1:], V[1:], 'g-')
        axs[1].set_xlabel('X (m)')
        axs[1].set_ylabel('V (m/s)')
        axs[1].grid(True)

        return axs

    def plot_all(self):
        """绘制完整结果图"""
        fig = plt.figure(figsize=(12, 8))
        gs = fig.add_gridspec(2, 2, height_ratios=[1, 1])

        # 轨迹
        ax1 = fig.add_subplot(gs[:, 0])
        ax1.axis('equal')
        self.plot_trajectory(ax1)

        # 攻角 & 速度
        ax2 = fig.add_subplot(gs[0, 1])
        ax3 = fig.add_subplot(gs[1, 1], sharex=ax2)
        self.plot_alpha_velocity([ax2, ax3])

        plt.tight_layout()

        plt.savefig('debug_plot.png')
        plt.show()

    def mkdir(self, path):
        # 去除首位空格
        path = path.strip()
        # 去除尾部 \ 符号
        path = path.rstrip("\\")
        # 判断路径是否存在
        isExists = os.path.exists(path)
        # 判断结果
        if not isExists:
            # 如果不存在则创建目录,创建目录操作函数
            '''
            os.mkdir(path)与os.makedirs(path)的区别是,当父目录不存在的时候os.mkdir(path)不会创建，os.makedirs(path)则会创建父目录
            '''
            # 此处路径最好使用utf-8解码，否则在磁盘中可能会出现乱码的情况
            os.makedirs(path)

    # 图片合成视频
    def picvideo(self, path, size, fps=60):
        filelist = os.listdir(path)
        # 获取该目录下的所有文件名

        '''
        fps:
        帧率：1秒钟有n张图片写进去[控制一张图片停留5秒钟，那就是帧率为1，重复播放这张图片5次] 
        如果文件夹下有50张 749*677的图片，这里设置1秒钟播放5张，那么这个视频的时长就是10秒
        '''

        file_path = "./" + str(111) + ".mp4"  # 导出路径
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')  # 不同视频编码对应不同视频格式（例：'I','4','2','0' 对应avi格式）

        video = cv2.VideoWriter(file_path, fourcc, fps, size)
        for item in filelist:
            if item.endswith('.png'):  # 判断图片后缀是否是.png
                item = path + '/' + item
                img = cv2.imread(item)  # 使用opencv读取图像，直接返回numpy.ndarray 对象，通道顺序为BGR ，注意是BGR，通道值默认范围0-255。

                video.write(img)  # 把图片写进视频

        video.release()  # 释放
        # cap=cv2.VideoCapture


if __name__ == "__main__":
    stab = Stab()
    # （可选）修改参数
    stab.V0 = 600
    stab.Psi0 = 0
    stab.Xfin = 100
    stab.Omega0 = 1
    stab.input_Nview = True
    stab.Nview = 100
    # try:
    #     os.system('rd /s /q "fig"')
    # except:
    #     None
    # stab.mkdir('fig')

    # 执行计算
    stab.CalcParameters()
    stab.CalcModel()
    stab.Dynamics()

    # 输出结果
    results = stab.get_results()
    print(f"Simulation ended at x = {results['x'][-1]:.2f} m")
    print("Status:", results['status'])

    # 保存 & 可视化
    stab.save_to_csv('my_run.csv')
    stab.plot_all()
    fig1 = plt.figure(figsize=(12, 8))
    plt.plot(stab.Xpr, stab.Ypr2, stab.Xpr, -stab.Ypr1)
    plt.axis('equal')
    plt.savefig('1.png')
    print('finished')
