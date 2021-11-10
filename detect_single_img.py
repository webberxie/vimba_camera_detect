import cv2
import time
import math
img = cv2.imread('./biaodin/biaodin1.png')
img_h,img_w,_ = img.shape
img = cv2.resize(img,(img_w//5,img_h//5))


# 检测角点
# 7*10,ret为bool变量，corners为角点矩阵(6*9=54个角点，包括x,y坐标)
ret, corners = cv2.findChessboardCorners(img, (6, 9), None)
# print(ret,corners.shape) # True , (54,1,2)
if not ret:
    print('没有检测到')
else:

    point1 = corners[0,0,:]
    point2 = corners[5,0,:]
    point3 = corners[-1,0,:]
    point4 = corners[-6,0,:]

    delta_1 = (point2 - point1) / 5
    delta_2 = (point4 - point1) / 8

    real_point1 = point1 - delta_1 - delta_2
    real_point2 = point2 + delta_1 - delta_2
    real_point3 = point3 + delta_1 + delta_2
    real_point4 = point4 - delta_1 + delta_2

    # 将四个真实边缘点绘制出来，矩形绘制
    cv2.circle(img, (real_point1[0],real_point1[1]), 10, (255, 0, 0), 2)
    cv2.circle(img, (real_point2[0],real_point2[1]), 10, (255, 0, 0), 2)
    cv2.circle(img, (real_point3[0],real_point3[1]), 10, (255, 0, 0), 2)
    cv2.circle(img, (real_point4[0],real_point4[1]), 10, (255, 0, 0), 2)
    # cv2.rectangle(img, (real_point1[0],real_point1[1]) , (real_point3[0],real_point3[1]), (0,255,0), 2)
    # 绘制矩形
    point_color = (0, 255, 0) # BGR
    thickness = 1
    lineType = 4
    cv2.line(img, (real_point1[0],real_point1[1]), (real_point2[0],real_point2[1]), point_color, thickness, lineType)
    cv2.line(img, (real_point2[0],real_point2[1]), (real_point3[0],real_point3[1]), point_color, thickness, lineType)
    cv2.line(img, (real_point3[0],real_point3[1]), (real_point4[0],real_point4[1]), point_color, thickness, lineType)
    cv2.line(img, (real_point4[0],real_point4[1]), (real_point1[0],real_point1[1]), point_color, thickness, lineType)


    cv2.drawChessboardCorners(img, (6, 9), corners, ret)  # 记住，OpenCV的绘制函数一般无返回值

# 标定的参数
div_dx = 7.47262955e+03
div_dy = 7.49407819e+03
u0 = 2.45439015e+03
v0 = 1.42906876e+03
fc = 0.025
W = 0.161 # 靶标真实宽度
# 根据标定结果，计算坐标
def cal_xy_with_uv(u0,v0,fc,div_dx,div_dy,u,v):
    x = (u - u0) * fc * fc * div_dx
    y = (v - v0) * fc * fc * div_dy
    return x,y

# 计算距离
def dis_cal(fc,W,w):
    '''

    :param fc: 焦距
    :param W: 靶标高度
    :param w: 靶标相机成像高度
    :return: 距离
    '''
    return fc * W / w

x1,y1 = cal_xy_with_uv(u0,v0,fc,div_dx,div_dy,real_point1[0],real_point1[1])
x2,y2 = cal_xy_with_uv(u0,v0,fc,div_dx,div_dy,real_point2[0],real_point2[1])
w = math.sqrt( (x1-x2)*(x1-x2) + (y1-y2)*(y1-y2) )

dis = dis_cal(fc,W,w)
print(dis)

# print(type(img))
cv2.imshow('img',img)
cv2.waitKey(0)