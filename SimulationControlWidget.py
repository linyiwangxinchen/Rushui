import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QDoubleSpinBox, QLabel, QProgressBar, QPushButton, QHBoxLayout, QComboBox, \
    QGridLayout, QGroupBox, QVBoxLayout, QWidget, QLineEdit

from CalculationThread import CalculationThread
from ThrustPlotWindow import ThrustPlotWindow


class SimulationControlWidget(QWidget):
    """仿真控制界面"""
    realtime_update = pyqtSignal(object)  # 修复：添加实时更新信号
    data_output_signal_f = pyqtSignal(dict)
    data_input_signal_f = pyqtSignal(bool)

    def __init__(self, stab_instance, parent=None):
        super().__init__(parent)
        self.rushui = stab_instance
        self.calc_thread = None
        self.init_ui()
        a = 1

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # ——————————入水参数——————————
        entry_group = QGroupBox("入水参数")
        entry_layout = QGridLayout()
        self.add_labeled_input(entry_layout, "起始时间 t0 (s):", 0, 0, -1000, 1000, 0, 0.001, "t0_input",
                               range_check=False)
        self.add_labeled_input(entry_layout, "终止时间 tend (s):", 1, 0, -1000, 1000, 0.2, 0.001, "tend_input",
                               range_check=False)
        self.add_labeled_input(entry_layout, "仿真步长 dt (s):", 2, 0, -1000, 1000, 0.0002, 0.00001, "dt_input",
                               range_check=False)
        self.add_labeled_input(entry_layout, "入水速度 v0 (m/s):", 3, 0, -1000, 1000, 300, 0.1, "v0_input",
                               range_check=False)
        self.add_labeled_input(entry_layout, "入水角 theta0 (deg):", 4, 0, -1000, 1000, -10, 0.01, "theta0_input",
                               range_check=False)
        self.add_labeled_input(entry_layout, "偏航角 psi0 (deg):", 5, 0, -1000, 1000, 0, 0.01, "psi0_input",
                               range_check=False)
        self.add_labeled_input(entry_layout, "横滚角 phi0 (deg):", 6, 0, -1000, 1000, 0, 0.01, "phi0_input",
                               range_check=False)
        self.add_labeled_input(entry_layout, "攻角 alpha0 (deg):", 7, 0, -1000, 1000, 0.03138, 0.0001, "alpha0_input",
                               range_check=False)
        self.add_labeled_input(entry_layout, "横滚角速度 wx0 (deg/s):", 8, 0, -1000, 1000, 0, 0.01, "wx0_input",
                               range_check=False)
        self.add_labeled_input(entry_layout, "偏航角速度 wy0 (deg/s):", 9, 0, -1000, 1000, 0, 0.01, "wy0_input",
                               range_check=False)
        self.add_labeled_input(entry_layout, "俯仰角速度 wz0 (deg/s):", 10, 0, -1000, 1000, 6.63, 0.01, "wz0_input",
                               range_check=False)
        entry_group.setLayout(entry_layout)

        # ——————————控制参数——————————
        control_group = QGroupBox("控制参数")
        control_layout_data = QGridLayout()
        self.add_labeled_input(control_layout_data, "横滚角速度增益 k_wz:", 0, 0, -1000, 1000, 0.09, 0.0001, "k_wz_input",
                               range_check=False)
        self.add_labeled_input(control_layout_data, "俯仰角增益 k_theta:", 1, 0, -1000, 1000, 0.02, 0.0001, "k_theta_input",
                               range_check=False)
        control_group.setLayout(control_layout_data)

        # ——————————控制参数——————————
        control_dive_group = QGroupBox("控制参数")
        control_dive_layout_data = QGridLayout()
        control_dive_layout_data.setContentsMargins(5, 5, 5, 5)
        control_dive_layout_data.setSpacing(5)

        # 俯仰角增益 kth (对应原self.kth)
        self.add_labeled_input(control_dive_layout_data, "俯仰角增益 ktheta:", 0, 0, -1000, 1000, 4, 0.1,
                               "ktheta_input", range_check=False)

        # 姿态同步增益 kps (关联kth)
        self.add_labeled_input(control_dive_layout_data, "姿态同步增益 k_ps:", 1, 0, -1000, 1000, 4, 0.1, "k_ps_input",
                               range_check=False)

        # 舵机响应增益 kph
        self.add_labeled_input(control_dive_layout_data, "舵机响应增益 k_ph:", 2, 0, -1000, 1000, 0.08, 0.01,
                               "k_ph_input", range_check=False)

        # 滚转角速度增益 kwx
        self.add_labeled_input(control_dive_layout_data, "滚转角速度增益 k_wx:", 3, 0, -1000, 1000, 0.0016562, 0.000001,
                               "k_wx_input", range_check=False)

        # 偏航角速度增益 kwz
        self.add_labeled_input(control_dive_layout_data, "偏航角速度增益 kwz:", 4, 0, -1000, 1000, 0.312, 0.001,
                               "kwz_input", range_check=False)

        # 垂向控制增益 kwy (关联kwz)
        self.add_labeled_input(control_dive_layout_data, "垂向控制增益 k_wy:", 5, 0, -1000, 1000, 0.312, 0.001,
                               "k_wy_input", range_check=False)

        control_dive_group.setLayout(control_dive_layout_data)

        # ——————————控制参数——————————
        dive_group = QGroupBox("控制参数")
        dive_layout_data = QGridLayout()
        dive_layout_data.setContentsMargins(5, 5, 5, 5)
        dive_layout_data.setSpacing(5)
        self.add_labeled_input(dive_layout_data, "水下仿真时间:", 0, 0, -1000, 1000, 3.41, 0.001,
                               "tend_under_input", range_check=False)
        self.add_labeled_input(dive_layout_data, "加速段推力 T1:", 1, 0, -1000, 1000000, 25080.6, 0.001,
                               "T1_input", range_check=False)
        self.add_labeled_input(dive_layout_data, "巡航段推力 T2:", 2, 0, -1000, 1000000, 6971.4, 0.001,
                               "T2_input", range_check=False)
        dive_group.setLayout(dive_layout_data)

        # ——————————推力设置—————————— (新增部分)
        thrust_group = QGroupBox("推力设置")
        thrust_layout = QGridLayout()
        thrust_layout.setContentsMargins(5, 5, 5, 5)
        thrust_layout.setSpacing(5)

        # 时间序列输入
        thrust_layout.addWidget(QLabel("时间序列 (s):"), 0, 0)
        self.time_sequence_input = QLineEdit()
        self.time_sequence_input.setPlaceholderText("示例: 0, 0.5, 1.0, 1.5, 2.0")
        self.time_sequence_input.setText("0, 0.56, 0.57, 100")
        thrust_layout.addWidget(self.time_sequence_input, 0, 1)

        # 推力序列输入
        thrust_layout.addWidget(QLabel("推力序列 (N):"), 1, 0)
        self.thrust_sequence_input = QLineEdit()
        self.thrust_sequence_input.setPlaceholderText("示例: 25000, 22000, 18000, 15000, 7000")
        self.thrust_sequence_input.setText("25080.6, 25080.6, 6971.4, 6971.4")

        thrust_layout.addWidget(self.thrust_sequence_input, 1, 1)

        # 展示曲线按钮
        self.plot_thrust_btn = QPushButton("展示推力时间曲线")
        self.plot_thrust_btn.setStyleSheet("background-color: #2196F3; color: white;")
        self.plot_thrust_btn.clicked.connect(self.show_thrust_plot)
        thrust_layout.addWidget(self.plot_thrust_btn, 2, 0, 1, 2, Qt.AlignCenter)

        thrust_group.setLayout(thrust_layout)


        # 控制按钮
        control_layout = QHBoxLayout()
        control_layout.setContentsMargins(0, 0, 0, 0)
        self.start_button = QPushButton("开始仿真")
        self.start_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.start_button.clicked.connect(self.start_simulation)
        self.pause_button = QPushButton("暂停")
        self.pause_button.setEnabled(False)
        self.pause_button.setStyleSheet("background-color: #2196F3; color: white;")
        self.pause_button.clicked.connect(self.pause_simulation)
        self.stop_button = QPushButton("停止")
        self.stop_button.setEnabled(False)
        self.stop_button.setStyleSheet("background-color: #f44336; color: white;")
        self.stop_button.clicked.connect(self.stop_simulation)
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.pause_button)
        control_layout.addWidget(self.stop_button)

        # 进度显示
        self.progress_bar = QProgressBar()
        self.progress_label = QLabel("准备就绪")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("font-weight: bold;")

        # 组合布局
        main_layout.addWidget(entry_group)
        main_layout.addWidget(control_group)
        main_layout.addWidget(control_dive_group)
        main_layout.addWidget(dive_group)
        main_layout.addWidget(thrust_group)  # 新增的推力设置组
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.progress_label)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def show_thrust_plot(self):
        """展示推力-时间曲线"""
        try:
            # 获取输入数据
            time_str = self.time_sequence_input.text().strip()
            thrust_str = self.thrust_sequence_input.text().strip()

            if not time_str or not thrust_str:
                QMessageBox.warning(self, "输入错误", "请输入时间序列和推力序列数据")
                return

            # 解析时间序列
            time_data = [float(t.strip()) for t in time_str.split(',') if t.strip()]
            thrust_data = [float(t.strip()) for t in thrust_str.split(',') if t.strip()]

            # 验证数据
            if len(time_data) != len(thrust_data):
                QMessageBox.warning(self, "数据错误",
                                    f"时间点数量({len(time_data)})与推力值数量({len(thrust_data)})不匹配")
                return

            if len(time_data) < 2:
                QMessageBox.warning(self, "数据不足", "至少需要两个数据点才能绘制曲线")
                return

            # 检查时间序列是否单调递增
            if any(time_data[i] >= time_data[i + 1] for i in range(len(time_data) - 1)):
                QMessageBox.warning(self, "时间序列错误", "时间序列必须是单调递增的")
                return

            # 创建并显示绘图窗口
            plot_window = ThrustPlotWindow(time_data, thrust_data, self)
            plot_window.exec_()

        except ValueError as e:
            QMessageBox.critical(self, "解析错误",
                                 f"数据格式错误: {str(e)}\n请确保输入的是逗号分隔的数字序列")
        except Exception as e:
            logging.exception("绘制推力曲线时出错")
            QMessageBox.critical(self, "错误", f"无法绘制曲线: {str(e)}")

    def add_labeled_input(self, layout, label_text, row, col, min_val, max_val, default_val, step, attr_name, range_check=True):
        """添加带标签的输入控件"""
        layout.addWidget(QLabel(label_text), row, col)
        spin_box = QDoubleSpinBox()
        spin_box.setDecimals(6)
        spin_box.setRange(min_val, max_val)
        spin_box.setSingleStep(step)
        spin_box.setValue(default_val)

        layout.addWidget(spin_box, row, col + 1)
        setattr(self, attr_name, spin_box)

    def ask_model(self):
        # 告诉model我要数据
        self.data_input_signal_f.emit(True)

    def to_model(self, Checki):
        # 向model发送数据
        data = {
            # ——————————入水参数——————————
            't0': self.t0_input.value(),  # 起始时间 (s)
            'tend': self.tend_input.value(),  # 终止时间 (s)
            'dt': self.dt_input.value(),  # 仿真步长 (s)
            'v0': self.v0_input.value(),  # 入水速度 (m/s)
            'theta0': self.theta0_input.value(),  # 弹道角 (deg)
            'psi0': self.psi0_input.value(),  # 偏航角 (deg)
            'phi0': self.phi0_input.value(),  # 横滚角 (deg)
            'alpha0': self.alpha0_input.value(),  # 攻角 (deg)
            'wx0': self.wx0_input.value(),  # 横滚角速度 (deg/s)
            'wy0': self.wy0_input.value(),  # 偏航角速度 (deg/s)
            'wz0': self.wz0_input.value(),  # 俯仰角速度 (deg/s)

            # ——————————控制参数 (修正分组)——————————
            # 注：原代码存在分组命名冲突，已按实际参数含义重新分组
            'k_wz': self.k_wz_input.value(),  # 偏航角速度增益 (控制参数)
            'k_theta': self.k_theta_input.value(),  # 俯仰角增益 (控制参数)

            'kwz': self.kwz_input.value(),  # 偏航角速度增益 (控制参数)
            'ktheta': self.ktheta_input.value(),  # 俯仰角增益 (控制参数)
            # ——————————深度控制参数——————————
            'k_ps': self.k_ps_input.value(),  # 姿态同步增益
            'k_ph': self.k_ph_input.value(),  # 舵机响应增益
            'k_wx': self.k_wx_input.value(),  # 滚转角速度增益
            'k_wy': self.k_wy_input.value(),  # 垂向控制增益
            'tend_under_input': self.tend_under_input.value(),
            'T1': self.T1_input.value(),
            'T2': self.T2_input.value(),

            # 两个新增的输入框
            'time_sequence': self.time_sequence_input.Text(),
            'thrust_sequence': self.thrust_sequence_input.Text()

        }
        self.data_output_signal_f.emit(data)

    def get_model(self, data):
        self.model_data = data

    def start_simulation(self):
        """启动仿真计算"""
        try:
            # 设置参数
            # 1. 从本窗口UI获取入水参数和控制参数
            # ——————————入水参数——————————
            t0 = self.t0_input.value()  # 起始时间 (s)
            tend = self.tend_input.value()  # 终止时间 (s)
            dt = self.dt_input.value()  # 仿真步长 (s)
            v0 = self.v0_input.value()  # 入水速度 (m/s)
            theta0 = self.theta0_input.value()  # 弹道角 (deg)
            psi0 = self.psi0_input.value()  # 偏航角 (deg)
            phi0 = self.phi0_input.value()  # 横滚角 (deg)
            alpha0 = self.alpha0_input.value()  # 攻角 (deg)
            wx0 = self.wx0_input.value()  # 横滚角速度 (deg/s)
            wy0 = self.wy0_input.value()  # 偏航角速度 (deg/s)
            wz0 = self.wz0_input.value()  # 俯仰角速度 (deg/s)

            # ——————————基础控制参数——————————
            # 注意：此处的k_wz和k_theta会被深度控制参数覆盖（UI存在重复定义）
            k_wz = self.k_wz_input.value()  # 偏航角速度增益 (基础控制)
            k_theta = self.k_theta_input.value()  # 俯仰角增益 (基础控制)

            # ——————————深度控制参数——————————
            k_ps = self.k_ps_input.value()  # 姿态同步增益
            k_ph = self.k_ph_input.value()  # 舵机响应增益
            k_wx = self.k_wx_input.value()  # 滚转角速度增益
            k_wy = self.k_wy_input.value()  # 垂向控制增益
            # 注意：深度控制组的k_wz和k_theta会覆盖基础控制组的值
            kwz = self.kwz_input.value()  # 偏航角速度增益 (深度控制)
            ktheta = self.ktheta_input.value()  # 俯仰角增益 (深度控制)
            tend_under = self.tend_under_input.value()

            self.ask_model()

            model_data = self.model_data
            # 几何与质量参数 (赋值到self.total命名空间)
            self.rushui.total.L = model_data['L']  # 长度 (m)
            self.rushui.total.S = model_data['S']  # 横截面积 (m²)
            self.rushui.total.V = model_data['V']  # 体积 (m³)
            self.rushui.total.m = model_data['m']  # 质量 (kg)
            self.rushui.total.xc = model_data['xc']  # 重心 x 坐标 (m)
            self.rushui.total.yc = model_data['yc']  # 重心 y 坐标 (m)
            self.rushui.total.zc = model_data['zc']  # 重心 z 坐标 (m)
            self.rushui.total.Jxx = model_data['Jxx']  # 转动惯量 Jxx (kg·m²)
            self.rushui.total.Jyy = model_data['Jyy']  # 转动惯量 Jyy (kg·m²)
            self.rushui.total.Jzz = model_data['Jzz']  # 转动惯量 Jzz (kg·m²)
            self.rushui.total.T = model_data['T']  # 推力 (N)

            # 空泡仿真参数 (直接赋值到实例)
            self.rushui.lk = model_data['lk']  # 空化器距重心距离 (m)
            self.rushui.rk = model_data['rk']  # 空化器半径 (m)
            self.rushui.sgm = model_data['sgm']  # 全局空化数
            self.rushui.dyc = model_data['dyc']  # 空泡轴线偏离 (m)

            # 水下物理几何参数 (直接赋值到实例)
            self.rushui.SGM = model_data['SGM']  # 水下空化数
            self.rushui.LW = model_data['LW']  # 水平鳍位置 (m)
            self.rushui.LH = model_data['LH']  # 垂直鳍位置 (m)

            # 舵机与角度限制参数 (需角度转弧度)
            RTD = self.rushui.RTD  # 获取弧度-角度转换因子 (180/π)

            # 角度类参数 (° -> rad)
            self.rushui.dkmax = model_data['dkmax'] / RTD  # 舵角上限 (rad)
            self.rushui.dkmin = model_data['dkmin'] / RTD  # 舵角下限 (rad)
            self.rushui.dk0 = model_data['dk0'] / RTD  # 舵角零位 (rad)
            self.rushui.ddmax = model_data['ddmax'] / RTD  # 最大深度变化率 (rad/s²)
            self.rushui.dvmax = model_data['dvmax'] / RTD  # 最大速度变化率 (rad/s²)
            self.rushui.dthetamax = model_data['dthetamax'] / RTD  # 最大俯仰角速率 (rad/s)
            self.rushui.wzmax = model_data['wzmax'] / RTD  # 最大偏航角速率 (rad/s)
            self.rushui.wxmax = model_data['wxmax'] / RTD  # 最大滚转角速率 (rad/s)
            self.rushui.dphimax = model_data['dphimax'] / RTD  # 最大滚转角加速度 (rad/s²)

            # 位移类参数 (直接赋值，单位m)
            self.rushui.deltaymax = model_data['deltaymax']  # 横向位移限制 (m)
            self.rushui.deltavymax = model_data['deltavymax']  # 垂向位移限制 (m)

            # 入水初始条件
            self.rushui.t0 = t0
            self.rushui.tend = tend
            self.rushui.dt = dt
            self.rushui.v0 = v0

            # ——————————入水参数—————————— (角度需转换为弧度)
            self.rushui.t0 = t0  # 起始时间 (s)
            self.rushui.tend = tend  # 终止时间 (s)
            self.rushui.dt = dt  # 仿真步长 (s)
            self.rushui.v0 = v0  # 入水速度 (m/s)
            self.rushui.theta0 = theta0 / RTD  # 弹道角 (rad)
            self.rushui.psi0 = psi0 / RTD  # 偏航角 (rad)
            self.rushui.phi0 = phi0 / RTD  # 横滚角 (rad)
            self.rushui.alpha0 = alpha0 / RTD  # 攻角 (rad)
            self.rushui.wx0 = wx0 / RTD  # 横滚角速度 (rad/s)
            self.rushui.wy0 = wy0 / RTD  # 偏航角速度 (rad/s)
            self.rushui.wz0 = wz0 / RTD  # 俯仰角速度 (rad/s)

            # ——————————基础控制参数—————————— (无量纲增益，直接赋值)
            # 注意：这些参数在Dan类中有独立用途
            self.rushui.k_wz = k_wz  # 偏航角速度增益
            self.rushui.k_theta = k_theta  # 俯仰角增益

            # ——————————深度控制参数—————————— (无量纲增益，直接赋值)
            # 与基础控制参数不同，这些用于水下控制律
            self.rushui.kps = k_ps  # 姿态同步增益 (对应kth)
            self.rushui.kph = k_ph  # 舵机响应增益
            self.rushui.kwx = k_wx  # 滚转角速度增益
            self.rushui.kwy = k_wy  # 垂向控制增益
            self.rushui.kwz = kwz  # 偏航角速度增益 (深度控制)
            self.rushui.kth = ktheta  # 俯仰角增益 (深度控制)

            # ——————————特殊关联参数——————————
            # Dan类中kps默认等于kth，但UI提供独立控制，此处显式同步
            self.rushui.kps = self.rushui.kth  # 确保姿态同步增益与俯仰增益一致
            self.rushui.tend_under = tend_under
            self.rushui.T1 = self.T1_input.value()
            self.rushui.T2 = self.T2_input.value()
            self.rushui._recalculate_update_input()

            # 如果已有线程，先停止
            if self.calc_thread and self.calc_thread.isRunning():
                self.calc_thread.stop()
                self.calc_thread.wait(2000)  # 等待2秒

            # 创建并启动计算线程
            self.calc_thread = CalculationThread(self.rushui)
            self.calc_thread.progress.connect(self.update_progress)
            self.calc_thread.realtime_update.connect(self.handle_realtime_update)
            self.calc_thread.finished.connect(self.simulation_finished)
            self.calc_thread.error.connect(self.handle_error)

            # 更新UI状态
            self.start_button.setEnabled(False)
            self.pause_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            self.progress_label.setText("计算中...")
            self.progress_bar.setValue(0)

            # 重置计算状态

            self.calc_thread.start()

        except Exception as e:
            logging.exception("启动仿真时出错")
            QMessageBox.critical(self, "错误", f"无法启动仿真: {str(e)}")

    def update_progress(self, percent, message):
        """更新进度显示"""
        self.progress_bar.setValue(percent)
        self.progress_label.setText(f"{message} ({percent}%)")

    def handle_realtime_update(self, data):
        """处理实时更新数据并转发信号"""
        if self.calc_thread and self.calc_thread.is_running:
            self.realtime_update.emit(data)

    def simulation_finished(self, results):
        """仿真完成处理"""
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)

        if results is not None:
            self.progress_label.setText("仿真完成!")
            QMessageBox.information(self, "完成", "仿真计算已完成！")
            logging.info("仿真计算成功完成")
        else:
            self.progress_label.setText("仿真已中止")

    def handle_error(self, error_message):
        """处理计算错误"""
        self.start_button.setEnabled(True)
        self.pause_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.progress_label.setText("计算出错")

        QMessageBox.critical(self, "计算错误", error_message)
        logging.error(f"计算错误: {error_message}")

    def pause_simulation(self):
        """暂停仿真"""
        if self.calc_thread and self.calc_thread.isRunning():
            if self.pause_button.text() == "暂停":
                self.calc_thread.pause()
                self.pause_button.setText("继续")
                self.progress_label.setText("计算已暂停")
                logging.info("计算已暂停")
            else:
                self.calc_thread.resume()
                self.pause_button.setText("暂停")
                self.progress_label.setText("计算继续中...")
                logging.info("计算继续中")

    def stop_simulation(self):
        """停止仿真"""
        if self.calc_thread and self.calc_thread.isRunning():
            # 请求线程停止
            self.calc_thread.stop()

            # 等待线程结束，设置更长的超时时间
            if not self.calc_thread.wait(1000):  # 等待5秒
                logging.warning("线程未能在5秒内正常终止，强制终止")
                self.calc_thread.terminate()
                self.calc_thread.wait()

            # 重置UI状态
            self.start_button.setEnabled(True)
            self.pause_button.setEnabled(False)
            self.stop_button.setEnabled(False)
            self.pause_button.setText("暂停")
            self.progress_label.setText("计算已停止")
            self.progress_bar.setValue(0)
            logging.info("计算已停止")

            # 仅在确定线程已终止后重置模型
            try:
                self.stab.__init__()
            except Exception as e:
                logging.error(f"重置模型时出错: {str(e)}")

            QMessageBox.information(self, "已停止", "计算已停止，可以重新设置参数开始新的仿真。")
