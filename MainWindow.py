import json
import time

import numpy as np
import pyqtgraph as pg
import logging
import sys
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMessageBox, QVBoxLayout, QTabWidget, QHBoxLayout, QWidget, QMainWindow, \
    QStatusBar, QLabel, QFileDialog, QDialog, QPushButton
from ModelParameterWidget import ModelParameterWidget
from SimulationControlWidget import SimulationControlWidget
from VisualizationWidget import VisualizationWidget
# from rushui_model import Rushui
from core import Dan as Rushui
from SimulationDiveWidget import SimulationDiveWidget
from PyQt5.QtGui import QPainter, QLinearGradient, QColor, QPalette, QBrush, QPixmap
import json
from read_data import read_data
from write_data import write_data
import os
from CustomExportDialog import CustomExportDialog
import math

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class MainWindow(QMainWindow):
    """主窗口"""
    to_data_signal = pyqtSignal(dict)

    def __init__(self):
        super().__init__()

        self.setWindowTitle("空水一体弹道与突防效能评估系统")
        self.setGeometry(100, 100, 1400, 900)

        # 创建Stab实例
        self.rushui = Rushui()

        # 创建中心部件
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # 创建左侧控制面板
        control_panel = QTabWidget()
        control_panel.setMaximumWidth(450)

        # 添加模型参数界面 (保持原有优点)
        self.model_param_widget = ModelParameterWidget(self.rushui)
        control_panel.addTab(self.model_param_widget, "初始条件")

        # 添加垂直入水界面
        self.sim_control_widget = SimulationControlWidget(self.rushui)
        control_panel.addTab(self.sim_control_widget, "弹道仿真")

        self.sim_dive_widget = SimulationDiveWidget(self.rushui)
        control_panel.addTab(self.sim_dive_widget, "毁伤模块")

        # 创建右侧面板
        right_panel = QVBoxLayout()
        right_panel.setContentsMargins(0, 0, 0, 0)
        right_panel.setSpacing(5)

        # 添加可视化界面
        self.visualization_widget = VisualizationWidget(self.rushui)
        right_panel.addWidget(self.visualization_widget, 1)

        # 创建状态栏
        status_bar = QStatusBar()
        self.setStatusBar(status_bar)
        self.status_label = QLabel("就绪 | 模型参数已初始化")
        self.status_label.setStyleSheet("padding: 3px;")
        status_bar.addWidget(self.status_label)

        # 连接信号
        self.sim_control_widget.realtime_update.connect(self.visualization_widget.handle_realtime_update)

        # 连接模型跟仿真两个界面的信号
        self.model_param_widget.data_input_signal_m.connect(self.sim_control_widget.to_model)
        self.sim_control_widget.data_input_signal_f.connect(self.model_param_widget.to_model)

        self.model_param_widget.data_output_signal_m.connect(self.sim_control_widget.get_model)
        self.sim_control_widget.data_output_signal_f.connect(self.model_param_widget.get_model)

        # 连接dive参数
        self.sim_dive_widget.data_input_signal_f.connect(self.to_all_data)
        self.to_data_signal.connect(self.sim_dive_widget.get_model)


        # 组合布局
        main_layout.addWidget(control_panel, 1)
        main_layout.addLayout(right_panel, 4)

        self.setCentralWidget(central_widget)

        # 创建菜单栏
        self.create_menu_bar()

        # 设置应用样式
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f5f5f5;
            }
            QTabWidget::pane {
                border: 1px solid #cccccc;
                background: white;
            }
            QTabBar::tab {
                background: #e0e0e0;
                border: 1px solid #cccccc;
                padding: 5px;
                margin-right: 2px;
            }
            QTabBar::tab:selected {
                background: #ffffff;
                border-bottom-color: #ffffff;
            }
            QPushButton {
                padding: 5px 10px;
                border-radius: 3px;
            }
            QGroupBox {
                font-weight: bold;
            }
            QLabel {
                font-size: 9pt;
            }
        """)
        pg.setConfigOptions(antialias=True)
        self.auto_load()

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        save_action = file_menu.addAction("保存配置")
        save_action.triggered.connect(self.save_configuration)

        load_action = file_menu.addAction("加载配置")
        load_action.triggered.connect(self.load_configuration)

        save_action_laptop = file_menu.addAction("导出配置到平台")
        save_action_laptop.triggered.connect(self.save_laptop_configuration)

        load_action_laptop = file_menu.addAction("读取平台配置")
        load_action_laptop.triggered.connect(self.load_laptop_configuration)

        # 自定义导出数据功能
        custom_export_action = file_menu.addAction("自定义导出数据")
        custom_export_action.triggered.connect(self.custom_export_data)

        file_menu.addSeparator()

        exit_action = file_menu.addAction("退出")
        exit_action.triggered.connect(self.close)

        # 视图菜单
        view_menu = menubar.addMenu("视图")

        reset_view_action = view_menu.addAction("重置视图")
        reset_view_action.triggered.connect(self.reset_view)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        about_action = help_menu.addAction("关于")
        about_action.triggered.connect(self.show_about)

    def save_configuration(self):
        """保存完整配置到文件"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存配置", "", "JSON Files (*.json);;All Files (*)"
            )
            if not filename:
                return

            # 收集模型参数
            model_params = {
                # 几何与质量参数
                'L': self.model_param_widget.L_input.value(),  # 长度 (m)
                'S': self.model_param_widget.S_input.value(),  # 横截面积 (m²)
                'V': self.model_param_widget.V_input.value(),  # 体积 (m³)
                'm': self.model_param_widget.m_input.value(),  # 质量 (kg)
                'xc': self.model_param_widget.xc_input.value(),  # 重心 x 坐标 (m)
                'yc': self.model_param_widget.yc_input.value(),  # 重心 y 坐标 (m)
                'zc': self.model_param_widget.zc_input.value(),  # 重心 z 坐标 (m)
                'Jxx': self.model_param_widget.Jxx_input.value(),  # 转动惯量 Jxx (kg·m²)
                'Jyy': self.model_param_widget.Jyy_input.value(),  # 转动惯量 Jyy (kg·m²)
                'Jzz': self.model_param_widget.Jzz_input.value(),  # 转动惯量 Jzz (kg·m²)
                'T': self.model_param_widget.T_input.value(),  # 推力 (N)

                # 空泡仿真参数
                'lk': self.model_param_widget.lk_input.value(),  # 空化器距重心距离 (m)
                'rk': self.model_param_widget.rk_input.value(),  # 空化器半径 (m)
                'sgm': self.model_param_widget.sgm_input.value(),  # 全局空化数
                'dyc': self.model_param_widget.dyc_input.value(),  # 空泡轴线偏离 (m)

                # 水下物理几何参数
                'SGM': self.model_param_widget.SGM_input.value(),  # 水下空化数
                'LW': self.model_param_widget.LW_input.value(),  # 水平鳍位置 (m)
                'LH': self.model_param_widget.LH_input.value(),  # 垂直鳍位置 (m)

                # 舵机与角度限制参数
                'dkmax': self.model_param_widget.dkmax_input.value(),  # 舵角上限 (°)
                'dkmin': self.model_param_widget.dkmin_input.value(),  # 舵角下限 (°)
                'dk0': self.model_param_widget.dk0_input.value(),  # 舵角零位 (°)
                'deltaymax': self.model_param_widget.deltaymax_input.value(),  # 横向位移限制 (m)
                'deltavymax': self.model_param_widget.deltavymax_input.value(),  # 垂向位移限制 (m)
                'ddmax': self.model_param_widget.ddmax_input.value(),  # 最大深度变化率 (°/s²)
                'dvmax': self.model_param_widget.dvmax_input.value(),  # 最大速度变化率 (°/s²)
                'dthetamax': self.model_param_widget.dthetamax_input.value(),  # 最大俯仰角速率 (°/s)
                'wzmax': self.model_param_widget.wzmax_input.value(),  # 最大偏航角速率 (°/s)
                'wxmax': self.model_param_widget.wxmax_input.value(),  # 最大滚转角速率 (°/s)
                'dphimax': self.model_param_widget.dphimax_input.value(),  # 最大滚转角加速度 (°/s²)
            }

            # 收集仿真参数
            sim_params = {
                # ——————————入水参数——————————
                't0': self.sim_control_widget.t0_input.value(),  # 起始时间 (s)
                'tend': self.sim_control_widget.tend_input.value(),  # 终止时间 (s)
                'dt': self.sim_control_widget.dt_input.value(),  # 仿真步长 (s)
                'v0': self.sim_control_widget.v0_input.value(),  # 入水速度 (m/s)
                'theta0': self.sim_control_widget.theta0_input.value(),  # 弹道角 (deg)
                'psi0': self.sim_control_widget.psi0_input.value(),  # 偏航角 (deg)
                'phi0': self.sim_control_widget.phi0_input.value(),  # 横滚角 (deg)
                'alpha0': self.sim_control_widget.alpha0_input.value(),  # 攻角 (deg)
                'wx0': self.sim_control_widget.wx0_input.value(),  # 横滚角速度 (deg/s)
                'wy0': self.sim_control_widget.wy0_input.value(),  # 偏航角速度 (deg/s)
                'wz0': self.sim_control_widget.wz0_input.value(),  # 俯仰角速度 (deg/s)

                # ——————————控制参数 (修正分组)——————————
                # 注：原代码存在分组命名冲突，已按实际参数含义重新分组
                'k_wz': self.sim_control_widget.k_wz_input.value(),  # 偏航角速度增益 (控制参数)
                'k_theta': self.sim_control_widget.k_theta_input.value(),  # 俯仰角增益 (控制参数)

                'kwz': self.sim_control_widget.kwz_input.value(),  # 偏航角速度增益 (控制参数)
                'ktheta': self.sim_control_widget.ktheta_input.value(),  # 俯仰角增益 (控制参数)
                # ——————————深度控制参数——————————
                'k_ps': self.sim_control_widget.k_ps_input.value(),  # 姿态同步增益
                'k_ph': self.sim_control_widget.k_ph_input.value(),  # 舵机响应增益
                'k_wx': self.sim_control_widget.k_wx_input.value(),  # 滚转角速度增益
                'k_wy': self.sim_control_widget.k_wy_input.value(),  # 垂向控制增益
                'tend_under': self.sim_control_widget.tend_under_input.value(),
                'T1': self.sim_control_widget.T1_input.value(),
                'T2': self.sim_control_widget.T2_input.value(),
                'time_sequence': self.sim_control_widget.time_sequence_input.text(),
                'thrust_sequence': self.sim_control_widget.thrust_sequence_input.text()
            }

            dive_params = {
                'ship_L': self.sim_dive_widget.ship_L_input.value(),
                'ship_M': self.sim_dive_widget.ship_M_input.value(),
                'ship_B': self.sim_dive_widget.ship_B_input.value(),
                'ship_T': self.sim_dive_widget.ship_T_input.value(),

                # 武器毁伤多次重复实验
                'burn_N': self.sim_dive_widget.burn_N_input.value(),
                'ship_if': self.sim_dive_widget.ship_if.currentIndex(),  # 是否手动设置舰艇类型
                'ship_tpye': self.sim_dive_widget.ship_tpye.currentIndex(),  # 选择的舰艇类型（注意变量名拼写）

                # 目标舰艇相关参数
                'ship_x_x': self.sim_dive_widget.ship_x_x_input.value(),  # x位置
                'ship_x_y': self.sim_dive_widget.ship_x_y_input.value(),  # y位置
                'ship_x_z': self.sim_dive_widget.ship_x_z_input.value(),  # z位置
                'ship_v_max': self.sim_dive_widget.ship_v_max_input.value(),  # 最大速度（节）
                'ship_a_max': self.sim_dive_widget.ship_a_max_input.value(),  # 最大加速度（m/s^2）

                # 空中入水飞行参数
                'air_t': self.sim_dive_widget.air_t_input.value(),  # 飞行时间(s)
                'air_L': self.sim_dive_widget.air_L_input.value(),  # 弹道距离(km)
                'air_theta': self.sim_dive_widget.air_theta_input.value(),  # 入水倾角(deg)
                'air_v': self.sim_dive_widget.air_v_input.value()  # 入水速度(m/s)
            }

            # 收集UI状态
            ui_state = {
                "CurrentTab": self.centralWidget().findChild(QTabWidget).currentIndex(),
                "VisualizationTab": self.visualization_widget.tab_widget.currentIndex()
            }

            # 组合所有配置
            config = {
                "model_params": model_params,
                "sim_params": sim_params,
                "dive_params": dive_params,
                "ui_state": ui_state,
                "config_version": "3.0",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            # 保存到文件
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)

            self.status_label.setText(f"配置已保存至: {filename}")
            QMessageBox.information(self, "保存成功", f"配置已成功保存至:\n{filename}")
            logging.info(f"配置已保存至: {filename}")
            # # 手动签出
            # names = []
            # datas = []
            # model_params_key = model_params.keys()
            # model_params_val = model_params.values()
            # sim_params_key = sim_params.keys()
            # sim_params_val = sim_params.values()
            # dive_params_key = dive_params.keys()
            # dive_params_val = dive_params.values()
            # a = 1
            # names = list(model_params_key) + list(sim_params_key) + list(dive_params_key)
            # datas = list(model_params_val) + list(sim_params_val) + list(dive_params_val)
            # fid = open('output.txt', 'w', encoding='utf-8')
            # for i in range(len(names)):
            #     namet, datat = self.get_data_info(datas[i])
            #     write_data(fid, namet, names[i], datat, datas[i])
            # fid.close()

        except Exception as e:
            logging.exception("保存配置时出错")
            QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")
            self.status_label.setText("保存配置失败")

    def save_laptop_configuration(self):
        """保存完整配置到文件"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存配置", "output.txt", "TXT Files (*.txt);;All Files (*)"
            )
            if not filename:
                return

                # 收集模型参数
            model_params = {
                # 几何与质量参数
                'L': self.model_param_widget.L_input.value(),  # 长度 (m)
                'S': self.model_param_widget.S_input.value(),  # 横截面积 (m²)
                'V': self.model_param_widget.V_input.value(),  # 体积 (m³)
                'm': self.model_param_widget.m_input.value(),  # 质量 (kg)
                'xc': self.model_param_widget.xc_input.value(),  # 重心 x 坐标 (m)
                'yc': self.model_param_widget.yc_input.value(),  # 重心 y 坐标 (m)
                'zc': self.model_param_widget.zc_input.value(),  # 重心 z 坐标 (m)
                'Jxx': self.model_param_widget.Jxx_input.value(),  # 转动惯量 Jxx (kg·m²)
                'Jyy': self.model_param_widget.Jyy_input.value(),  # 转动惯量 Jyy (kg·m²)
                'Jzz': self.model_param_widget.Jzz_input.value(),  # 转动惯量 Jzz (kg·m²)
                'T': self.model_param_widget.T_input.value(),  # 推力 (N)

                # 空泡仿真参数
                'lk': self.model_param_widget.lk_input.value(),  # 空化器距重心距离 (m)
                'rk': self.model_param_widget.rk_input.value(),  # 空化器半径 (m)
                'sgm': self.model_param_widget.sgm_input.value(),  # 全局空化数
                'dyc': self.model_param_widget.dyc_input.value(),  # 空泡轴线偏离 (m)

                # 水下物理几何参数
                'SGM': self.model_param_widget.SGM_input.value(),  # 水下空化数
                'LW': self.model_param_widget.LW_input.value(),  # 水平鳍位置 (m)
                'LH': self.model_param_widget.LH_input.value(),  # 垂直鳍位置 (m)

                # 舵机与角度限制参数
                'dkmax': self.model_param_widget.dkmax_input.value(),  # 舵角上限 (°)
                'dkmin': self.model_param_widget.dkmin_input.value(),  # 舵角下限 (°)
                'dk0': self.model_param_widget.dk0_input.value(),  # 舵角零位 (°)
                'deltaymax': self.model_param_widget.deltaymax_input.value(),  # 横向位移限制 (m)
                'deltavymax': self.model_param_widget.deltavymax_input.value(),  # 垂向位移限制 (m)
                'ddmax': self.model_param_widget.ddmax_input.value(),  # 最大深度变化率 (°/s²)
                'dvmax': self.model_param_widget.dvmax_input.value(),  # 最大速度变化率 (°/s²)
                'dthetamax': self.model_param_widget.dthetamax_input.value(),  # 最大俯仰角速率 (°/s)
                'wzmax': self.model_param_widget.wzmax_input.value(),  # 最大偏航角速率 (°/s)
                'wxmax': self.model_param_widget.wxmax_input.value(),  # 最大滚转角速率 (°/s)
                'dphimax': self.model_param_widget.dphimax_input.value(),  # 最大滚转角加速度 (°/s²)
            }

            # 收集仿真参数
            sim_params = {
                # ——————————入水参数——————————
                't0': self.sim_control_widget.t0_input.value(),  # 起始时间 (s)
                'tend': self.sim_control_widget.tend_input.value(),  # 终止时间 (s)
                'dt': self.sim_control_widget.dt_input.value(),  # 仿真步长 (s)
                'v0': self.sim_control_widget.v0_input.value(),  # 入水速度 (m/s)
                'theta0': self.sim_control_widget.theta0_input.value(),  # 弹道角 (deg)
                'psi0': self.sim_control_widget.psi0_input.value(),  # 偏航角 (deg)
                'phi0': self.sim_control_widget.phi0_input.value(),  # 横滚角 (deg)
                'alpha0': self.sim_control_widget.alpha0_input.value(),  # 攻角 (deg)
                'wx0': self.sim_control_widget.wx0_input.value(),  # 横滚角速度 (deg/s)
                'wy0': self.sim_control_widget.wy0_input.value(),  # 偏航角速度 (deg/s)
                'wz0': self.sim_control_widget.wz0_input.value(),  # 俯仰角速度 (deg/s)

                # ——————————控制参数 (修正分组)——————————
                # 注：原代码存在分组命名冲突，已按实际参数含义重新分组
                'k_wz': self.sim_control_widget.k_wz_input.value(),  # 偏航角速度增益 (控制参数)
                'k_theta': self.sim_control_widget.k_theta_input.value(),  # 俯仰角增益 (控制参数)

                'kwz': self.sim_control_widget.kwz_input.value(),  # 偏航角速度增益 (控制参数)
                'ktheta': self.sim_control_widget.ktheta_input.value(),  # 俯仰角增益 (控制参数)
                # ——————————深度控制参数——————————
                'k_ps': self.sim_control_widget.k_ps_input.value(),  # 姿态同步增益
                'k_ph': self.sim_control_widget.k_ph_input.value(),  # 舵机响应增益
                'k_wx': self.sim_control_widget.k_wx_input.value(),  # 滚转角速度增益
                'k_wy': self.sim_control_widget.k_wy_input.value(),  # 垂向控制增益
                'tend_under': self.sim_control_widget.tend_under_input.value(),
                'T1': self.sim_control_widget.T1_input.value(),
                'T2': self.sim_control_widget.T2_input.value(),
                'time_sequence': self.sim_control_widget.time_sequence_input.text(),
                'thrust_sequence': self.sim_control_widget.thrust_sequence_input.text()
            }

            dive_params = {
                'ship_L': self.sim_dive_widget.ship_L_input.value(),
                'ship_M': self.sim_dive_widget.ship_M_input.value(),
                'ship_B': self.sim_dive_widget.ship_B_input.value(),
                'ship_T': self.sim_dive_widget.ship_T_input.value(),

                # 武器毁伤多次重复实验
                'burn_N': self.sim_dive_widget.burn_N_input.value(),
                'ship_if': self.sim_dive_widget.ship_if.currentIndex(),  # 是否手动设置舰艇类型
                'ship_tpye': self.sim_dive_widget.ship_tpye.currentIndex(),  # 选择的舰艇类型（注意变量名拼写）

                # 目标舰艇相关参数
                'ship_x_x': self.sim_dive_widget.ship_x_x_input.value(),  # x位置
                'ship_x_y': self.sim_dive_widget.ship_x_y_input.value(),  # y位置
                'ship_x_z': self.sim_dive_widget.ship_x_z_input.value(),  # z位置
                'ship_v_max': self.sim_dive_widget.ship_v_max_input.value(),  # 最大速度（节）
                'ship_a_max': self.sim_dive_widget.ship_a_max_input.value(),  # 最大加速度（m/s^2）

                # 空中入水飞行参数
                'air_t': self.sim_dive_widget.air_t_input.value(),  # 飞行时间(s)
                'air_L': self.sim_dive_widget.air_L_input.value(),  # 弹道距离(km)
                'air_theta': self.sim_dive_widget.air_theta_input.value(),  # 入水倾角(deg)
                'air_v': self.sim_dive_widget.air_v_input.value()  # 入水速度(m/s)
            }

            # 收集UI状态
            ui_state = {
                "CurrentTab": self.centralWidget().findChild(QTabWidget).currentIndex(),
                "VisualizationTab": self.visualization_widget.tab_widget.currentIndex()
            }

            # 组合所有配置
            config = {
                "model_params": model_params,
                "sim_params": sim_params,
                "dive_params": dive_params,
                "ui_state": ui_state,
                "config_version": "3.0",
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
            }

            # 手动签出
            names = []
            datas = []
            model_params_key = model_params.keys()
            model_params_val = model_params.values()
            sim_params_key = sim_params.keys()
            sim_params_val = sim_params.values()
            dive_params_key = dive_params.keys()
            dive_params_value = dive_params.values()
            a = 1
            names = list(model_params_key) + list(sim_params_key) + list(dive_params_key)
            datas = list(model_params_val) + list(sim_params_val) + list(dive_params_value)
            fid = open(filename, 'w', encoding='utf-8')
            for i in range(len(names)):
                namet, datat = self.get_data_info(datas[i])
                write_data(fid, namet, names[i], datat, datas[i])
            fid.close()

            self.status_label.setText(f"配置已保存至: {filename}")
            QMessageBox.information(self, "保存成功", f"配置已成功保存至:\n{filename}")
            logging.info(f"配置已保存至: {filename}")

        except Exception as e:
            logging.exception("保存配置时出错")
            QMessageBox.critical(self, "错误", f"保存配置失败: {str(e)}")
            self.status_label.setText("保存配置失败")

    def load_configuration(self):
        """从文件加载完整配置"""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self, "加载配置", "", "JSON Files (*.json);;All Files (*)"
            )
            if not filename:
                return

            # 读取配置文件
            with open(filename, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 验证配置文件
            if "config_version" not in config:
                reply = QMessageBox.question(self, "配置文件版本",
                                             "配置文件版本不匹配，可能无法正确加载。是否继续?",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                if reply == QMessageBox.No:
                    return

            # 加载模型参数
            if "model_params" in config:
                mp = config["model_params"]
                self.model_param_widget.L_input.setValue(mp.get('L', None))
                self.model_param_widget.S_input.setValue(mp.get('S', None))
                self.model_param_widget.V_input.setValue(mp.get('V', None))
                self.model_param_widget.m_input.setValue(mp.get('m', None))
                self.model_param_widget.xc_input.setValue(mp.get('xc', None))
                self.model_param_widget.yc_input.setValue(mp.get('yc', None))
                self.model_param_widget.zc_input.setValue(mp.get('zc', None))
                self.model_param_widget.Jxx_input.setValue(mp.get('Jxx', None))
                self.model_param_widget.Jyy_input.setValue(mp.get('Jyy', None))
                self.model_param_widget.Jzz_input.setValue(mp.get('Jzz', None))
                self.model_param_widget.T_input.setValue(mp.get('T', None))
                self.model_param_widget.lk_input.setValue(mp.get('lk', None))
                self.model_param_widget.rk_input.setValue(mp.get('rk', None))
                self.model_param_widget.sgm_input.setValue(mp.get('sgm', None))
                self.model_param_widget.dyc_input.setValue(mp.get('dyc', None))
                self.model_param_widget.SGM_input.setValue(mp.get('SGM', None))
                self.model_param_widget.LW_input.setValue(mp.get('LW', None))
                self.model_param_widget.LH_input.setValue(mp.get('LH', None))
                self.model_param_widget.dkmax_input.setValue(mp.get('dkmax', None))
                self.model_param_widget.dkmin_input.setValue(mp.get('dkmin', None))
                self.model_param_widget.dk0_input.setValue(mp.get('dk0', None))
                self.model_param_widget.deltaymax_input.setValue(mp.get('deltaymax', None))
                self.model_param_widget.deltavymax_input.setValue(mp.get('deltavymax', None))
                self.model_param_widget.ddmax_input.setValue(mp.get('ddmax', None))
                self.model_param_widget.dvmax_input.setValue(mp.get('dvmax', None))
                self.model_param_widget.dthetamax_input.setValue(mp.get('dthetamax', None))
                self.model_param_widget.wzmax_input.setValue(mp.get('wzmax', None))
                self.model_param_widget.wxmax_input.setValue(mp.get('wxmax', None))
                self.model_param_widget.dphimax_input.setValue(mp.get('dphimax', None))

            # 加载仿真参数
            if "sim_params" in config:
                sp = config["sim_params"]
                self.sim_control_widget.t0_input.setValue(sp.get('t0', None))
                self.sim_control_widget.tend_input.setValue(sp.get('tend', None))
                self.sim_control_widget.dt_input.setValue(sp.get('dt', None))
                self.sim_control_widget.v0_input.setValue(sp.get('v0', None))
                self.sim_control_widget.theta0_input.setValue(sp.get('theta0', None))
                self.sim_control_widget.psi0_input.setValue(sp.get('psi0', None))
                self.sim_control_widget.phi0_input.setValue(sp.get('phi0', None))
                self.sim_control_widget.alpha0_input.setValue(sp.get('alpha0', None))
                self.sim_control_widget.wx0_input.setValue(sp.get('wx0', None))
                self.sim_control_widget.wy0_input.setValue(sp.get('wy0', None))
                self.sim_control_widget.wz0_input.setValue(sp.get('wz0', None))
                self.sim_control_widget.k_wz_input.setValue(sp.get('k_wz', None))
                self.sim_control_widget.k_theta_input.setValue(sp.get('k_theta', None))
                self.sim_control_widget.kwz_input.setValue(sp.get('kwz', None))
                self.sim_control_widget.ktheta_input.setValue(sp.get('ktheta', None))
                self.sim_control_widget.k_ps_input.setValue(sp.get('k_ps', None))
                self.sim_control_widget.k_ph_input.setValue(sp.get('k_ph', None))
                self.sim_control_widget.k_wx_input.setValue(sp.get('k_wx', None))
                self.sim_control_widget.k_wy_input.setValue(sp.get('k_wy', None))
                self.sim_control_widget.tend_under_input.setValue(sp.get('tend_under', None))
                self.sim_control_widget.T1_input.setValue(sp.get('T1', None))
                self.sim_control_widget.T2_input.setValue(sp.get('T2', None))
                self.sim_control_widget.time_sequence_input.setText(sp.get('time_sequence', None)),
                self.sim_control_widget.thrust_sequence_input.setText(sp.get('thrust_sequence', None))

            if "dive_params" in config:
                mmp = config['dive_params']
                self.sim_dive_widget.ship_L_input.setValue(mmp.get('ship_L', None))
                self.sim_dive_widget.ship_M_input.setValue(mmp.get('ship_M', None))
                self.sim_dive_widget.ship_B_input.setValue(mmp.get('ship_B', None))
                self.sim_dive_widget.ship_T_input.setValue(mmp.get('ship_T', None))
                self.sim_dive_widget.burn_N_input.setValue(mmp.get('burn_N', None))
                self.sim_dive_widget.ship_if.setCurrentIndex(int(mmp.get('ship_if', None))),
                self.sim_dive_widget.ship_tpye.setCurrentIndex(int(mmp.get('ship_tpye', None)))

                self.sim_dive_widget.ship_x_x_input.setValue(mmp.get('ship_x_x', None))
                self.sim_dive_widget.ship_x_y_input.setValue(mmp.get('ship_x_y', None))
                self.sim_dive_widget.ship_x_z_input.setValue(mmp.get('ship_x_z', None))
                self.sim_dive_widget.ship_v_max_input.setValue(mmp.get('ship_v_max', None))
                self.sim_dive_widget.ship_a_max_input.setValue(mmp.get('ship_a_max', None))
                self.sim_dive_widget.air_t_input.setValue(mmp.get('air_t', None))
                self.sim_dive_widget.air_L_input.setValue(mmp.get('air_L', None))
                self.sim_dive_widget.air_theta_input.setValue(mmp.get('air_theta', None))
                self.sim_dive_widget.air_v_input.setValue(mmp.get('air_v', None))

            # 加载UI状态
            if "ui_state" in config:
                ui = config["ui_state"]
                # 设置当前选中的标签页
                tab_widget = self.centralWidget().findChild(QTabWidget)
                if tab_widget:
                    tab_index = ui.get("CurrentTab", 0)
                    if 0 <= tab_index < tab_widget.count():
                        tab_widget.setCurrentIndex(tab_index)

                # 设置可视化标签页
                vis_tab_index = ui.get("VisualizationTab", 0)
                if 0 <= vis_tab_index < self.visualization_widget.tab_widget.count():
                    self.visualization_widget.tab_widget.setCurrentIndex(vis_tab_index)

            # 更新状态栏
            self.status_label.setText(f"配置已从: {filename} 加载")
            QMessageBox.information(self, "加载成功", f"配置已成功从:\n{filename}\n加载")
            logging.info(f"配置已从: {filename} 加载")

        except Exception as e:
            logging.exception("加载配置时出错")
            QMessageBox.critical(self, "错误", f"加载配置失败: {str(e)}")
            self.status_label.setText("加载配置失败")

    def load_laptop_configuration(self):
        """从文件加载完整配置"""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self, "加载配置", "input.txt", "TXT Files (*.txt);;All Files (*)"
            )
            if not filename:
                return

            t0, _, _ = read_data(filename, 't0')
            tend, _, _ = read_data(filename, 'tend')
            dt, _, _ = read_data(filename, 'dt')
            v0, _, _ = read_data(filename, 'v0')
            theta0, _, _ = read_data(filename, 'theta0')
            psi0, _, _ = read_data(filename, 'psi0')
            phi0, _, _ = read_data(filename, 'phi0')
            alpha0, _, _ = read_data(filename, 'alpha0')
            wx0, _, _ = read_data(filename, 'wx0')
            wy0, _, _ = read_data(filename, 'wy0')
            wz0, _, _ = read_data(filename, 'wz0')
            k_wz, _, _ = read_data(filename, 'k_wz')
            k_theta, _, _ = read_data(filename, 'k_theta')
            kwz, _, _ = read_data(filename, 'kwz')
            ktheta, _, _ = read_data(filename, 'ktheta')
            k_ps, _, _ = read_data(filename, 'k_ps')
            k_ph, _, _ = read_data(filename, 'k_ph')
            k_wx, _, _ = read_data(filename, 'k_wx')
            k_wy, _, _ = read_data(filename, 'k_wy')
            tend_under, _, _ = read_data(filename, 'tend_under')
            T1, _, _ = read_data(filename, 'T1')
            T2, _, _ = read_data(filename, 'T2')
            time_sequence, _, _ = read_data(filename, 'time_sequence')
            thrust_sequence, _, _ = read_data(filename, 'thrust_sequence')

            L, _, _ = read_data(filename, 'L')
            S, _, _ = read_data(filename, 'S')
            V, _, _ = read_data(filename, 'V')
            m, _, _ = read_data(filename, 'm')
            xc, _, _ = read_data(filename, 'xc')
            yc, _, _ = read_data(filename, 'yc')
            zc, _, _ = read_data(filename, 'zc')
            Jxx, _, _ = read_data(filename, 'Jxx')
            Jyy, _, _ = read_data(filename, 'Jyy')
            Jzz, _, _ = read_data(filename, 'Jzz')
            T, _, _ = read_data(filename, 'T')
            lk, _, _ = read_data(filename, 'lk')
            rk, _, _ = read_data(filename, 'rk')
            sgm, _, _ = read_data(filename, 'sgm')
            dyc, _, _ = read_data(filename, 'dyc')
            SGM, _, _ = read_data(filename, 'SGM')
            LW, _, _ = read_data(filename, 'LW')
            LH, _, _ = read_data(filename, 'LH')
            dkmax, _, _ = read_data(filename, 'dkmax')
            dkmin, _, _ = read_data(filename, 'dkmin')
            dk0, _, _ = read_data(filename, 'dk0')
            deltaymax, _, _ = read_data(filename, 'deltaymax')
            deltavymax, _, _ = read_data(filename, 'deltavymax')
            ddmax, _, _ = read_data(filename, 'ddmax')
            dvmax, _, _ = read_data(filename, 'dvmax')
            dthetamax, _, _ = read_data(filename, 'dthetamax')
            wzmax, _, _ = read_data(filename, 'wzmax')
            wxmax, _, _ = read_data(filename, 'wxmax')
            dphimax, _, _ = read_data(filename, 'dphimax')

            ship_L, _, _ = read_data(filename, 'ship_L')
            ship_M, _, _ = read_data(filename, 'ship_M')
            ship_B, _, _ = read_data(filename, 'ship_B')
            ship_T, _, _ = read_data(filename, 'ship_T')
            burn_N, _, _ = read_data(filename, 'burn_N')
            ship_if, _, _ = read_data(filename, 'ship_if')
            ship_tpye, _, _ = read_data(filename, 'ship_tpye')
            ship_x_x, _, _ = read_data(filename, 'ship_x_x')
            ship_x_y, _, _ = read_data(filename, 'ship_x_y')
            ship_x_z, _, _ = read_data(filename, 'ship_x_z')
            ship_v_max, _, _ = read_data(filename, 'ship_v_max')
            ship_a_max, _, _ = read_data(filename, 'ship_a_max')
            air_t, _, _ = read_data(filename, 'air_t')
            air_L, _, _ = read_data(filename, 'air_L')
            air_theta, _, _ = read_data(filename, 'air_theta')
            air_v, _, _ = read_data(filename, 'air_v')

            laptop_datas = {
                't0': t0,
                'tend': tend,
                'dt': dt,
                'v0': v0,
                'theta0': theta0,
                'psi0': psi0,
                'phi0': phi0,
                'alpha0': alpha0,
                'wx0': wx0,
                'wy0': wy0,
                'wz0': wz0,
                'k_wz': k_wz,
                'k_theta': k_theta,
                'kwz': kwz,
                'ktheta': ktheta,
                'k_ps': k_ps,
                'k_ph': k_ph,
                'k_wx': k_wx,
                'k_wy': k_wy,
                'tend_under': tend_under,
                'T1': T1,
                'T2': T2,
                'time_sequence': time_sequence,
                'thrust_sequence': thrust_sequence,
                'L': L,
                'S': S,
                'V': V,
                'm': m,
                'xc': xc,
                'yc': yc,
                'zc': zc,
                'Jxx': Jxx,
                'Jyy': Jyy,
                'Jzz': Jzz,
                'T': T,
                'lk': lk,
                'rk': rk,
                'sgm': sgm,
                'dyc': dyc,
                'SGM': SGM,
                'LW': LW,
                'LH': LH,
                'dkmax': dkmax,
                'dkmin': dkmin,
                'dk0': dk0,
                'deltaymax': deltaymax,
                'deltavymax': deltavymax,
                'ddmax': ddmax,
                'dvmax': dvmax,
                'dthetamax': dthetamax,
                'wzmax': wzmax,
                'wxmax': wxmax,
                'dphimax': dphimax,
                'ship_L': ship_L,
                'ship_M': ship_M,
                'ship_B': ship_B,
                'ship_T': ship_T,
                'burn_N': burn_N,
                'ship_if': ship_if,
                'ship_tpye': ship_tpye,
                'ship_x_x': ship_x_x,
                'ship_x_y': ship_x_y,
                'ship_x_z': ship_x_z,
                'ship_v_max': ship_v_max,
                'ship_a_max': ship_a_max,
                'air_t': air_t,
                'air_L': air_L,
                'air_theta': air_theta,
                'air_v': air_v,
            }


            # 验证配置文件

            mp = laptop_datas
            self.model_param_widget.L_input.setValue(mp.get('L', None))
            self.model_param_widget.S_input.setValue(mp.get('S', None))
            self.model_param_widget.V_input.setValue(mp.get('V', None))
            self.model_param_widget.m_input.setValue(mp.get('m', None))
            self.model_param_widget.xc_input.setValue(mp.get('xc', None))
            self.model_param_widget.yc_input.setValue(mp.get('yc', None))
            self.model_param_widget.zc_input.setValue(mp.get('zc', None))
            self.model_param_widget.Jxx_input.setValue(mp.get('Jxx', None))
            self.model_param_widget.Jyy_input.setValue(mp.get('Jyy', None))
            self.model_param_widget.Jzz_input.setValue(mp.get('Jzz', None))
            self.model_param_widget.T_input.setValue(mp.get('T', None))
            self.model_param_widget.lk_input.setValue(mp.get('lk', None))
            self.model_param_widget.rk_input.setValue(mp.get('rk', None))
            self.model_param_widget.sgm_input.setValue(mp.get('sgm', None))
            self.model_param_widget.dyc_input.setValue(mp.get('dyc', None))
            self.model_param_widget.SGM_input.setValue(mp.get('SGM', None))
            self.model_param_widget.LW_input.setValue(mp.get('LW', None))
            self.model_param_widget.LH_input.setValue(mp.get('LH', None))
            self.model_param_widget.dkmax_input.setValue(mp.get('dkmax', None))
            self.model_param_widget.dkmin_input.setValue(mp.get('dkmin', None))
            self.model_param_widget.dk0_input.setValue(mp.get('dk0', None))
            self.model_param_widget.deltaymax_input.setValue(mp.get('deltaymax', None))
            self.model_param_widget.deltavymax_input.setValue(mp.get('deltavymax', None))
            self.model_param_widget.ddmax_input.setValue(mp.get('ddmax', None))
            self.model_param_widget.dvmax_input.setValue(mp.get('dvmax', None))
            self.model_param_widget.dthetamax_input.setValue(mp.get('dthetamax', None))
            self.model_param_widget.wzmax_input.setValue(mp.get('wzmax', None))
            self.model_param_widget.wxmax_input.setValue(mp.get('wxmax', None))
            self.model_param_widget.dphimax_input.setValue(mp.get('dphimax', None))

            sp = laptop_datas
            self.sim_control_widget.t0_input.setValue(sp.get('t0', None))
            self.sim_control_widget.tend_input.setValue(sp.get('tend', None))
            self.sim_control_widget.dt_input.setValue(sp.get('dt', None))
            self.sim_control_widget.v0_input.setValue(sp.get('v0', None))
            self.sim_control_widget.theta0_input.setValue(sp.get('theta0', None))
            self.sim_control_widget.psi0_input.setValue(sp.get('psi0', None))
            self.sim_control_widget.phi0_input.setValue(sp.get('phi0', None))
            self.sim_control_widget.alpha0_input.setValue(sp.get('alpha0', None))
            self.sim_control_widget.wx0_input.setValue(sp.get('wx0', None))
            self.sim_control_widget.wy0_input.setValue(sp.get('wy0', None))
            self.sim_control_widget.wz0_input.setValue(sp.get('wz0', None))
            self.sim_control_widget.k_wz_input.setValue(sp.get('k_wz', None))
            self.sim_control_widget.k_theta_input.setValue(sp.get('k_theta', None))
            self.sim_control_widget.kwz_input.setValue(sp.get('kwz', None))
            self.sim_control_widget.ktheta_input.setValue(sp.get('ktheta', None))
            self.sim_control_widget.k_ps_input.setValue(sp.get('k_ps', None))
            self.sim_control_widget.k_ph_input.setValue(sp.get('k_ph', None))
            self.sim_control_widget.k_wx_input.setValue(sp.get('k_wx', None))
            self.sim_control_widget.k_wy_input.setValue(sp.get('k_wy', None))
            self.sim_control_widget.tend_under_input.setValue(sp.get('tend_under', None))
            self.sim_control_widget.T1_input.setValue(sp.get('T1', None))
            self.sim_control_widget.T2_input.setValue(sp.get('T2', None))
            self.sim_control_widget.time_sequence_input.setText(sp.get('time_sequence', None)),
            self.sim_control_widget.thrust_sequence_input.setText(sp.get('thrust_sequence', None))

            mmp = laptop_datas
            self.sim_dive_widget.ship_L_input.setValue(mmp.get('ship_L', None))
            self.sim_dive_widget.ship_M_input.setValue(mmp.get('ship_M', None))
            self.sim_dive_widget.ship_B_input.setValue(mmp.get('ship_B', None))
            self.sim_dive_widget.ship_T_input.setValue(mmp.get('ship_T', None))
            self.sim_dive_widget.burn_N_input.setValue(mmp.get('burn_N', None))
            self.sim_dive_widget.ship_if.setCurrentIndex(int(mmp.get('ship_if', None))),
            self.sim_dive_widget.ship_tpye.setCurrentIndex(int(mmp.get('ship_tpye', None)))

            self.sim_dive_widget.ship_x_x_input.setValue(mmp.get('ship_x_x', None))
            self.sim_dive_widget.ship_x_y_input.setValue(mmp.get('ship_x_y', None))
            self.sim_dive_widget.ship_x_z_input.setValue(mmp.get('ship_x_z', None))
            self.sim_dive_widget.ship_v_max_input.setValue(mmp.get('ship_v_max', None))
            self.sim_dive_widget.ship_a_max_input.setValue(mmp.get('ship_a_max', None))
            self.sim_dive_widget.air_t_input.setValue(mmp.get('air_t', None))
            self.sim_dive_widget.air_L_input.setValue(mmp.get('air_L', None))
            self.sim_dive_widget.air_theta_input.setValue(mmp.get('air_theta', None))
            self.sim_dive_widget.air_v_input.setValue(mmp.get('air_v', None))

            # 更新状态栏
            self.status_label.setText(f"配置已从: {filename} 加载")
            QMessageBox.information(self, "加载成功", f"配置已成功从:\n{filename}\n加载")
            logging.info(f"配置已从: {filename} 加载")

        except Exception as e:
            logging.exception("加载配置时出错")
            QMessageBox.critical(self, "错误", f"加载配置失败: {str(e)}")
            self.status_label.setText("加载配置失败")

    def reset_view(self):
        """重置视图"""
        self.visualization_widget.update_plots()
        QMessageBox.information(self, "重置成功", "视图已重置")

    def get_data_info(self, data):
        """根据数据类型返回对应的write_data参数"""
        if isinstance(data, str):
            return 'single', 'STR'
        elif isinstance(data, (int, float)):
            return 'single', 'FLT'
        elif isinstance(data, (list, tuple)):
            if len(data) == 0:
                return 'single', 'FLT'
            elif all(isinstance(x, (int, float)) for x in data):
                return 'array1', 'FLT'
            else:
                return 'array1', 'STR'
        elif isinstance(data, np.ndarray):
            if data.ndim == 1:
                return 'array1', 'FLT'
            elif data.ndim == 2:
                return 'array2', 'FLT'
            else:
                return 'single', 'FLT'  # 对于高维数组，暂时作为单个值处理
        else:
            # 默认处理其他类型
            return 'single', 'FLT'

    def show_about(self):
        """显示关于对话框"""
        # 创建自定义对话框
        dialog = QDialog(self)
        dialog.setWindowTitle("关于")
        dialog.setFixedSize(450, 320)
        dialog.setWindowFlags(dialog.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # 背景标签
        bg_label = QLabel(dialog)
        bg_label.setGeometry(0, 0, 450, 320)

        try:
            # 加载背景图片
            pixmap = QPixmap("./about/background_about.png")
            if pixmap.isNull():
                raise Exception("背景图片加载失败")

            # 按比例缩放图片以适应对话框
            scaled_pixmap = pixmap.scaled(450, 320, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)

            # 创建一个与对话框同样大小的图像
            bg_image = QPixmap(450, 320)
            bg_image.fill(Qt.transparent)

            painter = QPainter(bg_image)

            # 绘制缩放后的背景图片
            # 计算居中位置
            x = (450 - scaled_pixmap.width()) // 2
            y = (320 - scaled_pixmap.height()) // 2
            painter.drawPixmap(x, y, scaled_pixmap)

            # 绘制蓝粉渐变遮罩 (增加半透明效果)
            gradient = QLinearGradient(0, 0, 450, 320)
            gradient.setColorAt(0, QColor(70, 130, 220, 180))  # 蓝色
            gradient.setColorAt(1, QColor(220, 70, 150, 180))  # 粉色
            painter.setBrush(gradient)
            painter.setPen(Qt.NoPen)
            painter.drawRect(0, 0, 450, 320)

            # 添加一个半透明黑色层增强文字可读性
            painter.setBrush(QColor(0, 0, 0, 100))
            painter.drawRect(0, 0, 450, 320)

            painter.end()

            bg_label.setPixmap(bg_image)

        except Exception as e:
            # 如果加载图片失败，使用蓝粉渐变背景

            gradient = QLinearGradient(0, 0, 450, 320)
            gradient.setColorAt(0, QColor(70, 130, 220))  # 蓝色
            gradient.setColorAt(1, QColor(220, 70, 150))  # 粉色

            palette = QPalette()
            palette.setBrush(QPalette.Window, QBrush(gradient))
            dialog.setPalette(palette)
            dialog.setAutoFillBackground(True)
            logging.warning(f"加载背景图片失败，使用渐变背景: {str(e)}")

        # 关于文本
        about_text = """
        <h3 style="color: white; margin-bottom: 5px; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">超空泡航行体动力学仿真系统</h3>
        <p style="color: white; margin: 5px 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);"><b>版本:</b> 3.0</p>
        <p style="color: white; margin: 5px 0; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);"><b>开发单位:</b> NUDT</p>
        <p style="color: white; margin-top: 10px; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">© 2025 版权所有</p>
        <p style="color: #FFD700; margin-top: 15px; font-style: italic; text-shadow: 1px 1px 2px rgba(0,0,0,0.5);">
            Philia093 & WXC
        </p>
        """

        # 创建文本标签
        text_label = QLabel(about_text, dialog)
        text_label.setAlignment(Qt.AlignCenter)
        text_label.setStyleSheet("background-color: transparent;")
        text_label.setGeometry(0, 80, 450, 180)

        # 确定按钮
        ok_button = QPushButton("确定", dialog)
        ok_button.setGeometry(175, 270, 100, 35)
        ok_button.setStyleSheet("""
            QPushButton {
                background-color: rgba(70, 130, 220, 200);
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(50, 110, 200, 220);
            }
            QPushButton:pressed {
                background-color: rgba(30, 90, 180, 230);
            }
        """)
        ok_button.clicked.connect(dialog.accept)

        # 显示对话框
        dialog.exec_()

    def custom_export_data(self):
        """自定义导出数据"""
        dialog = CustomExportDialog(self.rushui, self)
        dialog.exec_()

    def auto_load(self):
        filename = 'input.txt'
        check_file = os.path.exists("./input.txt")
        if check_file:
            try:

                t0, _, _ = read_data('input.txt', 't0')
                tend, _, _ = read_data('input.txt', 'tend')
                dt, _, _ = read_data('input.txt', 'dt')
                v0, _, _ = read_data('input.txt', 'v0')
                theta0, _, _ = read_data('input.txt', 'theta0')
                psi0, _, _ = read_data('input.txt', 'psi0')
                phi0, _, _ = read_data('input.txt', 'phi0')
                alpha0, _, _ = read_data('input.txt', 'alpha0')
                wx0, _, _ = read_data('input.txt', 'wx0')
                wy0, _, _ = read_data('input.txt', 'wy0')
                wz0, _, _ = read_data('input.txt', 'wz0')
                k_wz, _, _ = read_data('input.txt', 'k_wz')
                k_theta, _, _ = read_data('input.txt', 'k_theta')
                kwz, _, _ = read_data('input.txt', 'kwz')
                ktheta, _, _ = read_data('input.txt', 'ktheta')
                k_ps, _, _ = read_data('input.txt', 'k_ps')
                k_ph, _, _ = read_data('input.txt', 'k_ph')
                k_wx, _, _ = read_data('input.txt', 'k_wx')
                k_wy, _, _ = read_data('input.txt', 'k_wy')
                tend_under, _, _ = read_data('input.txt', 'tend_under')
                T1, _, _ = read_data('input.txt', 'T1')
                T2, _, _ = read_data('input.txt', 'T2')
                time_sequence, _, _ = read_data('input.txt', 'time_sequence')
                thrust_sequence, _, _ = read_data('input.txt', 'thrust_sequence')

                L, _, _ = read_data('input.txt', 'L')
                S, _, _ = read_data('input.txt', 'S')
                V, _, _ = read_data('input.txt', 'V')
                m, _, _ = read_data('input.txt', 'm')
                xc, _, _ = read_data('input.txt', 'xc')
                yc, _, _ = read_data('input.txt', 'yc')
                zc, _, _ = read_data('input.txt', 'zc')
                Jxx, _, _ = read_data('input.txt', 'Jxx')
                Jyy, _, _ = read_data('input.txt', 'Jyy')
                Jzz, _, _ = read_data('input.txt', 'Jzz')
                T, _, _ = read_data('input.txt', 'T')
                lk, _, _ = read_data('input.txt', 'lk')
                rk, _, _ = read_data('input.txt', 'rk')
                sgm, _, _ = read_data('input.txt', 'sgm')
                dyc, _, _ = read_data('input.txt', 'dyc')
                SGM, _, _ = read_data('input.txt', 'SGM')
                LW, _, _ = read_data('input.txt', 'LW')
                LH, _, _ = read_data('input.txt', 'LH')
                dkmax, _, _ = read_data('input.txt', 'dkmax')
                dkmin, _, _ = read_data('input.txt', 'dkmin')
                dk0, _, _ = read_data('input.txt', 'dk0')
                deltaymax, _, _ = read_data('input.txt', 'deltaymax')
                deltavymax, _, _ = read_data('input.txt', 'deltavymax')
                ddmax, _, _ = read_data('input.txt', 'ddmax')
                dvmax, _, _ = read_data('input.txt', 'dvmax')
                dthetamax, _, _ = read_data('input.txt', 'dthetamax')
                wzmax, _, _ = read_data('input.txt', 'wzmax')
                wxmax, _, _ = read_data('input.txt', 'wxmax')
                dphimax, _, _ = read_data('input.txt', 'dphimax')

                ship_L, _, _ = read_data('input.txt', 'ship_L')
                ship_M, _, _ = read_data('input.txt', 'ship_M')
                ship_B, _, _ = read_data('input.txt', 'ship_B')
                ship_T, _, _ = read_data('input.txt', 'ship_T')
                burn_N, _, _ = read_data('input.txt', 'burn_N')
                ship_if, _, _ = read_data('input.txt', 'ship_if')
                ship_tpye, _, _ = read_data('input.txt', 'ship_tpye')
                ship_x_x, _, _ = read_data('input.txt', 'ship_x_x')
                ship_x_y, _, _ = read_data('input.txt', 'ship_x_y')
                ship_x_z, _, _ = read_data('input.txt', 'ship_x_z')
                ship_v_max, _, _ = read_data('input.txt', 'ship_v_max')
                ship_a_max, _, _ = read_data('input.txt', 'ship_a_max')
                air_t, _, _ = read_data('input.txt', 'air_t')
                air_L, _, _ = read_data('input.txt', 'air_L')
                air_theta, _, _ = read_data('input.txt', 'air_theta')
                air_v, _, _ = read_data('input.txt', 'air_v')

                laptop_datas = {
                    't0': t0,
                    'tend': tend,
                    'dt': dt,
                    'v0': v0,
                    'theta0': theta0,
                    'psi0': psi0,
                    'phi0': phi0,
                    'alpha0': alpha0,
                    'wx0': wx0,
                    'wy0': wy0,
                    'wz0': wz0,
                    'k_wz': k_wz,
                    'k_theta': k_theta,
                    'kwz': kwz,
                    'ktheta': ktheta,
                    'k_ps': k_ps,
                    'k_ph': k_ph,
                    'k_wx': k_wx,
                    'k_wy': k_wy,
                    'tend_under': tend_under,
                    'T1': T1,
                    'T2': T2,
                    'time_sequence': time_sequence,
                    'thrust_sequence': thrust_sequence,
                    'L': L,
                    'S': S,
                    'V': V,
                    'm': m,
                    'xc': xc,
                    'yc': yc,
                    'zc': zc,
                    'Jxx': Jxx,
                    'Jyy': Jyy,
                    'Jzz': Jzz,
                    'T': T,
                    'lk': lk,
                    'rk': rk,
                    'sgm': sgm,
                    'dyc': dyc,
                    'SGM': SGM,
                    'LW': LW,
                    'LH': LH,
                    'dkmax': dkmax,
                    'dkmin': dkmin,
                    'dk0': dk0,
                    'deltaymax': deltaymax,
                    'deltavymax': deltavymax,
                    'ddmax': ddmax,
                    'dvmax': dvmax,
                    'dthetamax': dthetamax,
                    'wzmax': wzmax,
                    'wxmax': wxmax,
                    'dphimax': dphimax,
                    'ship_L': ship_L,
                    'ship_M': ship_M,
                    'ship_B': ship_B,
                    'ship_T': ship_T,
                    'burn_N': burn_N,
                    'ship_if': ship_if,
                    'ship_tpye': ship_tpye,
                    'ship_x_x': ship_x_x,
                    'ship_x_y': ship_x_y,
                    'ship_x_z': ship_x_z,
                    'ship_v_max': ship_v_max,
                    'ship_a_max': ship_a_max,
                    'air_t': air_t,
                    'air_L': air_L,
                    'air_theta': air_theta,
                    'air_v': air_v,
                }

                # 验证配置文件

                mp = laptop_datas
                self.model_param_widget.L_input.setValue(mp.get('L', None))
                self.model_param_widget.S_input.setValue(mp.get('S', None))
                self.model_param_widget.V_input.setValue(mp.get('V', None))
                self.model_param_widget.m_input.setValue(mp.get('m', None))
                self.model_param_widget.xc_input.setValue(mp.get('xc', None))
                self.model_param_widget.yc_input.setValue(mp.get('yc', None))
                self.model_param_widget.zc_input.setValue(mp.get('zc', None))
                self.model_param_widget.Jxx_input.setValue(mp.get('Jxx', None))
                self.model_param_widget.Jyy_input.setValue(mp.get('Jyy', None))
                self.model_param_widget.Jzz_input.setValue(mp.get('Jzz', None))
                self.model_param_widget.T_input.setValue(mp.get('T', None))
                self.model_param_widget.lk_input.setValue(mp.get('lk', None))
                self.model_param_widget.rk_input.setValue(mp.get('rk', None))
                self.model_param_widget.sgm_input.setValue(mp.get('sgm', None))
                self.model_param_widget.dyc_input.setValue(mp.get('dyc', None))
                self.model_param_widget.SGM_input.setValue(mp.get('SGM', None))
                self.model_param_widget.LW_input.setValue(mp.get('LW', None))
                self.model_param_widget.LH_input.setValue(mp.get('LH', None))
                self.model_param_widget.dkmax_input.setValue(mp.get('dkmax', None))
                self.model_param_widget.dkmin_input.setValue(mp.get('dkmin', None))
                self.model_param_widget.dk0_input.setValue(mp.get('dk0', None))
                self.model_param_widget.deltaymax_input.setValue(mp.get('deltaymax', None))
                self.model_param_widget.deltavymax_input.setValue(mp.get('deltavymax', None))
                self.model_param_widget.ddmax_input.setValue(mp.get('ddmax', None))
                self.model_param_widget.dvmax_input.setValue(mp.get('dvmax', None))
                self.model_param_widget.dthetamax_input.setValue(mp.get('dthetamax', None))
                self.model_param_widget.wzmax_input.setValue(mp.get('wzmax', None))
                self.model_param_widget.wxmax_input.setValue(mp.get('wxmax', None))
                self.model_param_widget.dphimax_input.setValue(mp.get('dphimax', None))

                sp = laptop_datas
                self.sim_control_widget.t0_input.setValue(sp.get('t0', None))
                self.sim_control_widget.tend_input.setValue(sp.get('tend', None))
                self.sim_control_widget.dt_input.setValue(sp.get('dt', None))
                self.sim_control_widget.v0_input.setValue(sp.get('v0', None))
                self.sim_control_widget.theta0_input.setValue(sp.get('theta0', None))
                self.sim_control_widget.psi0_input.setValue(sp.get('psi0', None))
                self.sim_control_widget.phi0_input.setValue(sp.get('phi0', None))
                self.sim_control_widget.alpha0_input.setValue(sp.get('alpha0', None))
                self.sim_control_widget.wx0_input.setValue(sp.get('wx0', None))
                self.sim_control_widget.wy0_input.setValue(sp.get('wy0', None))
                self.sim_control_widget.wz0_input.setValue(sp.get('wz0', None))
                self.sim_control_widget.k_wz_input.setValue(sp.get('k_wz', None))
                self.sim_control_widget.k_theta_input.setValue(sp.get('k_theta', None))
                self.sim_control_widget.kwz_input.setValue(sp.get('kwz', None))
                self.sim_control_widget.ktheta_input.setValue(sp.get('ktheta', None))
                self.sim_control_widget.k_ps_input.setValue(sp.get('k_ps', None))
                self.sim_control_widget.k_ph_input.setValue(sp.get('k_ph', None))
                self.sim_control_widget.k_wx_input.setValue(sp.get('k_wx', None))
                self.sim_control_widget.k_wy_input.setValue(sp.get('k_wy', None))
                self.sim_control_widget.tend_under_input.setValue(sp.get('tend_under', None))
                self.sim_control_widget.T1_input.setValue(sp.get('T1', None))
                self.sim_control_widget.T2_input.setValue(sp.get('T2', None))
                self.sim_control_widget.time_sequence_input.setText(sp.get('time_sequence', None)),
                self.sim_control_widget.thrust_sequence_input.setText(sp.get('thrust_sequence', None))

                mmp = laptop_datas
                self.sim_dive_widget.ship_L_input.setValue(mmp.get('ship_L', None))
                self.sim_dive_widget.ship_M_input.setValue(mmp.get('ship_M', None))
                self.sim_dive_widget.ship_B_input.setValue(mmp.get('ship_B', None))
                self.sim_dive_widget.ship_T_input.setValue(mmp.get('ship_T', None))
                self.sim_dive_widget.burn_N_input.setValue(mmp.get('burn_N', None))
                self.sim_dive_widget.ship_if.setCurrentIndex(int(mmp.get('ship_if', None))),
                self.sim_dive_widget.ship_tpye.setCurrentIndex(int(mmp.get('ship_tpye', None)))

                self.sim_dive_widget.ship_x_x_input.setValue(mmp.get('ship_x_x', None))
                self.sim_dive_widget.ship_x_y_input.setValue(mmp.get('ship_x_y', None))
                self.sim_dive_widget.ship_x_z_input.setValue(mmp.get('ship_x_z', None))
                self.sim_dive_widget.ship_v_max_input.setValue(mmp.get('ship_v_max', None))
                self.sim_dive_widget.ship_a_max_input.setValue(mmp.get('ship_a_max', None))
                self.sim_dive_widget.air_t_input.setValue(mmp.get('air_t', None))
                self.sim_dive_widget.air_L_input.setValue(mmp.get('air_L', None))
                self.sim_dive_widget.air_theta_input.setValue(mmp.get('air_theta', None))
                self.sim_dive_widget.air_v_input.setValue(mmp.get('air_v', None))

                # 更新状态栏
                logging.info("加载配置成功")

            except Exception as e:
                logging.exception("加载配置时出错")

    def to_all_data(self, Checki):

        # 收集模型参数
        datas = {
            # 几何与质量参数
            'L': self.model_param_widget.L_input.value(),  # 长度 (m)
            'S': self.model_param_widget.S_input.value(),  # 横截面积 (m²)
            'V': self.model_param_widget.V_input.value(),  # 体积 (m³)
            'm': self.model_param_widget.m_input.value(),  # 质量 (kg)
            'xc': self.model_param_widget.xc_input.value(),  # 重心 x 坐标 (m)
            'yc': self.model_param_widget.yc_input.value(),  # 重心 y 坐标 (m)
            'zc': self.model_param_widget.zc_input.value(),  # 重心 z 坐标 (m)
            'Jxx': self.model_param_widget.Jxx_input.value(),  # 转动惯量 Jxx (kg·m²)
            'Jyy': self.model_param_widget.Jyy_input.value(),  # 转动惯量 Jyy (kg·m²)
            'Jzz': self.model_param_widget.Jzz_input.value(),  # 转动惯量 Jzz (kg·m²)
            'T': self.model_param_widget.T_input.value(),  # 推力 (N)

            # 空泡仿真参数
            'lk': self.model_param_widget.lk_input.value(),  # 空化器距重心距离 (m)
            'rk': self.model_param_widget.rk_input.value(),  # 空化器半径 (m)
            'sgm': self.model_param_widget.sgm_input.value(),  # 全局空化数
            'dyc': self.model_param_widget.dyc_input.value(),  # 空泡轴线偏离 (m)

            # 水下物理几何参数
            'SGM': self.model_param_widget.SGM_input.value(),  # 水下空化数
            'LW': self.model_param_widget.LW_input.value(),  # 水平鳍位置 (m)
            'LH': self.model_param_widget.LH_input.value(),  # 垂直鳍位置 (m)

            # 舵机与角度限制参数
            'dkmax': self.model_param_widget.dkmax_input.value(),  # 舵角上限 (°)
            'dkmin': self.model_param_widget.dkmin_input.value(),  # 舵角下限 (°)
            'dk0': self.model_param_widget.dk0_input.value(),  # 舵角零位 (°)
            'deltaymax': self.model_param_widget.deltaymax_input.value(),  # 横向位移限制 (m)
            'deltavymax': self.model_param_widget.deltavymax_input.value(),  # 垂向位移限制 (m)
            'ddmax': self.model_param_widget.ddmax_input.value(),  # 最大深度变化率 (°/s²)
            'dvmax': self.model_param_widget.dvmax_input.value(),  # 最大速度变化率 (°/s²)
            'dthetamax': self.model_param_widget.dthetamax_input.value(),  # 最大俯仰角速率 (°/s)
            'wzmax': self.model_param_widget.wzmax_input.value(),  # 最大偏航角速率 (°/s)
            'wxmax': self.model_param_widget.wxmax_input.value(),  # 最大滚转角速率 (°/s)
            'dphimax': self.model_param_widget.dphimax_input.value(),  # 最大滚转角加速度 (°/s²)

            # 收集仿真参数

            # ——————————入水参数——————————
            't0': self.sim_control_widget.t0_input.value(),  # 起始时间 (s)
            'tend': self.sim_control_widget.tend_input.value(),  # 终止时间 (s)
            'dt': self.sim_control_widget.dt_input.value(),  # 仿真步长 (s)
            'v0': self.sim_control_widget.v0_input.value(),  # 入水速度 (m/s)
            'theta0': self.sim_control_widget.theta0_input.value(),  # 弹道角 (deg)
            'psi0': self.sim_control_widget.psi0_input.value(),  # 偏航角 (deg)
            'phi0': self.sim_control_widget.phi0_input.value(),  # 横滚角 (deg)
            'alpha0': self.sim_control_widget.alpha0_input.value(),  # 攻角 (deg)
            'wx0': self.sim_control_widget.wx0_input.value(),  # 横滚角速度 (deg/s)
            'wy0': self.sim_control_widget.wy0_input.value(),  # 偏航角速度 (deg/s)
            'wz0': self.sim_control_widget.wz0_input.value(),  # 俯仰角速度 (deg/s)

            # ——————————控制参数 (修正分组)——————————
            # 注：原代码存在分组命名冲突，已按实际参数含义重新分组
            'k_wz': self.sim_control_widget.k_wz_input.value(),  # 偏航角速度增益 (控制参数)
            'k_theta': self.sim_control_widget.k_theta_input.value(),  # 俯仰角增益 (控制参数)

            'kwz': self.sim_control_widget.kwz_input.value(),  # 偏航角速度增益 (控制参数)
            'ktheta': self.sim_control_widget.ktheta_input.value(),  # 俯仰角增益 (控制参数)
            # ——————————深度控制参数——————————
            'k_ps': self.sim_control_widget.k_ps_input.value(),  # 姿态同步增益
            'k_ph': self.sim_control_widget.k_ph_input.value(),  # 舵机响应增益
            'k_wx': self.sim_control_widget.k_wx_input.value(),  # 滚转角速度增益
            'k_wy': self.sim_control_widget.k_wy_input.value(),  # 垂向控制增益
            'tend_under': self.sim_control_widget.tend_under_input.value(), # 水下仿真时间
            'T1': self.sim_control_widget.T1_input.value(),
            'T2': self.sim_control_widget.T2_input.value(),
            'time_sequence': self.sim_control_widget.time_sequence_input.text(),
            'thrust_sequence': self.sim_control_widget.thrust_sequence_input.text(),

            'ship_L': self.sim_dive_widget.ship_L_input.value(),
            'ship_M': self.sim_dive_widget.ship_M_input.value(),
            'ship_B': self.sim_dive_widget.ship_B_input.value(),
            'ship_T': self.sim_dive_widget.ship_T_input.value(),

            # 武器毁伤多次重复实验
            'burn_N': self.sim_dive_widget.burn_N_input.value(),
            'ship_if': self.sim_dive_widget.ship_if.currentIndex(),  # 是否手动设置舰艇类型
            'ship_tpye': self.sim_dive_widget.ship_tpye.currentIndex(),  # 选择的舰艇类型（注意变量名拼写）

            # 目标舰艇相关参数
            'ship_x_x': self.sim_dive_widget.ship_x_x_input.value(),  # x位置
            'ship_x_y': self.sim_dive_widget.ship_x_y_input.value(),  # y位置
            'ship_x_z': self.sim_dive_widget.ship_x_z_input.value(),  # z位置
            'ship_v_max': self.sim_dive_widget.ship_v_max_input.value(),  # 最大速度（节）
            'ship_a_max': self.sim_dive_widget.ship_a_max_input.value(),  # 最大加速度（m/s^2）

            # 空中入水飞行参数
            'air_t': self.sim_dive_widget.air_t_input.value(),  # 飞行时间(s)
            'air_L': self.sim_dive_widget.air_L_input.value(),  # 弹道距离(km)
            'air_theta': self.sim_dive_widget.air_theta_input.value(),  # 入水倾角(deg)
            'air_v': self.sim_dive_widget.air_v_input.value()  # 入水速度(m/s)
        }

        self.to_data_signal.emit(datas)


if __name__ == "__main__":
    # 过滤弃用警告
    import warnings

    warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*sipPyTypeDict.*")

    app = QApplication(sys.argv)

    # 设置应用程序样式
    app.setStyle("Fusion")

    # 调整字体大小
    font = app.font()
    font.setPointSize(9)
    app.setFont(font)

    # 创建并显示主窗口
    main_window = MainWindow()
    main_window.show()

    sys.exit(app.exec_())
