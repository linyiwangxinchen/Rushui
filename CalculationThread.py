import logging
import time

from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition


class CalculationThread(QThread):
    """后台计算线程，防止UI卡顿"""
    progress = pyqtSignal(int, str)  # 进度百分比和消息
    realtime_update = pyqtSignal(object)  # 实时更新数据
    finished = pyqtSignal(object)  # 计算完成，返回结果
    error = pyqtSignal(str)  # 发生错误

    def __init__(self, stab_instance, parent=None):
        super().__init__(parent)
        self.rushui = stab_instance
        self.is_running = True
        self.is_paused = False
        self.update_interval = 0.05  # 最小更新间隔（秒）
        self.last_update_time = 0
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()

    def run(self):
        try:
            # 准备计算
            self.progress.emit(0, "初始化计算参数...")

            # 设置回调函数
            self.rushui.update_callback = self.send_update
            self.rushui.progress_callback = self.send_progress


            # 启动主计算
            self.rushui.main()

            if not self.is_running:
                self.progress.emit(100, "计算已中止")
                return

            self.progress.emit(100, "计算完成")


        except Exception as e:
            logging.exception("计算过程中发生错误")
            self.error.emit(f"计算错误: {str(e)}")

    def update_model_parameters(self):
        """更新模型关键参数"""
        params = {
            'model_length': self.stab.Lm,
            'cavitator_diameter': self.stab.Dnmm,
            'cavitator_angle': self.stab.Beta,
            'cavitator_slope': self.stab.RibTan[0] if len(self.stab.RibTan) > 0 else 0,
            'pitch_disturbance': self.stab.Omega0,
            'velocity': self.stab.V0,
            'depth': self.stab.H0,
            'cavity_pressure': self.stab.Pc,
            'cavity_length': self.stab.Lc0 * self.stab.Rn * self.stab.Lm,
            'cavity_diameter': self.stab.Rc0 * self.stab.Lm,
            'force_coefficients': {
                'Cpr': self.stab.Cpr,
                'Cnx': self.stab.Cnx,
                'Cny': self.stab.Cny,
                'Cnm': self.stab.Cnm,
                'Csx': self.stab.Csx,
                'Csy': self.stab.Csy,
                'Csm': self.stab.Csm
            }
        }
        self.realtime_update.emit(params)

    def send_progress(self, j, max_steps):
        """发送计算进度"""
        if max_steps > 0:
            percent = int(j / max_steps * 100)  # 25%是前期准备，70%是主计算
            self.progress.emit(percent, f"正在计算: {j}/{max_steps} 步")

    def send_update(self, data):
        """发送实时更新数据，但控制发送频率"""
        current_time = time.time()
        if current_time - self.last_update_time > self.update_interval:
            self.mutex.lock()
            try:
                if self.is_paused:
                    self.wait_condition.wait(self.mutex)
                self.realtime_update.emit(data)
            finally:
                self.mutex.unlock()
                a = 1
            self.last_update_time = current_time

    def pause(self):
        """暂停计算线程"""
        self.mutex.lock()
        self.is_paused = True
        self.mutex.unlock()

    def resume(self):
        """恢复计算线程"""
        self.mutex.lock()
        self.is_paused = False
        self.wait_condition.wakeAll()
        self.mutex.unlock()

    def stop(self):
        """停止计算线程"""
        self.is_running = False
        self.resume()  # 确保线程不会卡在暂停状态


