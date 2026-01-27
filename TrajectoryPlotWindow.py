import logging
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.patches import Circle, RegularPolygon
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QPushButton,
                             QScrollArea, QWidget, QMessageBox, QSizePolicy,
                             QFrame)
from PyQt5.QtGui import QGuiApplication


class TrajectoryPlotWindow(QDialog):
    """船-弹轨迹展示窗口（含爆炸点标记+防遮挡布局）"""

    def __init__(self, sim_data_list, parent=None):
        super().__init__(parent)
        self.sim_data_list = sim_data_list
        self.setWindowTitle("船-弹轨迹与爆炸点分析")

        # DPI 自适应
        screen = QGuiApplication.primaryScreen() if hasattr(QGuiApplication, 'primaryScreen') else None
        self.dpi = screen.logicalDotsPerInch() if screen else 96.0
        self.scale_factor = self.dpi / 96.0

        # 设置窗口尺寸（增加顶部空间防遮挡）
        window_width = int(1000 * self.scale_factor)
        window_height = int(850 * self.scale_factor)
        self.resize(window_width, window_height)

        self._init_ui()

    def _init_ui(self):
        """初始化UI（含防遮挡填充）"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # 滚动区域（关键：设置viewport边距）
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll_area.setStyleSheet("""
            QScrollArea {
                border: none;
                background: white;
            }
            QScrollBar:vertical {
                width: 12px;
                background: #F5F5F5;
                margin: 15px 3px 15px 3px;
            }
            QScrollBar::handle:vertical {
                background: #C1C1C1;
                min-height: 30px;
                border-radius: 6px;
            }
        """)

        # 滚动内容容器（关键：顶部/底部填充防遮挡）
        scroll_content = QWidget()
        scroll_content.setStyleSheet("""
            QWidget {
                background-color: white;
                padding-top: 40px;    /* 顶部填充 - 防止被窗口标题栏遮挡 */
                padding-bottom: 50px; /* 底部填充 - 防止被滚动条/按钮遮挡 */
            }
        """)
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 0, 0)
        scroll_layout.setSpacing(25)  # 增加子图间距

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

        # 底部按钮区域
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setFrameShadow(QFrame.Sunken)
        separator.setStyleSheet("color: #D0D0D0; margin: 8px 0;")
        main_layout.addWidget(separator)

        close_btn = QPushButton("  关闭窗口  ")
        close_btn.setFixedHeight(int(42 * self.scale_factor))
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: #E53935;
                color: white;
                font-weight: bold;
                font-size: {11 * self.scale_factor}pt;
                border-radius: 6px;
                padding: 8px 25px;
            }}
            QPushButton:hover {{
                background-color: #C62828;
            }}
            QPushButton:pressed {{
                background-color: #B71C1C;
            }}
        """)
        close_btn.clicked.connect(self.close)
        btn_container = QWidget()
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.addWidget(close_btn, alignment=Qt.AlignCenter)
        main_layout.addWidget(btn_container)

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
        total_height = sum(cfg['height'] + 0.4 for cfg in plot_configs) + 0.4 * (n_sim - 1)

        # 创建Figure（关键：增加顶部边距防遮挡）
        self.figure = Figure(figsize=(10.0, total_height), dpi=self.dpi)
        self.figure.patch.set_facecolor('white')

        # 关键：设置全局边距（顶部留足2.5%空间防标题裁剪）
        self.figure.subplots_adjust(
            left=0.085,  # 左边距 8.5%
            right=0.97,  # 右边距 3%
            top=0.992,  # 顶部边距 0.8% - 根治首图遮挡
            bottom=0.025,  # 底部边距 2.5%
            hspace=0.55  # 子图垂直间距 55%
        )

        # 创建子图
        axes = self.figure.subplots(n_sim, 1, squeeze=False)
        if n_sim == 1:
            axes = [[axes[0, 0]]]

        # 绘制每个子图
        for idx, (ax_row, sim_data, config) in enumerate(zip(axes, self.sim_data_list, plot_configs)):
            ax = ax_row[0]
            self._plot_single_trajectory(ax, sim_data, idx + 1, n_sim, config)

        # 画布包装（关键：设置最小高度+边框）
        canvas = FigureCanvas(self.figure)
        canvas.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        canvas.setMinimumWidth(int(980 * self.scale_factor))
        canvas.setMinimumHeight(int(total_height * self.dpi * 1.05))  # 5%安全边距

        # 添加精致边框
        container = QWidget()
        container.setStyleSheet("""
            QWidget {
                border: 1px solid #E0E0E0;
                border-radius: 6px;
                background: white;
                margin: 0px;
            }
        """)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)  # 防止边框被裁剪
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

            # Y轴最小显示范围
            MIN_Y_RANGE = 15.0
            display_y_range = max(y_range, MIN_Y_RANGE)

            # 智能宽高比（2.8:1 ~ 4.5:1）
            raw_ratio = x_range / display_y_range if display_y_range > 0 else 12.0
            target_ratio = np.clip(raw_ratio * 0.68, 2.8, 4.5)

            width = 10.0
            height = width / target_ratio
            height = np.clip(height, 2.1, 3.3)

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
                'width': 10.0,
                'height': 2.6,
                'y_min_range': 15.0,
                'x_range': 500.0,
                'y_range': 10.0,
                'display_y_range': 15.0
            }

    def _find_explosion_index(self, ship_xy, dan_xy):
        """查找船弹最近距离点索引（仅XY平面）"""
        # 对齐轨迹长度（取最小长度）
        min_len = min(len(ship_xy), len(dan_xy))
        if min_len < 2:
            raise ValueError("轨迹点数不足")

        # 截断到相同长度
        ship_clip = ship_xy[:min_len]
        dan_clip = dan_xy[:min_len]

        # 计算欧氏距离
        distances = np.linalg.norm(ship_clip - dan_clip, axis=1)
        min_idx = np.argmin(distances)
        min_distance = distances[min_idx]

        return min_idx, min_distance

    def _plot_single_trajectory(self, ax, sim_data, sim_idx, total_sims, config):
        """绘制单次仿真轨迹（含爆炸点标记）"""
        try:
            # 提取数据
            ship_key = next((k for k in sim_data if 'ship_x' in k.lower()), 'ship_x_list')
            dan_key = next((k for k in sim_data if 'dan_line' in k.lower()), 'dan_line')

            ship_xy = np.array(sim_data[ship_key])[:, :2]
            dan_xy = np.array(sim_data[dan_key])[:, :2]

            # 颜色方案
            ship_color = '#1E88E5'  # 蓝色（船）
            dan_color = '#E53935'  # 红色（弹）
            explosion_color = '#D32F2F'  # 深红（爆炸）
            grid_color = '#F0F0F0'

            # === 绘制轨迹 ===
            ax.plot(ship_xy[:, 0], ship_xy[:, 1],
                    color=ship_color, linestyle='-', linewidth=2.4,
                    label='船', alpha=0.97, zorder=3)
            ax.plot(dan_xy[:, 0], dan_xy[:, 1],
                    color=dan_color, linestyle='--', linewidth=2.4,
                    label='弹', alpha=0.97, zorder=3)

            # 起点标记
            ax.plot(ship_xy[0, 0], ship_xy[0, 1], 'o',
                    color=ship_color, markersize=11, markeredgecolor='white',
                    markeredgewidth=2.5, zorder=5)
            ax.plot(dan_xy[0, 0], dan_xy[0, 1], 's',
                    color=dan_color, markersize=11, markeredgecolor='white',
                    markeredgewidth=2.5, zorder=5)

            # 终点标记
            ax.plot(ship_xy[-1, 0], ship_xy[-1, 1], '*',
                    color=ship_color, markersize=15, markeredgecolor='#FFD700',
                    markeredgewidth=2.2, zorder=5, alpha=0.92)
            ax.plot(dan_xy[-1, 0], dan_xy[-1, 1], 'X',
                    color=dan_color, markersize=15, markeredgecolor='#FFD700',
                    markeredgewidth=2.2, zorder=5, alpha=0.92)

            # 方向箭头
            self._add_multiple_arrows(ax, ship_xy, ship_color, 3)
            self._add_multiple_arrows(ax, dan_xy, dan_color, 3)

            # === 爆炸点计算与标记 ===
            try:
                min_idx, min_dist = self._find_explosion_index(ship_xy, dan_xy)
                explosion_point = dan_xy[min_idx]  # 以弹位置为爆炸点

                # 动态计算冲击波半径（基于Y轴范围）
                y_min, y_max = np.min(dan_xy[:, 1]), np.max(dan_xy[:, 1])
                wave_radius = max(18.0, (y_max - y_min) * 0.15)

                # 1. 冲击波圆环（3层渐变）
                for i, (rad, alpha) in enumerate([(wave_radius * 1.3, 0.15),
                                                  (wave_radius * 0.9, 0.25),
                                                  (wave_radius * 0.6, 0.35)]):
                    circle = Circle(explosion_point, rad,
                                    facecolor=explosion_color,
                                    edgecolor='none',
                                    alpha=alpha,
                                    zorder=4 - i)
                    ax.add_patch(circle)

                # 2. 爆炸核心（星形+圆形组合）
                # 外层发光圆
                core_circle = Circle(explosion_point, wave_radius * 0.35,
                                     facecolor='#FF6B6B',
                                     edgecolor='yellow',
                                     linewidth=2.0,
                                     alpha=0.85,
                                     zorder=6)
                ax.add_patch(core_circle)

                # 内层星爆
                ax.plot(explosion_point[0], explosion_point[1],
                        marker='*', color='white', markersize=22,
                        markeredgecolor=explosion_color, markeredgewidth=2.8,
                        zorder=7)

                # 3. 爆炸点标注（智能避让）
                self._add_explosion_annotation(ax, explosion_point, min_dist, sim_idx)

                # 图例项（仅添加一次）
                if sim_idx == 1:
                    # 创建代理艺术家用于图例
                    from matplotlib.lines import Line2D
                    explosion_proxy = Line2D([0], [0],
                                             marker='*',
                                             color='w',
                                             markerfacecolor='white',
                                             markeredgecolor=explosion_color,
                                             markersize=15,
                                             markeredgewidth=2.5,
                                             linestyle='None')
                    ax.legend(handles=ax.get_legend_handles_labels()[0] + [explosion_proxy],
                              labels=ax.get_legend_handles_labels()[1] + ['爆炸点'],
                              loc='upper right',
                              fontsize=9.5 * self.scale_factor,
                              ncol=3,
                              framealpha=0.95,
                              edgecolor='#CCCCCC',
                              fancybox=True)
                else:
                    ax.legend(loc='upper right',
                              fontsize=9.5 * self.scale_factor,
                              ncol=3,
                              framealpha=0.95,
                              edgecolor='#CCCCCC')

            except Exception as e:
                logging.warning(f"爆炸点标记失败 (仿真{sim_idx}): {e}")
                # 仍显示图例（不含爆炸点）
                ax.legend(loc='upper right',
                          fontsize=9.5 * self.scale_factor,
                          ncol=2,
                          framealpha=0.95,
                          edgecolor='#CCCCCC')

            # === 坐标轴设置 ===
            all_x = np.concatenate([ship_xy[:, 0], dan_xy[:, 0]])
            all_y = np.concatenate([ship_xy[:, 1], dan_xy[:, 1]])

            x_margin = 0.032 * (np.max(all_x) - np.min(all_x))
            ax.set_xlim(np.min(all_x) - x_margin, np.max(all_x) + x_margin)

            # Y轴智能范围
            y_center = np.mean(all_y)
            display_half_range = max(config['display_y_range'] / 2, 9.0)
            ax.set_ylim(y_center - display_half_range, y_center + display_half_range)

            # 水平参考线
            y_min, y_max = ax.get_ylim()
            if (y_max - y_min) > 7.0:
                mid_y = (y_min + y_max) / 2
                ax.axhline(y=mid_y, color=grid_color, linestyle='-', linewidth=1.5, zorder=1, alpha=0.8)
                ax.axhline(y=mid_y + 5, color=grid_color, linestyle=':', linewidth=1.0, zorder=1, alpha=0.6)
                ax.axhline(y=mid_y - 5, color=grid_color, linestyle=':', linewidth=1.0, zorder=1, alpha=0.6)

            # 标题（关键：增加pad防遮挡）
            title = f'仿真 {sim_idx}/{total_sims} | 最近距: {min_dist:.1f}m | X: {np.min(all_x):.0f}~{np.max(all_x):.0f}m'
            ax.set_title(title,
                         fontsize=12 * self.scale_factor,
                         fontweight='bold',
                         pad=18,  # 关键：增加标题间距
                         loc='left',
                         color='#1A237E')

            # 坐标轴标签
            ax.set_xlabel('X 坐标 (m)', fontsize=10.5 * self.scale_factor, labelpad=8)
            ax.set_ylabel('Y 坐标 (m)', fontsize=10.5 * self.scale_factor, labelpad=8)

            # 网格与样式
            ax.grid(True, linestyle='--', alpha=0.72, linewidth=1.0, zorder=0)
            ax.set_axisbelow(True)

            # 精简边框
            for spine in ['top', 'right']:
                ax.spines[spine].set_visible(False)
            for spine in ['left', 'bottom']:
                ax.spines[spine].set_linewidth(1.4)
                ax.spines[spine].set_color('#78909C')

            # 刻度优化
            ax.tick_params(axis='both',
                           labelsize=9.5 * self.scale_factor,
                           length=5,
                           width=1.1,
                           pad=6,
                           colors='#263238')

            # Y轴放大提示
            if config['y_range'] < config['y_min_range'] * 0.85:
                ax.text(0.99, 0.04, f'ⓘ Y轴放大显示 (实际波动{config["y_range"]:.1f}m)',
                        transform=ax.transAxes,
                        ha='right',
                        va='bottom',
                        fontsize=8 * self.scale_factor,
                        color='#424242',
                        style='italic',
                        alpha=0.92,
                        bbox=dict(boxstyle='round,pad=0.4',
                                  facecolor='#E8F5E9',
                                  alpha=0.85,
                                  edgecolor='#81C784',
                                  linewidth=1.2))

        except Exception as e:
            logging.exception(f"仿真{sim_idx}绘制异常")
            ax.text(0.5, 0.5, f'轨迹绘制失败:\n{str(e)}',
                    transform=ax.transAxes,
                    ha='center',
                    va='center',
                    fontsize=11 * self.scale_factor,
                    color='#D32F2F',
                    fontweight='bold',
                    alpha=0.9,
                    bbox=dict(boxstyle='round,pad=0.8',
                              facecolor='#FFEBEE',
                              alpha=0.9,
                              edgecolor='#EF5350',
                              linewidth=2))
            ax.set_title(f'仿真 {sim_idx}（渲染错误）',
                         fontsize=12 * self.scale_factor,
                         color='#D32F2F',
                         pad=18)

    def _add_multiple_arrows(self, ax, trajectory, color, num_arrows=3):
        """在轨迹上均匀添加多个方向箭头"""
        if len(trajectory) < 15 or num_arrows < 1:
            return

        positions = np.linspace(0.25, 0.75, num_arrows)
        for pos in positions:
            idx = int(pos * (len(trajectory) - 1))
            if idx < 3 or idx >= len(trajectory) - 3:
                continue

            start = trajectory[idx - 2]
            end = trajectory[idx + 2]

            dx = end[0] - start[0]
            dy = end[1] - start[1]
            norm = np.hypot(dx, dy)
            if norm < 1e-5:
                continue

            arrow_frac = 0.6
            arrow_end = start + np.array([dx, dy]) * arrow_frac

            ax.annotate('',
                        xy=arrow_end,
                        xytext=start,
                        arrowprops=dict(arrowstyle='->',
                                        lw=2.0,
                                        color=color,
                                        alpha=0.9,
                                        mutation_scale=18))

    def _add_explosion_annotation(self, ax, point, distance, sim_idx):
        """添加爆炸点智能标注（自动避让）"""
        x_min, x_max = ax.get_xlim()
        y_min, y_max = ax.get_ylim()

        # 计算安全偏移量
        x_range = x_max - x_min
        y_range = y_max - y_min
        x_offset = x_range * 0.035
        y_offset = y_range * 0.045

        # 尝试4个方向放置标注（右上 > 左上 > 右下 > 左下）
        positions = [
            (point[0] + x_offset, point[1] + y_offset, 'left', 'bottom'),  # 右上
            (point[0] - x_offset, point[1] + y_offset, 'right', 'bottom'),  # 左上
            (point[0] + x_offset, point[1] - y_offset, 'left', 'top'),  # 右下
            (point[0] - x_offset, point[1] - y_offset, 'right', 'top')  # 左下
        ]

        # 选择第一个不超出边界的方位
        for x, y, ha, va in positions:
            if x_min + x_range * 0.1 < x < x_max - x_range * 0.1 and y_min + y_range * 0.1 < y < y_max - y_range * 0.1:
                break
        else:
            # 全部超出则使用默认右上
            x, y, ha, va = positions[0]

        # 创建爆炸标注
        label_text = f'爆炸点\n(距{distance:.1f}m)'
        ax.text(x, y, label_text,
                fontsize=9.5 * self.scale_factor,
                color='#B71C1C',
                fontweight='bold',
                ha=ha,
                va=va,
                linespacing=1.6,
                bbox=dict(boxstyle='round,pad=0.5',
                          facecolor='#FFCCBC',
                          edgecolor='#E64A19',
                          linewidth=1.8,
                          alpha=0.92),
                zorder=8)