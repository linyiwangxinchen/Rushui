import logging
import threading

import numpy as np
import pandas as pd
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QToolBar, QAction, QHBoxLayout, QPushButton, QFileDialog, \
    QMessageBox

from CavityVisualizationWidget import CavityVisualizationWidget
from CompactParameterDisplayWidget import CompactParameterDisplayWidget


class VisualizationWidget(QWidget):
    """结果可视化界面 """

    def __init__(self, stab_instance, parent=None):
        super().__init__(parent)
        self.stab = stab_instance
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建标签页
        self.tab_widget = QTabWidget()

        # 空泡形状视图
        self.cavity_tab = QWidget()
        cavity_layout = QVBoxLayout()
        cavity_layout.setContentsMargins(0, 0, 0, 0)
        self.cavity_visualization = CavityVisualizationWidget(self.stab)
        cavity_layout.addWidget(self.cavity_visualization)
        self.cavity_tab.setLayout(cavity_layout)

        # 轨迹视图
        trajectory_tab = QWidget()
        trajectory_layout = QVBoxLayout()
        trajectory_layout.setContentsMargins(0, 0, 0, 0)

        self.trajectory_plot = pg.PlotWidget(title="航行体轨迹")
        self.trajectory_plot.setLabel('left', 'Y (m)')
        self.trajectory_plot.setLabel('bottom', 'X (m)')
        self.trajectory_plot.showGrid(x=True, y=True, alpha=0.3)
        self.trajectory_plot.setAspectLocked(True)  # 保持纵横比一致

        # 创建轨迹数据项
        self.trajectory_data = self.trajectory_plot.plot(pen=pg.mkPen('b', width=2))

        # 添加工具栏
        self.trajectory_toolbar = QToolBar()
        self.trajectory_toolbar.setFloatable(False)
        self.trajectory_toolbar.setMovable(False)

        self.reset_trajectory_view = QAction("重置视图", self)
        self.reset_trajectory_view.triggered.connect(lambda: self.trajectory_plot.autoRange())
        self.trajectory_toolbar.addAction(self.reset_trajectory_view)

        self.export_trajectory_image = QAction("导出图像", self)
        self.export_trajectory_image.triggered.connect(lambda: self.export_plot_image(self.trajectory_plot))
        self.trajectory_toolbar.addAction(self.export_trajectory_image)

        trajectory_layout.addWidget(self.trajectory_toolbar)
        trajectory_layout.addWidget(self.trajectory_plot)
        trajectory_tab.setLayout(trajectory_layout)

        # 攻角和速度视图
        dynamics_tab = QWidget()
        dynamics_layout = QVBoxLayout()
        dynamics_layout.setContentsMargins(0, 0, 0, 0)

        # 创建GraphicsLayout用于多子图
        self.dynamics_layout_widget = pg.GraphicsLayoutWidget()

        # 创建两个子图
        self.alpha_plot = self.dynamics_layout_widget.addPlot(row=0, col=0, title="攻角 Alpha")
        self.alpha_plot.setLabel('left', '攻角 Alpha (°)')
        self.alpha_plot.setLabel('bottom', 'X (m)')
        self.alpha_plot.showGrid(x=True, y=True, alpha=0.3)
        self.alpha_data = self.alpha_plot.plot(pen=pg.mkPen('r', width=2))

        self.velocity_plot = self.dynamics_layout_widget.addPlot(row=1, col=0, title="速度 V")
        self.velocity_plot.setLabel('left', '速度 V (m/s)')
        self.velocity_plot.setLabel('bottom', 'X (m)')
        self.velocity_plot.showGrid(x=True, y=True, alpha=0.3)
        self.velocity_data = self.velocity_plot.plot(pen=pg.mkPen('g', width=2))

        # 添加工具栏
        self.dynamics_toolbar = QToolBar()
        self.dynamics_toolbar.setFloatable(False)
        self.dynamics_toolbar.setMovable(False)

        self.reset_dynamics_view = QAction("重置视图", self)
        self.reset_dynamics_view.triggered.connect(lambda: self.dynamics_layout_widget.autoRange())
        self.dynamics_toolbar.addAction(self.reset_dynamics_view)

        self.export_dynamics_image = QAction("导出图像", self)
        self.export_dynamics_image.triggered.connect(lambda: self.export_plot_image(self.dynamics_layout_widget))
        self.dynamics_toolbar.addAction(self.export_dynamics_image)

        dynamics_layout.addWidget(self.dynamics_toolbar)
        dynamics_layout.addWidget(self.dynamics_layout_widget)
        dynamics_tab.setLayout(dynamics_layout)

        # 添加标签页
        self.tab_widget.addTab(self.cavity_tab, "空泡形状")
        # self.tab_widget.addTab(trajectory_tab, "轨迹")
        # self.tab_widget.addTab(dynamics_tab, "动力学参数")

        # 实时参数显示
        self.param_display = CompactParameterDisplayWidget(self.stab)

        # 控制按钮
        button_layout = QHBoxLayout()
        self.update_button = QPushButton("更新视图")
        self.update_button.clicked.connect(self.update_plots)
        self.export_button = QPushButton("导出数据")
        self.export_button.clicked.connect(self.export_data)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.export_button)

        # 组合布局
        main_layout.addWidget(self.param_display)
        main_layout.addWidget(self.tab_widget, 1)
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)

    def export_plot_image(self, plot_widget):
        """导出指定绘图部件的图像"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存图像", "", "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
            )
            if filename:
                if isinstance(plot_widget, pg.PlotWidget):
                    exporter = pg.exporters.ImageExporter(plot_widget.plotItem)
                elif isinstance(plot_widget, pg.GraphicsLayoutWidget):
                    exporter = pg.exporters.ImageExporter(plot_widget.scene())
                else:
                    QMessageBox.warning(self, "警告", "不支持的绘图部件类型")
                    return

                exporter.export(filename)
                QMessageBox.information(self, "导出成功", f"图像已保存至 {filename}")
        except Exception as e:
            logging.error(f"导出图像失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"导出图像失败: {str(e)}")

    def update_plots(self):
        """更新所有图表"""
        try:
            # 获取结果

            self.trajectory_data.setData([], [])
            self.trajectory_plot.autoRange()

            self.alpha_data.setData([], [])
            self.alpha_plot.autoRange()

            # 速度
            self.velocity_data.setData([], [])
            self.velocity_plot.autoRange()

            logging.info("图表已更新")
        except Exception as e:
            logging.exception("更新图表时出错")
            QMessageBox.warning(self, "警告", f"更新图表失败: {str(e)}")

    def export_data(self):
        """导出数据"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "导出数据", "", "CSV Files (*.csv);;Excel Files (*.xlsx);;All Files (*)"
            )
            if filename:
                results = self.stab.get_results()
                df = pd.DataFrame({
                    'x_m': results['x'],
                    'y_m': results['y'],
                    'psi_rad': results['psi'],
                    'alpha_rad': results['alpha'][:len(results['x'])],
                    'V_m_s': results['V'][:len(results['x'])],
                    't_s': results['t'][:len(results['x'])],
                    'SG': results['SG'][:len(results['x'])],
                })
                if filename.endswith('.csv'):
                    df.to_csv(filename, index=False)
                elif filename.endswith('.xlsx'):
                    df.to_excel(filename, index=False)
                QMessageBox.information(self, "导出成功", f"数据已导出至 {filename}")
                logging.info(f"数据已导出至 {filename}")
        except Exception as e:
            logging.exception("导出数据时出错")
            QMessageBox.critical(self, "错误", f"导出失败: {str(e)}")

    def handle_realtime_update(self, data):
        """处理实时更新数据"""
        try:
            # 更新参数显示
            self.param_display.update_parameters(data)
            # self.thread_update_parameters(data)

            # 更新空泡形状
            self.cavity_visualization.update_plot(data)
            # self.thread_update_plot(data)
            # QTimer.singleShot(0, lambda: self.param_display.update_parameters(data))
            # QTimer.singleShot(0, lambda: self.cavity_visualization.update_plot(data))

        except Exception as e:
            logging.exception("处理实时更新数据时出错")

    def handle_realtime_update1(self, data):
        """处理实时更新数据"""
        try:
            # 更新参数显示
            self.param_display.update_parameters(data)
            # self.thread_update_parameters(data)

            # 更新空泡形状
            self.cavity_visualization.update_plot(data)
            # self.thread_update_plot(data)
            # QTimer.singleShot(0, lambda: self.param_display.update_parameters(data))
            # QTimer.singleShot(0, lambda: self.cavity_visualization.update_plot(data))

        except Exception as e:
            logging.exception("处理实时更新数据时出错")

    def thread_update_plot(self, data):  # fun是一个函数  args是一组参数对象
        '''将函数打包进线程'''
        t = threading.Thread(target=self.cavity_visualization.update_plot, args=[data], daemon=True)  # target接受函数对象  arg接受参数  线程会把这个参数传递给func这个函数
        t.start()  # 启动线程

    def thread_update_parameters(self, data):  # fun是一个函数  args是一组参数对象
        '''将函数打包进线程'''
        t = threading.Thread(target=self.param_display.update_parameters, args=[data], daemon=True)  # target接受函数对象  arg接受参数  线程会把这个参数传递给func这个函数
        t.start()  # 启动线程

