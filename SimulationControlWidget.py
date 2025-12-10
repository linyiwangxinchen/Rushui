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
        # 弹体参数
        dan_group = QGroupBox("弹体参数")
        dan_layout = QGridLayout()
        dan_layout.setContentsMargins(5, 5, 5, 5)
        dan_layout.setSpacing(5)

        self.add_labeled_input(dan_layout, "弹体L:", 0, 0, -1000, 1000, 3.195, 0.0001, "L_input", range_check=False)
        self.add_labeled_input(dan_layout, "弹体S:", 1, 0, -1000, 1000, 0.0356, 0.0001, "S_input", range_check=False)
        self.add_labeled_input(dan_layout, "弹体V:", 2, 0, -1000, 1000, 0, 0.0001, "V_input", range_check=False)
        self.add_labeled_input(dan_layout, "弹体m:", 3, 0, -1000, 1000, 114.7, 0.0001, "m_input", range_check=False)
        self.add_labeled_input(dan_layout, "弹体xc:", 4, 0, -1000, 1000, -0.0188, 0.0001, "xc_input", range_check=False)
        self.add_labeled_input(dan_layout, "弹体yc:", 5, 0, -1000, 1000, -0.0017, 0.0001, "yc_input", range_check=False)
        self.add_labeled_input(dan_layout, "弹体zc:", 6, 0, -1000, 1000, 0.0008, 0.0001, "zc_input", range_check=False)
        self.add_labeled_input(dan_layout, "弹体Jxx:", 7, 0, -1000, 1000, 0.63140684, 0.0001, "jxx_input", range_check=False)
        self.add_labeled_input(dan_layout, "弹体Jyy:", 8, 0, -1000, 1000, 57.06970864, 0.0001, "jyy_input", range_check=False)
        self.add_labeled_input(dan_layout, "弹体Jzz:", 9, 0, -1000, 1000, 57.07143674, 0.0001, "jzz_input", range_check=False)
        dan_group.setLayout(dan_layout)

        # 初始条件组
        init_group = QGroupBox("积分参数")
        init_layout = QGridLayout()
        init_layout.setContentsMargins(5, 5, 5, 5)
        init_layout.setSpacing(5)

        self.add_labeled_input(init_layout, "积分步长dt:", 0, 0, -1000, 1000, 0.001, 0.0001, "dt_input", range_check=False)
        self.add_labeled_input(init_layout, "积分起始时间t0:", 1, 0, -1000, 1000, 0.539, 0.01, "t0_input", range_check=False)
        self.add_labeled_input(init_layout, "积分截止时间tend:", 2, 0, -1000, 1000, 3.41, 1.0, "tend_input", range_check=False)
        # layout, label_text, row, col, min_val, max_val, default_val, step, attr_name, range_check
        init_group.setLayout(init_layout)

        # 仿真设置组
        sim_group = QGroupBox("起始条件")
        sim_layout = QGridLayout()
        sim_layout.setContentsMargins(5, 5, 5, 5)
        sim_layout.setSpacing(5)

        self.add_labeled_input(sim_layout, "启控深度YCS (m):", 0, 0, -1000, 1000, -3.45, 1.0, "ycs_input", range_check=False)
        self.add_labeled_input(sim_layout, "启控俯仰角THETACS (deg):", 1, 0, -1000, 1000, -2.5086, 1.0, "thetacs_input", range_check=False)
        self.add_labeled_input(sim_layout, "启控垂向速度VYCS (m/s):", 2, 0, -1000, 1000, -0.01323, 1.0, "yvcs_input", range_check=False)
        self.add_labeled_input(sim_layout, "启控偏航角PSICS (deg):", 3, 0, -1000, 1000, 9.17098, 1.0, "psics_input", range_check=False)

        # 开题
        # 基于智能预测的高速入水过程
        # 高速入水过程智能预测方法
        # 流动控制方法，大量预测，流动外形，开展入水过程流动控制
        # 流动控制方法实验验证与数据对比分析

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
        main_layout.addWidget(dan_group)
        main_layout.addWidget(init_group)
        main_layout.addWidget(sim_group)
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
                # 弹体参数
            'L': self.L_input.value(),    # 弹体总长
            'S': self.S_input.value(),    # 参考面积
            'V': self.V_input.value(),    # 体积
            'm': self.m_input.value(),    # 质量
            'xc': self.xc_input.value(),  # 质心x坐标
            'yc': self.yc_input.value(),  # 质心y坐标
            'zc': self.zc_input.value(),  # 质心z坐标
            'Jxx': self.jxx_input.value(),# x轴转动惯量
            'Jyy': self.jyy_input.value(),# y轴转动惯量
            'Jzz': self.jzz_input.value(),# z轴转动惯量

            # 积分参数
            'dt': self.dt_input.value(),  # 积分步长
            't0': self.t0_input.value(),  # 起始时间
            'tend': self.tend_input.value(),  # 截止时间

            # 起始条件
            'ycs': self.ycs_input.value(),        # 启控深度 (m)
            'thetacs': self.thetacs_input.value(),# 启控俯仰角 (deg)
            'yvcs': self.yvcs_input.value(),      # 启控垂向速度 (m/s)
            'psics': self.psics_input.value()     # 启控偏航角 (deg)
        }
        self.data_output_signal_f.emit(data)

    def get_model(self, data):
        self.model_data = data

    def start_simulation(self):
        """启动仿真计算"""
        try:
            # 设置参数

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
