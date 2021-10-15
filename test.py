'''
@Author: 谢雨含
@First edit: 2021.9.20
@Last edit: 2021.10.14
@Use: 智能光电感知实验课示例代码demo，实现相机实时展示检测框，以及目标距离
'''
from vimba import *
import cv2
import numpy as np

# 检测靶标函数
def detect_circle_demo(image):

    dst = cv2.GaussianBlur(image,(13,15),15)  # 使用高斯模糊，修改卷积核ksize也可以检测出来
    gray = dst
    # gray = cv2.cvtColor(dst,cv2.COLOR_BGR2GRAY)  # 转为灰度图

    circles = cv2.HoughCircles(gray,cv2.HOUGH_GRADIENT,1,30,param1=20,param2=60,minRadius=0,maxRadius=0)
    # print(circles)
    if circles is None:
        return None,None,None

    # 找最大的圆形（此部分代码应当改为找黑色占比最大的圆形才对，可优化）
    circles = np.uint16(np.around(circles)) #around对数据四舍五入，为整数
    max_radis,max_circle=0,None
    for i in circles[0,:]:
        if i[2]>max_radis:
            max_radis=i[2]
            max_circle=i
    center_x,center_y,radis=max_circle[0],max_circle[1],max_circle[2]

    return center_x,center_y,radis

# 距离计算函数
def distance_to_camera(W, F, P):

    # compute and return the distance from the maker to the camera

    # 仅保留三位小数
    return round( (W * F) / P,3)

# 检测框实时可视化demo，由于计算的延迟，故展示效果会比较卡顿；算法还可优化，以减少计算延迟
def demo():
    with Vimba.get_instance() as vimba:
        cams = vimba.get_all_cameras()
        with cams[0] as cam:
            exposure_time = cam.ExposureTime
            time = exposure_time.get()
            # 改变曝光时间
            # inc = exposure_time.get_increment()
            # exposure_time.set(time + inc * 10)
            print('exposure_time:',time)
            # 曝光时间

            Frame_Rate=cam.get_feature_by_name("AcquisitionFrameRateEnable")
            Frame_Rate.set(True)
            Frame_Rate=cam.get_feature_by_name("AcquisitionFrameRate")
            Frame_Rate.set(1.2)
            print('FrameRate:', Frame_Rate)
            # 帧率

            gain = cam.get_feature_by_name("Gain")
            gain.set(1)
            print('Gain:', gain)
            # 增益

            # Aquire single frame synchronously
            # frame = cam.get_frame()
            # Aquire 10 frames synchronously
            for frame in cam.get_frame_generator(limit=100):
                frame_temp = frame.as_opencv_image()

                # resize_frame = cv2.resize(frame_temp,(300,400))
                center_x, center_y, radis = detect_circle_demo(frame_temp)
                if not center_x:
                    print('没有检测到圆形')
                else:
                    print('圆心在照片中的位置(像素)：', center_x, center_y, '半径长度（m）:', radis)

                    # 初始焦距测算实验
                    # F = (P * D) / W
                    # 初始测试中，相机拍摄靶标距离0.38m，靶标直径0.1m,在拍摄照片中直径占据像素长度为1028像素;
                    # 后续微调焦距，可视为微小误差；故我们视焦距为一定值
                    focallength = (1028 * 0.38) / 0.1
                    # 当前测试，计算距离
                    W = 0.1
                    dis = distance_to_camera(W, focallength, radis)

                # 绘图展示
                resize_rate = 6
                img_w, img_h, _ = frame_temp.shape
                #print('当前图片分辨率：','高度：',img_h,'宽度：',img_w)
                frame_temp = cv2.resize(frame_temp, (int(img_h / resize_rate), int(img_w / resize_rate)))
                if center_x!=None:
                    cv2.circle(frame_temp, (int(center_x / resize_rate), int(center_y / resize_rate)), int(radis / resize_rate),
                               (0, 0, 255), 2)
                    cv2.circle(frame_temp, (int(center_x / resize_rate), int(center_y / resize_rate)), 2, (255, 0, 0), 2)  # 圆心
                    print('当前靶标与摄像头距离(m)：', dis)
                cv2.imshow("detect_circle_demo", frame_temp)
                cv2.waitKey(1)
if __name__ == "__main__":
    demo()

