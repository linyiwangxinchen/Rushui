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

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        save_action = file_menu.addAction("保存配置")
        save_action.triggered.connect(self.save_configuration)

        load_action = file_menu.addAction("加载配置")
        load_action.triggered.connect(self.load_configuration)

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
            lengths, diams = self.model_param_widget.get_section_parameters()
            model_params = {
                "Lm": self.model_param_widget.length_input.value(),
                "Lf": self.model_param_widget.forebody_length_input.value(),
                "Lh": self.model_param_widget.cavity_length_input.value(),
                "DLh": self.model_param_widget.cavity_left_diam_input.value(),
                "DRh": self.model_param_widget.cavity_right_diam_input.value(),
                "Rhof": self.model_param_widget.forebody_density_input.value(),
                "Rhoa": self.model_param_widget.aftbody_density_input.value(),
                "Rhoh": self.model_param_widget.cavity_density_input.value(),
                "Dnmm": self.model_param_widget.cavitator_diam_input.value(),
                "Beta": self.model_param_widget.cavitator_angle_input.value(),
                "Delta": self.model_param_widget.cavitator_swing_input.value(),
                "Ncon": self.model_param_widget.section_count_input.value(),
                "ConeLen": lengths,
                "BaseDiam": diams,
                "Omega0": self.stab.Omega0
            }

            # 收集仿真参数
            sim_params = {
                "V0": self.sim_control_widget.v0_input.value(),
                "H0": self.sim_control_widget.h0_input.value(),
                "Psi0": self.sim_control_widget.psi0_input.value(),
                "Omega0": self.sim_control_widget.omega0_input.value(),
                "Gamma0": self.sim_control_widget.gamma0_input.value(),
                "Pc0": self.sim_control_widget.pc0_input.value(),
                "Xfin": self.sim_control_widget.xfin_input.value(),
                "HX": self.sim_control_widget.hx_input.value(),
                "Scale": self.sim_control_widget.scale_input.value(),
                "PerturbationType": self.sim_control_widget.perturbation_combo.currentIndex(),
                "NviewSetting": self.sim_control_widget.nview_combo.currentIndex(),
                "Nview": self.sim_control_widget.Nview_input.value()
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
                self.model_param_widget.length_input.setValue(mp.get("Lm", 0.5))
                self.model_param_widget.forebody_length_input.setValue(mp.get("Lf", 59.0))
                self.model_param_widget.cavity_length_input.setValue(mp.get("Lh", 20.0))
                self.model_param_widget.cavity_left_diam_input.setValue(mp.get("DLh", 6.0))
                self.model_param_widget.cavity_right_diam_input.setValue(mp.get("DRh", 6.0))
                self.model_param_widget.forebody_density_input.setValue(mp.get("Rhof", 17.6))
                self.model_param_widget.aftbody_density_input.setValue(mp.get("Rhoa", 4.5))
                self.model_param_widget.cavity_density_input.setValue(mp.get("Rhoh", 0.0))
                self.model_param_widget.cavitator_diam_input.setValue(mp.get("Dnmm", 1.5))
                self.model_param_widget.cavitator_angle_input.setValue(mp.get("Beta", 180.0))
                self.model_param_widget.cavitator_swing_input.setValue(mp.get("Delta", 0.0))
                self.model_param_widget.section_count_input.setValue(mp.get("Ncon", 3))

                # 更新分段表格
                if "ConeLen" in mp and "BaseDiam" in mp:
                    lengths = mp["ConeLen"]
                    diams = mp["BaseDiam"]
                    self.model_param_widget.update_section_table()
                    for i in range(min(self.model_param_widget.section_count_input.value(), len(lengths), len(diams))):
                        self.model_param_widget.section_table.item(i, 0).setText(str(lengths[i]))
                        self.model_param_widget.section_table.item(i, 1).setText(str(diams[i]))

                # 更新Stab实例
                self.stab.Omega0 = mp.get("Omega0", 1.0)

            # 加载仿真参数
            if "sim_params" in config:
                sp = config["sim_params"]
                self.sim_control_widget.v0_input.setValue(sp.get("V0", 600.0))
                self.sim_control_widget.h0_input.setValue(sp.get("H0", 30.0))
                self.sim_control_widget.psi0_input.setValue(sp.get("Psi0", 0.0))
                self.sim_control_widget.omega0_input.setValue(sp.get("Omega0", 1.0))
                self.sim_control_widget.gamma0_input.setValue(sp.get("Gamma0", 1.0))
                self.sim_control_widget.pc0_input.setValue(sp.get("Pc0", 2350.0))
                self.sim_control_widget.xfin_input.setValue(sp.get("Xfin", 100.0))
                self.sim_control_widget.hx_input.setValue(sp.get("HX", 0.05))
                self.sim_control_widget.scale_input.setValue(sp.get("Scale", 1.0))
                self.sim_control_widget.perturbation_combo.setCurrentIndex(sp.get("PerturbationType", 0))
                self.sim_control_widget.nview_combo.setCurrentIndex(sp.get("NviewSetting", 1))
                self.sim_control_widget.Nview_input.setValue(sp.get("Nview", 500))

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
