import os
import time
import numpy as np
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from PyQt5.QtCore import QThread, pyqtSignal
import imageio


class VideoGenerationThread(QThread):
    """视频生成线程"""
    progress = pyqtSignal(int, str)  # 进度百分比, 消息
    finished = pyqtSignal(str)  # 完成信号，返回视频路径
    error = pyqtSignal(str)  # 错误信号

    def __init__(self, rushui_instance, fps=30, parent=None):
        super().__init__(parent)
        self.rushui = rushui_instance
        self.fps = fps
        self._is_running = True
        self.output_dir = "fig"
        self.video_name = "输出.mp4"

    def stop(self):
        self._is_running = False

    def run(self):
        # try:
        if 1:
            # 检查数据是否存在
            if not hasattr(self.rushui, 'plot_dan_x_list') or len(self.rushui.plot_dan_x_list) == 0:
                self.error.emit("⚠ 无仿真数据！请先运行仿真。")
                return

            # 创建输出目录
            if os.path.exists(self.output_dir):
                import shutil
                shutil.rmtree(self.output_dir)
            os.makedirs(self.output_dir, exist_ok=True)

            total_frames = len(self.rushui.plot_dan_x_list)
            self.progress.emit(5, f"📊 准备生成视频 ({total_frames} 数据点)...")
            time.sleep(0.2)

            # 计算采样间隔
            sim_time = self.rushui.tend - self.rushui.t0
            total_sim_steps = len(self.rushui.plot_dan_x_list)
            sim_dt = sim_time / total_sim_steps

            target_duration = total_sim_steps * sim_dt
            required_frames = int(target_duration * self.fps * 100)
            if required_frames == 0:
                required_frames = 1
            sample_interval = max(1, total_sim_steps // required_frames)

            self.progress.emit(10, f"🎬 采样策略: 每{sample_interval}步 → {required_frames}帧 ({self.fps}fps)")
            time.sleep(0.2)

            # 生成帧图像
            frame_files = []
            frames_to_generate = min(required_frames, total_sim_steps // sample_interval)

            for i in range(frames_to_generate):
                if not self._is_running:
                    self.progress.emit(0, "🛑 已取消")
                    return

                data_idx = i * sample_interval
                if data_idx >= total_sim_steps:
                    break

                # 绘制当前帧
                fig = self._create_frame(data_idx, i, frames_to_generate)
                frame_path = os.path.join(self.output_dir, f"frame_{i:06d}.png")
                fig.savefig(frame_path, dpi=100, bbox_inches='tight', facecolor='white')
                plt.close(fig)
                frame_files.append(frame_path)

                # 更新进度
                progress = 15 + int((i + 1) / frames_to_generate * 35)
                if i % 10 == 0:
                    self.progress.emit(progress, f"🖼️ 绘制帧 {i + 1}/{frames_to_generate}")
                    time.sleep(0.01)

            if not self._is_running:
                return

            # 合成视频
            self.progress.emit(55, "🎥 合成视频中...")
            time.sleep(0.2)

            video_path = os.path.join(os.getcwd(), self.video_name)

            with imageio.get_writer(video_path, fps=self.fps, codec='libx264',
                                    quality=8, macro_block_size=None) as writer:
                for idx, frame_path in enumerate(frame_files):
                    if not self._is_running:
                        return
                    image = imageio.imread(frame_path)
                    writer.append_data(image)

                    progress = 55 + int((idx + 1) / len(frame_files) * 40)
                    if idx % 5 == 0:
                        self.progress.emit(progress, f"🎞️ 合成: {idx + 1}/{len(frame_files)} 帧")
                        time.sleep(0.01)

            self.progress.emit(100, "✅ 视频生成完成！")
            time.sleep(0.3)
            self.finished.emit(video_path)

        # except Exception as e:
        #     import traceback
        #     error_msg = f"视频生成失败: {str(e)}"
        #     self.error.emit(error_msg)
        #     self.progress.emit(0, "❌ 生成失败")

    def _create_frame(self, data_idx, frame_num, total_frames):
        """创建单帧图像"""
        fig, ax = plt.subplots(figsize=(8, 5))

        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Arial Unicode MS', 'DejaVu Sans']
        plt.rcParams['axes.unicode_minus'] = False

        # 绘制空泡上轮廓
        if hasattr(self.rushui, 'plot_pao_up_x_list') and data_idx < len(self.rushui.plot_pao_up_x_list):
            ax.plot(self.rushui.plot_pao_up_x_list[data_idx],
                    self.rushui.plot_pao_up_y_list[data_idx],
                    'b-', linewidth=1.5, label='空泡上轮廓', alpha=0.85)

        # 绘制空泡下轮廓
        if hasattr(self.rushui, 'plot_pao_down_x_list') and data_idx < len(self.rushui.plot_pao_down_x_list):
            ax.plot(self.rushui.plot_pao_down_x_list[data_idx],
                    self.rushui.plot_pao_down_y_list[data_idx],
                    'b-', linewidth=1.5, label='空泡下轮廓', alpha=0.85)

        # 绘制空泡轴线
        if hasattr(self.rushui, 'plot_zhou_x_list') and data_idx < len(self.rushui.plot_zhou_x_list):
            ax.plot(self.rushui.plot_zhou_x_list[data_idx],
                    self.rushui.plot_zhou_y_list[data_idx],
                    'r--', linewidth=1.0, label='空泡轴线', alpha=0.9)

        # 绘制弹体轮廓
        if hasattr(self.rushui, 'plot_dan_x_list') and data_idx < len(self.rushui.plot_dan_x_list):
            ax.plot(self.rushui.plot_dan_x_list[data_idx],
                    self.rushui.plot_dan_y_list[data_idx],
                    'k-', linewidth=2.5, label='航行体', alpha=0.95)

        # 设置坐标轴

        ax.set_xlim(-3.5, 3.5)
        ax.set_ylim(-2, 2)
        ax.set_xlabel('X (m)', fontsize=10)
        ax.set_ylabel('Y (m)', fontsize=10)
        ax.set_title(f'超空泡航行体入水过程 (帧 {frame_num + 1}/{total_frames})',
                     fontsize=11, pad=8)
        ax.grid(True, linestyle='--', alpha=0.3)
        ax.set_aspect('equal', adjustable='box')
        ax.legend(loc='upper right', fontsize=8, framealpha=0.85)

        # 添加水线
        ax.axhline(y=0, color='c', linestyle='--', linewidth=1.5, alpha=0.7)

        # 添加状态信息
        info_texts = []
        if hasattr(self.rushui, 'ys') and data_idx < len(self.rushui.ys):
            y_pos = self.rushui.ys[data_idx][10]
            vx = self.rushui.ys[data_idx][0]
            vy = self.rushui.ys[data_idx][1]
            v = np.sqrt(vx ** 2 + vy ** 2)
            info_texts.append(f'深度: {abs(y_pos):.2f}m')
            info_texts.append(f'速度: {v:.1f}m/s')

        if hasattr(self.rushui, 'ts') and data_idx < len(self.rushui.ts):
            t = self.rushui.ts[data_idx]
            info_texts.append(f'时间: {t:.3f}s')

        if info_texts:
            info_text = ' | '.join(info_texts)
            ax.text(0.5, 0.95, info_text, transform=ax.transAxes,
                    fontsize=9, verticalalignment='top', horizontalalignment='center',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='lightyellow',
                              edgecolor='gray', alpha=0.8))

        plt.tight_layout()
        return fig