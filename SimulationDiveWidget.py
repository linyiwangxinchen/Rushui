import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QDoubleSpinBox, QLabel, QProgressBar, QPushButton, QHBoxLayout, QComboBox, \
    QGridLayout, QGroupBox, QVBoxLayout, QWidget

from CalculationThread import CalculationThread


class SimulationDiveWidget(QWidget):
    """仿真控制界面"""
    realtime_update = pyqtSignal(object)  # 修复：添加实时更新信号
    data_output_signal_f = pyqtSignal(dict)
    data_input_signal_f = pyqtSignal(bool)

    def __init__(self, rushui_instance, parent=None):
        super().__init__(parent)
        self.rushui = rushui_instance
        self.calc_thread = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # 初始条件组
        init_group = QGroupBox("初始条件")
        init_layout = QGridLayout()
        init_layout.setContentsMargins(5, 5, 5, 5)
        init_layout.setSpacing(5)

        self.add_labeled_input(init_layout, "初始速度 V0 (m/s):", 0, 0, 10.0, 2000.0, 600.0, 10.0, "v0_input")
        self.add_labeled_input(init_layout, "初始俯仰角 Psi0 (°):", 1, 0, -90.0, 90.0, 0.0, 0.1, "psi0_input")
        self.add_labeled_input(init_layout, "初始角速度 Omega0 (rad/s):", 2, 0, -100.0, 100.0, 10, 0.1, "omega0_input")

        # 加一点，AI是个什么鬼嘛……这都能漏
        self.add_labeled_input(init_layout, "初始攻角 Gamma (°):", 3, 0, -180, 180, -60, 1, "gamma0_input")

        self.add_labeled_input(init_layout, "环境压力 Pc (Pa):", 4, 0, 0, 10000, 2350, 1000, "pc0_input")


        init_group.setLayout(init_layout)

        # 仿真设置组
        sim_group = QGroupBox("仿真设置")
        sim_layout = QGridLayout()
        sim_layout.setContentsMargins(5, 5, 5, 5)
        sim_layout.setSpacing(5)

        self.add_labeled_input(sim_layout, "终点位置 Xfin (m):", 0, 0, 0.1, 1000.0, 10.0, 1.0, "xfin_input")
        self.add_labeled_input(sim_layout, "计算步长 HX:", 1, 0, 0.001, 0.5, 0.01, 0.01, "hx_input")
        self.add_labeled_input(sim_layout, "缩放比例 Scale:", 2, 0, 0.1, 10.0, 1.0, 0.1, "scale_input")

        sim_layout.addWidget(QLabel("扰动类型:"), 3, 0)
        self.perturbation_combo = QComboBox()
        self.perturbation_combo.addItems([
            "无扰动",
            "脉冲扰动",
            "周期扰动",
            "用户定义扰动"
        ])
        self.perturbation_combo.setCurrentIndex(0)
        sim_layout.addWidget(self.perturbation_combo, 3, 1)

        sim_layout.addWidget(QLabel("是否手动设置最大历史步长Nview:"), 4, 0)
        self.nview_combo = QComboBox()
        self.nview_combo.addItems([
            "否",
            "是"
        ])
        self.nview_combo.setCurrentIndex(1)
        sim_layout.addWidget(self.nview_combo, 4, 1)

        self.add_labeled_input(sim_layout, "Nview:", 5, 0, 1, 10000, 232, 100, "Nview_input")

        sim_group.setLayout(sim_layout)

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
        main_layout.addWidget(init_group)
        main_layout.addWidget(sim_group)
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.progress_label)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def add_labeled_input(self, layout, label_text, row, col, min_val, max_val, default_val, step, attr_name):
        """添加带标签的输入控件"""
        layout.addWidget(QLabel(label_text), row, col)
        spin_box = QDoubleSpinBox()
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
            'V0': self.v0_input.value(),
            'H0': self.h0_input.value(),
            'Psi0': self.psi0_input.value(),
            'Omega0': self.omega0_input.value(),
            'Xfin': self.xfin_input.value(),
            'HX': self.hx_input.value(),
            'Scale': self.scale_input.value(),
            'Gamma': self.gamma0_input.value(),
            'Pc': self.pc0_input.value()
        }
        self.data_output_signal_f.emit(data)

    def get_model(self, data):
        self.model_data = data

    def start_simulation(self):
        """启动仿真计算"""
        try:
            # 重置状态
            # Rushui模型不需要设置这些标志，因为计算流程不同
            # self.rushui.FlagSurface = False
            # self.rushui.FlagWashed = False
            # self.rushui.FlagBroken = False
            # self.rushui.FlagFinish = False

            # 设置参数 - Rushui模型使用不同的参数设置方式
            # 这里我们使用ModelParameterWidget中的参数设置
            self.ask_model()

            # 设置Rushui特定参数
            # 弹体参数
            if hasattr(self.model_data, 'L'):
                self.rushui.L = self.model_data['L']
            if hasattr(self.model_data, 'S'):
                self.rushui.S = self.model_data['S']
            if hasattr(self.model_data, 'V'):
                self.rushui.V = self.model_data['V']
            if hasattr(self.model_data, 'm'):
                self.rushui.m = self.model_data['m']
            if hasattr(self.model_data, 'xc'):
                self.rushui.xc = self.model_data['xc']
            if hasattr(self.model_data, 'yc'):
                self.rushui.yc = self.model_data['yc']
            if hasattr(self.model_data, 'zc'):
                self.rushui.zc = self.model_data['zc']
            if hasattr(self.model_data, 'Jxx'):
                self.rushui.Jxx = self.model_data['Jxx']
            if hasattr(self.model_data, 'Jyy'):
                self.rushui.Jyy = self.model_data['Jyy']
            if hasattr(self.model_data, 'Jzz'):
                self.rushui.Jzz = self.model_data['Jzz']

            # 从当前界面获取参数
            # 设置积分参数
            self.rushui.dt = self.hx_input.value()  # 使用hx_input作为dt
            self.rushui.t0 = self.psi0_input.value()  # 使用psi0_input作为t0
            self.rushui.tend = self.xfin_input.value()  # 使用xfin_input作为tend

            # 设置初始条件
            self.rushui.y0 = self.v0_input.value()  # 使用v0_input作为y0
            self.rushui.Omega0 = self.omega0_input.value()
            # 注意：倾斜入水的参数设置需要根据Rushui模型的具体参数进行调整

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
            # Rushui模型不需要手动设置这些状态

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
                self.rushui.__init__()
            except Exception as e:
                logging.error(f"重置模型时出错: {str(e)}")

            QMessageBox.information(self, "已停止", "计算已停止，可以重新设置参数开始新的仿真。")
