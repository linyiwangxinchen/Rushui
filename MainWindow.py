import json
import time
import pyqtgraph as pg
import logging
import sys
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMessageBox, QVBoxLayout, QTabWidget, QHBoxLayout, QWidget, QMainWindow, \
    QStatusBar, QLabel, QFileDialog, QDialog, QPushButton
from ModelParameterWidget import ModelParameterWidget
from SimulationControlWidget import SimulationControlWidget
from VisualizationWidget import VisualizationWidget
from rushui_model import Rushui
from SimulationDiveWidget import SimulationDiveWidget
from PyQt5.QtGui import QPainter, QLinearGradient, QColor, QPalette, QBrush, QPixmap
import json
from read_data import read_data
from write_data import write_data
import os
import math

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class MainWindow(QMainWindow):
    """主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("入水空泡仿真系统")
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
        control_panel.addTab(self.sim_control_widget, "积分参量")


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
                'x0': self.model_param_widget.x0_input.value(),
                'y0': self.model_param_widget.y0_input.value(),
                'z0': self.model_param_widget.z0_input.value(),
                'theta': self.model_param_widget.theta_input.value(),
                'psi': self.model_param_widget.psi_input.value(),
                'phi': self.model_param_widget.phi_input.value(),
                'vx': self.model_param_widget.vx_input.value(),
                'vy': self.model_param_widget.vy_input.value(),
                'vz': self.model_param_widget.vz_input.value(),
                'wx': self.model_param_widget.wx_input.value(),
                'wy': self.model_param_widget.wy_input.value(),
                'wz': self.model_param_widget.wz_input.value(),
                'dk': self.model_param_widget.dk_input.value(),
                'ds': self.model_param_widget.ds_input.value(),
                'dxx': self.model_param_widget.dxx_input.value(),
                'dkf': self.model_param_widget.dkf_input.value(),
                'dsf': self.model_param_widget.dsf_input.value(),
                'dxf': self.model_param_widget.dxf_input.value(),
                't1': self.model_param_widget.t1_input.value(),
                't2': self.model_param_widget.t2_input.value(),
                'kth': self.model_param_widget.kth_input.value(),
                'kps': self.model_param_widget.kps_input.value(),
                'kph': self.model_param_widget.kph_input.value(),
                'kwx': self.model_param_widget.kwx_input.value(),
                'kwz': self.model_param_widget.kwz_input.value(),
                'kwy': self.model_param_widget.kwy_input.value()
            }

            # 收集仿真参数
            sim_params = {
                "L": self.sim_control_widget.L_input.value(),
                "S": self.sim_control_widget.S_input.value(),
                "V": self.sim_control_widget.V_input.value(),
                "m": self.sim_control_widget.m_input.value(),
                "xc": self.sim_control_widget.xc_input.value(),
                "yc": self.sim_control_widget.yc_input.value(),
                "zc": self.sim_control_widget.zc_input.value(),
                "Jxx": self.sim_control_widget.jxx_input.value(),
                "Jyy": self.sim_control_widget.jyy_input.value(),
                "Jzz": self.sim_control_widget.jzz_input.value(),
                "dt": self.sim_control_widget.dt_input.value(),
                "t0": self.sim_control_widget.t0_input.value(),
                "tend": self.sim_control_widget.tend_input.value(),
                "ycs": self.sim_control_widget.ycs_input.value(),
                "thetacs": self.sim_control_widget.thetacs_input.value(),
                "yvcs": self.sim_control_widget.yvcs_input.value(),
                "psics": self.sim_control_widget.psics_input.value()
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
            # 手动签出
            # names = []
            # datas = []
            # model_params_key = model_params.keys()
            # model_params_val = model_params.values()
            # sim_params_key = sim_params.keys()
            # sim_params_val = sim_params.values()
            # a = 1
            # names = list(model_params_key) + list(sim_params_key)
            # datas = list(model_params_val) + list(sim_params_val)
            # fid = open('output.txt', 'w', encoding='utf-8')
            # for i in range(len(names)):
            #     write_data(fid, 'single', names[i], 'FLT', datas[i])
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
                'x0': self.model_param_widget.x0_input.value(),
                'y0': self.model_param_widget.y0_input.value(),
                'z0': self.model_param_widget.z0_input.value(),
                'theta': self.model_param_widget.theta_input.value(),
                'psi': self.model_param_widget.psi_input.value(),
                'phi': self.model_param_widget.phi_input.value(),
                'vx': self.model_param_widget.vx_input.value(),
                'vy': self.model_param_widget.vy_input.value(),
                'vz': self.model_param_widget.vz_input.value(),
                'wx': self.model_param_widget.wx_input.value(),
                'wy': self.model_param_widget.wy_input.value(),
                'wz': self.model_param_widget.wz_input.value(),
                'dk': self.model_param_widget.dk_input.value(),
                'ds': self.model_param_widget.ds_input.value(),
                'dxx': self.model_param_widget.dxx_input.value(),
                'dkf': self.model_param_widget.dkf_input.value(),
                'dsf': self.model_param_widget.dsf_input.value(),
                'dxf': self.model_param_widget.dxf_input.value(),
                't1': self.model_param_widget.t1_input.value(),
                't2': self.model_param_widget.t2_input.value(),
                'kth': self.model_param_widget.kth_input.value(),
                'kps': self.model_param_widget.kps_input.value(),
                'kph': self.model_param_widget.kph_input.value(),
                'kwx': self.model_param_widget.kwx_input.value(),
                'kwz': self.model_param_widget.kwz_input.value(),
                'kwy': self.model_param_widget.kwy_input.value()
            }

            # 收集仿真参数
            sim_params = {
                "L": self.sim_control_widget.L_input.value(),
                "S": self.sim_control_widget.S_input.value(),
                "V": self.sim_control_widget.V_input.value(),
                "m": self.sim_control_widget.m_input.value(),
                "xc": self.sim_control_widget.xc_input.value(),
                "yc": self.sim_control_widget.yc_input.value(),
                "zc": self.sim_control_widget.zc_input.value(),
                "Jxx": self.sim_control_widget.jxx_input.value(),
                "Jyy": self.sim_control_widget.jyy_input.value(),
                "Jzz": self.sim_control_widget.jzz_input.value(),
                "dt": self.sim_control_widget.dt_input.value(),
                "t0": self.sim_control_widget.t0_input.value(),
                "tend": self.sim_control_widget.tend_input.value(),
                "ycs": self.sim_control_widget.ycs_input.value(),
                "thetacs": self.sim_control_widget.thetacs_input.value(),
                "yvcs": self.sim_control_widget.yvcs_input.value(),
                "psics": self.sim_control_widget.psics_input.value()
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
            a = 1
            names = list(model_params_key) + list(sim_params_key)
            datas = list(model_params_val) + list(sim_params_val)
            fid = open(filename, 'w', encoding='utf-8')
            for i in range(len(names)):
                write_data(fid, 'single', names[i], 'FLT', datas[i])
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
                self.model_param_widget.x0_input.setValue(mp.get('x0', 27.82448))
                self.model_param_widget.y0_input.setValue(mp.get('y0', -3.45))
                self.model_param_widget.z0_input.setValue(mp.get('z0', 0.05623))
                self.model_param_widget.theta_input.setValue(mp.get('theta', 0))
                self.model_param_widget.psi_input.setValue(mp.get('psi', 0))
                self.model_param_widget.phi_input.setValue(mp.get('phi', 6.84184))
                self.model_param_widget.vx_input.setValue(mp.get('vx', 100.96949))
                self.model_param_widget.vy_input.setValue(mp.get('vy', -0.01323))
                self.model_param_widget.vz_input.setValue(mp.get('vz', -0.95246))
                self.model_param_widget.wx_input.setValue(mp.get('wx', 242.955))
                self.model_param_widget.wy_input.setValue(mp.get('wy', -42.435))
                self.model_param_widget.wz_input.setValue(mp.get('wz', 56.515))
                self.model_param_widget.dk_input.setValue(mp.get('dk', -2.9377))
                self.model_param_widget.ds_input.setValue(mp.get('ds', 0.94986))
                self.model_param_widget.dxx_input.setValue(mp.get('dxx', 0.94986))
                self.model_param_widget.dkf_input.setValue(mp.get('dkf', -2.50238))
                self.model_param_widget.dsf_input.setValue(mp.get('dsf', 0.38547))
                self.model_param_widget.dxf_input.setValue(mp.get('dxf', 0.30266))
                self.model_param_widget.t1_input.setValue(mp.get('t1', 25080.6))
                self.model_param_widget.t2_input.setValue(mp.get('t2', 6971.4))
                self.model_param_widget.kth_input.setValue(mp.get('kth', 4))
                self.model_param_widget.kps_input.setValue(mp.get('kps', 4))
                self.model_param_widget.kph_input.setValue(mp.get('kph', 0.08))
                self.model_param_widget.kwx_input.setValue(mp.get('kwx', 0.0016562))
                self.model_param_widget.kwz_input.setValue(mp.get('kwz', 0.312))
                self.model_param_widget.kwy_input.setValue(mp.get('kwy', 0.312))

            # 加载仿真参数
            if "sim_params" in config:
                sp = config["sim_params"]
                self.sim_control_widget.L_input.setValue(sp.get("L", 3.195))
                self.sim_control_widget.S_input.setValue(sp.get("S", 0.0356))
                self.sim_control_widget.V_input.setValue(sp.get("V", 0))
                self.sim_control_widget.m_input.setValue(sp.get("m", 114.7))
                self.sim_control_widget.xc_input.setValue(sp.get("xc", -0.0188))
                self.sim_control_widget.yc_input.setValue(sp.get("yc", -0.0017))
                self.sim_control_widget.zc_input.setValue(sp.get("zc", 0.0008))
                self.sim_control_widget.jxx_input.setValue(sp.get("Jxx", 0.63140684))
                self.sim_control_widget.jyy_input.setValue(sp.get("Jyy", 57.06970864))
                self.sim_control_widget.jzz_input.setValue(sp.get("Jzz", 57.07143674))
                self.sim_control_widget.dt_input.setValue(sp.get("dt", 0.001))
                self.sim_control_widget.t0_input.setValue(sp.get("t0", 0.539))
                self.sim_control_widget.tend_input.setValue(sp.get("tend", 3.41))
                self.sim_control_widget.ycs_input.setValue(sp.get("ycs", -3.45))
                self.sim_control_widget.thetacs_input.setValue(sp.get("thetacs", -2.5086))
                self.sim_control_widget.yvcs_input.setValue(sp.get("yvcs", -0.01323))
                self.sim_control_widget.psics_input.setValue(sp.get("psics", 9.17098))

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

            x0, _, _ = read_data('input.txt', 'x0')
            y0, _, _ = read_data('input.txt', 'y0')
            z0, _, _ = read_data('input.txt', 'z0')
            theta, _, _ = read_data('input.txt', 'theta')
            psi, _, _ = read_data('input.txt', 'psi')
            phi, _, _ = read_data('input.txt', 'phi')
            vx, _, _ = read_data('input.txt', 'vx')
            vy, _, _ = read_data('input.txt', 'vy')
            vz, _, _ = read_data('input.txt', 'vz')
            wx, _, _ = read_data('input.txt', 'wx')
            wy, _, _ = read_data('input.txt', 'wy')
            wz, _, _ = read_data('input.txt', 'wz')
            dk, _, _ = read_data('input.txt', 'dk')
            ds, _, _ = read_data('input.txt', 'ds')
            dxx, _, _ = read_data('input.txt', 'dxx')
            dkf, _, _ = read_data('input.txt', 'dkf')
            dsf, _, _ = read_data('input.txt', 'dsf')
            dxf, _, _ = read_data('input.txt', 'dxf')
            t1, _, _ = read_data('input.txt', 't1')
            t2, _, _ = read_data('input.txt', 't2')
            kth, _, _ = read_data('input.txt', 'kth')
            kps, _, _ = read_data('input.txt', 'kps')
            kph, _, _ = read_data('input.txt', 'kph')
            kwx, _, _ = read_data('input.txt', 'kwx')
            kwz, _, _ = read_data('input.txt', 'kwz')
            kwy, _, _ = read_data('input.txt', 'kwy')
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
            dt, _, _ = read_data('input.txt', 'dt')
            t0, _, _ = read_data('input.txt', 't0')
            tend, _, _ = read_data('input.txt', 'tend')
            ycs, _, _ = read_data('input.txt', 'ycs')
            thetacs, _, _ = read_data('input.txt', 'thetacs')
            yvcs, _, _ = read_data('input.txt', 'yvcs')
            psics, _, _ = read_data('input.txt', 'psics')

            laptop_datas = {
                'x0': x0,
                'y0': y0,
                'z0': z0,
                'theta': theta,
                'psi': psi,
                'phi': phi,
                'vx': vx,
                'vy': vy,
                'vz': vz,
                'wx': wx,
                'wy': wy,
                'wz': wz,
                'dk': dk,
                'ds': ds,
                'dxx': dxx,
                'dkf': dkf,
                'dsf': dsf,
                'dxf': dxf,
                't1': t1,
                't2': t2,
                'kth': kth,
                'kps': kps,
                'kph': kph,
                'kwx': kwx,
                'kwz': kwz,
                'kwy': kwy,
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
                'dt': dt,
                't0': t0,
                'tend': tend,
                'ycs': ycs,
                'thetacs': thetacs,
                'yvcs': yvcs,
                'psics': psics
            }

            # 验证配置文件

            mp = laptop_datas
            self.model_param_widget.x0_input.setValue(mp.get('x0', 27.82448))
            self.model_param_widget.y0_input.setValue(mp.get('y0', -3.45))
            self.model_param_widget.z0_input.setValue(mp.get('z0', 0.05623))
            self.model_param_widget.theta_input.setValue(mp.get('theta', 0))
            self.model_param_widget.psi_input.setValue(mp.get('psi', 0))
            self.model_param_widget.phi_input.setValue(mp.get('phi', 6.84184))
            self.model_param_widget.vx_input.setValue(mp.get('vx', 100.96949))
            self.model_param_widget.vy_input.setValue(mp.get('vy', -0.01323))
            self.model_param_widget.vz_input.setValue(mp.get('vz', -0.95246))
            self.model_param_widget.wx_input.setValue(mp.get('wx', 242.955))
            self.model_param_widget.wy_input.setValue(mp.get('wy', -42.435))
            self.model_param_widget.wz_input.setValue(mp.get('wz', 56.515))
            self.model_param_widget.dk_input.setValue(mp.get('dk', -2.9377))
            self.model_param_widget.ds_input.setValue(mp.get('ds', 0.94986))
            self.model_param_widget.dxx_input.setValue(mp.get('dxx', 0.94986))
            self.model_param_widget.dkf_input.setValue(mp.get('dkf', -2.50238))
            self.model_param_widget.dsf_input.setValue(mp.get('dsf', 0.38547))
            self.model_param_widget.dxf_input.setValue(mp.get('dxf', 0.30266))
            self.model_param_widget.t1_input.setValue(mp.get('t1', 25080.6))
            self.model_param_widget.t2_input.setValue(mp.get('t2', 6971.4))
            self.model_param_widget.kth_input.setValue(mp.get('kth', 4))
            self.model_param_widget.kps_input.setValue(mp.get('kps', 4))
            self.model_param_widget.kph_input.setValue(mp.get('kph', 0.08))
            self.model_param_widget.kwx_input.setValue(mp.get('kwx', 0.0016562))
            self.model_param_widget.kwz_input.setValue(mp.get('kwz', 0.312))
            self.model_param_widget.kwy_input.setValue(mp.get('kwy', 0.312))

            sp = laptop_datas
            self.sim_control_widget.L_input.setValue(sp.get("L", 3.195))
            self.sim_control_widget.S_input.setValue(sp.get("S", 0.0356))
            self.sim_control_widget.V_input.setValue(sp.get("V", 0))
            self.sim_control_widget.m_input.setValue(sp.get("m", 114.7))
            self.sim_control_widget.xc_input.setValue(sp.get("xc", -0.0188))
            self.sim_control_widget.yc_input.setValue(sp.get("yc", -0.0017))
            self.sim_control_widget.zc_input.setValue(sp.get("zc", 0.0008))
            self.sim_control_widget.jxx_input.setValue(sp.get("Jxx", 0.63140684))
            self.sim_control_widget.jyy_input.setValue(sp.get("Jyy", 57.06970864))
            self.sim_control_widget.jzz_input.setValue(sp.get("Jzz", 57.07143674))
            self.sim_control_widget.dt_input.setValue(sp.get("dt", 0.001))
            self.sim_control_widget.t0_input.setValue(sp.get("t0", 0.539))
            self.sim_control_widget.tend_input.setValue(sp.get("tend", 3.41))
            self.sim_control_widget.ycs_input.setValue(sp.get("ycs", -3.45))
            self.sim_control_widget.thetacs_input.setValue(sp.get("thetacs", -2.5086))
            self.sim_control_widget.yvcs_input.setValue(sp.get("yvcs", -0.01323))
            self.sim_control_widget.psics_input.setValue(sp.get("psics", 9.17098))
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

    def auto_load(self):
        filename = 'input.txt'
        check_file = os.path.exists("./input.txt")
        if check_file:
            try:
                x0, _, _ = read_data('input.txt', 'x0')
                y0, _, _ = read_data('input.txt', 'y0')
                z0, _, _ = read_data('input.txt', 'z0')
                theta, _, _ = read_data('input.txt', 'theta')
                psi, _, _ = read_data('input.txt', 'psi')
                phi, _, _ = read_data('input.txt', 'phi')
                vx, _, _ = read_data('input.txt', 'vx')
                vy, _, _ = read_data('input.txt', 'vy')
                vz, _, _ = read_data('input.txt', 'vz')
                wx, _, _ = read_data('input.txt', 'wx')
                wy, _, _ = read_data('input.txt', 'wy')
                wz, _, _ = read_data('input.txt', 'wz')
                dk, _, _ = read_data('input.txt', 'dk')
                ds, _, _ = read_data('input.txt', 'ds')
                dxx, _, _ = read_data('input.txt', 'dxx')
                dkf, _, _ = read_data('input.txt', 'dkf')
                dsf, _, _ = read_data('input.txt', 'dsf')
                dxf, _, _ = read_data('input.txt', 'dxf')
                t1, _, _ = read_data('input.txt', 't1')
                t2, _, _ = read_data('input.txt', 't2')
                kth, _, _ = read_data('input.txt', 'kth')
                kps, _, _ = read_data('input.txt', 'kps')
                kph, _, _ = read_data('input.txt', 'kph')
                kwx, _, _ = read_data('input.txt', 'kwx')
                kwz, _, _ = read_data('input.txt', 'kwz')
                kwy, _, _ = read_data('input.txt', 'kwy')
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
                dt, _, _ = read_data('input.txt', 'dt')
                t0, _, _ = read_data('input.txt', 't0')
                tend, _, _ = read_data('input.txt', 'tend')
                ycs, _, _ = read_data('input.txt', 'ycs')
                thetacs, _, _ = read_data('input.txt', 'thetacs')
                yvcs, _, _ = read_data('input.txt', 'yvcs')
                psics, _, _ = read_data('input.txt', 'psics')

                laptop_datas = {
                    'x0': x0,
                    'y0': y0,
                    'z0': z0,
                    'theta': theta,
                    'psi': psi,
                    'phi': phi,
                    'vx': vx,
                    'vy': vy,
                    'vz': vz,
                    'wx': wx,
                    'wy': wy,
                    'wz': wz,
                    'dk': dk,
                    'ds': ds,
                    'dxx': dxx,
                    'dkf': dkf,
                    'dsf': dsf,
                    'dxf': dxf,
                    't1': t1,
                    't2': t2,
                    'kth': kth,
                    'kps': kps,
                    'kph': kph,
                    'kwx': kwx,
                    'kwz': kwz,
                    'kwy': kwy,
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
                    'dt': dt,
                    't0': t0,
                    'tend': tend,
                    'ycs': ycs,
                    'thetacs': thetacs,
                    'yvcs': yvcs,
                    'psics': psics
                }

                # 验证配置文件

                mp = laptop_datas
                self.model_param_widget.x0_input.setValue(mp.get('x0', 27.82448))
                self.model_param_widget.y0_input.setValue(mp.get('y0', -3.45))
                self.model_param_widget.z0_input.setValue(mp.get('z0', 0.05623))
                self.model_param_widget.theta_input.setValue(mp.get('theta', 0))
                self.model_param_widget.psi_input.setValue(mp.get('psi', 0))
                self.model_param_widget.phi_input.setValue(mp.get('phi', 6.84184))
                self.model_param_widget.vx_input.setValue(mp.get('vx', 100.96949))
                self.model_param_widget.vy_input.setValue(mp.get('vy', -0.01323))
                self.model_param_widget.vz_input.setValue(mp.get('vz', -0.95246))
                self.model_param_widget.wx_input.setValue(mp.get('wx', 242.955))
                self.model_param_widget.wy_input.setValue(mp.get('wy', -42.435))
                self.model_param_widget.wz_input.setValue(mp.get('wz', 56.515))
                self.model_param_widget.dk_input.setValue(mp.get('dk', -2.9377))
                self.model_param_widget.ds_input.setValue(mp.get('ds', 0.94986))
                self.model_param_widget.dxx_input.setValue(mp.get('dxx', 0.94986))
                self.model_param_widget.dkf_input.setValue(mp.get('dkf', -2.50238))
                self.model_param_widget.dsf_input.setValue(mp.get('dsf', 0.38547))
                self.model_param_widget.dxf_input.setValue(mp.get('dxf', 0.30266))
                self.model_param_widget.t1_input.setValue(mp.get('t1', 25080.6))
                self.model_param_widget.t2_input.setValue(mp.get('t2', 6971.4))
                self.model_param_widget.kth_input.setValue(mp.get('kth', 4))
                self.model_param_widget.kps_input.setValue(mp.get('kps', 4))
                self.model_param_widget.kph_input.setValue(mp.get('kph', 0.08))
                self.model_param_widget.kwx_input.setValue(mp.get('kwx', 0.0016562))
                self.model_param_widget.kwz_input.setValue(mp.get('kwz', 0.312))
                self.model_param_widget.kwy_input.setValue(mp.get('kwy', 0.312))

                sp = laptop_datas
                self.sim_control_widget.L_input.setValue(sp.get("L", 3.195))
                self.sim_control_widget.S_input.setValue(sp.get("S", 0.0356))
                self.sim_control_widget.V_input.setValue(sp.get("V", 0))
                self.sim_control_widget.m_input.setValue(sp.get("m", 114.7))
                self.sim_control_widget.xc_input.setValue(sp.get("xc", -0.0188))
                self.sim_control_widget.yc_input.setValue(sp.get("yc", -0.0017))
                self.sim_control_widget.zc_input.setValue(sp.get("zc", 0.0008))
                self.sim_control_widget.jxx_input.setValue(sp.get("Jxx", 0.63140684))
                self.sim_control_widget.jyy_input.setValue(sp.get("Jyy", 57.06970864))
                self.sim_control_widget.jzz_input.setValue(sp.get("Jzz", 57.07143674))
                self.sim_control_widget.dt_input.setValue(sp.get("dt", 0.001))
                self.sim_control_widget.t0_input.setValue(sp.get("t0", 0.539))
                self.sim_control_widget.tend_input.setValue(sp.get("tend", 3.41))
                self.sim_control_widget.ycs_input.setValue(sp.get("ycs", -3.45))
                self.sim_control_widget.thetacs_input.setValue(sp.get("thetacs", -2.5086))
                self.sim_control_widget.yvcs_input.setValue(sp.get("yvcs", -0.01323))
                self.sim_control_widget.psics_input.setValue(sp.get("psics", 9.17098))
                # 更新状态栏
                logging.info("加载配置成功")

            except Exception as e:
                logging.exception("加载配置时出错")


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
