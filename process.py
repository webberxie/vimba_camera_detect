'''
@Author: 谢雨含
@First edit: 2021.10.12
@Last edit: 2021.10.14
@Use: 智能光电感知实验课示例代码，实现相机基本参数展示，实时画面采集展示，靶标检测、定位距离
'''

from ui3 import *
from PyQt5.QtGui import QImage,QPixmap
from PyQt5.QtCore import *
# from PyQt5.QtCore import QThread, pyqtSignal#多线程
from PyQt5.QtWidgets import *
import sys
import cv2
import numpy as np
from test import detect_circle_demo,distance_to_camera
from vimba import *


class Ui_example(QWidget):
    def __init__(self,name='机器视觉'):
        # 构造函数
        super().__init__()
        # 采集线程
        self._translate = QCoreApplication.translate
        self.mythread = MyThread()  # 实例化自己建立的任务线程类
        self.mythread.signal.connect(self.image_callback)  # 设置任务线程发射信号触发的函数
        self.mythread.signal2.connect(self.showdata)
        self.initUI(name)


    def initUI(self, name):
        # 初始化函数
        self.ui = Ui_Form()  # 引用designer设计好的窗口
        self.ui.setupUi(self)
        self.setWindowTitle(name)
        self.initConnect()
        self.mythread.start()  # 启动任务线程

    def initConnect(self):
        # 初始化信号与槽:链接识别键与分析识别函数analysis
        self.ui.pushButton.clicked.connect(self.analysis)
        pass

    def analysis(self):
        # 按下识别键后，进行目标检测，计算距离
        global img
        center_x, center_y, radis = detect_circle_demo(img)
        if not center_x:
            print('没有检测到圆形')
        else:
            print('圆心在照片中的位置(像素)：', center_x, center_y, '半径长度:', radis)

            # 初始焦距测算实验标定
            # F = (P * D) / W
            # 初始测试中，相机拍摄靶标距离0.38m，靶标直径0.1m,在拍摄照片中直径占据像素长度为1028像素;
            # 后续微调焦距，可视为微小误差；故我们视焦距为一定值
            focallength = (1028 * 0.38) / 0.1
            # 当前测试（已知靶标宽度0.1m），根据相似三角原理，计算距离
            W = 0.1
            dis = distance_to_camera(W, focallength, radis)

            # 显示目标radis(指占据原图缩少像素，单位:pixel)，dis(单位：m)
            self.ui.label_12.setText(self._translate("Form", str(radis)+' '+'pixel'))
            self.ui.label_13.setText(self._translate("Form", str(dis)+' '+'m'))
        return None

    # =======================多线程回调
    def image_callback(self, image):  # 这里的image就是任务线程传回的图像数据,类型必须是已经定义好的数据类型
        global img
        img = image
        img_w,img_h,_ = image.shape
        # print('get')

        # 实时图像可视化
        resize_rate = 6  # 图像缩小比例，方便展示
        frame_temp = image
        img_w, img_h, _ = frame_temp.shape
        # print('当前图片分辨率：', '高度：', img_h, '宽度：', img_w)
        frame_temp = cv2.resize(frame_temp, (int(img_h / resize_rate), int(img_w / resize_rate)))
        cv2.imshow("real time image", frame_temp)
        cv2.waitKey(1)

        # 图像展示于QT界面中，由于图像格式无法转换，故此部分不处理，改为由cv2展示替代
        image = QImage(image.data, img_w, img_h, 1, QImage.Format_Indexed8)
        self.ui.label_7.setPixmap(QPixmap.fromImage(image))


    # 输入数据：[time, Frame_Rate, gain, img_w, img_h,frame_set,gain_set]
    def showdata(self,data):
        # 曝光时间
        self.ui.label_8.setText(self._translate("Form", str(data[0])))
        # 帧率
        self.ui.label_9.setText(self._translate("Form", str(data[5])))
        # 分辨率
        self.ui.label_10.setText(self._translate("Form", str(data[3])+' '+str(data[4])))
        # 增益
        self.ui.label_11.setText(self._translate("Form", str(data[6])))





# 多线程类
class MyThread(QThread):  # 建立一个任务线程类
    signal = pyqtSignal(np.ndarray)  # 设置触发信号传递的参数数据类型,传递信号必须事先定义好数据类型
    signal2 = pyqtSignal(list)

    def __init__(self):
        super(MyThread, self).__init__()

    def run(self):  # 在启动线程后任务从这个函数里面开始执行
        with Vimba.get_instance() as vimba:
            cams = vimba.get_all_cameras()
            # 获取当前相机
            with cams[0] as cam:
                # 曝光时间
                exposure_time = cam.ExposureTime
                time = exposure_time.get()
                # inc = exposure_time.get_increment()
                # exposure_time.set(time + inc *100 )
                print('exposure_time:', time)


                # 帧率
                Frame_Rate = cam.get_feature_by_name("AcquisitionFrameRateEnable")
                Frame_Rate.set(True)
                Frame_Rate = cam.get_feature_by_name("AcquisitionFrameRate")
                frame_set = 10
                Frame_Rate.set(frame_set)
                print('FrameRate:', Frame_Rate)


                # 增益
                gain = cam.get_feature_by_name("Gain")
                gain_set = 1
                gain.set(gain_set)
                print('Gain:', gain_set)


                # Acquire single frame synchronously
                # frame = cam.get_frame()
                # Acquire  frames synchronously
                # limit为最大时限
                for frame in cam.get_frame_generator(limit=100000):
                    # 获得当前帧图像
                    frame_temp = frame.as_opencv_image()
                    img_w, img_h, _ = frame_temp.shape
                    basic_data_list = [time,Frame_Rate,gain,img_w, img_h,frame_set,gain_set]
                    self.signal2.emit(basic_data_list)
                    self.signal.emit(frame_temp)  # 任务线程发射信号,图像，基本数据作为参数传递给主线程
        return None



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Ui_example()
    ex.show()
    sys.exit(app.exec_())