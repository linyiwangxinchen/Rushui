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

    def __init__(self, stab_instance, parent=None):
        super().__init__(parent)
        self.stab = stab_instance
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
            # 基本参数
            self.result_labels['model_length'].setText(f"{self.stab.Lm:.4f}")
            self.result_labels['cavitator_diameter'].setText(f"{self.stab.Dnmm:.4f}")
            self.result_labels['cavitator_angle'].setText(f"{self.stab.Beta:.4f}")
            self.result_labels['cavitator_slope'].setText(
                f"{self.stab.RibTan[0] if len(self.stab.RibTan) > 0 else 0:.4f}")
            self.result_labels['pitch_disturbance'].setText(f"{self.stab.Omega0:.4f}")
            self.result_labels['velocity'].setText(f"{self.stab.V0:.4f}")
            self.result_labels['depth'].setText(f"{self.stab.H0:.4f}")
            self.result_labels['cavity_pressure'].setText(f"{self.stab.Pc:.4f}")
            self.result_labels['cavity_length'].setText(f"{self.stab.Lc0 * self.stab.Rn * self.stab.Lm:.4f}")
            self.result_labels['cavity_diameter'].setText(f"{self.stab.Rc0 * self.stab.Lm:.4f}")

            # 更新力系数
            self.stab.DragCone()
            self.stab.MaxLoad()

            # 计算力系数
            if self.stab.FlagDive:
                if self.stab.GammaDive + self.stab.Delta + self.stab.Psi0 == -90.0:
                    cnx = self.stab.CnMax
                else:
                    cnx = 0.0
                cny = 0.0
            else:
                cnx = self.stab.CnMax * np.cos(self.stab.Psi0Rad + self.stab.DeltaRad) * self.stab.COS_D
                cny = -self.stab.CnMax * np.cos(self.stab.Psi0Rad + self.stab.DeltaRad) * self.stab.SIN_D

            cnm = cny * self.stab.Xc
            csx = 0.0
            csy = 0.0
            csm = 0.0

            self.force_result_labels['cpr'].setText(f"{self.stab.Cpr:.4f}")
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
                # 收集所有参数
                lengths, diams = self.get_section_parameters()
                params = {
                    "Lm": self.length_input.value(),
                    "Lf": self.forebody_length_input.value(),
                    "Lh": self.cavity_length_input.value(),
                    "DLh": self.cavity_left_diam_input.value(),
                    "DRh": self.cavity_right_diam_input.value(),
                    "Rhof": self.forebody_density_input.value(),
                    "Rhoa": self.aftbody_density_input.value(),
                    "Rhoh": self.cavity_density_input.value(),
                    "Dnmm": self.cavitator_diam_input.value(),
                    "Beta": self.cavitator_angle_input.value(),
                    "Delta": self.cavitator_swing_input.value(),
                    "Ncon": self.section_count_input.value(),
                    "ConeLen": lengths,
                    "BaseDiam": diams,
                    "Omega0": self.stab.Omega0,
                    "V0": self.stab.V0,
                    "H0": self.stab.H0
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

                # 更新Stab实例
                self.stab.Omega0 = params.get("Omega0", 1.0)
                self.stab.V0 = params.get("V0", 600.0)
                self.stab.H0 = params.get("H0", 30.0)

                QMessageBox.information(self, "加载成功", f"参数已从 {filename} 加载")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败: {str(e)}")
