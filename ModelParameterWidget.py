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
        geometry_group = QGroupBox("总体参数")

        # 初始位置&姿态条件
        geo_layout = QGridLayout()
        geo_layout.setContentsMargins(5, 5, 5, 5)
        geo_layout.setSpacing(5)
        # 从第6行开始添加（前5行已被初始位置/角度参数占用）
        start_row = 0
        self.add_param_input(geo_layout, "长度 L (m):", start_row + 0, 0.1, 10.0, 3.195, 0.01, "L_input",
                             range_check=True)
        self.add_param_input(geo_layout, "横截面积 S (m²):", start_row + 1, 0.001, 1.0, 0.0356, 0.0001, "S_input",
                             range_check=True)
        self.add_param_input_noVisible(geo_layout, "初始沾湿体积 V (m³):", start_row + 2, 0.0, 10.0, 0.0, 0.001, "V_input",
                             range_check=True)

        self.add_param_input(geo_layout, "质量 m (kg):", start_row + 3, 1.0, 1000.0, 114.7, 0.1, "m_input",
                             range_check=True)
        self.add_param_input(geo_layout, "重心 xc (m):", start_row + 4, -5.0, 5.0, -0.0188, 0.0001, "xc_input",
                             range_check=True)
        self.add_param_input(geo_layout, "重心 yc (m):", start_row + 5, -5.0, 5.0, -0.0017, 0.0001, "yc_input",
                             range_check=True)
        self.add_param_input(geo_layout, "重心 zc (m):", start_row + 6, -5.0, 5.0, 0.0008, 0.0001, "zc_input",
                             range_check=True)
        self.add_param_input(geo_layout, "转动惯量 Jxx (kg·m²):", start_row + 7, 0.01, 1000.0, 0.63140684, 0.01,
                             "Jxx_input", range_check=True)
        self.add_param_input(geo_layout, "转动惯量 Jyy (kg·m²):", start_row + 8, 0.01, 1000.0, 57.06970864, 0.01,
                             "Jyy_input", range_check=True)
        self.add_param_input(geo_layout, "转动惯量 Jzz (kg·m²):", start_row + 9, 0.01, 1000.0, 57.07143674, 0.01,
                             "Jzz_input", range_check=True)
        self.add_param_input(geo_layout, "推力 T (N):", start_row + 10, 0.0, 10000.0, 0.0, 0.1, "T_input",
                             range_check=True)
        geometry_group.setLayout(geo_layout)


        # 空化器参数
        mass_group = QGroupBox("构型参数")
        mass_layout = QGridLayout()
        mass_layout.setContentsMargins(5, 5, 5, 5)
        mass_layout.setSpacing(5)
        self.add_param_input(mass_layout, "空化器距重心 lk (m):", 0, -1000, 1000, 1.714, 0.1, "lk_input",
                             range_check=False)
        self.add_param_input(mass_layout, "空化器半径 rk (m):", 1, -1000, 1000, 0.021, 0.001, "rk_input",
                             range_check=False)
        self.add_param_input(mass_layout, "初始空化数 sgm:", 2, -1000, 1000, 0, 0.1, "sgm_input", range_check=False)
        self.add_param_input_noVisible(mass_layout, "空泡轴线偏离 dyc (m):", 3, -1000, 1000, 0, 0.001, "dyc_input",
                             range_check=False)
        self.add_param_input(mass_layout, "水平鳍位置 LW(m):", 4, -1000, 1000, 0.021, 0.001, "LW_input",
                             range_check=False)
        self.add_param_input(mass_layout, "垂直鳍位置 LH (m):", 5, -1000, 1000, 0, 0.1, "LH_input", range_check=False)

        mass_group.setLayout(mass_layout)

        # 物理几何参数
        dive_model_group = QGroupBox("水下航行参数")
        dive_model_layout = QGridLayout()
        dive_model_layout.setContentsMargins(5, 5, 5, 5)
        dive_model_layout.setSpacing(5)
        self.add_param_input(dive_model_layout, "巡航空化数 SGM:", 0, -1000, 1000, 0.018, 0.01, "SGM_input",
                             range_check=False)

        dive_model_group.setLayout(dive_model_layout)

        # 仿真控制参数
        # ============= 舵机与角度限制参数 =============
        control_limits_group = QGroupBox("控制限幅参数")
        control_limits_layout = QGridLayout()
        control_limits_layout.setContentsMargins(5, 5, 5, 5)
        control_limits_layout.setSpacing(5)

        # 舵角参数 (单位: 度)
        self.add_param_input(control_limits_layout, "舵角上限 dkmax (°):", 0, -90, 90, 0, 0.1, "dkmax_input")
        self.add_param_input(control_limits_layout, "舵角下限 dkmin (°):", 1, -90, 90, -4, 0.1, "dkmin_input")
        self.add_param_input(control_limits_layout, "舵角零位 dk0 (°):", 2, -90, 90, -2.61917, 0.01, "dk0_input")

        # 位移限制 (单位: 米)
        self.add_param_input(control_limits_layout, "横向位移限制 Δymax (m):", 3, 0, 100, 10, 0.1, "deltaymax_input")
        self.add_param_input(control_limits_layout, "垂向位移限制 Δvymax (m):", 4, 0, 100, 10, 0.1, "deltavymax_input")

        # 角度变化率 (单位: 度/秒)
        self.add_param_input(control_limits_layout, "最大深度变化率 ddmax (°/s²):", 5, 0, 50, 10, 0.1,
                             "ddmax_input")
        self.add_param_input(control_limits_layout, "最大速度变化率 dvmax (°/s²):", 6, 0, 50, 5, 0.1,
                             "dvmax_input")
        self.add_param_input(control_limits_layout, "最大俯仰角速率 dθmax (°/s):", 7, 0, 30, 5, 0.1,
                             "dthetamax_input")
        self.add_param_input(control_limits_layout, "最大偏航角速率 wzmax (°/s):", 8, 0, 100, 30, 0.5,
                             "wzmax_input")
        self.add_param_input(control_limits_layout, "最大滚转角速率 wxmax (°/s):", 9, 0, 500, 300, 1,
                             "wxmax_input")
        self.add_param_input(control_limits_layout, "最大滚转角加速度 dφmax (°/s²):", 10, 0, 200, 60, 0.5,
                             "dphimax_input")

        control_limits_group.setLayout(control_limits_layout)

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
        main_layout.addWidget(dive_model_group)
        main_layout.addWidget(control_limits_group)
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

    def add_param_input_noVisible(self, layout, label_text, row, min_val, max_val, default_val, step, attr_name, range_check=True):
        labeli = QLabel(label_text)
        labeli.setVisible(False)
        layout.addWidget(labeli, row, 0)
        spin_box = QDoubleSpinBox()
        spin_box.setDecimals(6)
        # if range_check:
        spin_box.setRange(min_val, max_val)
        spin_box.setSingleStep(step)
        spin_box.setValue(default_val)
        spin_box.setVisible(False)
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
            # 几何与质量参数
            'L': self.L_input.value(),  # 长度 (m)
            'S': self.S_input.value(),  # 横截面积 (m²)
            'V': self.V_input.value(),  # 体积 (m³)
            'm': self.m_input.value(),  # 质量 (kg)
            'xc': self.xc_input.value(),  # 重心 x 坐标 (m)
            'yc': self.yc_input.value(),  # 重心 y 坐标 (m)
            'zc': self.zc_input.value(),  # 重心 z 坐标 (m)
            'Jxx': self.Jxx_input.value(),  # 转动惯量 Jxx (kg·m²)
            'Jyy': self.Jyy_input.value(),  # 转动惯量 Jyy (kg·m²)
            'Jzz': self.Jzz_input.value(),  # 转动惯量 Jzz (kg·m²)
            'T': self.T_input.value(),  # 推力 (N)

            # 空泡仿真参数
            'lk': self.lk_input.value(),  # 空化器距重心距离 (m)
            'rk': self.rk_input.value(),  # 空化器半径 (m)
            'sgm': self.sgm_input.value(),  # 全局空化数
            'dyc': self.dyc_input.value(),  # 空泡轴线偏离 (m)

            # 水下物理几何参数
            'SGM': self.SGM_input.value(),  # 水下空化数
            'LW': self.LW_input.value(),  # 水平鳍位置 (m)
            'LH': self.LH_input.value(),  # 垂直鳍位置 (m)

            # 舵机与角度限制参数
            'dkmax': self.dkmax_input.value(),  # 舵角上限 (°)
            'dkmin': self.dkmin_input.value(),  # 舵角下限 (°)
            'dk0': self.dk0_input.value(),  # 舵角零位 (°)
            'deltaymax': self.deltaymax_input.value(),  # 横向位移限制 (m)
            'deltavymax': self.deltavymax_input.value(),  # 垂向位移限制 (m)
            'ddmax': self.ddmax_input.value(),  # 最大深度变化率 (°/s²)
            'dvmax': self.dvmax_input.value(),  # 最大速度变化率 (°/s²)
            'dthetamax': self.dthetamax_input.value(),  # 最大俯仰角速率 (°/s)
            'wzmax': self.wzmax_input.value(),  # 最大偏航角速率 (°/s)
            'wxmax': self.wxmax_input.value(),  # 最大滚转角速率 (°/s)
            'dphimax': self.dphimax_input.value(),  # 最大滚转角加速度 (°/s²)
        }

        self.data_output_signal_m.emit(data)

    def to_model1(self, Checki):
        # 向model发送数据
        data = {
            # 几何与质量参数
            'L': self.L_input.value(),  # 长度 (m)
            'S': self.S_input.value(),  # 横截面积 (m²)
            'V': self.V_input.value(),  # 体积 (m³)
            'm': self.m_input.value(),  # 质量 (kg)
            'xc': self.xc_input.value(),  # 重心 x 坐标 (m)
            'yc': self.yc_input.value(),  # 重心 y 坐标 (m)
            'zc': self.zc_input.value(),  # 重心 z 坐标 (m)
            'Jxx': self.Jxx_input.value(),  # 转动惯量 Jxx (kg·m²)
            'Jyy': self.Jyy_input.value(),  # 转动惯量 Jyy (kg·m²)
            'Jzz': self.Jzz_input.value(),  # 转动惯量 Jzz (kg·m²)
            'T': self.T_input.value(),  # 推力 (N)

            # 空泡仿真参数
            'lk': self.lk_input.value(),  # 空化器距重心距离 (m)
            'rk': self.rk_input.value(),  # 空化器半径 (m)
            'sgm': self.sgm_input.value(),  # 全局空化数
            'dyc': self.dyc_input.value(),  # 空泡轴线偏离 (m)

            # 水下物理几何参数
            'SGM': self.SGM_input.value(),  # 水下空化数
            'LW': self.LW_input.value(),  # 水平鳍位置 (m)
            'LH': self.LH_input.value(),  # 垂直鳍位置 (m)

            # 舵机与角度限制参数
            'dkmax': self.dkmax_input.value(),  # 舵角上限 (°)
            'dkmin': self.dkmin_input.value(),  # 舵角下限 (°)
            'dk0': self.dk0_input.value(),  # 舵角零位 (°)
            'deltaymax': self.deltaymax_input.value(),  # 横向位移限制 (m)
            'deltavymax': self.deltavymax_input.value(),  # 垂向位移限制 (m)
            'ddmax': self.ddmax_input.value(),  # 最大深度变化率 (°/s²)
            'dvmax': self.dvmax_input.value(),  # 最大速度变化率 (°/s²)
            'dthetamax': self.dthetamax_input.value(),  # 最大俯仰角速率 (°/s)
            'wzmax': self.wzmax_input.value(),  # 最大偏航角速率 (°/s)
            'wxmax': self.wxmax_input.value(),  # 最大滚转角速率 (°/s)
            'dphimax': self.dphimax_input.value(),  # 最大滚转角加速度 (°/s²)
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
                params = {
                    # 几何与质量参数 (新增分组)
                    'L': self.L_input.value(),  # 长度 (m)
                    'S': self.S_input.value(),  # 横截面积 (m²)
                    'V': self.V_input.value(),  # 体积 (m³)
                    'm': self.m_input.value(),  # 质量 (kg)
                    'xc': self.xc_input.value(),  # 重心 x 坐标 (m)
                    'yc': self.yc_input.value(),  # 重心 y 坐标 (m)
                    'zc': self.zc_input.value(),  # 重心 z 坐标 (m)
                    'Jxx': self.Jxx_input.value(),  # 转动惯量 Jxx (kg·m²)
                    'Jyy': self.Jyy_input.value(),  # 转动惯量 Jyy (kg·m²)
                    'Jzz': self.Jzz_input.value(),  # 转动惯量 Jzz (kg·m²)
                    'T': self.T_input.value(),  # 推力 (N)

                    # 空泡仿真参数
                    'lk': self.lk_input.value(),  # 空化器距重心距离 (m)
                    'rk': self.rk_input.value(),  # 空化器半径 (m)
                    'sgm': self.sgm_input.value(),  # 全局空化数
                    'dyc': self.dyc_input.value(),  # 空泡轴线偏离 (m)

                    # 水下物理几何参数
                    'SGM': self.SGM_input.value(),  # 水下空化数
                    'LW': self.LW_input.value(),  # 水平鳍位置 (m)
                    'LH': self.LH_input.value(),  # 垂直鳍位置 (m)

                    # 舵机与角度限制参数
                    'dkmax': self.dkmax_input.value(),  # 舵角上限 (°)
                    'dkmin': self.dkmin_input.value(),  # 舵角下限 (°)
                    'dk0': self.dk0_input.value(),  # 舵角零位 (°)
                    'deltaymax': self.deltaymax_input.value(),  # 横向位移限制 (m)
                    'deltavymax': self.deltavymax_input.value(),  # 垂向位移限制 (m)
                    'ddmax': self.ddmax_input.value(),  # 最大深度变化率 (°/s²)
                    'dvmax': self.dvmax_input.value(),  # 最大速度变化率 (°/s²)
                    'dthetamax': self.dthetamax_input.value(),  # 最大俯仰角速率 (°/s)
                    'wzmax': self.wzmax_input.value(),  # 最大偏航角速率 (°/s)
                    'wxmax': self.wxmax_input.value(),  # 最大滚转角速率 (°/s)
                    'dphimax': self.dphimax_input.value(),  # 最大滚转角加速度 (°/s²)
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
                # 更新UI - 几何与质量参数
                self.L_input.setValue(params.get('L', 3.195))  # 长度 (m)
                self.S_input.setValue(params.get('S', 0.0356))  # 横截面积 (m²)
                self.V_input.setValue(params.get('V', 0.0))  # 体积 (m³)
                self.m_input.setValue(params.get('m', 114.7))  # 质量 (kg)
                self.xc_input.setValue(params.get('xc', -0.0188))  # 重心 xc (m)
                self.yc_input.setValue(params.get('yc', -0.0017))  # 重心 yc (m)
                self.zc_input.setValue(params.get('zc', 0.0008))  # 重心 zc (m)
                self.Jxx_input.setValue(params.get('Jxx', 0.63140684))  # 转动惯量 Jxx (kg·m²)
                self.Jyy_input.setValue(params.get('Jyy', 57.06970864))  # 转动惯量 Jyy (kg·m²)
                self.Jzz_input.setValue(params.get('Jzz', 57.07143674))  # 转动惯量 Jzz (kg·m²)
                self.T_input.setValue(params.get('T', 0.0))  # 推力 (N)

                # 更新UI - 空泡仿真参数
                self.lk_input.setValue(params.get('lk', 1.714))  # 空化器距重心 lk (m)
                self.rk_input.setValue(params.get('rk', 0.021))  # 空化器半径 rk (m)
                self.sgm_input.setValue(params.get('sgm', 0.0))  # 全局空化数 sgm
                self.dyc_input.setValue(params.get('dyc', 0.0))  # 空泡轴线偏离 dyc (m)

                # 更新UI - 水下物理几何参数
                self.SGM_input.setValue(params.get('SGM', 0.018))  # 水下空化数 SGM
                self.LW_input.setValue(params.get('LW', 0.021))  # 水平鳍位置 LW (m)
                self.LH_input.setValue(params.get('LH', 0.0))  # 垂直鳍位置 LH (m)

                # 更新UI - 舵机与角度限制参数
                self.dkmax_input.setValue(params.get('dkmax', 0.0))  # 舵角上限 dkmax (°)
                self.dkmin_input.setValue(params.get('dkmin', -4.0))  # 舵角下限 dkmin (°)
                self.dk0_input.setValue(params.get('dk0', -2.61917))  # 舵角零位 dk0 (°)
                self.deltaymax_input.setValue(params.get('deltaymax', 10.0))  # 横向位移限制 Δymax (m)
                self.deltavymax_input.setValue(params.get('deltavymax', 10.0))  # 垂向位移限制 Δvymax (m)
                self.ddmax_input.setValue(params.get('ddmax', 10.0))  # 最大深度变化率 ddmax (°/s²)
                self.dvmax_input.setValue(params.get('dvmax', 5.0))  # 最大速度变化率 dvmax (°/s²)
                self.dthetamax_input.setValue(params.get('dthetamax', 5.0))  # 最大俯仰角速率 dθmax (°/s)
                self.wzmax_input.setValue(params.get('wzmax', 30.0))  # 最大偏航角速率 wzmax (°/s)
                self.wxmax_input.setValue(params.get('wxmax', 300.0))  # 最大滚转角速率 wxmax (°/s)
                self.dphimax_input.setValue(params.get('dphimax', 60.0))  # 最大滚转角加速度 dφmax (°/s²)

                QMessageBox.information(self, "加载成功", f"参数已从 {filename} 加载")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载失败: {str(e)}")
