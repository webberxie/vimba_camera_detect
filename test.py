'''
@Author: 谢雨含
@First edit: 2021.9.20
@Last edit: 2021.10.14
@Use: 智能光电感知实验课示例代码,包括距离测算函数，靶标检测函数
'''

import cv2
import math

# 距离计算函数
def distance_to_camera(W, F, P):

    # compute and return the distance from the maker to the camera

    '''

    :param W: 靶标短边的实际距离(0.161m)
    :param F: 焦距
    :param P: 靶标短边的像素宽度(pixel)
    :return: 距离(m)
    '''

    # 仅保留三位小数
    return round( (W * F) / P,3)

# 检测靶标函数
def detect(img):
    '''

    :param img: 输入图像
    :return: img(叠加靶标检测结果的图像)，ret(bool,是否检测到靶标)，w(检测靶标的的短边欧式距离，单位：pixel)
    '''
    # 检测角点
    # 靶标整体7*10,ret为bool变量，corners为角点矩阵(6*9=54个角点，包括x,y坐标)
    ret, corners = cv2.findChessboardCorners(img, (6, 9), None)
    # print(ret,corners.shape) # True , (54,1,2)
    if not ret:
        print('没有检测到靶标')
        w = -1
    else:
        point1 = corners[0, 0, :]
        point2 = corners[5, 0, :]
        point3 = corners[-1, 0, :]
        point4 = corners[-6, 0, :]

        delta_1 = (point2 - point1) / 5
        delta_2 = (point4 - point1) / 8

        real_point1 = (point1 - delta_1 - delta_2).astype(int)
        real_point2 = (point2 + delta_1 - delta_2).astype(int)
        real_point3 = (point3 + delta_1 + delta_2).astype(int)
        real_point4 = (point4 - delta_1 + delta_2).astype(int)

        # 将四个真实边缘点绘制出来，矩形绘制
        cv2.circle(img, (real_point1[0], real_point1[1]), 10, (255, 0, 0), 2)
        cv2.circle(img, (real_point2[0], real_point2[1]), 10, (255, 0, 0), 2)
        cv2.circle(img, (real_point3[0], real_point3[1]), 10, (255, 0, 0), 2)
        cv2.circle(img, (real_point4[0], real_point4[1]), 10, (255, 0, 0), 2)
        # cv2.rectangle(img, (real_point1[0],real_point1[1]) , (real_point3[0],real_point3[1]), (0,255,0), 2)
        # 绘制矩形(四点两两连线)
        point_color = (255, 255, 0)  # BGR
        thickness = 5
        lineType = 4
        # 注：此处如果报错，要求为int，将所有点转为int类型；部分版本支持float类型输入
        cv2.line(img, (real_point1[0], real_point1[1]), (real_point2[0], real_point2[1]), point_color, thickness,
                 lineType)
        cv2.line(img, (real_point2[0], real_point2[1]), (real_point3[0], real_point3[1]), point_color, thickness,
                 lineType)
        cv2.line(img, (real_point3[0], real_point3[1]), (real_point4[0], real_point4[1]), point_color, thickness,
                 lineType)
        cv2.line(img, (real_point4[0], real_point4[1]), (real_point1[0], real_point1[1]), point_color, thickness,
                 lineType)

        dis = real_point1 - real_point2
        w = math.sqrt(dis[0]*dis[0] + dis[1]*dis[1])
    return img,ret,w




