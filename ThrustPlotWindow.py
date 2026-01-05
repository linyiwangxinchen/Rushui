import logging
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtWidgets import (QMessageBox, QDoubleSpinBox, QLabel, QProgressBar,
                            QPushButton, QHBoxLayout, QComboBox, QGridLayout,
                            QGroupBox, QVBoxLayout, QWidget, QDialog, QLineEdit,
                            QSizePolicy, QSpacerItem)


class ThrustPlotWindow(QDialog):
    """推力-时间曲线展示窗口"""

    def __init__(self, time_data, thrust_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle("推力-时间曲线")
        self.resize(800, 600)

        layout = QVBoxLayout(self)

        # 创建 matplotlib 画布
        self.figure = Figure(figsize=(8, 6), dpi=100)
        self.canvas = FigureCanvas(self.figure)
        self.canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # 绘制曲线
        self.plot_curve(time_data, thrust_data)

        layout.addWidget(self.canvas)

        # 添加关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)

    def plot_curve(self, time_data, thrust_data):
        """绘制推力-时间曲线"""
        ax = self.figure.add_subplot(111)
        ax.plot(time_data, thrust_data, 'b-', linewidth=2)
        ax.set_title('推力-时间曲线', fontsize=14)
        ax.set_xlabel('时间 (s)', fontsize=12)
        ax.set_ylabel('推力 (N)', fontsize=12)
        ax.grid(True, linestyle='--', alpha=0.7)

        # 设置坐标轴样式
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.tick_params(axis='both', which='major', labelsize=10)

        # 自动调整布局
        self.figure.tight_layout()
        self.canvas.draw()