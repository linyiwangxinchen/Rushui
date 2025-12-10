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
        self.model_plot = self.plot_widget.plot(pen=pg.mkPen('r', width=3), name='模型')
        self.upper_cavity_plot = self.plot_widget.plot(pen=pg.mkPen('b', width=2), name='上边界')
        self.lower_cavity_plot = self.plot_widget.plot(pen=pg.mkPen('b', width=2), name='下边界')

        self.water_plot = self.plot_widget.plot(pen=pg.mkPen('b', width=2), name='水面')

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

    def first_plot(self):
        """首次绘制"""
        with self.plot_mutex:
            try:
                if self.stab.FlagDive:
                    # 重置数据
                    self.upper_cavity_plot.setData([], [])
                    self.lower_cavity_plot.setData([], [])
                    self.model_plot.setData([], [])
                    # === 计算旋转角度 ===
                    gamma_rad = np.deg2rad(self.stab.GammaDive)  # 入水角度转为弧度
                    cos_g = np.cos(gamma_rad)
                    sin_g = np.sin(gamma_rad)

                    # 计算初始偏移
                    xs0 = -self.stab.Rn * cos_g ** 2 / sin_g if abs(sin_g) > 1e-10 else 0
                    ys0 = self.stab.Rn * cos_g
                    self.stab.xs0 = xs0
                    self.stab.ys0 = ys0
                    self.stab.COS_G = cos_g
                    self.stab.SIN_G = sin_g

                    # 设置全局变量
                    self.stab.GammaRad = gamma_rad

                    # 旋转模型
                    self.stab.TurnModelOnGamma(gamma_rad)

                    # 应用位移
                    xs2, ys2 = self.stab.TurnPointOnGamma(self.stab.xs1, self.stab.Yabs)
                    xs2 = xs2 - xs0
                    ys2 = ys2 - ys0
                    if not hasattr(self.stab, 'xc0'):
                        # 加入绘图记录初始位置，方便后面那些东东转移，可能用不到
                        self.stab.xc0, self.stab.yc0 = self.stab.TurnPointOnGamma(-self.stab.Xabs, self.stab.Yabs)

                    xc, yc = self.stab.TurnPointOnGamma(-self.stab.Xabs, self.stab.Yabs)

                    # === 绘制模型 ===
                    model_points = np.column_stack((
                        xs2 + self.stab.XGmod - xc,
                        ys2 + self.stab.YGmod - yc
                    ))

                    # 绘制模型主体
                    self.model_plot.setData(model_points[:, 0] * self.stab.Lm, model_points[:, 1] * self.stab.Lm)

                    # === 绘制质心 ===
                    xc, yc = self.stab.TurnPointOnGamma(-self.stab.Xabs, self.stab.Yabs)

                    # === 重构的空腔轮廓绘制 - 修复连接问题 ===
                    cavity_color = 'blue'
                    cavity_linewidth = 1.5
                    x = 0
                    # 主要修复：增强空腔轮廓生成
                    if hasattr(self.stab, 'Xpr') and hasattr(self.stab, 'Ypr1') and hasattr(self.stab,
                                                                                            'Ypr2') and hasattr(
                        self.stab, 'Ipr'):
                        # 1. 上部空腔轮廓
                        iup = 3
                        if ys2 + self.stab.YGmod[1] < 0:  # 上分离点在水下
                            # 起始点（上分离点）
                            cavity_points_upper = [(xs2 + self.stab.XGmod[1], ys2 + self.stab.YGmod[1])]

                            # 检查是否有足够的点进行处理
                            if hasattr(self.stab, 'XcBeg') and len(self.stab.XcBeg) >= 4:
                                # 处理前几个特殊点
                                xpr_val = self.stab.Xpr[1]  # Fortran索引2

                                if xpr_val < self.stab.XcBeg[1]:  # XcBeg(2)
                                    RcBegX = self.stab.Rn * (1.0 + 3.0 * xpr_val / self.stab.Rn) ** (1.0 / 3.0)
                                    xt, yt = self.stab.TurnPointOnGamma(xpr_val,
                                                                        RcBegX + self.stab.Yax0[self.stab.Jend])
                                    if ys2 + yt <= 0:
                                        cavity_points_upper.append((xs2 + xt, ys2 + yt))

                                elif xpr_val < self.stab.XcBeg[2]:  # XcBeg(3)
                                    xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[1],
                                                                        self.stab.RcBeg[1] + self.stab.Yax0[
                                                                            self.stab.Jend])
                                    if ys2 + yt <= 0:
                                        cavity_points_upper.append((xs2 + xt, ys2 + yt))
                                    RcBegX = self.stab.Rn * (1.0 + 3.0 * xpr_val / self.stab.Rn) ** (1.0 / 3.0)
                                    xt, yt = self.stab.TurnPointOnGamma(xpr_val,
                                                                        RcBegX + self.stab.Yax0[self.stab.Jend])
                                    if ys2 + yt <= 0:
                                        cavity_points_upper.append((xs2 + xt, ys2 + yt))

                                elif xpr_val < self.stab.XcBeg[3]:  # XcBeg(4)
                                    xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[1],
                                                                        self.stab.RcBeg[1] + self.stab.Yax0[
                                                                            self.stab.Jend])
                                    if ys2 + yt + self.stab.RcBeg[1] <= 0:
                                        cavity_points_upper.append((xs2 + xt, ys2 + yt))
                                    xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[2],
                                                                        self.stab.RcBeg[2] + self.stab.Yax0[
                                                                            self.stab.Jend])
                                    if ys2 + yt <= 0:
                                        cavity_points_upper.append((xs2 + xt, ys2 + yt))
                                    RcBegX = self.stab.Rn * (1.0 + 3.0 * xpr_val / self.stab.Rn) ** (1.0 / 3.0)
                                    xt, yt = self.stab.TurnPointOnGamma(xpr_val,
                                                                        RcBegX + self.stab.Yax0[self.stab.Jend])
                                    if ys2 + yt <= 0:
                                        cavity_points_upper.append((xs2 + xt, ys2 + yt))

                                else:
                                    xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[1],
                                                                        self.stab.RcBeg[1] + self.stab.Yax0[
                                                                            self.stab.Jend])
                                    if ys2 + yt <= 0:
                                        cavity_points_upper.append((xs2 + xt, ys2 + yt))
                                    xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[2],
                                                                        self.stab.RcBeg[2] + self.stab.Yax0[
                                                                            self.stab.Jend])
                                    if ys2 + yt <= 0:
                                        cavity_points_upper.append((xs2 + xt, ys2 + yt))
                                    xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[3],
                                                                        self.stab.RcBeg[3] + self.stab.Yax0[
                                                                            self.stab.Jend])
                                    if ys2 + yt <= 0:
                                        cavity_points_upper.append((xs2 + xt, ys2 + yt))
                                    xt, yt = self.stab.TurnPointOnGamma(xpr_val, self.stab.Ypr2[1])
                                    if ys2 + yt <= 0:
                                        cavity_points_upper.append((xs2 + xt, ys2 + yt))

                            for i in range(3, self.stab.Ipr + 2):
                                idx = i - 1  # Fortran to Python索引

                                if idx >= len(self.stab.Xpr):
                                    break

                                # 根据x的位置选择正确的y值
                                if hasattr(self.stab, 'XcBeg') and len(self.stab.XcBeg) >= 4:
                                    if self.stab.Xpr[idx] < self.stab.XcBeg[1]:  # XcBeg(2)
                                        RcBegX = self.stab.Rn * (1.0 + 3.0 * self.stab.Xpr[idx] / self.stab.Rn) ** (
                                                1.0 / 3.0)
                                        xt, yt = self.stab.TurnPointOnGamma(self.stab.Xpr[idx],
                                                                            RcBegX + self.stab.Yax0[self.stab.Jend])
                                        if ys2 + yt <= 0:
                                            cavity_points_upper.append((xs2 + xt, ys2 + yt))

                                    elif self.stab.Xpr[idx] < self.stab.XcBeg[2]:  # XcBeg(3)
                                        RcBegX = self.stab.Rn * (1.0 + 3.0 * self.stab.Xpr[idx] / self.stab.Rn) ** (
                                                1.0 / 3.0)
                                        xt, yt = self.stab.TurnPointOnGamma(x, RcBegX + self.stab.Yax0[self.stab.Jend])
                                        if ys2 + yt <= 0:
                                            cavity_points_upper.append((xs2 + xt, ys2 + yt))

                                    elif self.stab.Xpr[idx] < self.stab.XcBeg[3]:  # XcBeg(4)
                                        RcBegX = self.stab.Rn * (1.0 + 3.0 * self.stab.Xpr[idx] / self.stab.Rn) ** (
                                                1.0 / 3.0)
                                        xt, yt = self.stab.TurnPointOnGamma(x, RcBegX + self.stab.Yax0[self.stab.Jend])
                                        if ys2 + yt <= 0:
                                            cavity_points_upper.append((xs2 + xt, ys2 + yt))

                                    elif self.stab.Rcav[self.stab.Jend, idx] != 0:
                                        xt, yt = self.stab.TurnPointOnGamma(self.stab.Xpr[idx - 1],
                                                                            self.stab.Ypr2[idx - 1])
                                        if ys2 + yt <= 0:
                                            cavity_points_upper.append((xs2 + xt, ys2 + yt))
                                        xt, yt = self.stab.TurnPointOnGamma(self.stab.Xpr[idx], self.stab.Ypr2[idx])
                                        if ys2 + yt <= 0:
                                            cavity_points_upper.append((xs2 + xt, ys2 + yt))
                                    else:
                                        a = 1
                                    if ys2 + yt > 0:
                                        iup = i
                                        break

                            if self.stab.Ipr > 2:
                                x = self.stab.Xpr[iup - 2]
                                while True:
                                    x = x + 0.001
                                    y = self.stab.ExtraUpperCav(x)
                                    xt, yt = self.stab.TurnPointOnGamma(x, y)
                                    if ys2 + yt >= 0:
                                        cavity_points_upper.append((xs2 + xt, ys2 + yt))
                                        break

                            # 4. 绘制上部空腔轮廓
                            if len(cavity_points_upper) > 1:
                                # # 再次去重并排序
                                # cavity_points_upper = self.stab.remove_duplicate_points(cavity_points_upper)
                                #
                                # # 确保点按x顺序排列
                                # cavity_points_upper.sort(key=lambda p: p[0])

                                upper_x, upper_y = zip(*cavity_points_upper)
                                upper_x = np.array(upper_x) - xc
                                upper_y = np.array(upper_y) - yc
                                self.upper_cavity_plot.setData(upper_x * self.stab.Lm, upper_y * self.stab.Lm)

                        # 5. 修复下部空腔轮廓
                        lower_sep_idx = 2 * self.stab.Ncon + 3 - 1  # Fortran索引 2*Ncon+3 -> Python索引 2*Ncon+2
                        if lower_sep_idx < len(self.stab.XGmod) and lower_sep_idx < len(self.stab.YGmod):
                            cavity_points_lower = [
                                (xs2 + self.stab.XGmod[lower_sep_idx], ys2 + self.stab.YGmod[lower_sep_idx])]

                            # 处理前几个特殊点
                            if hasattr(self.stab, 'XcBeg') and len(self.stab.XcBeg) >= 4:
                                xpr_val = self.stab.Xpr[1]  # Fortran索引2

                                if xpr_val < self.stab.XcBeg[1]:  # XcBeg(2)
                                    RcBegX = self.stab.Rn * (1.0 + 3.0 * xpr_val / self.stab.Rn) ** (1.0 / 3.0)
                                    xt, yt = self.stab.TurnPointOnGamma(xpr_val,
                                                                        -RcBegX + self.stab.Yax0[self.stab.Jend])
                                    cavity_points_lower.append((xs2 + xt, ys2 + yt))

                                elif xpr_val < self.stab.XcBeg[2]:  # XcBeg(3)
                                    xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[1],
                                                                        -self.stab.RcBeg[1] + self.stab.Yax0[
                                                                            self.stab.Jend])
                                    cavity_points_lower.append((xs2 + xt, ys2 + yt))
                                    RcBegX = self.stab.Rn * (1.0 + 3.0 * xpr_val / self.stab.Rn) ** (1.0 / 3.0)
                                    xt, yt = self.stab.TurnPointOnGamma(xpr_val,
                                                                        -RcBegX + self.stab.Yax0[self.stab.Jend])
                                    cavity_points_lower.append((xs2 + xt, ys2 + yt))

                                elif xpr_val < self.stab.XcBeg[3]:  # XcBeg(4)
                                    xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[1],
                                                                        -self.stab.RcBeg[1] + self.stab.Yax0[
                                                                            self.stab.Jend])
                                    cavity_points_lower.append((xs2 + xt, ys2 + yt))
                                    xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[2],
                                                                        -self.stab.RcBeg[2] + self.stab.Yax0[
                                                                            self.stab.Jend])
                                    cavity_points_lower.append((xs2 + xt, ys2 + yt))
                                    RcBegX = self.stab.Rn * (1.0 + 3.0 * xpr_val / self.stab.Rn) ** (1.0 / 3.0)
                                    xt, yt = self.stab.TurnPointOnGamma(xpr_val,
                                                                        -RcBegX + self.stab.Yax0[self.stab.Jend])
                                    cavity_points_lower.append((xs2 + xt, ys2 + yt))

                                else:
                                    # 添加所有过渡点
                                    xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[1],
                                                                        -self.stab.RcBeg[1] + self.stab.Yax0[
                                                                            self.stab.Jend])
                                    cavity_points_lower.append((xs2 + xt, ys2 + yt))
                                    xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[2],
                                                                        -self.stab.RcBeg[2] + self.stab.Yax0[
                                                                            self.stab.Jend])
                                    cavity_points_lower.append((xs2 + xt, ys2 + yt))
                                    xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[3],
                                                                        -self.stab.RcBeg[3] + self.stab.Yax0[
                                                                            self.stab.Jend])
                                    cavity_points_lower.append((xs2 + xt, ys2 + yt))
                                    xt, yt = self.stab.TurnPointOnGamma(xpr_val, self.stab.Ypr1[1])
                                    cavity_points_lower.append((xs2 + xt, ys2 + yt))

                            # 处理主体点
                            for i in range(3, self.stab.Ipr + 2):
                                idx = i - 1  # Fortran to Python索引

                                if idx >= len(self.stab.Xpr):
                                    break

                                x = self.stab.Xpr[idx]

                                if hasattr(self.stab, 'XcBeg'):
                                    if x < self.stab.XcBeg[1]:  # XcBeg(2)
                                        RcBegX = self.stab.Rn * (1.0 + 3.0 * x / self.stab.Rn) ** (1.0 / 3.0)
                                        xt, yt = self.stab.TurnPointOnGamma(x, -RcBegX + self.stab.Yax0[self.stab.Jend])
                                        cavity_points_lower.append((xs2 + xt, ys2 + yt))

                                    elif x < self.stab.XcBeg[2]:  # XcBeg(3)
                                        RcBegX = self.stab.Rn * (1.0 + 3.0 * x / self.stab.Rn) ** (1.0 / 3.0)
                                        xt, yt = self.stab.TurnPointOnGamma(x, -RcBegX + self.stab.Yax0[self.stab.Jend])
                                        cavity_points_lower.append((xs2 + xt, ys2 + yt))

                                    elif x < self.stab.XcBeg[3]:  # XcBeg(4)
                                        RcBegX = self.stab.Rn * (1.0 + 3.0 * x / self.stab.Rn) ** (1.0 / 3.0)
                                        xt, yt = self.stab.TurnPointOnGamma(x, -RcBegX + self.stab.Yax0[self.stab.Jend])
                                        cavity_points_lower.append((xs2 + xt, ys2 + yt))

                                    elif self.stab.Rcav[self.stab.Jend, idx] != 0:
                                        xt, yt = self.stab.TurnPointOnGamma(self.stab.Xpr[idx - 1],
                                                                            self.stab.Ypr1[idx - 1])
                                        cavity_points_lower.append((xs2 + xt, ys2 + yt))
                                        xt, yt = self.stab.TurnPointOnGamma(self.stab.Xpr[idx], self.stab.Ypr1[idx])
                                        cavity_points_lower.append((xs2 + xt, ys2 + yt))

                            if self.stab.Ipr > 2:
                                x = self.stab.Xpr[self.stab.Ipr]
                                while True:
                                    x = x + 0.001
                                    y = self.stab.ExtraLowerCav(x)
                                    xt, yt = self.stab.TurnPointOnGamma(x, y)
                                    if ys2 + yt >= 0:
                                        cavity_points_lower.append((xs2 + xt, ys2 + yt))
                                        break

                            # 7. 绘制下部空腔轮廓
                            if len(cavity_points_lower) > 1:
                                # # 去重并排序
                                # cavity_points_lower = self.stab.remove_duplicate_points(cavity_points_lower)
                                #
                                # # 确保点按x顺序排列
                                # cavity_points_lower.sort(key=lambda p: p[0])

                                lower_x, lower_y = zip(*cavity_points_lower)
                                lower_x = np.array(lower_x) - xc
                                lower_y = np.array(lower_y) - yc

                                self.lower_cavity_plot.setData(lower_x * self.stab.Lm, lower_y * self.stab.Lm)

                else:
                    # 重置数据
                    self.upper_cavity_plot.setData([], [])
                    self.lower_cavity_plot.setData([], [])
                    self.model_plot.setData([], [])

                    # 如果有实时数据，使用实时数据
                    if hasattr(self.stab, 'FlagCav') and self.stab.FlagCav:
                        if hasattr(self.stab, 'Xpr') and hasattr(self.stab, 'Ypr1') and hasattr(self.stab, 'Ypr2'):
                            # === 绘制空腔轮廓 ===
                            if hasattr(self.stab, 'FlagCav') and self.stab.FlagCav and not self.stab.FlagFirst:
                                # 修正：获取当前空泡轴线的y偏移
                                current_Yax0 = self.stab.Yax0[self.stab.Jend] if hasattr(self.stab, 'Yax0') else 0.0

                                # --- 上部空腔轮廓 ---
                                if len(self.stab.Xmod) > 1 and len(self.stab.Ymod) > 1:
                                    upper_x = [self.stab.Xmod[1]]  # 上分离点x
                                    upper_y = [self.stab.Ymod[1]]  # 上分离点y

                                    # 计算并添加其他点
                                    for i in range(2, self.stab.Ipr + 1):
                                        if i - 1 < len(self.stab.Xpr):
                                            x_point = self.stab.Xpr[i - 1]
                                            if x_point < self.stab.XcBeg[1]:  # 区域1
                                                RcBegX = self.stab.Rn * (1.0 + 3.0 * x_point / self.stab.Rn) ** (1 / 3)
                                                y_point = RcBegX + current_Yax0
                                            elif x_point < self.stab.XcBeg[2]:  # 区域2
                                                if i == 2:  # 第一个点需要特殊处理
                                                    RcBegX1 = self.stab.Rn * (
                                                            1.0 + 3.0 * self.stab.XcBeg[1] / self.stab.Rn) ** (1 / 3)
                                                    upper_x.append(self.stab.XcBeg[1])
                                                    upper_y.append(RcBegX1 + current_Yax0)
                                                RcBegX = self.stab.Rn * (1.0 + 3.0 * x_point / self.stab.Rn) ** (1 / 3)
                                                y_point = RcBegX + current_Yax0
                                            elif x_point < self.stab.XcBeg[3]:  # 区域3
                                                if i == 2:  # 第一个点需要特殊处理
                                                    RcBegX1 = self.stab.Rn * (
                                                            1.0 + 3.0 * self.stab.XcBeg[1] / self.stab.Rn) ** (1 / 3)
                                                    RcBegX2 = self.stab.Rn * (
                                                            1.0 + 3.0 * self.stab.XcBeg[2] / self.stab.Rn) ** (1 / 3)
                                                    upper_x.append(self.stab.XcBeg[1])
                                                    upper_y.append(RcBegX1 + current_Yax0)
                                                    upper_x.append(self.stab.XcBeg[2])
                                                    upper_y.append(RcBegX2 + current_Yax0)
                                                RcBegX = self.stab.Rn * (1.0 + 3.0 * x_point / self.stab.Rn) ** (1 / 3)
                                                y_point = RcBegX + current_Yax0
                                            else:  # 区域4
                                                if i == 2:  # 第一个点需要特殊处理
                                                    upper_x.append(self.stab.XcBeg[1])
                                                    upper_y.append(self.stab.RcBeg[1] + current_Yax0)
                                                    upper_x.append(self.stab.XcBeg[2])
                                                    upper_y.append(self.stab.RcBeg[2] + current_Yax0)
                                                    upper_x.append(self.stab.XcBeg[3])
                                                    upper_y.append(self.stab.RcBeg[3] + current_Yax0)
                                                if hasattr(self.stab, 'Ypr2') and i - 1 < len(self.stab.Ypr2):
                                                    y_point = self.stab.Ypr2[i - 1]
                                                else:
                                                    y_point = 0.0
                                            upper_x.append(x_point)
                                            upper_y.append(y_point)

                                    # 设置上部空腔轮廓数据
                                    upper_x = np.array(upper_x) * self.stab.Lm
                                    upper_y = np.array(upper_y) * self.stab.Lm
                                    self.upper_cavity_plot.setData(upper_x, upper_y)

                                # --- 下部空腔轮廓 ---
                                if len(self.stab.Xmod) > 2 * self.stab.Ncon + 2 and len(
                                        self.stab.Ymod) > 2 * self.stab.Ncon + 2:
                                    lower_x = [self.stab.Xmod[2 * self.stab.Ncon + 2]]  # 下分离点x
                                    lower_y = [self.stab.Ymod[2 * self.stab.Ncon + 2]]  # 下分离点y

                                    # 计算并添加其他点
                                    for i in range(2, self.stab.Ipr + 1):
                                        if i - 1 < len(self.stab.Xpr):
                                            x_point = self.stab.Xpr[i - 1]
                                            if x_point < self.stab.XcBeg[1]:  # 区域1
                                                RcBegX = self.stab.Rn * (1.0 + 3.0 * x_point / self.stab.Rn) ** (1 / 3)
                                                y_point = -RcBegX + current_Yax0
                                            elif x_point < self.stab.XcBeg[2]:  # 区域2
                                                if i == 2:  # 第一个点需要特殊处理
                                                    RcBegX1 = self.stab.Rn * (
                                                            1.0 + 3.0 * self.stab.XcBeg[1] / self.stab.Rn) ** (1 / 3)
                                                    lower_x.append(self.stab.XcBeg[1])
                                                    lower_y.append(-RcBegX1 + current_Yax0)
                                                RcBegX = self.stab.Rn * (1.0 + 3.0 * x_point / self.stab.Rn) ** (1 / 3)
                                                y_point = -RcBegX + current_Yax0
                                            elif x_point < self.stab.XcBeg[3]:  # 区域3
                                                if i == 2:  # 第一个点需要特殊处理
                                                    RcBegX1 = self.stab.Rn * (
                                                            1.0 + 3.0 * self.stab.XcBeg[1] / self.stab.Rn) ** (1 / 3)
                                                    RcBegX2 = self.stab.Rn * (
                                                            1.0 + 3.0 * self.stab.XcBeg[2] / self.stab.Rn) ** (1 / 3)
                                                    lower_x.append(self.stab.XcBeg[1])
                                                    lower_y.append(-RcBegX1 + current_Yax0)
                                                    lower_x.append(self.stab.XcBeg[2])
                                                    lower_y.append(-RcBegX2 + current_Yax0)
                                                RcBegX = self.stab.Rn * (1.0 + 3.0 * x_point / self.stab.Rn) ** (1 / 3)
                                                y_point = -RcBegX + current_Yax0
                                            else:  # 区域4
                                                if i == 2:  # 第一个点需要特殊处理
                                                    lower_x.append(self.stab.XcBeg[1])
                                                    lower_y.append(-self.stab.RcBeg[1] + current_Yax0)
                                                    lower_x.append(self.stab.XcBeg[2])
                                                    lower_y.append(-self.stab.RcBeg[2] + current_Yax0)
                                                    lower_x.append(self.stab.XcBeg[3])
                                                    lower_y.append(-self.stab.RcBeg[3] + current_Yax0)
                                                if hasattr(self.stab, 'Ypr1') and i - 1 < len(self.stab.Ypr1):
                                                    y_point = self.stab.Ypr1[i - 1]
                                                else:
                                                    y_point = 0.0
                                            lower_x.append(x_point)
                                            lower_y.append(y_point)

                                    # 设置下部空腔轮廓数据
                                    lower_x = np.array(lower_x) * self.stab.Lm
                                    lower_y = np.array(lower_y) * self.stab.Lm
                                    self.lower_cavity_plot.setData(lower_x, lower_y)

                    if self.stab.FlagFirst:
                        self.stab.FlagFirst = False

                    # 绘制模型轮廓
                    if hasattr(self.stab, 'Xmod') and hasattr(self.stab, 'Ymod'):
                        Xmod = np.array(self.stab.Xmod) * self.stab.Lm
                        Ymod = np.array(self.stab.Ymod) * self.stab.Lm
                        self.model_plot.setData(Xmod, Ymod)


            except Exception as e:
                logging.exception("更新空泡形状图时出错")
                # 显示错误信息
                text_item = pg.TextItem(f"错误: {str(e)}", anchor=(0.5, 0.5), color=(255, 0, 0))
                self.plot_widget.addItem(text_item)
                text_item.setPos(0.5, 0.5)

            if self.stab.FlagDive:
                # 设置合理的坐标范围
                if hasattr(self.stab, 'Lm') and hasattr(self.stab, 'Scale'):
                    scale = getattr(self.stab, 'Scale', 1.0)
                    # self.plot_widget.setXRange(-0.1 * scale * self.stab.Lm, 1.1 * scale * self.stab.Lm)
                    # self.plot_widget.setYRange(-0.2 * scale * self.stab.Lm, 0.2 * scale * self.stab.Lm)
                    kk = 0.5
                    self.plot_widget.setXRange(-0.5 * scale * self.stab.Lm / kk, 0.7 * scale * self.stab.Lm / kk)
                    self.plot_widget.setYRange(-0.3 * scale * self.stab.Lm / kk, 0.3 * scale * self.stab.Lm / kk)
            else:
                # 设置合理的坐标范围
                if hasattr(self.stab, 'Lm') and hasattr(self.stab, 'Scale'):
                    scale = getattr(self.stab, 'Scale', 1.0)
                    # self.plot_widget.setXRange(-0.1 * scale * self.stab.Lm, 1.1 * scale * self.stab.Lm)
                    # self.plot_widget.setYRange(-0.2 * scale * self.stab.Lm, 0.2 * scale * self.stab.Lm)
                    kk = 0.7
                    self.plot_widget.setXRange(-0.3 * scale * self.stab.Lm / kk, 1 * scale * self.stab.Lm / kk)
                    self.plot_widget.setYRange(-0.2 * scale * self.stab.Lm / kk, 0.2 * scale * self.stab.Lm / kk)

    def update_plot(self, data=None):
        """更新空泡形状图"""
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval:
            return

        if self.FirstPlot:
            # self.first_plot()
            self.FirstPlot = False
            return
        else:
            if self.SecondPlot:
                self.first_plot()
                self.SecondPlot = False
                return

        try:
            if self.stab.FlagDive:
                # self.upper_cavity_plot.setData([], [])
                # self.lower_cavity_plot.setData([], [])
                # self.model_plot.setData([], [])
                upper_x = data['points']['upper_x']
                upper_y = data['points']['upper_y']
                lower_x = data['points']['lower_x']
                lower_y = data['points']['lower_y']
                model_x = data['points']['model_x']
                model_y = data['points']['model_y']
                # 绘制模型主体
                self.model_plot.setData(model_x * self.stab.Lm, model_y * self.stab.Lm)

                self.upper_cavity_plot.setData(upper_x * self.stab.Lm, upper_y * self.stab.Lm)

                self.lower_cavity_plot.setData(lower_x * self.stab.Lm, lower_y * self.stab.Lm)

            else:
                self.upper_cavity_plot.setData([], [])
                self.lower_cavity_plot.setData([], [])
                self.model_plot.setData([], [])
                upper_x = data['points']['upper_x']
                upper_y = data['points']['upper_y']
                lower_x = data['points']['lower_x']
                lower_y = data['points']['lower_y']
                model_x = data['points']['model_x']
                model_y = data['points']['model_y']
                # 绘制模型主体
                self.model_plot.setData(model_x * self.stab.Lm, model_y * self.stab.Lm)

                self.upper_cavity_plot.setData(upper_x * self.stab.Lm, upper_y * self.stab.Lm)

                self.lower_cavity_plot.setData(lower_x * self.stab.Lm, lower_y * self.stab.Lm)


        except Exception as e:
            logging.exception("更新空泡形状图时出错")
            # 显示错误信息
            # text_item = pg.TextItem(f"错误: {str(e)}", anchor=(0.5, 0.5), color=(255, 0, 0))
            # self.plot_widget.addItem(text_item)
            # text_item.setPos(0.5, 0.5)

        self.last_update_time = current_time

    def first_plot1(self, data=None):
        """更新空泡形状图"""
        current_time = time.time()
        if current_time - self.last_update_time < self.update_interval:
            return

        try:
            if self.stab.FlagDive:
                # self.upper_cavity_plot.setData([], [])
                # self.lower_cavity_plot.setData([], [])
                # self.model_plot.setData([], [])
                upper_x = data['points']['upper_x']
                upper_y = data['points']['upper_y']
                lower_x = data['points']['lower_x']
                lower_y = data['points']['lower_y']
                model_x = data['points']['model_x']
                model_y = data['points']['model_y']
                # 绘制模型主体
                self.model_plot.setData(model_x * self.stab.Lm, model_y * self.stab.Lm)

                self.upper_cavity_plot.setData(upper_x * self.stab.Lm, upper_y * self.stab.Lm)

                self.lower_cavity_plot.setData(lower_x * self.stab.Lm, lower_y * self.stab.Lm)

                scale = getattr(self.stab, 'Scale', 1.0)
                # self.plot_widget.setXRange(-0.1 * scale * self.stab.Lm, 1.1 * scale * self.stab.Lm)
                # self.plot_widget.setYRange(-0.2 * scale * self.stab.Lm, 0.2 * scale * self.stab.Lm)
                kk = 0.5
                self.plot_widget.setXRange(-0.5 * scale * self.stab.Lm / kk, 0.7 * scale * self.stab.Lm / kk)
                self.plot_widget.setYRange(-0.3 * scale * self.stab.Lm / kk, 0.3 * scale * self.stab.Lm / kk)


            else:
                self.upper_cavity_plot.setData([], [])
                self.lower_cavity_plot.setData([], [])
                self.model_plot.setData([], [])
                upper_x = data['points']['upper_x']
                upper_y = data['points']['upper_y']
                lower_x = data['points']['lower_x']
                lower_y = data['points']['lower_y']
                model_x = data['points']['model_x']
                model_y = data['points']['model_y']
                # 绘制模型主体
                self.model_plot.setData(model_x * self.stab.Lm, model_y * self.stab.Lm)

                self.upper_cavity_plot.setData(upper_x * self.stab.Lm, upper_y * self.stab.Lm)

                self.lower_cavity_plot.setData(lower_x * self.stab.Lm, lower_y * self.stab.Lm)

                scale = getattr(self.stab, 'Scale', 1.0)
                # self.plot_widget.setXRange(-0.1 * scale * self.stab.Lm, 1.1 * scale * self.stab.Lm)
                # self.plot_widget.setYRange(-0.2 * scale * self.stab.Lm, 0.2 * scale * self.stab.Lm)
                kk = 2
                self.plot_widget.setXRange(-0.1 * scale * self.stab.Lm / kk, 1.1 * scale * self.stab.Lm / kk)
                self.plot_widget.setYRange(-0.2 * scale * self.stab.Lm / kk, 0.2 * scale * self.stab.Lm / kk)


        except Exception as e:
            logging.exception("更新空泡形状图时出错")
            # 显示错误信息
            # text_item = pg.TextItem(f"错误: {str(e)}", anchor=(0.5, 0.5), color=(255, 0, 0))
            # self.plot_widget.addItem(text_item)
            # text_item.setPos(0.5, 0.5)

        self.last_update_time = current_time
