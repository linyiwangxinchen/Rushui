import logging
import time

from PyQt5.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition


class CalculationThread(QThread):
    """后台计算线程，防止UI卡顿"""
    progress = pyqtSignal(int, str)  # 进度百分比和消息
    realtime_update = pyqtSignal(object)  # 实时更新数据
    finished = pyqtSignal(object)  # 计算完成，返回结果
    error = pyqtSignal(str)  # 发生错误

    def __init__(self, rushui_instance, parent=None):
        super().__init__(parent)
        self.rushui = rushui_instance
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
            
            # 从界面获取参数并更新到rushui实例
            self.update_parameters_from_ui()
            
            self.progress.emit(10, "设置初始条件...")
            self.rushui.set_initial_conditions()
            self.rushui.update_initial_conditions()
            
            self.progress.emit(20, "准备动力学仿真...")
            
            # 设置回调函数
            self.rushui.update_callback = self.send_update
            self.rushui.progress_callback = self.send_progress
            
            self.progress.emit(30, "开始求解轨迹...")
            
            # 启动主计算 - Rushui使用solve_trajectory方法
            self.rushui.solve_trajectory()
            
            if not self.is_running:
                self.progress.emit(100, "计算已中止")
                return
            
            self.progress.emit(95, "处理结果数据...")
            
            # Rushui的结果直接存储在实例中(ts, ys等属性)
            results = {
                'status': 'success',
                'ts': self.rushui.ts,
                'ys': self.rushui.ys,
                'message': '计算完成'
            }

            self.progress.emit(100, "计算完成")
            self.finished.emit(results)

        except Exception as e:
            logging.exception("计算过程中发生错误")
            self.error.emit(f"计算错误: {str(e)}")

    def update_parameters_from_ui(self):
        """从界面获取参数并更新到rushui实例"""
        # 从ModelParameterWidget获取的参数
        if hasattr(self.rushui, 'x0'):
            # 位置参数
            self.rushui.x0 = self.rushui.x0  # 从界面获取
            self.rushui.y0 = self.rushui.y0
            self.rushui.z0 = self.rushui.z0
            # 姿态参数
            self.rushui.theta = self.rushui.theta / self.rushui.RTD  # 转换为弧度
            self.rushui.psi = self.rushui.psi / self.rushui.RTD
            self.rushui.phi = self.rushui.phi / self.rushui.RTD
            # 速度参数
            self.rushui.vx = self.rushui.vx
            self.rushui.vy = self.rushui.vy
            self.rushui.vz = self.rushui.vz
            # 角速度参数
            self.rushui.wx = self.rushui.wx / self.rushui.RTD  # 转换为弧度
            self.rushui.wy = self.rushui.wy / self.rushui.RTD
            self.rushui.wz = self.rushui.wz / self.rushui.RTD
            # 空化器参数
            self.rushui.DK = self.rushui.dk / self.rushui.RTD
            self.rushui.DS = self.rushui.ds / self.rushui.RTD
            self.rushui.DX = self.rushui.dxx / self.rushui.RTD
            self.rushui.dkf = self.rushui.dkf / self.rushui.RTD
            self.rushui.dsf = self.rushui.dsf / self.rushui.RTD
            self.rushui.dxf = self.rushui.dxf / self.rushui.RTD
            # 推力参数
            self.rushui.T1 = self.rushui.t1
            self.rushui.T2 = self.rushui.t2
            # 控制参数
            self.rushui.kth = self.rushui.kth
            self.rushui.kps = self.rushui.kps
            self.rushui.kph = self.rushui.kph
            self.rushui.kwx = self.rushui.kwx
            self.rushui.kwz = self.rushui.kwz
            self.rushui.kwy = self.rushui.kwy
        # 从SimulationControlWidget获取的参数
        if hasattr(self.rushui, 'dt'):
            self.rushui.dt = self.rushui.dt
        if hasattr(self.rushui, 't0'):
            self.rushui.t0 = self.rushui.t0
        if hasattr(self.rushui, 'tend'):
            self.rushui.tend = self.rushui.tend
        # 从SimulationControlWidget获取的起始条件参数
        if hasattr(self.rushui, 'YCS'):
            self.rushui.YCS = self.rushui.ycs
        if hasattr(self.rushui, 'THETACS'):
            self.rushui.THETACS = self.rushui.thetacs / self.rushui.RTD
        if hasattr(self.rushui, 'VYCS'):
            self.rushui.VYCS = self.rushui.yvcs
        if hasattr(self.rushui, 'PSICS'):
            self.rushui.PSICS = self.rushui.psics / self.rushui.RTD

    def update_model_parameters(self):
        """更新模型关键参数"""
        params = {
            'model_length': self.rushui.L,
            'cavitator_diameter': self.rushui.RK * 2,  # 直径是半径的2倍
            'cavitator_angle': self.rushui.Beta,
            'pitch_disturbance': self.rushui.Omega0,
            'velocity': self.rushui.vx,
            'depth': self.rushui.y0,
            'cavity_pressure': self.rushui.Pc,
            'cavity_length': self.rushui.LK,
            'cavity_diameter': self.rushui.RK * 2,
            'force_coefficients': {
                'Cpr': self.rushui.Cpr if hasattr(self.rushui, 'Cpr') else 0,
                'Cnx': self.rushui.Cya if hasattr(self.rushui, 'Cya') else 0,
                'Cny': self.rushui.Cydc if hasattr(self.rushui, 'Cydc') else 0,
                'Cnm': self.rushui.Cywz if hasattr(self.rushui, 'Cywz') else 0,
                'Csx': self.rushui.mza if hasattr(self.rushui, 'mza') else 0,
                'Csy': self.rushui.mzdc if hasattr(self.rushui, 'mzdc') else 0,
                'Csm': self.rushui.mzwz if hasattr(self.rushui, 'mzwz') else 0
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


