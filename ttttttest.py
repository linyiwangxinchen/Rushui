#                    _ooOoo_
#                   o8888888o
#                   88" . "88
#                   (| -_- |)
#                   O\  =  /O
#                ____/`---'\____
#              .'  \\|     |//  `.
#             /  \\|||  :  |||//  \
#            /  _||||| -:- |||||-  \
#            |   | \\\  -  /// |   |
#            | \_|  ''\---/''  |   |
#            \  .-\__  `-`  ___/-. /
#          ___`. .'  /--.--\  `. . __
#       ."" '<  `.___\_<|>_/___.'  >'"".
#      | | :  `- \`.;`\ _ /`;.`/ - ` : | |
#      \  \ `-.   \_ __\ /__ _/   .-` /  /
# ======`-.____`-.___\_____/___.-`____.-'======
#                    `=---='
# ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
#             佛祖保佑       永无BUG
# ——————————控制参数——————————
control_dive_group = QGroupBox("入水参数")
control_dive_layout_data = QGridLayout()
control_dive_layout_data.setContentsMargins(5, 5, 5, 5)
control_dive_layout_data.setSpacing(5)

# 俯仰角增益 kth (对应原self.kth)
self.add_labeled_input(control_dive_layout_data, "俯仰角增益 k_theta:", 0, 0, -1000, 1000, 4, 0.1, "k_theta_input", range_check=False)

# 姿态同步增益 kps (关联kth)
self.add_labeled_input(control_dive_layout_data, "姿态同步增益 k_ps:", 1, 0, -1000, 1000, 4, 0.1, "k_ps_input", range_check=False)

# 舵机响应增益 kph
self.add_labeled_input(control_dive_layout_data, "舵机响应增益 k_ph:", 2, 0, -1000, 1000, 0.08, 0.01, "k_ph_input", range_check=False)

# 滚转角速度增益 kwx
self.add_labeled_input(control_dive_layout_data, "滚转角速度增益 k_wx:", 3, 0, -1000, 1000, 0.0016562, 0.000001, "k_wx_input", range_check=False)

# 偏航角速度增益 kwz
self.add_labeled_input(control_dive_layout_data, "偏航角速度增益 k_wz:", 4, 0, -1000, 1000, 0.312, 0.001, "k_wz_input", range_check=False)

# 垂向控制增益 kwy (关联kwz)
self.add_labeled_input(control_dive_layout_data, "垂向控制增益 k_wy:", 5, 0, -1000, 1000, 0.312, 0.001, "k_wy_input", range_check=False)

control_dive_group.setLayout(control_dive_layout_data)