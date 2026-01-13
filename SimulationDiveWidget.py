import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QDoubleSpinBox, QLabel, QProgressBar, QPushButton, QHBoxLayout, QComboBox, \
    QGridLayout, QGroupBox, QVBoxLayout, QWidget

from CalculationThread import CalculationThread
from MCS import MSC

class SimulationDiveWidget(QWidget):
    """仿真控制界面"""
    realtime_update = pyqtSignal(object)  # 修复：添加实时更新信号
    data_output_signal_f = pyqtSignal(dict)
    data_input_signal_f = pyqtSignal(bool)

    def __init__(self, stab_instance, parent=None):
        super().__init__(parent)
        self.stab = stab_instance
        self.calc_thread = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)

        # 初始条件组
        init_group = QGroupBox("毁伤目标参数选定")
        init_layout = QGridLayout()
        init_layout.setContentsMargins(5, 5, 5, 5)
        init_layout.setSpacing(5)

        self.add_labeled_input(init_layout, "目标舰艇长度 ship_L (m):", 0, 0, 0, 20000.0, 315.7728, 1.0, "ship_L_input")
        self.add_labeled_input(init_layout, "目标舰艇质量 ship_M (kg):", 1, 0, 0, 780000000, 78000000, 100, "ship_M_input")
        self.add_labeled_input(init_layout, "目标舰艇宽度 ship_B (m):", 2, 0, 0, 10000, 76.8096, 0.1, "ship_B_input")
        self.add_labeled_input(init_layout, "舰艇吃水深度 ship_T (m):", 3, 0, 0, 10000, 10.8966, 1, "ship_T_input")
        init_group.setLayout(init_layout)

        # 仿真设置组
        sim_group = QGroupBox("武器毁伤多次重复实验")
        sim_layout = QGridLayout()
        sim_layout.setContentsMargins(5, 5, 5, 5)
        sim_layout.setSpacing(5)

        self.add_labeled_input(sim_layout, "打靶重复次数:", 0, 0, 1, 100, 3, 1.0, "burn_N_input")

        sim_layout.addWidget(QLabel("是否手动设置舰艇类型:"), 1, 0)
        self.ship_if = QComboBox()
        self.ship_if.addItems([
            "否",
            "是"
        ])
        self.ship_if.setCurrentIndex(0)
        sim_layout.addWidget(self.ship_if, 1, 1)

        sim_layout.addWidget(QLabel("选择舰艇类型:"), 2, 0)
        self.ship_tpye = QComboBox()
        self.ship_tpye.addItems([
            "福莱斯特",
            "萨拉托加",
            "游骑兵",
            "独立"
        ])
        self.ship_tpye.setCurrentIndex(0)
        sim_layout.addWidget(self.ship_tpye, 2, 1)

        sim_group.setLayout(sim_layout)

        ship_x_group = QGroupBox("目标舰艇相关参数（从入水点开始计算）")
        ship_x_layout = QGridLayout()
        ship_x_layout.setContentsMargins(5, 5, 5, 5)
        ship_x_layout.setSpacing(5)
        self.add_labeled_input(ship_x_layout, "目标舰艇位置x (m):", 0, 0, 0, 1000, 120, 1.0, "ship_x_x_input")
        self.add_labeled_input(ship_x_layout, "目标舰艇位置y (m):", 1, 0, 0, 1000, 0, 1.0, "ship_x_y_input")
        self.add_labeled_input(ship_x_layout, "目标舰艇位置z (m):", 2, 0, 0, 1000, 0, 1.0, "ship_x_z_input")
        self.add_labeled_input(ship_x_layout, "目标舰艇最大速度（节）:", 3, 0, 0, 1000, 46, 1.0, "ship_v_max_input")
        self.add_labeled_input(ship_x_layout, "目标舰艇最大加速度（m/s^2）:", 4, 0, 0, 1000, 2, 1.0, "ship_a_max_input")
        ship_x_group.setLayout(ship_x_layout)

        dan_air_group = QGroupBox("空中入水飞行参数（从平台读取）")
        dan_air_layout = QGridLayout()
        dan_air_layout.setContentsMargins(5, 5, 5, 5)
        dan_air_layout.setSpacing(5)
        # 如果是324，那么就是：
        # self.add_labeled_input(dan_air_layout, "空中飞行时间t (s):", 0, 0, 0, 1000, 639.0679, 1.0, "air_t_input")
        # self.add_labeled_input(dan_air_layout, "空中弹道距离L (km):", 1, 0, 0, 1000, 513.54423, 1.0, "air_L_input")
        # self.add_labeled_input(dan_air_layout, "入水弹道倾角theta (deg):", 2, 0, -1000, 1000, -14.295, 1.0, "air_theta_input")
        # self.add_labeled_input(dan_air_layout, "入水速度v (m/s):", 3, 0, 0, 1000, 301.6168, 1.0, "air_v_input")
        # 如果是213，那么就是：
        self.add_labeled_input(dan_air_layout, "空中飞行时间t (s):", 0, 0, 0, 1000, 699.53, 1.0, "air_t_input")
        self.add_labeled_input(dan_air_layout, "空中弹道距离L (km):", 1, 0, 0, 1000, 519.8217, 1.0, "air_L_input")
        self.add_labeled_input(dan_air_layout, "入水弹道倾角theta (deg):", 2, 0, -1000, 1000, -10.1 , 1.0, "air_theta_input")
        self.add_labeled_input(dan_air_layout, "入水速度v (m/s):", 3, 0, 0, 1000, 273.63, 1.0, "air_v_input")

        dan_air_layout.addWidget(QLabel("是否开启电磁制导:"), 4, 0)
        self.dan_aim_tpye = QComboBox()
        self.dan_aim_tpye.addItems([
            "否",
            "是"
        ])
        self.dan_aim_tpye.setCurrentIndex(0)
        dan_air_layout.addWidget(self.dan_aim_tpye, 4, 1)

        self.add_labeled_input(dan_air_layout, "不开启电磁制导的起爆距离 (m):", 5, 0, 0, 1000, 10, 1.0, "dan_L_input")

        dan_air_group.setLayout(dan_air_layout)

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

        result_group = QGroupBox("计算结果")
        # 结果显示区域
        result_layout = QGridLayout()
        result_layout.setContentsMargins(5, 5, 5, 5)
        result_layout.setSpacing(3)

        # 计算结果标签
        self.result_labels = {}
        result_params = [
            ("综合毁伤概率", "P", "%"),

        ]

        row = 0
        for name, key, unit in result_params:
            result_layout.addWidget(QLabel(f"{name}:"), row, 0)
            label = QLabel("0.0000")
            self.result_labels[key] = label
            result_layout.addWidget(label, row, 1)
            if unit:
                result_layout.addWidget(QLabel(unit), row, 2)
            row += 1

        result_group.setLayout(result_layout)

        # 组合布局
        main_layout.addWidget(init_group)
        main_layout.addWidget(sim_group)
        main_layout.addWidget(ship_x_group)
        main_layout.addWidget(dan_air_group)
        main_layout.addLayout(control_layout)
        main_layout.addWidget(self.progress_bar)
        main_layout.addWidget(self.progress_label)
        main_layout.addWidget(result_group)
        main_layout.addStretch()

        self.setLayout(main_layout)

    def add_labeled_input(self, layout, label_text, row, col, min_val, max_val, default_val, step, attr_name):
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
            # 毁伤目标参数选定
            'ship_L': self.ship_L_input.value(),
            'ship_M': self.ship_M_input.value(),
            'ship_B': self.ship_B_input.value(),
            'ship_T': self.ship_T_input.value(),

            # 武器毁伤多次重复实验
            'burn_N': self.burn_N_input.value(),
            'ship_if': self.ship_if.currentIndex(),  # 是否手动设置舰艇类型
            'ship_tpye': self.ship_tpye.currentIndex(),  # 选择的舰艇类型（注意变量名拼写）

            # 目标舰艇相关参数
            'ship_x_x': self.ship_x_x_input.value(),  # x位置
            'ship_x_y': self.ship_x_y_input.value(),  # y位置
            'ship_x_z': self.ship_x_z_input.value(),  # z位置
            'ship_v_max': self.ship_v_max_input.value(),  # 最大速度（节）
            'ship_a_max': self.ship_a_max_input.value(),  # 最大加速度（m/s^2）

            # 空中入水飞行参数
            'air_t': self.air_t_input.value(),  # 飞行时间(s)
            'air_L': self.air_L_input.value(),  # 弹道距离(km)
            'air_theta': self.air_theta_input.value(),  # 入水倾角(deg)
            'air_v': self.air_v_input.value()  # 入水速度(m/s)
        }
        self.data_output_signal_f.emit(data)

    def get_model(self, data):
        self.model_data = data

    def start_simulation(self):
        """启动仿真计算"""
        try:
            # 重置状态
            self.ask_model()

            self.stab = MSC()
            self.stab.model_data = self.model_data
            self.stab.ship_L = self.ship_L_input.value()
            self.stab.ship_M = self.ship_M_input.value()
            self.stab.ship_B = self.ship_B_input.value()
            self.stab.ship_T = self.ship_T_input.value()
            self.stab.ifship = self.ship_if.currentIndex()
            self.stab.ship_kind = self.ship_tpye.currentIndex()
            self.stab.N_burn = self.burn_N_input.value()
            self.stab.ifdian = self.ifdian.value()
            self.stab.dian_L = self.dian_L_input.value()


            # 创建并启动计算线程
            self.calc_thread = CalculationThread(self.stab)
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
            self.stab.Jend = 0
            self.stab.Ihis = 1
            self.stab.Nhis = -1

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
        self.result_labels['P'].setText('%.2f' % (sum(data['P_list'])/len(data['P_list']) * 100))
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
