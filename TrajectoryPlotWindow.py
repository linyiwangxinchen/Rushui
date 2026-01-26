import logging
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QPushButton,
                             QScrollArea, QWidget, QMessageBox, QSizePolicy,
                             QFrame)
from PyQt5.QtGui import QGuiApplication


class TrajectoryPlotWindow(QDialog):
    """船-弹轨迹展示窗口（独立子图+防遮挡布局）"""

    def __init__(self, sim_data_list, parent=None):
        super().__init__(parent)
        self.sim_data_list = sim_data_list
        self.setWindowTitle("船-弹轨迹展示（独立子图）")

        # DPI 自适应
        screen = QGuiApplication.primaryScreen() if hasattr(QGuiApplication, 'primaryScreen') else None
        self.dpi = screen.logicalDotsPerInch() if screen else 96.0
        self.scale_factor = self.dpi / 96.0

        # 设置窗口尺寸（增加10%高度预防遮挡）
        window_width = int(980 * self.scale_factor)
        window_height = int(820 * self.scale_factor)
        self.resize(window_width, window_height)

        self._init_ui()

    def _init_ui(self):
        """初始化带滚动区域的UI（含防遮挡填充）"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(10)

        # 滚动区域（关键：设置viewport边距防止内容被裁剪）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)

        # 滚动内容容器（添加顶部/底部填充防止遮挡）
        scroll_content = QWidget()
        scroll_content.setStyleSheet("""
            QWidget {
                background-color: white;
                padding-top: 25px;   /* 顶部填充 - 防止被窗口标题栏遮挡 */
                padding-bottom: 30px; /* 底部填充 - 防止被滚动条/按钮遮挡 */
            }
        """)
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(20)  # 增加子图间距

        # 创建轨迹画布
        try:
            canvas_container = self._create_trajectory_canvas()
            scroll_layout.addWidget(canvas_container)
            scroll_layout.addStretch(1)
        except Exception as e:
            logging.exception("轨迹画布创建失败")
            QMessageBox.critical(self, "错误", f"轨迹绘制失败:\n{str(e)}")
            self.close()
            return

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # 底部按钮区域（添加分隔线提升视觉层次）
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #CCCCCC;")
        main_layout.addWidget(separator)

        close_btn = QPushButton("关闭")
        close_btn.setFixedHeight(int(38 * self.scale_factor))
        close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                border-radius: 4px;
                padding: 5px 15px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        close_btn.clicked.connect(self.close)
        main_layout.addWidget(close_btn)

    def _create_trajectory_canvas(self):
        """创建含N个子图的画布（防遮挡布局）"""
        n_sim = len(self.sim_data_list)
        if n_sim == 0:
            raise ValueError("仿真数据列表为空")

        # 计算每个子图配置
        plot_configs = []
        for sim_data in self.sim_data_list:
            config = self._calculate_plot_dimensions(sim_data)
            plot_configs.append(config)

        # 计算总高度（含安全边距）
        # 每个子图：实际高度 + 标题预留空间(0.35英寸) + 间距(0.3英寸)
        total_height = sum(cfg['height'] + 0.35 for cfg in plot_configs) + 0.3 * (n_sim - 1)

        # 创建Figure（固定宽度9.5英寸，提供充足左右边距）
        self.figure = Figure(figsize=(9.5, total_height), dpi=self.dpi)

        # 关键：设置全局边距（顶部留足空间防遮挡）
        self.figure.subplots_adjust(
            left=0.09,  # 左边距 9%
            right=0.96,  # 右边距 4%
            top=0.985,  # 顶部边距 1.5% - 防止标题被裁剪
            bottom=0.03,  # 底部边距 3%
            hspace=0.45  # 子图垂直间距 45%
        )

        # 创建子图（使用subplots便于统一管理）
        axes = self.figure.subplots(n_sim, 1, squeeze=False)
        if n_sim == 1:
            axes = [[axes[0, 0]]]  # 统一为二维数组

        # 绘制每个子图
        for idx, (ax_row, sim_data, config) in enumerate(zip(axes, self.sim_data_list, plot_configs)):
            ax = ax_row[0]
            self._plot_single_trajectory(ax, sim_data, idx + 1, n_sim, config)

        # 画布包装（关键：设置最小高度防止初始遮挡）
        canvas = FigureCanvas(self.figure)
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        canvas.setMinimumWidth(int(950 * self.scale_factor))
        canvas.setMinimumHeight(int(total_height * self.dpi * 1.02))  # 额外2%安全边距

        # 添加画布边框提升视觉层次
        container = QWidget()
        container.setStyleSheet("QWidget { border: 1px solid #E0E0E0; border-radius: 4px; background: white; }")
        layout = QVBoxLayout(container)
        layout.setContentsMargins(1, 1, 1, 1)  # 微边距防止边框被裁剪
        layout.addWidget(canvas)
        return container

    def _calculate_plot_dimensions(self, sim_data):
        """智能计算子图尺寸（基于数据范围）"""
        try:
            # 容错提取数据
            ship_key = next((k for k in sim_data if 'ship_x' in k.lower()), 'ship_x_list')
            dan_key = next((k for k in sim_data if 'dan_line' in k.lower()), 'dan_line')

            ship_xy = np.array(sim_data[ship_key])[:, :2]
            dan_xy = np.array(sim_data[dan_key])[:, :2]

            all_x = np.concatenate([ship_xy[:, 0], dan_xy[:, 0]])
            all_y = np.concatenate([ship_xy[:, 1], dan_xy[:, 1]])

            x_range = np.ptp(all_x)
            y_range = np.ptp(all_y)

            # Y轴最小显示范围（突出微小波动）
            MIN_Y_RANGE = 15.0
            display_y_range = max(y_range, MIN_Y_RANGE)

            # 智能宽高比（2.8:1 ~ 4.5:1 优化视觉）
            raw_ratio = x_range / display_y_range if display_y_range > 0 else 12.0
            target_ratio = np.clip(raw_ratio * 0.65, 2.8, 4.5)

            # 固定宽度9.5英寸，计算高度
            width = 9.5
            height = width / target_ratio

            # 限制高度范围 [2.0, 3.2] 英寸
            height = np.clip(height, 2.0, 3.2)

            return {
                'width': width,
                'height': height,
                'y_min_range': MIN_Y_RANGE,
                'x_range': x_range,
                'y_range': y_range,
                'display_y_range': display_y_range
            }
        except Exception as e:
            logging.warning(f"尺寸计算失败: {e}")
            return {
                'width': 9.5,
                'height': 2.5,
                'y_min_range': 15.0,
                'x_range': 500.0,
                'y_range': 10.0,
                'display_y_range': 15.0
            }

    def _plot_single_trajectory(self, ax, sim_data, sim_idx, total_sims, config):
        """绘制单次仿真轨迹（防遮挡优化）"""
        try:
            # 提取数据
            ship_key = next((k for k in sim_data if 'ship_x' in k.lower()), 'ship_x_list')
            dan_key = next((k for k in sim_data if 'dan_line' in k.lower()), 'dan_line')

            ship_xy = np.array(sim_data[ship_key])[:, :2]
            dan_xy = np.array(sim_data[dan_key])[:, :2]

            # 颜色方案（增强对比度）
            ship_color = '#1E88E5'  # 鲜明蓝色
            dan_color = '#E53935'  # 鲜明红色
            grid_color = '#EEEEEE'

            # 绘制轨迹
            ax.plot(ship_xy[:, 0], ship_xy[:, 1],
                    color=ship_color, linestyle='-', linewidth=2.3,
                    label='船', alpha=0.96, zorder=4)
            ax.plot(dan_xy[:, 0], dan_xy[:, 1],
                    color=dan_color, linestyle='--', linewidth=2.3,
                    label='弹', alpha=0.96, zorder=4)

            # 起点标记（加大尺寸提升可见性）
            ax.plot(ship_xy[0, 0], ship_xy[0, 1], 'o',
                    color=ship_color, markersize=10, markeredgecolor='white',
                    markeredgewidth=2.2, zorder=6)
            ax.plot(dan_xy[0, 0], dan_xy[0, 1], 's',
                    color=dan_color, markersize=10, markeredgecolor='white',
                    markeredgewidth=2.2, zorder=6)

            # 终点标记
            ax.plot(ship_xy[-1, 0], ship_xy[-1, 1], '*',
                    color=ship_color, markersize=14, markeredgecolor='#FFD700',
                    markeredgewidth=2.0, zorder=6, alpha=0.9)
            ax.plot(dan_xy[-1, 0], dan_xy[-1, 1], 'X',
                    color=dan_color, markersize=14, markeredgecolor='#FFD700',
                    markeredgewidth=2.0, zorder=6, alpha=0.9)

            # 多箭头方向指示
            self._add_multiple_arrows(ax, ship_xy, ship_color, 3)
            self._add_multiple_arrows(ax, dan_xy, dan_color, 3)

            # 智能坐标轴范围
            all_x = np.concatenate([ship_xy[:, 0], dan_xy[:, 0]])
            all_y = np.concatenate([ship_xy[:, 1], dan_xy[:, 1]])

            x_margin = 0.035 * (np.max(all_x) - np.min(all_x))
            ax.set_xlim(np.min(all_x) - x_margin, np.max(all_x) + x_margin)

            # Y轴：确保最小显示范围 + 智能居中
            y_center = np.mean(all_y)
            display_half_range = max(config['display_y_range'] / 2, 8.5)
            ax.set_ylim(y_center - display_half_range, y_center + display_half_range)

            # 水平参考线（增强Y方向感知）
            y_min, y_max = ax.get_ylim()
            if (y_max - y_min) > 6.0:
                mid_y = (y_min + y_max) / 2
                ax.axhline(y=mid_y, color=grid_color, linestyle='-', linewidth=1.3, zorder=1, alpha=0.7)
                ax.axhline(y=mid_y + 5, color=grid_color, linestyle=':', linewidth=0.9, zorder=1, alpha=0.5)
                ax.axhline(y=mid_y - 5, color=grid_color, linestyle=':', linewidth=0.9, zorder=1, alpha=0.5)

            # 标题（关键：增加pad防止与图形重叠）
            title = f'仿真 {sim_idx}/{total_sims} | X: {np.min(all_x):.0f}~{np.max(all_x):.0f}m, Y: {np.min(all_y):.1f}~{np.max(all_y):.1f}m'
            ax.set_title(title,
                         fontsize=11.5 * self.scale_factor,
                         fontweight='bold',
                         pad=14,  # 关键：增加标题与图形间距
                         loc='left',
                         color='#263238')

            # 坐标轴标签
            ax.set_xlabel('X 坐标 (m)', fontsize=10 * self.scale_factor, labelpad=7)
            ax.set_ylabel('Y 坐标 (m)', fontsize=10 * self.scale_factor, labelpad=7)

            # 网格与样式
            ax.grid(True, linestyle='--', alpha=0.68, linewidth=0.95, zorder=0)
            ax.set_axisbelow(True)

            # 精简边框
            for spine in ['top', 'right']:
                ax.spines[spine].set_visible(False)
            for spine in ['left', 'bottom']:
                ax.spines[spine].set_linewidth(1.3)
                ax.spines[spine].set_color('#90A4AE')

            # 刻度优化
            ax.tick_params(axis='both',
                           labelsize=9 * self.scale_factor,
                           length=4.5,
                           width=1.0,
                           pad=5,
                           colors='#424242')

            # 图例（右上角，避免遮挡轨迹）
            ax.legend(loc='upper right',
                      fontsize=9 * self.scale_factor,
                      ncol=2,
                      framealpha=0.94,
                      edgecolor='#BDBDBD',
                      fancybox=True)

            # Y轴放大提示（右下角，小字）
            if config['y_range'] < config['y_min_range'] * 0.9:
                ax.text(0.99, 0.03, f'ⓘ Y轴放大显示 (实际波动{config["y_range"]:.1f}m)',
                        transform=ax.transAxes,
                        ha='right',
                        va='bottom',
                        fontsize=7.5 * self.scale_factor,
                        color='#546E7A',
                        style='italic',
                        alpha=0.9,
                        bbox=dict(boxstyle='round,pad=0.3', facecolor='#E3F2FD', alpha=0.7, edgecolor='none'))

        except Exception as e:
            logging.exception(f"仿真{sim_idx}绘制异常")
            ax.text(0.5, 0.5, f'轨迹绘制失败:\n{str(e)}',
                    transform=ax.transAxes,
                    ha='center',
                    va='center',
                    fontsize=10.5 * self.scale_factor,
                    color='#E53935',
                    fontweight='bold',
                    alpha=0.85,
                    bbox=dict(boxstyle='round,pad=0.6', facecolor='#FFEBEE', alpha=0.85))
            ax.set_title(f'仿真 {sim_idx}（错误）',
                         fontsize=11.5 * self.scale_factor,
                         color='#E53935',
                         pad=14)

    def _add_multiple_arrows(self, ax, trajectory, color, num_arrows=3):
        """在轨迹上均匀添加多个方向箭头"""
        if len(trajectory) < 12 or num_arrows < 1:
            return

        # 选择均匀分布的点（避开起点终点15%区域）
        positions = np.linspace(0.22, 0.78, num_arrows)
        for pos in positions:
            idx = int(pos * (len(trajectory) - 1))
            if idx < 2 or idx >= len(trajectory) - 2:
                continue

            start = trajectory[idx - 1]
            end = trajectory[idx + 1]

            dx = end[0] - start[0]
            dy = end[1] - start[1]
            norm = np.hypot(dx, dy)
            if norm < 1e-5:
                continue

            # 优化箭头长度避免重叠
            arrow_frac = 0.55
            mid_point = start + np.array([dx, dy]) * 0.5
            arrow_end = start + np.array([dx, dy]) * arrow_frac

            ax.annotate('',
                        xy=arrow_end,
                        xytext=start,
                        arrowprops=dict(arrowstyle='->',
                                        lw=1.8,
                                        color=color,
                                        alpha=0.88,
                                        mutation_scale=16))