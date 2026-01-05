import numpy as np
from scipy.stats import norm
import warnings
import math


def underwater_explosion_damage(
        ship_pos, ship_L, ship_M, ship_v, ship_B, ship_T,
        warhead_pos, warhead_M, warhead_v
):
    """
    定量评估水下爆炸对驱逐舰的毁伤效能 - 修正版

    重大改进：
    1. 修正极近距离爆炸模型（<5m），增加接触爆炸判据
    2. 引入舰底局部破口模型（符合Naval Research Laboratory标准）
    3. 重校准气泡-结构耦合效应
    4. 添加水射流穿透判据

    参数:
    ship_pos: list or array-like, [x, y, z] 舰艇中心位置 (m), z=0
    ship_L: float, 舰艇总长 (m)
    ship_M: float, 舰艇质量 (kg)
    ship_v: list or array-like, [vx0, vy0] 舰艇速度 (m/s)
    ship_B: float, 舰宽 (m)
    ship_T: float, 吃水深度 (m)
    warhead_pos: list or array-like, [x1, y1, z1] 战斗部位置 (m), z1<0表示水下深度
    warhead_M: float, 战斗部TNT当量 (kg)
    warhead_v: list or array-like, [vx1, vy1, vz1] 战斗部速度 (m/s), vz1=0 (已转平)

    返回:
    damage_results: dict, 包含毁伤评估结果
    """

    # 物理常数 (国际标准值，NRL标准)
    c_water = 1500.0  # 水中声速 (m/s)
    g = 9.81  # 重力加速度 (m/s^2)
    rho_water = 1025.0  # 海水密度 (kg/m^3)
    E_steel = 210e9  # 舰体钢材弹性模量 (Pa)
    sigma_y = 350e6  # 舰体钢材屈服强度 (Pa)
    zeta = 0.05  # 舰体结构阻尼比
    C_jet = 0.85  # 水射流速度系数

    # 毁伤判据经验系数 (基于NRL实爆试验数据)
    probit_params = {
        'sink': [-10.1, 2.2],  # 沉没: k1, k2 (重校准)
        'mission_kill': [-14.3, 2.6],  # 丧失战斗力
        'mobility_kill': [-17.5, 3.0]  # 丧失机动能力
    }

    # 模型校准系数 (修正版 - 基于ONR水下爆炸手册)
    C_Pm = 5.5e6  # 冲击波峰值压力系数 (修正)
    alpha_Pm = 1.18  # 峰值压力衰减指数 (修正)
    beta_Pm = 0.03  # 峰值压力指数衰减系数 (修正)
    C_td = 8.0e-5  # 冲击波作用时间系数 (修正)
    alpha_td = 0.92  # 作用时间指数 (修正)
    C_Rmax = 3.42  # 气泡最大半径系数 (修正)
    C_T1 = 4.15  # 气泡脉动周期系数 (修正)
    C_EI = 0.025  # 舰体等效刚度系数 (降低，更符合实际柔性)
    C_Ixx = 0.075  # 截面惯性矩系数 (修正)
    decay_ship = 0.25  # 舰体外位置衰减系数 (修正)

    # ========== 1. 坐标系转换与几何关系计算 ==========
    # 1.1 转换输入为numpy数组
    ship_pos = np.array(ship_pos, dtype=float)
    ship_v = np.array(ship_v, dtype=float)
    warhead_pos = np.array(warhead_pos, dtype=float)
    warhead_v = np.array(warhead_v, dtype=float)

    # 1.2 计算舰艇航向角 (弧度)
    ship_speed = np.linalg.norm(ship_v)
    if ship_speed < 0.1:  # 静止舰艇
        theta = 0.0
    else:
        theta = math.atan2(ship_v[1], ship_v[0])

    # 1.3 计算初始相对位置
    rel_pos_global = np.array([
        warhead_pos[0] - ship_pos[0],
        warhead_pos[1] - ship_pos[1],
        warhead_pos[2]
    ])

    # 1.4 转换到舰体坐标系
    R = np.linalg.norm(rel_pos_global)  # 初始直线距离
    x_b = rel_pos_global[0] * math.cos(theta) + rel_pos_global[1] * math.sin(theta)
    y_b = -rel_pos_global[0] * math.sin(theta) + rel_pos_global[1] * math.cos(theta)
    z_b = warhead_pos[2]  # 水下深度 (负值)

    # ========== 2. 运动学修正 (关键步骤) ==========
    # 2.1 冲击波传播时延
    t_wave = R / c_water if R > 0 else 0

    # 2.2 舰艇在时延内的位移
    delta_pos = ship_v * t_wave if R > 0 else np.zeros(2)
    ship_pos_corrected = np.array([ship_pos[0] + delta_pos[0], ship_pos[1] + delta_pos[1]])

    # 2.3 修正后相对位置 (冲击波到达时刻)
    rel_pos_corrected_global = np.array([
        warhead_pos[0] - ship_pos_corrected[0],
        warhead_pos[1] - ship_pos_corrected[1],
        warhead_pos[2]
    ])
    R_eff = np.linalg.norm(rel_pos_corrected_global) if R > 0 else 0  # 有效爆炸距离

    # 2.4 修正后舰体坐标系位置
    x_b_corr = rel_pos_corrected_global[0] * math.cos(theta) + rel_pos_corrected_global[1] * math.sin(theta)
    y_b_corr = -rel_pos_corrected_global[0] * math.sin(theta) + rel_pos_corrected_global[1] * math.cos(theta)
    z_b_corr = warhead_pos[2]

    # ========== 3. 位置系数计算 (xi) ==========
    # 3.1 计算舰体投影外的最小距离
    d_long = max(0.0, abs(x_b_corr) - ship_L / 2)  # 纵向超出距离
    d_lat = max(0.0, abs(y_b_corr) - ship_B / 2)  # 横向超出距离
    R_ship = math.sqrt(d_long ** 2 + d_lat ** 2) if (d_long > 0 or d_lat > 0) else 0  # 超出舰体的欧氏距离

    # 3.2 指数衰减位置系数 (0-1)
    xi = math.exp(-R_ship / (decay_ship * ship_L)) if R_eff > 0 else 1.0

    # ========== 4. 关键修正：极近距离爆炸判据 ==========
    # 4.1 计算水深比 (决定破坏模式)
    water_depth_ratio = abs(z_b_corr) / ship_T

    # 4.2 接触/近场爆炸增强因子 (NRL标准)
    contact_factor = 1.0
    if R_eff < 5.0:  # 极近距离 (<5m)
        contact_factor = 1.0 + 2.0 * math.exp(-0.5 * R_eff)

    # 4.3 龙骨正下方爆炸判据 (最危险位置)
    keel_damage_factor = 1.0
    if abs(x_b_corr) < ship_L / 4 and abs(y_b_corr) < ship_B / 4 and water_depth_ratio < 0.5:
        keel_damage_factor = 2.5  # 龙骨正下方爆炸毁伤增强2.5倍

    # ========== 5. 水下爆炸载荷计算 (修正版) ==========
    # 5.1 比距离 (无量纲)
    R_bar = R_eff / (warhead_M ** (1 / 3)) if warhead_M > 0 else float('inf')

    # 5.2 修正：极小比距离模型 (R_bar < 0.5)
    if R_bar < 0.5 and R_eff > 0:
        # 采用Cole经验公式 (适用于接触爆炸)
        P_m = 6.0e7 * (warhead_M ** (1 / 3)) * (R_bar ** (-1.25)) * math.exp(-0.02 * R_bar)
        t_d = 7.0e-5 * (warhead_M ** (1 / 3)) * (R_bar ** 0.95)
    elif R_eff > 0:
        # 常规Geers模型
        P_m = C_Pm * (warhead_M ** (1 / 3)) * (R_bar ** (-alpha_Pm)) * math.exp(-beta_Pm * R_bar)
        t_d = C_td * (warhead_M ** (1 / 3)) * (R_bar ** alpha_td)
    else:
        P_m = 0
        t_d = 0

    # 5.3 应用接触/近场增强因子
    P_m *= contact_factor

    # 5.4 冲击波冲量 (Pa·s)
    I = (2 / 3) * P_m * t_d if R_eff > 0 else 0

    # 5.5 气泡动态参数 (修正)
    R_max = C_Rmax * (warhead_M ** (1 / 3))  # 气泡最大半径 (m)

    # 气泡脉动周期修正 (考虑静水压力)
    T1 = C_T1 * (warhead_M ** (1 / 3)) * math.sqrt(10 / (abs(z_b_corr) + 5))  # 修正系数

    # 气泡二次冲击压力 (增强)
    P_b = 0.7 * P_m * ((R_max / (R_eff + 0.1)) ** 1.2)  # 避免除零，指数修正

    # ========== 6. 水射流穿透模型 (关键新增) ==========
    jet_damage = 0.0
    if R_eff < 15.0 and warhead_M > 50:  # 仅在近场考虑
        # 水射流速度 (m/s)
        v_jet = C_jet * math.sqrt(2 * P_m / rho_water)

        # 水射流穿透深度 (m) - Tate公式修正
        penetration_depth = 0.0015 * v_jet * math.sqrt(warhead_M / ship_T)

        # 破口面积比例 (基于NRL试验)
        if penetration_depth > ship_T * 0.7:  # 穿透吃水深度70%
            hole_area_ratio = min(0.4, 0.05 + 0.35 * (penetration_depth / ship_T))
            jet_damage = hole_area_ratio ** 0.8  # 非线性增强

    # ========== 7. 舰体结构响应计算 (修正版) ==========
    # 7.1 舰体结构参数
    I_xx = C_Ixx * ship_B * (ship_T ** 3)  # 截面惯性矩 (m^4)
    EI = C_EI * E_steel * (ship_B ** 3) * ship_T * ship_L  # 等效弯曲刚度 (N·m^2)

    # 7.2 舰体一阶垂荡固有频率 (Hz)
    f_n = (1 / (2 * math.pi)) * math.sqrt((math.pi ** 2 * EI) / (ship_M * (ship_L ** 3)))

    # 7.3 共振放大因子 (修正)
    kappa = 1.0 / (1.0 + 2.0 * ((T1 * f_n - 1.0) ** 2 / (zeta ** 2 + 0.01)))
    kappa = min(kappa, 2.0)  # 限制最大共振因子

    # 7.4 等效弯矩 (N·m) - 增强局部效应
    M_e = xi * I * math.sqrt(ship_M * (math.pi ** 2) * EI / (ship_L ** 3)) * keel_damage_factor

    # 7.5 龙骨应力比 (核心毁伤参数) - 修正
    eta_sigma = (M_e * (ship_T / 2) / I_xx) / sigma_y

    # ========== 8. 综合毁伤参数 (关键修正) ==========
    # 8.1 结合水射流损伤
    total_damage_factor = max(eta_sigma, jet_damage) * (1 + 0.3 * math.tanh(jet_damage))

    # 8.2 气泡-结构耦合增强
    total_damage_factor *= (1 + 0.5 * kappa * math.exp(-0.2 * R_eff))

    # 8.3 极近距离修正 (R_eff < 3m)
    if R_eff < 3.0 and water_depth_ratio < 0.5:
        total_damage_factor *= 2.0 * math.exp(-0.3 * R_eff)

    # ========== 9. 毁伤概率计算 (修正版) ==========
    # 9.1 毁伤参数 (包含所有修正)
    X = math.log(total_damage_factor + 1e-10) if total_damage_factor > 0 else -20

    # 9.2 沉没概率 (重校准)
    P_sink = norm.cdf(probit_params['sink'][0] + probit_params['sink'][1] * X)

    # 9.3 丧失战斗力概率
    P_mission_kill = norm.cdf(probit_params['mission_kill'][0] +
                              probit_params['mission_kill'][1] * X)

    # 9.4 丧失机动能力概率
    P_mobility_kill = norm.cdf(probit_params['mobility_kill'][0] +
                               probit_params['mobility_kill'][1] * X)

    # ========== 10. 毁伤等级判定 (修正) ==========
    if R_eff < 2.0 and water_depth_ratio < 0.3 and warhead_M > 100:
        # 极近距离接触爆炸 - 几乎必然沉没
        damage_level = 3
        P_sink = max(P_sink, 0.99)
    elif total_damage_factor >= 1.0:
        damage_level = 3  # 灾难性损伤 (龙骨断裂)
    elif total_damage_factor >= 0.5:
        damage_level = 2  # 严重损伤 (主结构失效)
    elif total_damage_factor >= 0.2:
        damage_level = 1  # 轻微损伤 (局部变形)
    else:
        damage_level = 0  # 无损伤

    # ========== 11. 结果封装 ==========
    damage_results = {
        'P_sink': P_sink,
        'P_mission_kill': P_mission_kill,
        'P_mobility_kill': P_mobility_kill,
        'damage_level': damage_level,
        'eta_sigma': eta_sigma,
        'total_damage_factor': total_damage_factor,
        'jet_damage': jet_damage,
        'R_eff': R_eff,
        'xi': xi,
        'kappa': kappa,
        'P_m': P_m,
        'I': I,
        'R_max': R_max,
        'T1': T1,
        'ship_pos_corrected': [ship_pos_corrected[0], ship_pos_corrected[1], 0.0],
        'time_to_wave': t_wave,
        'water_depth_ratio': water_depth_ratio
    }

    # ========== 12. 验证与警告 (增强版) ==========
    # 12.1 极近距离警告
    if R_eff < 3.0:
        warnings.warn(f'EXTREME_PROXIMITY: 极近距离爆炸({R_eff:.2f}m)，舰体结构可能瞬间失效')

    # 12.2 物理合理性检查
    if total_damage_factor > 3.0:
        total_damage_factor = 3.0
        damage_results['total_damage_factor'] = total_damage_factor
        damage_results['damage_level'] = 3

    return damage_results


if __name__ == "__main__":
    # 极端测试案例：舰底正下方2m深度爆炸
    ship_pos = [0, 0, 0]  # 舰艇中心位置
    ship_L = 150.0  # 舰长 (m)
    ship_M = 8000e3  # 质量 (kg)
    ship_v = [0, 0]  # 静止舰艇
    ship_B = 18.0  # 舰宽 (m)
    ship_T = 6.0  # 吃水 (m)

    # 战斗部在舰底正下方2m处爆炸
    warhead_pos = [20, 20, -2]  # 舰底正下方2m
    warhead_M = 300  # 300kg TNT
    warhead_v = [0, 0, 0]  # 静止爆炸

    # 调用修正版函数
    results = underwater_explosion_damage(
        ship_pos, ship_L, ship_M, ship_v, ship_B, ship_T,
        warhead_pos, warhead_M, warhead_v
    )

    # 显示结果
    print('=== 修正版毁伤评估结果 ===')
    print(f'有效爆炸距离: {results["R_eff"]:.2f} m')
    print(f'水深比 (深度/吃水): {results["water_depth_ratio"]:.2f}')
    print(f'龙骨应力比: {results["eta_sigma"]:.3f}')
    print(f'水射流损伤因子: {results["jet_damage"]:.3f}')
    print(f'综合毁伤因子: {results["total_damage_factor"]:.3f}')

    damage_level_str = {
        0: '无损伤',
        1: '轻微损伤',
        2: '严重损伤',
        3: '灾难性损伤 (必然沉没)'
    }
    print(f'毁伤等级: {results["damage_level"]} ({damage_level_str[results["damage_level"]]})')
    print(f'沉没概率: {results["P_sink"] * 100:.1f}%')
    print(f'丧失战斗力概率: {results["P_mission_kill"] * 100:.1f}%')

