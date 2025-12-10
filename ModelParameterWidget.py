import sys
import numpy as np
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QGridLayout, QLabel, QDoubleSpinBox,
    QPushButton, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView,
    QSpinBox, QMessageBox, QFileDialog, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal


class ModelParameterWidget(QWidget):
    """弹体参数设置界面"""
    data_output_signal_m = pyqtSignal(dict)
    data_input_signal_m = pyqtSignal(bool)
    data_output_signal_m1 = pyqtSignal(dict)
    data_input_signal_m1 = pyqtSignal(bool)

    def __init__(self, rushui_instance, parent=None):
        super().__init__(parent)
        self.rushui = rushui_instance
        self.init_ui()
        self.load_default_parameters()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # 创建分组框
        geometry_group = QGroupBox("初始位置&姿态条件")
        mass_group = QGroupBox("初始速度&角速度条件")
        cavitator_group = QGroupBox("空化器参数")
        push_group = QGroupBox("推力参数")
        pid_group = QGroupBox("控制参数")
        result_group = QGroupBox("计算结果")

        # 初始位置&姿态条件
        geo_layout = QGridLayout()
        geo_layout.setContentsMargins(5, 5, 5, 5)
        geo_layout.setSpacing(5)

        self.add_param_input(geo_layout, "初始x0:", 0, -1000, 1000.0, 27.82448, 0.1, "x0_input", range_check=False)
        self.add_param_input(geo_layout, "初始y0:", 1, -1000, 1000, -3.45, 0.1, "y0_input", range_check=False)
        self.add_param_input(geo_layout, "初始z0:", 2, -1000, 1000, 0.05623, 0.1, "z0_input", range_check=False)
        self.add_param_input(geo_layout, "初始theta(deg):", 3, -1000, 1000, 0, 0.1, "theta_input", range_check=False)
        self.add_param_input(geo_layout, "初始psi(deg):", 4, -1000, 1000, 0, 0.1, "psi_input", range_check=False)
        self.add_param_input(geo_layout, "初始phi(deg):", 5, -1000, 1000, 6.84184, 0.1, "phi_input", range_check=False)

        geometry_group.setLayout(geo_layout)

        # 初始速度&角速度条件
        mass_layout = QGridLayout()
        mass_layout.setContentsMargins(5, 5, 5, 5)
        mass_layout.setSpacing(5)

        self.add_param_input(mass_layout, "初始vx:", 0, -1000, 1000, 100.96949, 0.1, "vx_input", range_check=False)
        self.add_param_input(mass_layout, "初始vy:", 1, -1000, 1000, -0.01323, 1.0, "vy_input", range_check=False)
        self.add_param_input(mass_layout, "初始vz:", 2, -1000, 1000, -0.95246, 1.0, "vz_input", range_check=False)
        self.add_param_input(mass_layout, "初始wx(deg):", 3, -1000, 1000, 242.955, 1.0, "wx_input", range_check=False)
        self.add_param_input(mass_layout, "初始wy(deg):", 4, -1000, 1000, -42.435, 1.0, "wy_input", range_check=False)
        self.add_param_input(mass_layout, "初始wz(deg):", 5, -1000, 1000, 56.515, 1.0, "wz_input", range_check=False)

        mass_group.setLayout(mass_layout)

        # 空化器参数布局
        cavitator_layout = QGridLayout()
        cavitator_layout.setContentsMargins(5, 5, 5, 5)
        cavitator_layout.setSpacing(5)

        # self.add_param_input(cavitator_layout, "初始vx:", 0, -1000, 1000, 0, 1.0, "vx_input", range_check=False)
        # self.add_param_input(cavitator_layout, "初始vy:", 1, -1000, 1000, 0, 1.0, "vy_input", range_check=False)
        # self.add_param_input(cavitator_layout, "初始vz:", 2, -1000, 1000, 0, 1.0, "vz_input", range_check=False)
        # self.add_param_input(cavitator_layout, "初始wx:", 3, -1000, 1000, 0, 1.0, "wx_input", range_check=False)
        # self.add_param_input(cavitator_layout, "初始wy:", 4, -1000, 1000, 0, 1.0, "wy_input", range_check=False)
        # self.add_param_input(cavitator_layout, "初始wz:", 5, -1000, 1000, 0, 1.0, "wz_input", range_check=False)
        self.add_param_input(cavitator_layout, "空化器DK (deg):", 0, -1000, 1000, -2.9377, 1.0, "dk_input", range_check=False)
        self.add_param_input(cavitator_layout, "空化器DS (deg):", 1, -1000, 1000, 0.94986, 1.0, "ds_input", range_check=False)
        self.add_param_input(cavitator_layout, "空化器DX (deg):", 2, -1000, 1000, 0.94986, 1.0, "dxx_input", range_check=False)
        self.add_param_input(cavitator_layout, "空化器dkf(deg):", 3, -1000, 1000, -2.50238, 1.0, "dkf_input", range_check=False)
        self.add_param_input(cavitator_layout, "空化器dsf(deg):", 4, -1000, 1000, 0.38547, 1.0, "dsf_input", range_check=False)
        self.add_param_input(cavitator_layout, "空化器dxf(deg):", 5, -1000, 1000, 0.30266, 1.0, "dxf_input", range_check=False)

        cavitator_group.setLayout(cavitator_layout)


        # 推力设置部分
        push_layout = QGridLayout()
        push_layout.setContentsMargins(5, 5, 5, 5)
        push_layout.setSpacing(5)

        self.add_param_input(push_layout, "初始T1:", 0, -100000, 100000, 25080.6, 1.0, "t1_input", range_check=False)
        self.add_param_input(push_layout, "初始T2:", 1, -100000, 100000, 6971.4, 1.0, "t2_input", range_check=False)
        push_group.setLayout(push_layout)


        # 控制参数部分
        pid_layout = QGridLayout()
        pid_layout.setContentsMargins(5, 5, 5, 5)
        pid_layout.setSpacing(5)

        self.add_param_input(pid_layout, "kth:", 0, -1000, 1000, 4, 0.001, "kth_input", range_check=False)
        self.add_param_input(pid_layout, "kps:", 1, -1000, 1000, 4, 0.001, "kps_input", range_check=False)
        self.add_param_input(pid_layout, "kph:", 2, -1000, 1000, 0.08, 0.001, "kph_input", range_check=False)
        self.add_param_input(pid_layout, "kwx:", 3, -1000, 1000, 0.0016562, 0.001, "kwx_input", range_check=False)
        self.add_param_input(pid_layout, "kwz:", 4, -1000, 1000, 0.312, 0.001, "kwz_input", range_check=False)
        self.add_param_input(pid_layout, "kwy:", 5, -1000, 1000, 0.312, 0.001, "kwy_input", range_check=False)

        pid_group.setLayout(pid_layout)

        # 按钮区域
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("保存参数配置")
        self.save_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.save_button.clicked.connect(self.save_parameters)
        self.load_button = QPushButton("加载参数配置")
        self.load_button.clicked.connect(self.load_parameters)
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.load_button)


        # 组合所有布局
        main_layout.addWidget(geometry_group)
        main_layout.addWidget(mass_group)
        main_layout.addWidget(cavitator_group)
        main_layout.addWidget(push_group)
        main_layout.addWidget(pid_group)
        main_layout.addLayout(button_layout)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def add_param_input(self, layout, label_text, row, min_val, max_val, default_val, step, attr_name, range_check=True):
        """添加参数输入控件"""
        layout.addWidget(QLabel(label_text), row, 0)
        spin_box = QDoubleSpinBox()
        spin_box.setDecimals(6)
        # if range_check:
        spin_box.setRange(min_val, max_val)
        spin_box.setSingleStep(step)
        spin_box.setValue(default_val)
        layout.addWidget(spin_box, row, 1)
        setattr(self, attr_name, spin_box)

    def update_section_table(self):
        """更新分段参数表格"""
        count = self.section_count_input.value()
        self.section_table.setRowCount(count)

        # 设置默认值
        default_lengths = [24.0, 35.0, 90.0]
        default_diams = [6.0, 9.5, 15.0]

        for i in range(count):
            length_item = QTableWidgetItem(str(default_lengths[i] if i < len(default_lengths) else "10.0"))
            diam_item = QTableWidgetItem(str(default_diams[i] if i < len(default_diams) else "5.0"))
            note_item = QTableWidgetItem(f"第 {i + 1} 节")

            self.section_table.setItem(i, 0, length_item)
            self.section_table.setItem(i, 1, diam_item)
            self.section_table.setItem(i, 2, note_item)

    def get_section_parameters(self):
        """从表格获取分段参数"""
        count = self.section_table.rowCount()
        lengths = []
        diams = []

        for i in range(count):
            try:
                length = float(self.section_table.item(i, 0).text())
                diam = float(self.section_table.item(i, 1).text())
                lengths.append(length)
                diams.append(diam)
            except (ValueError, AttributeError):
                lengths.append(10.0)
                diams.append(5.0)

        return lengths, diams

    def load_default_parameters(self):
        """加载默认参数"""
        # self.length_input.setValue(0.5)
        # self.forebody_length_input.setValue(59.0)
        # self.cavity_length_input.setValue(20.0)
        # self.cavity_left_diam_input.setValue(6.0)
        # self.cavity_right_diam_input.setValue(6.0)
        # self.forebody_density_input.setValue(17.6)
        # self.aftbody_density_input.setValue(4.5)
        # self.cavity_density_input.setValue(0.0)
        # self.cavitator_diam_input.setValue(1.5)
        # self.cavitator_angle_input.setValue(180.0)
        # self.cavitator_swing_input.setValue(0.0)
        # self.section_count_input.setValue(3)
        # self.update_section_table()
        pass

    def ask_model(self):
        # 告诉model我要数据
        self.data_input_signal_m.emit(True)

    def to_model(self, Checki):
        # 向model发送数据
        data = {
            # 初始位置&姿态条件
            'x0': self.x0_input.value(),
            'y0': self.y0_input.value(),
            'z0': self.z0_input.value(),
            'theta': self.theta_input.value(),
            'psi': self.psi_input.value(),
            'phi': self.phi_input.value(),

            # 初始速度&角速度条件
            'vx': self.vx_input.value(),
            'vy': self.vy_input.value(),
            'vz': self.vz_input.value(),
            'wx': self.wx_input.value(),
            'wy': self.wy_input.value(),
            'wz': self.wz_input.value(),

            # 空化器参数
            'dk': self.dk_input.value(),
            'ds': self.ds_input.value(),
            'dxx': self.dxx_input.value(),  # 注意：对应"空化器DX"参数
            'dkf': self.dkf_input.value(),
            'dsf': self.dsf_input.value(),
            'dxf': self.dxf_input.value(),

            # 推力设置
            't1': self.t1_input.value(),
            't2': self.t2_input.value(),

            # 控制参数
            'kth': self.kth_input.value(),
            'kps': self.kps_input.value(),
            'kph': self.kph_input.value(),
            'kwx': self.kwx_input.value(),
            'kwz': self.kwz_input.value(),
            'kwy': self.kwy_input.value()
        }
        
        # 将参数更新到rushui实例
        self.rushui.x0 = data['x0']
        self.rushui.y0 = data['y0']
        self.rushui.z0 = data['z0']
        self.rushui.theta = data['theta'] / self.rushui.RTD  # 转换为弧度
        self.rushui.psi = data['psi'] / self.rushui.RTD
        self.rushui.phi = data['phi'] / self.rushui.RTD
        self.rushui.vx = data['vx']
        self.rushui.vy = data['vy']
        self.rushui.vz = data['vz']
        self.rushui.wx = data['wx'] / self.rushui.RTD  # 转换为弧度
        self.rushui.wy = data['wy'] / self.rushui.RTD
        self.rushui.wz = data['wz'] / self.rushui.RTD
        self.rushui.DK = data['dk'] / self.rushui.RTD
        self.rushui.DS = data['ds'] / self.rushui.RTD
        self.rushui.DX = data['dxx'] / self.rushui.RTD
        self.rushui.dkf = data['dkf'] / self.rushui.RTD
        self.rushui.dsf = data['dsf'] / self.rushui.RTD
        self.rushui.dxf = data['dxf'] / self.rushui.RTD
        self.rushui.T1 = data['t1']
        self.rushui.T2 = data['t2']
        self.rushui.kth = data['kth']
        self.rushui.kps = data['kps']
        self.rushui.kph = data['kph']
        self.rushui.kwx = data['kwx']
        self.rushui.kwz = data['kwz']
        self.rushui.kwy = data['kwy']
        
        self.data_output_signal_m.emit(data)

    def to_model1(self, Checki):
        # 向model发送数据
        data = {
            # 初始位置&姿态条件
            'x0': self.x0_input.value(),
            'y0': self.y0_input.value(),
            'z0': self.z0_input.value(),
            'theta': self.theta_input.value(),
            'psi': self.psi_input.value(),
            'phi': self.phi_input.value(),

            # 初始速度&角速度条件
            'vx': self.vx_input.value(),
            'vy': self.vy_input.value(),
            'vz': self.vz_input.value(),
            'wx': self.wx_input.value(),
            'wy': self.wy_input.value(),
            'wz': self.wz_input.value(),

            # 空化器参数
            'dk': self.dk_input.value(),
            'ds': self.ds_input.value(),
            'dxx': self.dxx_input.value(),  # 注意：对应"空化器DX"参数
            'dkf': self.dkf_input.value(),
            'dsf': self.dsf_input.value(),
            'dxf': self.dxf_input.value(),

            # 推力设置
            't1': self.t1_input.value(),
            't2': self.t2_input.value(),

            # 控制参数
            'kth': self.kth_input.value(),
            'kps': self.kps_input.value(),
            'kph': self.kph_input.value(),
            'kwx': self.kwx_input.value(),
            'kwz': self.kwz_input.value(),
            'kwy': self.kwy_input.value()
        }
        
        # 将参数更新到rushui实例
        self.rushui.x0 = data['x0']
        self.rushui.y0 = data['y0']
        self.rushui.z0 = data['z0']
        self.rushui.theta = data['theta'] / self.rushui.RTD  # 转换为弧度
        self.rushui.psi = data['psi'] / self.rushui.RTD
        self.rushui.phi = data['phi'] / self.rushui.RTD
        self.rushui.vx = data['vx']
        self.rushui.vy = data['vy']
        self.rushui.vz = data['vz']
        self.rushui.wx = data['wx'] / self.rushui.RTD  # 转换为弧度
        self.rushui.wy = data['wy'] / self.rushui.RTD
        self.rushui.wz = data['wz'] / self.rushui.RTD
        self.rushui.DK = data['dk'] / self.rushui.RTD
        self.rushui.DS = data['ds'] / self.rushui.RTD
        self.rushui.DX = data['dxx'] / self.rushui.RTD
        self.rushui.dkf = data['dkf'] / self.rushui.RTD
        self.rushui.dsf = data['dsf'] / self.rushui.RTD
        self.rushui.dxf = data['dxf'] / self.rushui.RTD
        self.rushui.T1 = data['t1']
        self.rushui.T2 = data['t2']
        self.rushui.kth = data['kth']
        self.rushui.kps = data['kps']
        self.rushui.kph = data['kph']
        self.rushui.kwx = data['kwx']
        self.rushui.kwz = data['kwz']
        self.rushui.kwy = data['kwy']
        
        self.data_output_signal_m1.emit(data)

    def get_model(self, data):
        self.model_data = data

    def get_model1(self, data):
        self.model_data = data

    def show_success_dialog(self):
        """显示自定义成功对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("计算完成")
        dialog.setWindowModality(Qt.WindowModal)

        # 设置对话框样式
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                border: 1px solid #cccccc;
                border-radius: 8px;
            }
            QLabel {
                font-size: 12px;
                padding: 10px;
            }
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)

        # 消息内容
        message_label = QLabel("✅ 模型参数计算成功！")
        message_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2e7d32;")
        layout.addWidget(message_label, alignment=Qt.AlignCenter)

        detail_label = QLabel("模型几何与质量分布已成功计算，可以继续进行动力学仿真。")
        detail_label.setWordWrap(True)
        layout.addWidget(detail_label)

        # 按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.setMinimumWidth(80)
        ok_button.clicked.connect(dialog.accept)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        dialog.setLayout(layout)
        dialog.exec_()

    def show_error_dialog(self, message):
        """显示自定义错误对话框"""
        dialog = QDialog(self)
        dialog.setWindowTitle("错误")
        dialog.setWindowModality(Qt.WindowModal)

        # 设置对话框样式
        dialog.setStyleSheet("""
            QDialog {
                background-color: #f5f5f5;
                border: 1px solid #cccccc;
                border-radius: 8px;
            }
            QLabel {
                font-size: 12px;
                padding: 10px;
            }
            QPushButton {
                background-color: #f44336;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 6px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e53935;
            }
            QPushButton:pressed {
                background-color: #d32f2f;
            }
        """)

        layout = QVBoxLayout()
        layout.setContentsMargins(20, 15, 20, 15)
        layout.setSpacing(15)

        # 消息内容
        message_label = QLabel("❌ 错误")
        message_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #c62828;")
        layout.addWidget(message_label, alignment=Qt.AlignCenter)

        detail_label = QLabel(message)
        detail_label.setWordWrap(True)
        layout.addWidget(detail_label)

        # 按钮
        button_layout = QHBoxLayout()
        ok_button = QPushButton("确定")
        ok_button.setMinimumWidth(80)
        ok_button.clicked.connect(dialog.accept)
        button_layout.addStretch()
        button_layout.addWidget(ok_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

        dialog.setLayout(layout)
        dialog.exec_()

    def update_result_display(self):
        """更新计算结果显示"""
        try:
            # 基本参数 - 使用Rushui模型参数
            self.result_labels['model_length'].setText(f"{self.rushui.L:.4f}")
            self.result_labels['cavitator_diameter'].setText(f"{self.rushui.RK * 2:.4f}")  # 直径是半径的2倍
            self.result_labels['cavitator_angle'].setText(f"{self.rushui.Beta:.4f}")
            self.result_labels['cavitator_slope'].setText(
                f"{self.rushui.Beta:.4f}")  # Rushui模型使用Beta作为锥角
            self.result_labels['pitch_disturbance'].setText(f"{self.rushui.Omega0:.4f}")
            self.result_labels['velocity'].setText(f"{self.rushui.vx:.4f}")
            self.result_labels['depth'].setText(f"{self.rushui.y0:.4f}")
            self.result_labels['cavity_pressure'].setText(f"{self.rushui.Pc:.4f}")
            self.result_labels['cavity_length'].setText(f"{self.rushui.LK:.4f}")
            self.result_labels['cavity_diameter'].setText(f"{self.rushui.RK * 2:.4f}")

            # 更新力系数 - Rushui模型不需要这些计算
            # self.rushui.DragCone()
            # self.rushui.MaxLoad()

            # Rushui模型的力系数
            cnx = 0.0  # 从Rushui模型获取
            cny = 0.0  # 从Rushui模型获取
            cnm = 0.0  # 从Rushui模型获取
            csx = 0.0  # 从Rushui模型获取
            csy = 0.0  # 从Rushui模型获取
            csm = 0.0  # 从Rushui模型获取

            self.force_result_labels['cpr'].setText(f"{self.rushui.Cpr:.4f}")
            self.force_result_labels['cnx'].setText(f"{cnx:.4f}")
            self.force_result_labels['cny'].setText(f"{cny:.4f}")
            self.force_result_labels['cnm'].setText(f"{cnm:.4f}")
            self.force_result_labels['csx'].setText(f"{csx:.4f}")
            self.force_result_labels['csy'].setText(f"{csy:.4f}")
            self.force_result_labels['csm'].setText(f"{csm:.4f}")

        except Exception as e:
            QMessageBox.warning(self, "警告", f"更新结果显示失败: {str(e)}")

    def save_parameters(self):
        """保存参数配置到文件"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存参数配置", "", "JSON Files (*.json);;All Files (*)"
            )

            if filename:
                # 收集所有参数 - 使用Rushui模型参数
                params = {
                    "L": self.rushui.L,
                    "S": self.rushui.S,
                    "V": self.rushui.V,
                    "m": self.rushui.m,
                    "xc": self.rushui.xc,
                    "yc": self.rushui.yc,
                    "zc": self.rushui.zc,
                    "Jxx": self.rushui.Jxx,
                    "Jyy": self.rushui.Jyy,
                    "Jzz": self.rushui.Jzz,
                    "RK": self.rushui.RK,
                    "Beta": self.rushui.Beta,
                    "LK": self.rushui.LK,
                    "Pc": self.rushui.Pc,
                    "Omega0": self.rushui.Omega0,
                    "x0": self.rushui.x0,
                    "y0": self.rushui.y0,
                    "z0": self.rushui.z0,
                    "theta": self.rushui.theta * self.rushui.RTD,  # 转换为度
                    "psi": self.rushui.psi * self.rushui.RTD,
                    "phi": self.rushui.phi * self.rushui.RTD,
                    "vx": self.rushui.vx,
                    "vy": self.rushui.vy,
                    "vz": self.rushui.vz,
                    "wx": self.rushui.wx * self.rushui.RTD,  # 转换为度
                    "wy": self.rushui.wy * self.rushui.RTD,
                    "wz": self.rushui.wz * self.rushui.RTD,
                    "DK": self.rushui.DK * self.rushui.RTD,
                    "DS": self.rushui.DS * self.rushui.RTD,
                    "DX": self.rushui.DX * self.rushui.RTD,
                    "dkf": self.rushui.dkf * self.rushui.RTD,
                    "dsf": self.rushui.dsf * self.rushui.RTD,
                    "dxf": self.rushui.dxf * self.rushui.RTD,
                    "T1": self.rushui.T1,
                    "T2": self.rushui.T2,
                    "kth": self.rushui.kth,
                    "kps": self.rushui.kps,
                    "kph": self.rushui.kph,
                    "kwx": self.rushui.kwx,
                    "kwz": self.rushui.kwz,
                    "kwy": self.rushui.kwy
                }

                # 保存为JSON
                with open(filename, 'w') as f:
                    json.dump(params, f, indent=4)

                QMessageBox.information(self, "保存成功", f"参数已保存至 {filename}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存失败: {str(e)}")

    def load_parameters(self):
        """从文件加载参数配置"""
        try:
            filename, _ = QFileDialog.getOpenFileName(
                self, "加载参数配置", "", "JSON Files (*.json);;All Files (*)"
            )

            if filename:
                with open(filename, 'r') as f:
                    params = json.load(f)

                # 更新UI
                self.length_input.setValue(params.get("Lm", 0.5))
                self.forebody_length_input.setValue(params.get("Lf", 59.0))
                self.cavity_length_input.setValue(params.get("Lh", 20.0))
                self.cavity_left_diam_input.setValue(params.get("DLh", 6.0))
                self.cavity_right_diam_input.setValue(params.get("DRh", 6.0))
                self.forebody_density_input.setValue(params.get("Rhof", 17.6))
                self.aftbody_density_input.setValue(params.get("Rhoa", 4.5))
                self.cavity_density_input.setValue(params.get("Rhoh", 0.0))
                self.cavitator_diam_input.setValue(params.get("Dnmm", 1.5))
                self.cavitator_angle_input.setValue(params.get("Beta", 180.0))
                self.cavitator_swing_input.setValue(params.get("Delta", 0.0))
                self.section_count_input.setValue(params.get("Ncon", 3))

                # 更新分段表格
                lengths = params.get("ConeLen", [24.0, 35.0, 90.0])
                diams = params.get("BaseDiam", [6.0, 9.5, 15.0])
                self.update_section_table()

                for i in range(min(self.section_count_input.value(), len(lengths), len(diams))):
                    self.section_table.item(i, 0).setText(str(lengths[i]))
                    self.section_table.item(i, 1).setText(str(diams[i]))

                # 更新Rushui实例
                self.rushui.Omega0 = params.get("Omega0", 1.0)
                self.rushui.V0 = params.get("V0", 600.0)
                self.rushui.H0 = params.get("H0", 30.0)

                QMessageBox.information(self, "加载成功", f"参数已从 {filename} 加载")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败: {str(e)}")
