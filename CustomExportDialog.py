import sys

try:
    from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget,
                                 QPushButton, QCheckBox, QLabel, QScrollArea,
                                 QWidget, QGridLayout, QGroupBox, QFrame)
    from PyQt5.QtCore import Qt

    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("PyQt5 not available, using console interface for testing")

from write_data import write_data
import numpy as np


class CustomExportDialog(QDialog):
    def __init__(self, rushui_instance, parent=None):
        self.rushui = rushui_instance
        self.parent = parent

        if GUI_AVAILABLE:
            super().__init__(parent)
            self.setWindowTitle("自定义数据导出")
            self.setGeometry(200, 200, 600, 500)
        else:
            # 如果GUI不可用，只初始化数据
            pass

        self.init_ui()

    def init_ui(self):
        if not GUI_AVAILABLE:
            # 如果GUI不可用，提供一个简单的控制台界面进行测试
            print("GUI不可用，提供控制台界面进行测试")
            self.console_export()
            return

        layout = QVBoxLayout()

        # 提示标签
        label = QLabel("请选择要导出的数据变量:")
        label.setStyleSheet("font-weight: bold; font-size: 12pt;")
        layout.addWidget(label)

        # 创建滚动区域以容纳大量变量
        scroll_area = QScrollArea()
        scroll_content = QWidget()
        self.grid_layout = QGridLayout(scroll_content)

        # 获取rushui实例的所有属性（包括嵌套属性）
        self.attributes = []
        self.checkboxes = {}

        # 获取对象的所有属性名
        self._collect_attributes(self.rushui, '')

        # 为每个属性创建复选框
        row = 0
        col = 0
        for attr_path, attr_value in self.attributes:
            checkbox = QCheckBox(attr_path)
            checkbox.setToolTip(f"类型: {type(attr_value).__name__}, 值: {str(attr_value)[:50]}...")
            self.checkboxes[attr_path] = checkbox
            self.grid_layout.addWidget(checkbox, row, col)

            # 每行放2个复选框
            col += 1
            if col >= 2:
                col = 0
                row += 1

        # 如果没有属性，显示提示
        if not self.attributes:
            label_no_attrs = QLabel("未找到可导出的属性")
            self.grid_layout.addWidget(label_no_attrs, 0, 0)

        scroll_area.setWidget(scroll_content)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # 按钮区域
        button_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("全选")
        self.select_all_btn.clicked.connect(self.select_all)
        button_layout.addWidget(self.select_all_btn)

        self.clear_all_btn = QPushButton("清空")
        self.clear_all_btn.clicked.connect(self.clear_all)
        button_layout.addWidget(self.clear_all_btn)

        self.export_btn = QPushButton("导出")
        self.export_btn.clicked.connect(self.export_selected)
        self.export_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold;")
        button_layout.addWidget(self.export_btn)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_btn)

        layout.addLayout(button_layout)
        if GUI_AVAILABLE:
            self.setLayout(layout)

    def _collect_attributes(self, obj, prefix=''):
        """递归收集对象的所有属性（包括嵌套属性）"""
        if obj is None:
            return

        for attr_name in dir(obj):
            # 忽略私有属性和方法
            if not attr_name.startswith('_') and not callable(getattr(obj, attr_name)):
                attr_value = getattr(obj, attr_name)
                attr_path = f"{prefix}.{attr_name}" if prefix else attr_name

                # 检查属性值是否是复杂对象（但不是基本数据类型）
                if self._is_complex_object(attr_value):
                    # 递归收集嵌套属性
                    self._collect_attributes(attr_value, attr_path)
                else:
                    # 添加到属性列表
                    self.attributes.append((attr_path, attr_value))

    def _is_complex_object(self, obj):
        """判断对象是否是复杂对象（需要进一步展开）"""
        if obj is None:
            return False
        # 基本数据类型不需要展开
        if isinstance(obj, (str, int, float, bool, list, tuple, np.ndarray)):
            return False
        # 检查是否是模块或其他特殊类型
        obj_type = type(obj).__name__
        if obj_type in ['module', 'function', 'builtin_function_or_method', 'type']:
            return False
        # 其他对象视为复杂对象
        return True

    def select_all(self):
        """全选所有复选框"""
        if not GUI_AVAILABLE:
            return
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(True)

    def clear_all(self):
        """清空所有复选框"""
        if not GUI_AVAILABLE:
            return
        for checkbox in self.checkboxes.values():
            checkbox.setChecked(False)

    def export_selected(self):
        """导出选中的数据"""
        if not GUI_AVAILABLE:
            return

        selected_attrs = []
        for attr_path, checkbox in self.checkboxes.items():
            if checkbox.isChecked():
                selected_attrs.append(attr_path)

        if not selected_attrs:
            # 没有选择任何项，给出提示但不关闭对话框
            from PyQt5.QtWidgets import QMessageBox
            if GUI_AVAILABLE:
                QMessageBox.warning(self, "警告", "请至少选择一个要导出的变量！")
            return

        # 打开文件并写入数据
        try:
            with open('output.txt', 'w', encoding='utf-8') as fid:
                for attr_path in selected_attrs:
                    # 通过路径获取属性值
                    attr_value = self._get_attribute_by_path(attr_path)

                    if attr_value is not None:
                        # 自动判断数据类型并选择适当的导出方式
                        data_type, format_type = self.get_data_info(attr_value)

                        # 调用write_data函数写入数据
                        write_data(fid, data_type, attr_path, format_type, attr_value)
                    else:
                        print(f"警告: 无法获取属性路径 '{attr_path}' 的值")

            from PyQt5.QtWidgets import QMessageBox
            if GUI_AVAILABLE:
                QMessageBox.information(self, "成功", f"已成功导出 {len(selected_attrs)} 个变量到 output.txt 文件!")
            self.accept()  # 关闭对话框

        except Exception as e:
            from PyQt5.QtWidgets import QMessageBox
            if GUI_AVAILABLE:
                QMessageBox.critical(self, "错误", f"导出数据时发生错误: {str(e)}")

    def _get_attribute_by_path(self, path):
        """通过路径字符串获取属性值，例如 'total.L' """
        obj = self.rushui
        attrs = path.split('.')

        for attr in attrs:
            if obj is None:
                return None
            try:
                obj = getattr(obj, attr)
            except AttributeError:
                return None
        return obj

    def get_data_info(self, data):
        """根据数据类型返回对应的write_data参数"""
        if isinstance(data, str):
            return 'single', 'STR'
        elif isinstance(data, (int, float)):
            return 'single', 'FLT'
        elif isinstance(data, (list, tuple)):
            if len(data) == 0:
                return 'single', 'FLT'
            elif all(isinstance(x, (int, float)) for x in data):
                return 'array1', 'FLT'
            else:
                return 'array1', 'STR'
        elif isinstance(data, np.ndarray):
            if data.ndim == 1:
                return 'array1', 'FLT'
            elif data.ndim == 2:
                return 'array2', 'FLT'
            else:
                return 'single', 'FLT'  # 对于高维数组，暂时作为单个值处理
        else:
            # 默认处理其他类型
            return 'single', 'FLT'

    def console_export(self):
        """控制台导出功能，用于测试"""
        print(f"找到 {len(self.attributes)} 个可导出的属性")

        # 获取前10个属性进行演示
        selected_attrs = [attr_path for attr_path, _ in self.attributes[:10]]

        print(f"将导出以下 {len(selected_attrs)} 个变量:")
        for attr_path in selected_attrs:
            attr_value = self._get_attribute_by_path(attr_path)
            print(f"  - {attr_path}: {type(attr_value).__name__}")

        # 执行导出
        try:
            with open('output.txt', 'w', encoding='utf-8') as fid:
                for attr_path in selected_attrs:
                    attr_value = self._get_attribute_by_path(attr_path)

                    if attr_value is not None:
                        # 自动判断数据类型并选择适当的导出方式
                        data_type, format_type = self.get_data_info(attr_value)

                        # 调用write_data函数写入数据
                        write_data(fid, data_type, attr_path, format_type, attr_value)
                    else:
                        print(f"警告: 无法获取属性路径 '{attr_path}' 的值")

            print(f"\n成功导出 {len(selected_attrs)} 个变量到 output.txt 文件!")

        except Exception as e:
            print(f"导出数据时发生错误: {str(e)}")

    def exec_(self):
        """执行对话框，如果GUI不可用则执行控制台导出"""
        if GUI_AVAILABLE:
            return super().exec_()
        else:
            self.console_export()
            return 1  # 模拟成功执行


if __name__ == "__main__":
    if GUI_AVAILABLE:
        from PyQt5.QtWidgets import QApplication
        from core import Dan

        app = QApplication(sys.argv)

        # 创建测试实例
        rushui_test = Dan()
        dialog = CustomExportDialog(rushui_test)
        dialog.show()

        sys.exit(app.exec_())
    else:
        # GUI不可用时的测试
        from core import Dan

        rushui_test = Dan()
        dialog = CustomExportDialog(rushui_test)
        dialog.exec_()
