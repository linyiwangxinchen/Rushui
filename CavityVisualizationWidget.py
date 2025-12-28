import logging
import threading
import time

import numpy as np
import pyqtgraph as pg
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QToolBar, QAction, QFileDialog, QMessageBox


class CavityVisualizationWidget(QWidget):
    """空泡形状实时可视化"""

    def __init__(self, stab_instance, parent=None):
        super().__init__(parent)

        self.stab = stab_instance
        self.last_update_time = 0
        self.update_interval = 0.05  # 最小更新间隔（秒）
        self.FirstPlot = True
        self.SecondPlot = True
        self.plot_mutex = threading.Lock()
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 创建PyQtGraph绘图部件
        # pg.setConfigOption('background', '#FFFFFF')
        pg.setConfigOption('background', '#FFFFFF')
        pg.setConfigOption('foreground', 'k')
        self.plot_widget = pg.PlotWidget(title="实时空泡形状")

        self.plot_widget.setLabel('left', 'Y (m)')
        self.plot_widget.setLabel('bottom', 'X (m)')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        self.plot_widget.setAspectLocked(True)  # 保持纵横比一致

        # 创建工具栏
        self.toolbar = QToolBar()
        self.toolbar.setFloatable(False)
        self.toolbar.setMovable(False)

        # 添加工具按钮
        self.reset_view_action = QAction("重置视图", self)
        self.reset_view_action.triggered.connect(self.reset_view)
        self.toolbar.addAction(self.reset_view_action)

        self.export_action = QAction("导出图像", self)
        self.export_action.triggered.connect(self.export_image)
        self.toolbar.addAction(self.export_action)

        # 添加图例
        self.legend = self.plot_widget.addLegend()

        # 创建绘图项
        # 绘制弹体轮廓
        # plt.plot(posb[0, :], posb[1, :], 'b-', linewidth=2, label='Body')
        # 绘制空泡轴线
        # plt.plot(cav0[:, 0], cav0[:, 1], 'k-', linewidth=1, label='Cavity Axis')
        # 绘制空泡轮廓（上半部分）
        # plt.plot(cav1[:, 0], cav1[:, 1], 'r--', linewidth=1, label='Upper Cavity')
        # 绘制空泡轮廓（下半部分）
        # plt.plot(cav2[:, 0], cav2[:, 1], 'r--', linewidth=1, label='Lower Cavity')
        self.model_plot = self.plot_widget.plot(pen=pg.mkPen('b', width=3), name='模型')
        self.pass_plot = self.plot_widget.plot(pen=pg.mkPen('k', width=3), name='轨迹')
        self.upper_cavity_plot = self.plot_widget.plot(pen=pg.mkPen('r', width=2, style=pg.QtCore.Qt.DashLine), name='上边界')
        self.lower_cavity_plot = self.plot_widget.plot(pen=pg.mkPen('r', width=2, style=pg.QtCore.Qt.DashLine), name='下边界')

        main_layout.addWidget(self.toolbar)
        main_layout.addWidget(self.plot_widget)
        self.setLayout(main_layout)
        self.update_plot()

    def reset_view(self):
        """重置视图范围"""
        if hasattr(self.stab, 'Lm') and hasattr(self.stab, 'Scale'):
            scale = getattr(self.stab, 'Scale', 1.0)
            self.plot_widget.setXRange(-0.1 * scale * self.stab.Lm, 1.1 * scale * self.stab.Lm)
            self.plot_widget.setYRange(-0.2 * scale * self.stab.Lm, 0.2 * scale * self.stab.Lm)

    def export_image(self):
        """导出图像"""
        try:
            filename, _ = QFileDialog.getSaveFileName(
                self, "保存图像", "", "PNG Files (*.png);;JPEG Files (*.jpg);;All Files (*)"
            )
            if filename:
                exporter = pg.exporters.ImageExporter(self.plot_widget.plotItem)
                exporter.export(filename)
                QMessageBox.information(self, "导出成功", f"图像已保存至 {filename}")
        except Exception as e:
            logging.error(f"导出图像失败: {str(e)}")
            QMessageBox.critical(self, "错误", f"导出图像失败: {str(e)}")

    def first_plot(self, data):
        """首次绘制"""
        with self.plot_mutex:
            try:
                plot_dan_x = data['points']['plot_dan_x']
                plot_dan_y = data['points']['plot_dan_y']
                plot_zhou_x = data['points']['plot_zhou_x']
                plot_zhou_y = data['points']['plot_zhou_y']
                plot_pao_up_x = data['points']['plot_pao_up_x']
                plot_pao_up_y = data['points']['plot_pao_up_y']
                plot_pao_down_x = data['points']['plot_pao_down_x']
                plot_pao_down_y = data['points']['plot_pao_down_y']
                # 绘制模型主体
                self.model_plot.setData(plot_dan_x, plot_dan_y)
                self.pass_plot.setData(plot_zhou_x, plot_zhou_y)
                self.upper_cavity_plot.setData(plot_pao_up_x, plot_pao_up_y)
                self.lower_cavity_plot.setData(plot_pao_down_x, plot_pao_down_y)

                self.plot_widget.setXRange(-3, 3)
                self.plot_widget.setYRange(-0.5, 0.5)
            except:
                None


    def update_plot(self, data=None):
        """更新空泡形状图"""
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval:
            return

        if self.FirstPlot:
            self.first_plot(data)
            self.FirstPlot = False
            return
        else:
            if self.SecondPlot:
                self.first_plot(data)
                self.SecondPlot = False
                return

        try:
            plot_dan_x = data['points']['plot_dan_x']
            plot_dan_y = data['points']['plot_dan_y']
            plot_zhou_x = data['points']['plot_zhou_x']
            plot_zhou_y = data['points']['plot_zhou_y']
            plot_pao_up_x = data['points']['plot_pao_up_x']
            plot_pao_up_y = data['points']['plot_pao_up_y']
            plot_pao_down_x = data['points']['plot_pao_down_x']
            plot_pao_down_y = data['points']['plot_pao_down_y']
            # 绘制模型主体
            self.model_plot.setData(plot_dan_x, plot_dan_y)
            self.pass_plot.setData(plot_zhou_x, plot_zhou_y)
            self.upper_cavity_plot.setData(plot_pao_up_x, plot_pao_up_y)
            self.lower_cavity_plot.setData(plot_pao_down_x, plot_pao_down_y)

        except Exception as e:
            logging.exception("更新空泡形状图时出错")
            # 显示错误信息
            # text_item = pg.TextItem(f"错误: {str(e)}", anchor=(0.5, 0.5), color=(255, 0, 0))
            # self.plot_widget.addItem(text_item)
            # text_item.setPos(0.5, 0.5)

        self.last_update_time = current_time
