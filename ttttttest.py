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

# === 绘制水区域 ===
hwidth = self.stab.Hwidth
# 水下区域
water_polygon = plt.Polygon([[-hwidth, - yc], [hwidth, - yc], [hwidth, -hwidth], [-hwidth, -hwidth]],
                            color='lightblue', alpha=0.7)
ax.add_patch(water_polygon)

# 水上区域
above_water_polygon = plt.Polygon([[-hwidth, - yc], [hwidth, - yc], [hwidth, hwidth], [-hwidth, hwidth]],
                                  color='white', alpha=0.9)
ax.add_patch(above_water_polygon)

# === 绘制模型 ===
model_points = np.column_stack((
    xs2 + self.stab.XGmod - xc,
    ys2 + self.stab.YGmod - yc
))

# 绘制模型主体
model_polygon = plt.Polygon(model_points, facecolor='green', alpha=0.8, edgecolor='black')
ax.add_patch(model_polygon)

# === 绘制加强肋 ===
if hasattr(self.stab, 'XGrib') and hasattr(self.stab, 'YGrib'):
    for j in range(0, self.stab.Ncon - 1):
        idx1 = 2 * j
        idx2 = 2 * j + 1
        if idx1 < len(self.stab.XGrib) and idx2 < len(self.stab.XGrib):
            plt.plot([xs2 + self.stab.XGrib[idx1] - xc, xs2 + self.stab.XGrib[idx2] - xc],
                     [ys2 + self.stab.YGrib[idx1] - yc, ys2 + self.stab.YGrib[idx2] - yc],
                     'k-', linewidth=1)

# === 绘制质心 ===
xc, yc = self.stab.TurnPointOnGamma(-self.stab.Xabs, self.stab.Yabs)

# plt.plot(xc, yc, 'ro', markersize=5, label='质心')
plt.plot(0, 0, 'ro', markersize=5, label='质心')

# === 绘制网格 ===
grid_color = 'gray'
grid_alpha = 0.3

# 垂直网格线
dx = 2.0 * hwidth / 10.0
for j in range(1, 10):
    x = -hwidth + j * dx
    plt.plot([x, x], [-hwidth, hwidth], color=grid_color, alpha=grid_alpha, linestyle='--')

# 水平网格线
dy = dx
for j in range(1, 10):
    y = -hwidth + j * dy
    plt.plot([-hwidth, hwidth], [y, y], color=grid_color, alpha=grid_alpha, linestyle='--')

# === 绘制水面和参考线 ===
plt.plot([-hwidth, hwidth], [- yc, - yc], 'b-', linewidth=1.5, label='水面')
plt.plot([0, 0], [-hwidth, hwidth], color='gray', linestyle='--', alpha=0.7)

# x轴方向（根据入水角度）
x_axis_length = 2.0 * self.stab.Scale
plt.plot([x_axis_length * cos_g, -x_axis_length * cos_g],
         [-x_axis_length * sin_g, x_axis_length * sin_g],
         'k-', alpha=0.7, label='x轴')

# === 重构的空腔轮廓绘制 - 修复连接问题 ===
cavity_color = 'blue'
cavity_linewidth = 1.5
x = 0
# 主要修复：增强空腔轮廓生成
if hasattr(self.stab, 'Xpr') and hasattr(self.stab, 'Ypr1') and hasattr(self.stab, 'Ypr2') and hasattr(self.stab, 'Ipr'):
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
                xt, yt = self.stab.TurnPointOnGamma(xpr_val, RcBegX + self.stab.Yax0[self.stab.Jend])
                if ys2 + yt <= 0:
                    cavity_points_upper.append((xs2 + xt, ys2 + yt))

            elif xpr_val < self.stab.XcBeg[2]:  # XcBeg(3)
                xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[1], self.stab.RcBeg[1] + self.stab.Yax0[self.stab.Jend])
                if ys2 + yt <= 0:
                    cavity_points_upper.append((xs2 + xt, ys2 + yt))
                RcBegX = self.stab.Rn * (1.0 + 3.0 * xpr_val / self.stab.Rn) ** (1.0 / 3.0)
                xt, yt = self.stab.TurnPointOnGamma(xpr_val, RcBegX + self.stab.Yax0[self.stab.Jend])
                if ys2 + yt <= 0:
                    cavity_points_upper.append((xs2 + xt, ys2 + yt))

            elif xpr_val < self.stab.XcBeg[3]:  # XcBeg(4)
                xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[1], self.stab.RcBeg[1] + self.stab.Yax0[self.stab.Jend])
                if ys2 + yt + self.stab.RcBeg[1] <= 0:
                    cavity_points_upper.append((xs2 + xt, ys2 + yt))
                xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[2], self.stab.RcBeg[2] + self.stab.Yax0[self.stab.Jend])
                if ys2 + yt <= 0:
                    cavity_points_upper.append((xs2 + xt, ys2 + yt))
                RcBegX = self.stab.Rn * (1.0 + 3.0 * xpr_val / self.stab.Rn) ** (1.0 / 3.0)
                xt, yt = self.stab.TurnPointOnGamma(xpr_val, RcBegX + self.stab.Yax0[self.stab.Jend])
                if ys2 + yt <= 0:
                    cavity_points_upper.append((xs2 + xt, ys2 + yt))

            else:
                xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[1], self.stab.RcBeg[1] + self.stab.Yax0[self.stab.Jend])
                if ys2 + yt <= 0:
                    cavity_points_upper.append((xs2 + xt, ys2 + yt))
                xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[2], self.stab.RcBeg[2] + self.stab.Yax0[self.stab.Jend])
                if ys2 + yt <= 0:
                    cavity_points_upper.append((xs2 + xt, ys2 + yt))
                xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[3], self.stab.RcBeg[3] + self.stab.Yax0[self.stab.Jend])
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
                    RcBegX = self.stab.Rn * (1.0 + 3.0 * self.stab.Xpr[idx] / self.stab.Rn) ** (1.0 / 3.0)
                    xt, yt = self.stab.TurnPointOnGamma(self.stab.Xpr[idx], RcBegX + self.stab.Yax0[self.stab.Jend])
                    if ys2 + yt <= 0:
                        cavity_points_upper.append((xs2 + xt, ys2 + yt))

                elif self.stab.Xpr[idx] < self.stab.XcBeg[2]:  # XcBeg(3)
                    RcBegX = self.stab.Rn * (1.0 + 3.0 * self.stab.Xpr[idx] / self.stab.Rn) ** (1.0 / 3.0)
                    xt, yt = self.stab.TurnPointOnGamma(x, RcBegX + self.stab.Yax0[self.stab.Jend])
                    if ys2 + yt <= 0:
                        cavity_points_upper.append((xs2 + xt, ys2 + yt))

                elif self.stab.Xpr[idx] < self.stab.XcBeg[3]:  # XcBeg(4)
                    RcBegX = self.stab.Rn * (1.0 + 3.0 * self.stab.Xpr[idx] / self.stab.Rn) ** (1.0 / 3.0)
                    xt, yt = self.stab.TurnPointOnGamma(x, RcBegX + self.stab.Yax0[self.stab.Jend])
                    if ys2 + yt <= 0:
                        cavity_points_upper.append((xs2 + xt, ys2 + yt))

                elif self.stab.Rcav[self.stab.Jend, idx] != 0:
                    xt, yt = self.stab.TurnPointOnGamma(self.stab.Xpr[idx - 1], self.stab.Ypr2[idx - 1])
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
            plt.plot(upper_x, upper_y, color=cavity_color, linewidth=cavity_linewidth)

    # 5. 修复下部空腔轮廓
    lower_sep_idx = 2 * self.stab.Ncon + 3 - 1  # Fortran索引 2*Ncon+3 -> Python索引 2*Ncon+2
    if lower_sep_idx < len(self.stab.XGmod) and lower_sep_idx < len(self.stab.YGmod):
        cavity_points_lower = [(xs2 + self.stab.XGmod[lower_sep_idx], ys2 + self.stab.YGmod[lower_sep_idx])]

        # 处理前几个特殊点
        if hasattr(self.stab, 'XcBeg') and len(self.stab.XcBeg) >= 4:
            xpr_val = self.stab.Xpr[1]  # Fortran索引2

            if xpr_val < self.stab.XcBeg[1]:  # XcBeg(2)
                RcBegX = self.stab.Rn * (1.0 + 3.0 * xpr_val / self.stab.Rn) ** (1.0 / 3.0)
                xt, yt = self.stab.TurnPointOnGamma(xpr_val, -RcBegX + self.stab.Yax0[self.stab.Jend])
                cavity_points_lower.append((xs2 + xt, ys2 + yt))

            elif xpr_val < self.stab.XcBeg[2]:  # XcBeg(3)
                xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[1], -self.stab.RcBeg[1] + self.stab.Yax0[self.stab.Jend])
                cavity_points_lower.append((xs2 + xt, ys2 + yt))
                RcBegX = self.stab.Rn * (1.0 + 3.0 * xpr_val / self.stab.Rn) ** (1.0 / 3.0)
                xt, yt = self.stab.TurnPointOnGamma(xpr_val, -RcBegX + self.stab.Yax0[self.stab.Jend])
                cavity_points_lower.append((xs2 + xt, ys2 + yt))

            elif xpr_val < self.stab.XcBeg[3]:  # XcBeg(4)
                xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[1], -self.stab.RcBeg[1] + self.stab.Yax0[self.stab.Jend])
                cavity_points_lower.append((xs2 + xt, ys2 + yt))
                xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[2], -self.stab.RcBeg[2] + self.stab.Yax0[self.stab.Jend])
                cavity_points_lower.append((xs2 + xt, ys2 + yt))
                RcBegX = self.stab.Rn * (1.0 + 3.0 * xpr_val / self.stab.Rn) ** (1.0 / 3.0)
                xt, yt = self.stab.TurnPointOnGamma(xpr_val, -RcBegX + self.stab.Yax0[self.stab.Jend])
                cavity_points_lower.append((xs2 + xt, ys2 + yt))

            else:
                # 添加所有过渡点
                xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[1], -self.stab.RcBeg[1] + self.stab.Yax0[self.stab.Jend])
                cavity_points_lower.append((xs2 + xt, ys2 + yt))
                xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[2], -self.stab.RcBeg[2] + self.stab.Yax0[self.stab.Jend])
                cavity_points_lower.append((xs2 + xt, ys2 + yt))
                xt, yt = self.stab.TurnPointOnGamma(self.stab.XcBeg[3], -self.stab.RcBeg[3] + self.stab.Yax0[self.stab.Jend])
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
                    xt, yt = self.stab.TurnPointOnGamma(self.stab.Xpr[idx - 1], self.stab.Ypr1[idx - 1])
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

            plt.plot(lower_x, lower_y, color=cavity_color, linewidth=cavity_linewidth)
