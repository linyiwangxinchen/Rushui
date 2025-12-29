import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QHBoxLayout, QLabel, QGridLayout


class CompactParameterDisplayWidget(QWidget):
    """参数显示面板"""
    def __init__(self, stab_instance, parent=None):
        super().__init__(parent)
        self.rushui = stab_instance
        self.init_ui()
        self.current_data = {}

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # 创建紧凑的分组显示
        self.create_motion_group(main_layout)
        self.create_force_group(main_layout)
        self.create_contact_group(main_layout)

        self.setLayout(main_layout)
        self.setStyleSheet("""
            QGroupBox {
                border: 1px solid #cccccc;
                border-radius: 3px;
                margin-top: 1ex;
                font-weight: bold;
                padding: 2px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 5px;
                padding: 0 2px;
                font-size: 10pt;
            }
            QLabel {
                font-family: Consolas, monospace;
                font-size: 9pt;
                padding: 1px;
            }
            QLabel.highlight {
                color: #d32f2f;
                font-weight: bold;
            }
        """)

    def create_motion_group(self, layout):
        motion_group = QGroupBox("当前运动状态")
        group_layout = QVBoxLayout()
        group_layout.setContentsMargins(5, 5, 5, 5)
        group_layout.setSpacing(2)

        # 第一行：时间 + 位置
        row1 = QHBoxLayout()
        row1.setContentsMargins(0, 9, 0, 0)

        time_layout = QVBoxLayout()
        time_layout.addWidget(QLabel("时间:"))
        self.time_label = QLabel("T = 0.0000 s")
        self.time_label.setMinimumWidth(180)
        time_layout.addWidget(self.time_label)
        row1.addLayout(time_layout)

        # 添加攻角
        alpha_layout = QVBoxLayout()
        alpha_layout.addWidget(QLabel("攻角:"))
        self.alpha_label = QLabel("Alpha = 0.0000 °")
        self.alpha_label.setMinimumWidth(180)
        alpha_layout.addWidget(self.alpha_label)
        row1.addLayout(alpha_layout)

        # 第二行：速度 + 角度
        row2 = QHBoxLayout()
        row2.setContentsMargins(0, 0, 0, 0)

        pos_layout = QVBoxLayout()
        pos_layout.addWidget(QLabel("位置:"))
        self.pos_label = QLabel("X = 0.0000 m, Y = 0.0000 m, Z = 0.0000 m")
        self.pos_label.setMinimumWidth(180)
        pos_layout.addWidget(self.pos_label)
        row2.addLayout(pos_layout)

        vel_layout = QVBoxLayout()
        vel_layout.addWidget(QLabel("速度:"))
        self.vel_label = QLabel("Vx = 0.0000 m/s, Vy = 0.0000 m/s, Vz = 0.0000 m/s")
        self.vel_label.setMinimumWidth(180)
        vel_layout.addWidget(self.vel_label)
        row2.addLayout(vel_layout)

        # 第三行：角速度
        row3 = QHBoxLayout()
        row3.setContentsMargins(0, 0, 0, 0)

        angle_layout = QVBoxLayout()
        angle_layout.addWidget(QLabel("姿态:"))
        self.angle_label = QLabel("Theta = 0.0000°, Psi = 0.0000°, Phi = 0.0000°")
        self.angle_label.setMinimumWidth(180)
        angle_layout.addWidget(self.angle_label)
        row3.addLayout(angle_layout)

        omega_layout = QVBoxLayout()
        omega_layout.addWidget(QLabel("角速度:"))
        self.omega_label = QLabel("wx = 0.0000 °/s, wy = 0.0000 °/s, wz = 0.0000 °/s")
        self.omega_label.setMinimumWidth(180)
        omega_layout.addWidget(self.omega_label)
        row3.addLayout(omega_layout)

        group_layout.addLayout(row1)
        group_layout.addLayout(row2)
        group_layout.addLayout(row3)

        motion_group.setLayout(group_layout)
        layout.addWidget(motion_group)

    def create_force_group(self, layout):
        force_group = QGroupBox("力系数")
        group_layout = QGridLayout()
        group_layout.setContentsMargins(5, 8, 5, 5)
        group_layout.setSpacing(2)

        # 添加标题行
        group_layout.addWidget(QLabel("系数"), 0, 0)
        group_layout.addWidget(QLabel("值"), 0, 1)
        group_layout.addWidget(QLabel("系数"), 0, 2)
        group_layout.addWidget(QLabel("值"), 0, 3)

        # 第一行
        group_layout.addWidget(QLabel("Fx:"), 1, 0)
        self.fx_label = QLabel("0.0000")
        group_layout.addWidget(self.fx_label, 1, 1)

        group_layout.addWidget(QLabel("Mx:"), 1, 2)
        self.mx_label = QLabel("0.0000")
        group_layout.addWidget(self.mx_label, 1, 3)

        # 第二行
        group_layout.addWidget(QLabel("Fy:"), 2, 0)
        self.fy_label = QLabel("0.0000")
        group_layout.addWidget(self.fy_label, 2, 1)

        group_layout.addWidget(QLabel("My:"), 2, 2)
        self.my_label = QLabel("0.0000")
        group_layout.addWidget(self.my_label, 2, 3)

        # 第三行
        group_layout.addWidget(QLabel("Fz:"), 3, 0)
        self.fz_label = QLabel("0.0000")
        group_layout.addWidget(self.fz_label, 3, 1)

        group_layout.addWidget(QLabel("Mz:"), 3, 2)
        self.mz_label = QLabel("0.0000")
        group_layout.addWidget(self.mz_label, 3, 3)

        force_group.setLayout(group_layout)
        layout.addWidget(force_group)

    def create_contact_group(self, layout):
        contact_group = QGroupBox("接触与应力信息")
        group_layout = QGridLayout()
        group_layout.setContentsMargins(5, 8, 5, 5)
        group_layout.setSpacing(2)

        # 添加标题行
        group_layout.addWidget(QLabel("参数"), 0, 0)
        group_layout.addWidget(QLabel("值"), 0, 1)
        group_layout.addWidget(QLabel("参数"), 0, 2)
        group_layout.addWidget(QLabel("值"), 0, 3)

        # 第一行
        group_layout.addWidget(QLabel("接触次数:"), 1, 0)
        self.n_contacts_label = QLabel("0")
        self.n_contacts_label.setMinimumWidth(50)
        group_layout.addWidget(self.n_contacts_label, 1, 1)

        group_layout.addWidget(QLabel("水压扰动:"), 1, 2)
        self.pressure_label = QLabel("0.0000 MPa")
        self.pressure_label.setMinimumWidth(80)
        group_layout.addWidget(self.pressure_label, 1, 3)

        # 第二行
        group_layout.addWidget(QLabel("上间隙:"), 2, 0)
        self.h2_label = QLabel("-0.0000 mm")
        group_layout.addWidget(self.h2_label, 2, 1)

        group_layout.addWidget(QLabel("下间隙:"), 2, 2)
        self.h1_label = QLabel("-0.0000 mm")
        group_layout.addWidget(self.h1_label, 2, 3)

        # 第三行
        group_layout.addWidget(QLabel("正应力:"), 3, 0)
        self.sigma_label = QLabel("0.00 MPa")
        self.sigma_label.setMinimumWidth(60)
        group_layout.addWidget(self.sigma_label, 3, 1)

        group_layout.addWidget(QLabel("切应力:"), 3, 2)
        self.tau_label = QLabel("0.00 MPa")
        self.tau_label.setMinimumWidth(60)
        group_layout.addWidget(self.tau_label, 3, 3)

        contact_group.setLayout(group_layout)
        layout.addWidget(contact_group)

    def update_parameters(self, data):
        """更新显示的参数"""
        self.current_data = data
        # data = {
        #     'motions': {
        #         't': self.t,
        #         'alphat': self.alphat,
        #         'y': self.y
        #     },
        #     'points': {
        #         'plot_dan_x': self.plot_dan_x,
        #         'plot_dan_y': self.plot_dan_y,
        #         'plot_zhou_x': self.plot_zhou_x,
        #         'plot_zhou_y': self.plot_zhou_y,
        #         'plot_pao_up_x': self.plot_pao_up_x,
        #         'plot_pao_up_y': self.plot_pao_up_y,
        #         'plot_pao_down_x': self.plot_pao_down_x,
        #         'plot_pao_down_y': self.plot_pao_down_y
        #     },
        #     'forces': {
        #         'AFM': self.AFM
        #     }
        # }
        # 运动参数
        if 'motions' in data:

            motion = data['motions']
            if 't' in motion:
                self.time_label.setText(f"{motion['t']:.4f} s")
            if 'alphat' in motion:
                self.alpha_label.setText(f"Alpha = {motion['alphat']:.4f} °")
            if 'y' in motion:
                if len(motion['y'].shape) == 2:
                    self.pos_label.setText(f"X = {motion['y'][9, 0]:.4f} m, Y = {motion['y'][10, 0]:.4f} m, Z = {motion['y'][11, 0]:.4f} m")
                    self.vel_label.setText(f"Vx = {motion['y'][0, 0]:.4f} m/s, Vy = {motion['y'][1, 0]:.4f} m/s, Vz = {motion['y'][2, 0]:.4f} m/s")
                    self.angle_label.setText(f"Theta = {motion['y'][6, 0] * self.rushui.RTD:.4f}°, Psi = {motion['y'][7, 0] * self.rushui.RTD:.4f}°, {motion['y'][8, 0] * self.rushui.RTD:.4f}°")
                    self.omega_label.setText(f"wx = {motion['y'][3, 0] * self.rushui.RTD:.4f} °/s, wy = {motion['y'][4, 0] * self.rushui.RTD:.4f} °/s, wz = {motion['y'][5, 0] * self.rushui.RTD:.4f} °/s")
                else:
                    self.pos_label.setText(
                        f"X = {motion['y'][9]:.4f} m, Y = {motion['y'][10]:.4f} m, Z = {motion['y'][11]:.4f} m")
                    self.vel_label.setText(
                        f"Vx = {motion['y'][0]:.4f} m/s, Vy = {motion['y'][1]:.4f} m/s, Vz = {motion['y'][2]:.4f} m/s")
                    self.angle_label.setText(
                        f"Theta = {motion['y'][6] * self.rushui.RTD:.4f}°, Psi = {motion['y'][7] * self.rushui.RTD:.4f}°, {motion['y'][8] * self.rushui.RTD:.4f}°")
                    self.omega_label.setText(
                        f"wx = {motion['y'][3] * self.rushui.RTD:.4f} °/s, wy = {motion['y'][4] * self.rushui.RTD:.4f} °/s, wz = {motion['y'][5] * self.rushui.RTD:.4f} °/s")

        # 力系数
        if 'forces' in data:
            forces = data['forces']['AFM']
            self.fx_label.setText(f"{forces[0]:.4f}")
            self.fy_label.setText(f"{forces[1]:.4f}")
            self.fz_label.setText(f"{forces[2]:.4f}")
            self.mx_label.setText(f"{forces[3]:.4f}")
            self.my_label.setText(f"{forces[4]:.4f}")
            self.mz_label.setText(f"{forces[5]:.4f}")

        # 接触与应力
        if 'contact' in data:
            contact = data['contact']
            self.n_contacts_label.setText(str(contact.get('n_contacts', 0)))
            self.pressure_label.setText(f"{contact.get('pressure', 0.0):.4f} MPa")
            self.h2_label.setText(f"{contact.get('h2', 0.0) * self.stab.Lmm:.4f} mm")
            self.h1_label.setText(f"{contact.get('h1', 0.0) * self.stab.Lmm:.4f} mm")

            if 'stress' in contact:
                stress = contact['stress']
                sigma_val = abs(stress.get('sigma_max', 0.0))
                tau_val = abs(stress.get('tau_max', 0.0))

                # 超过阈值时高亮显示
                SIGMA_LIMIT = 500  # MPa
                TAU_LIMIT = 300  # MPa

                self.sigma_label.setText(f"{sigma_val:.2f} MPa")
                if sigma_val > SIGMA_LIMIT:
                    self.sigma_label.setStyleSheet("color: red; font-weight: bold;")
                else:
                    self.sigma_label.setStyleSheet("")

                self.tau_label.setText(f"{tau_val:.2f} MPa")
                if tau_val > TAU_LIMIT:
                    self.tau_label.setStyleSheet("color: red; font-weight: bold;")
                else:
                    self.tau_label.setStyleSheet("")

