import os
import cv2
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QProgressBar,
                             QLabel, QPushButton, QHBoxLayout, QFrame,
                             QWidget, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QImage, QPixmap
import logging


class VideoGenerationDialog(QDialog):
    """独立视频生成与播放窗口 - 可与主窗口同时存在"""
    cancelled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🎬 视频生成与播放")
        self.resize(700, 580)
        self.setWindowFlags(self.windowFlags() | Qt.Window)  # 非模态，可独立存在
        self.setWindowModality(Qt.NonModal)
        self._cancelled = False

        # 视频播放相关
        self.video_path = None
        self.cap = None
        self.timer = None
        self.is_playing = False

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # 标题栏
        title_frame = QFrame()
        title_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #2196F3, stop:1 #21CBF3);
                border-radius: 6px;
                padding: 8px;
            }
        """)
        title_layout = QHBoxLayout(title_frame)

        self.title_label = QLabel("🎬 视频生成中...")
        self.title_label.setStyleSheet("color: white; font-size: 16pt; font-weight: bold;")
        title_layout.addWidget(self.title_label)

        main_layout.addWidget(title_frame)

        # 进度区域
        progress_frame = QFrame()
        progress_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 12px;
            }
        """)
        progress_layout = QVBoxLayout(progress_frame)

        self.progress_label = QLabel("准备生成视频...")
        self.progress_label.setStyleSheet("font-size: 11pt; color: #555; font-weight: bold;")
        self.progress_label.setAlignment(Qt.AlignCenter)
        progress_layout.addWidget(self.progress_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #2196F3;
                border-radius: 5px;
                text-align: center;
                height: 22px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                            stop:0 #4CAF50, stop:1 #8BC34A);
                width: 20px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)

        main_layout.addWidget(progress_frame)

        # 视频播放区域（初始隐藏）
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: #1a1a1a;
                border: 2px solid #424242;
                border-radius: 6px;
            }
        """)
        self.video_label.setMinimumHeight(320)
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setVisible(False)

        main_layout.addWidget(self.video_label)

        # 播放控制区域（初始隐藏）
        self.control_container = QWidget()
        self.control_container.setVisible(False)
        control_layout = QHBoxLayout(self.control_container)
        control_layout.setContentsMargins(0, 5, 0, 0)
        control_layout.setSpacing(15)
        control_layout.setAlignment(Qt.AlignCenter)

        self.play_btn = QPushButton("▶ 播放")
        self.play_btn.setFixedWidth(100)
        self.play_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                border: none;
                border-radius: 20px;
                padding: 8px 15px;
                font-size: 12pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #43A047;
            }
            QPushButton:disabled {
                background-color: #bdbdbd;
            }
        """)
        self.play_btn.clicked.connect(self.toggle_playback)
        control_layout.addWidget(self.play_btn)

        self.restart_btn = QPushButton("⏮ 重新播放")
        self.restart_btn.setFixedWidth(120)
        self.restart_btn.setEnabled(False)
        self.restart_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3; 
                color: white; 
                border: none;
                border-radius: 20px;
                padding: 8px 15px;
                font-size: 11pt;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
            QPushButton:disabled {
                background-color: #bdbdbd;
            }
        """)
        self.restart_btn.clicked.connect(self.restart_playback)
        control_layout.addWidget(self.restart_btn)

        main_layout.addWidget(self.control_container)

        # 按钮区域
        button_frame = QFrame()
        button_frame.setStyleSheet("""
            QFrame {
                background-color: #f8f9fa;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                padding: 10px;
            }
        """)
        button_layout = QHBoxLayout(button_frame)
        button_layout.setSpacing(12)

        self.cancel_btn = QPushButton("❌ 取消")
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f44336; 
                color: white; 
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        self.cancel_btn.clicked.connect(self.cancel_operation)
        button_layout.addWidget(self.cancel_btn)

        self.minimize_btn = QPushButton("❐ 后台运行")
        self.minimize_btn.setStyleSheet("""
            QPushButton {
                background-color: #9e9e9e; 
                color: white; 
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #757575;
            }
        """)
        self.minimize_btn.clicked.connect(self.hide)
        button_layout.addWidget(self.minimize_btn)

        self.close_btn = QPushButton("✓ 完成")
        self.close_btn.setEnabled(False)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50; 
                color: white; 
                border: none;
                border-radius: 4px;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:disabled {
                background-color: #bdbdbd;
            }
        """)
        self.close_btn.clicked.connect(self.accept)
        button_layout.addWidget(self.close_btn)

        main_layout.addWidget(button_frame)

        # 添加伸缩空间
        main_layout.addStretch(1)

    def update_progress(self, percent, message):
        """更新进度"""
        self.progress_bar.setValue(percent)
        self.progress_label.setText(message)

        # 视频生成完成后显示播放区域
        if percent >= 100 and "完成" in message:
            self.title_label.setText("✅ 视频生成完成")
            self.title_label.setStyleSheet("color: white; font-size: 16pt; font-weight: bold;")
            self.cancel_btn.setVisible(False)
            self.minimize_btn.setText("❐ 隐藏")
            self.close_btn.setEnabled(True)

            # 显示视频播放区域
            self.video_label.setVisible(True)
            self.control_container.setVisible(True)
            self.adjustSize()

    def cancel_operation(self):
        """取消操作"""
        if not self._cancelled:
            self._cancelled = True
            self.cancel_btn.setEnabled(False)
            self.cancel_btn.setText("取消中...")
            self.title_label.setText("🛑 正在取消...")
            self.cancelled.emit()

    def is_cancelled(self):
        return self._cancelled

    def show_video(self, video_path):
        """加载并显示视频 - 使用OpenCV实现兼容性最好的播放"""
        if not os.path.exists(video_path):
            return

        self.video_path = video_path
        self.cap = cv2.VideoCapture(video_path)

        if not self.cap.isOpened():
            logging.error(f"无法打开视频文件: {video_path}")
            return

        # 启用控制按钮
        self.play_btn.setEnabled(True)
        self.restart_btn.setEnabled(True)

        # 自动开始播放
        self.start_playback()

    def start_playback(self):
        """开始播放"""
        if self.cap is None or not self.cap.isOpened():
            return

        self.is_playing = True
        self.play_btn.setText("⏸ 暂停")

        # 设置定时器（根据视频帧率）
        fps = self.cap.get(cv2.CAP_PROP_FPS)
        if fps <= 0:
            fps = 30
        interval = int(1000 / fps)

        if self.timer:
            self.timer.stop()
            self.timer.deleteLater()

        self.timer = QTimer(self)
        self.timer.setInterval(interval)
        self.timer.timeout.connect(self.update_frame)
        self.timer.start()

        # 立即显示第一帧
        self.update_frame()

    def pause_playback(self):
        """暂停播放"""
        self.is_playing = False
        self.play_btn.setText("▶ 播放")
        if self.timer:
            self.timer.stop()

    def toggle_playback(self):
        """切换播放/暂停"""
        if self.is_playing:
            self.pause_playback()
        else:
            self.start_playback()

    def restart_playback(self):
        """重新播放"""
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            if not self.is_playing:
                self.start_playback()

    def update_frame(self):
        """更新视频帧"""
        if not self.cap or not self.cap.isOpened() or not self.is_playing:
            return

        ret, frame = self.cap.read()
        if not ret:
            # 视频结束，自动重播
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            ret, frame = self.cap.read()
            if not ret:
                self.pause_playback()
                return

        # 转换颜色空间 BGR -> RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # 转换为QImage
        h, w, ch = frame.shape
        bytes_per_line = ch * w
        q_img = QImage(frame.data, w, h, bytes_per_line, QImage.Format_RGB888)

        # 缩放以适应标签
        pixmap = QPixmap.fromImage(q_img)
        scaled_pixmap = pixmap.scaled(self.video_label.size(),
                                      Qt.KeepAspectRatio,
                                      Qt.SmoothTransformation)
        self.video_label.setPixmap(scaled_pixmap)

    def closeEvent(self, event):
        """关闭事件处理"""
        if self.timer:
            self.timer.stop()
            self.timer.deleteLater()
            self.timer = None

        if self.cap:
            self.cap.release()
            self.cap = None

        if self.progress_bar.value() >= 100 or self._cancelled:
            event.accept()
        else:
            event.ignore()  # 阻止关闭进行中的生成