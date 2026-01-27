import sys
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QPushButton, QApplication
from PyQt5.QtCore import pyqtSignal


class MinCallbackIntervalDialog(QDialog):
    """用于设置min_callback_interval参数的对话框"""

    interval_changed = pyqtSignal(float)  # 信号，当参数改变时发出

    def __init__(self, current_interval=0.05, parent=None):
        super().__init__(parent)
        self.current_interval = current_interval
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("设置界面更新时间差")
        self.setFixedSize(350, 120)

        layout = QVBoxLayout()

        # 参数输入布局
        param_layout = QHBoxLayout()
        param_layout.addWidget(QLabel("界面更新时间差 (秒):"))

        self.interval_spinbox = QDoubleSpinBox()
        self.interval_spinbox.setRange(0.001, 1.0)  # 设置范围：0.001秒到1秒
        self.interval_spinbox.setSingleStep(0.001)   # 步长为0.001
        self.interval_spinbox.setDecimals(3)         # 显示3位小数
        self.interval_spinbox.setValue(self.current_interval)

        param_layout.addWidget(self.interval_spinbox)
        layout.addLayout(param_layout)

        # 按钮布局
        button_layout = QHBoxLayout()

        ok_button = QPushButton("确定")
        ok_button.clicked.connect(self.accept)

        cancel_button = QPushButton("取消")
        cancel_button.clicked.connect(self.reject)

        button_layout.addWidget(ok_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_interval(self):
        """获取设置的时间间隔值"""
        return self.interval_spinbox.value()

    def accept(self):
        """确认按钮点击事件"""
        interval = self.get_interval()
        self.interval_changed.emit(interval)
        super().accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = MinCallbackIntervalDialog(current_interval=0.05)
    if dialog.exec_() == QDialog.Accepted:
        print(f"设置的时间间隔: {dialog.get_interval()}")
    else:
        print("取消设置")