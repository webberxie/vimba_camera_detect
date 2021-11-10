'''
@Author: 谢雨含、郑凯元
@First edit: 2021.10.12
@Last edit: 2021.10.26
@Use: 智能光电感知实验课示例代码，实现相机基本参数展示，实时画面采集展示，靶标检测、定位距离
说明：该代码分类两个部分，线程ui_example实现ui界面，线程MyThread实现相机参数读取与设置，相机图像回传给ui界面
'''

'''
说明：
1、需要将在calibration标定好的focallength数值,给class Ui_example的子函数analysis2，将focallength的值设置为该数
2、如果进程卡住，或者异常退出，尝试以下方法：
（1）检查是否python端代码，与vimba viewer同时占用了相机；
（2）检查vimba viewer是否可以正常显示图像；可以的话再退出vimba viewer，重新运行该代码
（3）每一次修改相机内部参数后，可能第一次运行会出现异常退出；重新运行一次即可
3、如果相机没有检测到靶标，尝试以下方法：
（1）调大相机曝光时间到8000us，调节增益到12；这两个参数越大，图像越明亮
（2）检查靶标是否完全在镜头内（只有完全在镜头内才会检测到其角点）
4、如果vimba viewer检测不到相机，可能为主机该USB接口不适配导致，换主机的其他USB接口
'''

from ui import *
from PyQt5.QtGui import QImage,QPixmap
from PyQt5.QtCore import QTimer
from PyQt5.QtCore import *
# from PyQt5.QtCore import QThread, pyqtSignal#多线程
from PyQt5.QtWidgets import *
import sys
import cv2
import numpy as np
from test import distance_to_camera,detect
from vimba import *
import time


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
        #self.mythread.start()  # 启动任务线程
        self.ui.lineEdit.editingFinished.connect(self.change_exposure) #输入曝光时间
        self.ui.lineEdit_4.editingFinished.connect(self.change_gain) #输入增益
        i, okPressed = QInputDialog.getInt(self, "初始化帧率","请设置相机帧率在(1-15)",10,1,15)
        if okPressed:
            self.mythread.getfps = i
            self.mythread.start()
        else:
            sys.exit()

    def start_thread(self):
        self.mythread.start()  # 启动任务线程

    def initConnect(self):
        # 初始化信号与槽:链接识别键与分析识别函数analysis
        self.ui.pushButton.clicked.connect(self.analysis1)
        self.ui.pushButton_2.clicked.connect(self.analysis2)
        pass

    #修改曝光时间
    def change_exposure(self):
        try:
            value = int(self.ui.lineEdit.text())
            if value >=180:
                with Vimba.get_instance() as vimba:
                    cams = vimba.get_all_cameras()
                    # 获取当前相机
                    with cams[0] as cam:
                        exposure_time = cam.ExposureTime

                        exp_time = value
                        exposure_time.set(exp_time)
            else:
                QMessageBox.information(self,"曝光时间设置错误","曝光时间必须大于180（微秒）",QMessageBox.Yes)
                self.ui.lineEdit.clear()
        except:
            QMessageBox.information(self, "曝光时间设置错误", "请输入正确的格式")
            self.ui.lineEdit.clear()

    #修改增益
    def change_gain(self):
        if self.ui.lineEdit_4.text()=='':
            return
        else:
            try:
                value = int(self.ui.lineEdit_4.text()) #如果输入格式错误则报错，跳到except部分
                if value >=0 and value<=23: #判断增益是否在范围内
                    with Vimba.get_instance() as vimba:
                        cams = vimba.get_all_cameras()
                        # 获取当前相机
                        with cams[0] as cam:
                            gain = cam.get_feature_by_name("Gain")
                            gain_set = int(self.ui.lineEdit_4.text())
                            gain.set(gain_set)
                else:
                    QMessageBox.information(self,"增益设置错误","增益设置范围为：0—23")
                    self.ui.lineEdit_4.clear()
            except:
                QMessageBox.information(self, "增益设置错误", "请输入正确的格式")
                self.ui.lineEdit_4.clear()

    def analysis1(self):

        global w,resize_rate

        # 显示目标短边尺寸(指占据原图缩少像素，单位:pixel)
        self.ui.label_12.setText(self._translate("Form", str(round(w * resize_rate ,3)) + ' ' + 'pixel'))
    def analysis2(self):
        # 按下识别键后，进行计算距离
        global w , resize_rate
        # 初始焦距测算实验标定方法1
        # F = (P * D) / W
        # 初始测试中，相机拍摄靶标距离0.60m，靶标高度0.161m,在拍摄照片中直径占据像素长度为1711像素;
        # 后续微调焦距，可视为微小误差；故我们视焦距为一定值
        # focallength = (1711 * 0.60) / 0.161

        # 初始标定方法2(使用calibration.py，多张图片进行标定，取内存矩阵的fx/fy/fx与fy的平均值)
        focallength = 7601

        # 当前测试（已知靶标宽度0.161m），根据相似三角原理，计算距离
        W = 0.161
        dis = distance_to_camera(W, focallength, w * resize_rate) # 由于在展示区域缩放了3倍

        # 显示目标距离(m)
        self.ui.label_13.setText(self._translate("Form", str(dis)+' '+'m'))
        return None

    # =======================多线程回调
    def image_callback(self, image):  # 这里的image就是任务线程传回的图像数据,类型必须是已经定义好的数据类型
        start_time = time.time()
        global img , w ,resize_rate
        img = image
        img_w,img_h,_ = image.shape
        # print('get')

        # 实时图像可视化
        resize_rate = 3  # 图像缩小比例，方便展示
        self.frame_temp = image
        img_w, img_h, _ = self.frame_temp.shape
        # print('当前图片分辨率：', '高度：', img_h, '宽度：', img_w)
        self.frame_temp = cv2.resize(self.frame_temp, (int(img_h / resize_rate), int(img_w / resize_rate)))#适应ui界面

        #执行检测操作
        self.frame_temp,ret,w = detect(self.frame_temp)

        height, width= self.frame_temp.shape
        image = QImage(self.frame_temp.data, width, height, width,QImage.Format_Indexed8) #修改图像格式为QImage以便在UI中展示
        self.ui.label_7.setPixmap(QPixmap.fromImage(image))
        end_time = time.time()  # 结束时间
        print("img callback time:%f" % (end_time - start_time))  # 结束时间-开始时间


    # 输入数据：[time, Frame_Rate, gain, img_w, img_h,frame_set,gain_set]
    def showdata(self,data):
        # 曝光时间
        self.ui.lineEdit.setPlaceholderText(self._translate("Form", str(data[0])))
        # 帧率
        self.ui.label_15.setText(self._translate("Form", str(data[5])))
        # 分辨率
        self.ui.label_14.setText(self._translate("Form", str(data[3])+' '+str(data[4])))
        # 增益
        self.ui.lineEdit_4.setPlaceholderText(self._translate("Form", str(data[6])))


# 多线程类
class MyThread(QThread):  # 建立一个任务线程类
    signal = pyqtSignal(np.ndarray)  # 设置触发信号传递的参数数据类型,传递信号必须事先定义好数据类型
    signal2 = pyqtSignal(list)

    def __init__(self):
        super(MyThread, self).__init__()
        self.getfps = 10

    def run(self):  # 在启动线程后任务从这个函数里面开始执行
        with Vimba.get_instance() as vimba:
            cams = vimba.get_all_cameras()
            # 获取当前相机
            with cams[0] as cam:
                # 曝光时间
                exposure_time = cam.ExposureTime
                exp_time = exposure_time.get()
                print('exposure_time:', exp_time)


                # 帧率
                Frame_Rate = cam.get_feature_by_name("AcquisitionFrameRateEnable")
                Frame_Rate.set(True)
                Frame_Rate = cam.get_feature_by_name("AcquisitionFrameRate")
                frame_set = self.getfps
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
                    basic_data_list = [exp_time,Frame_Rate,gain,img_w, img_h,frame_set,gain_set]
                    self.signal2.emit(basic_data_list)
                    self.signal.emit(frame_temp)  # 任务线程发射信号,图像，基本数据作为参数传递给主线程
                    time.sleep(0.5)


        return None



if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Ui_example()
    ex.show()
    sys.exit(app.exec_())