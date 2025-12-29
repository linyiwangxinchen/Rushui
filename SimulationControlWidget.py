import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QDoubleSpinBox, QLabel, QProgressBar, QPushButton, QHBoxLayout, QComboBox, \
    QGridLayout, QGroupBox, QVBoxLayout, QWidget

from CalculationThread import CalculationThread


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
        self.add_labeled_input(entry_layout, "终止时间 tend (s):", 1, 0, -1000, 1000, 1, 0.001, "tend_input",
                               range_check=False)
        self.add_labeled_input(entry_layout, "仿真步长 dt (s):", 2, 0, -1000, 1000, 0.0002, 0.00001, "dt_input",
                               range_check=False)
        self.add_labeled_input(entry_layout, "入水速度 v0 (m/s):", 3, 0, -1000, 1000, 300, 0.1, "v0_input",
                               range_check=False)
        self.add_labeled_input(entry_layout, "弹道角 theta0 (deg):", 4, 0, -1000, 1000, -10, 0.01, "theta0_input",
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
        control_group = QGroupBox("入水参数")
        control_layout_data = QGridLayout()
        self.add_labeled_input(control_layout_data, "横滚角速度增益 k_wz:", 0, 0, -1000, 1000, 0.06, 0.0001, "k_wz_input",
                               range_check=False)
        self.add_labeled_input(control_layout_data, "俯仰角增益 k_theta:", 1, 0, -1000, 1000, 0.04, 0.0001, "k_theta_input",
                               range_check=False)
        control_group.setLayout(control_layout_data)

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
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.progress_label)
        main_layout.addStretch()

        self.setLayout(main_layout)

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
            # 积分参数 (正确分组)
            'dt': self.dt_input.value(),
            't0': self.t0_input.value(),
            'tend': self.tend_input.value(),

            # 入水条件 (新增分组)
            'v0': self.v0_input.value(),  # 入水速度 (m/s)
            'theta0': self.theta0_input.value(),  # 弹道角 (deg)
            'psi0': self.psi0_input.value(),  # 偏航角 (deg)
            'phi0': self.phi0_input.value(),  # 横滚角 (deg)
            'alpha0': self.alpha0_input.value(),  # 攻角 (deg)
            'wx0': self.wx0_input.value(),  # 横滚角速度 (deg/s)
            'wy0': self.wy0_input.value(),  # 偏航角速度 (deg/s)
            'wz0': self.wz0_input.value(),  # 俯仰角速度 (deg/s)

            # 控制参数 (正确分组)
            'k_wz': self.k_wz_input.value(),
            'k_theta': self.k_theta_input.value()
        }
        self.data_output_signal_f.emit(data)

    def get_model(self, data):
        self.model_data = data

    def start_simulation(self):
        """启动仿真计算"""
        try:
            # 设置参数
            # 1. 从本窗口UI获取入水参数和控制参数
            dt = self.dt_input.value()
            t0 = self.t0_input.value()
            tend = self.tend_input.value()
            v0 = self.v0_input.value()
            theta0_deg = self.theta0_input.value()  # 角度单位
            psi0_deg = self.psi0_input.value()  # 角度单位
            phi0_deg = self.phi0_input.value()  # 角度单位
            alpha0_deg = self.alpha0_input.value()  # 角度单位
            wx0_deg = self.wx0_input.value()  # 角度/秒
            wy0_deg = self.wy0_input.value()  # 角度/秒
            wz0_deg = self.wz0_input.value()  # 角度/秒
            k_wz = self.k_wz_input.value()
            k_theta = self.k_theta_input.value()

            self.ask_model()

            model_data = self.model_data
            # 总体参数
            self.rushui.total.L = model_data['L']
            self.rushui.total.S = model_data['S']
            self.rushui.total.V = model_data['V']
            self.rushui.total.m = model_data['m']
            self.rushui.total.xc = model_data['xc']
            self.rushui.total.yc = model_data['yc']
            self.rushui.total.zc = model_data['zc']
            self.rushui.total.Jxx = model_data['Jxx']
            self.rushui.total.Jyy = model_data['Jyy']
            self.rushui.total.Jzz = model_data['Jzz']
            self.rushui.total.T = model_data['T']

            # 空化器参数
            self.rushui.lk = model_data['lk']  # 空化器距重心
            self.rushui.rk = model_data['rk']  # 空化器半径
            self.rushui.sgm = model_data['sgm']  # 全局空化数

            # 入水初始条件
            self.rushui.t0 = t0
            self.rushui.tend = tend
            self.rushui.dt = dt
            self.rushui.v0 = v0

            # 角度转换为弧度
            self.rushui.theta0 = theta0_deg / self.rushui.rtd
            self.rushui.psi0 = psi0_deg / self.rushui.rtd
            self.rushui.phi0 = phi0_deg / self.rushui.rtd
            self.rushui.alpha0 = alpha0_deg / self.rushui.rtd
            self.rushui.wx0 = wx0_deg / self.rushui.rtd
            self.rushui.wy0 = wy0_deg / self.rushui.rtd
            self.rushui.wz0 = wz0_deg / self.rushui.rtd

            # 控制参数
            self.rushui.k_wz = k_wz
            self.rushui.k_theta = k_theta

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
