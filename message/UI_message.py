# coding:utf-8
from threading import Thread
from socket import *
import sys
from time import gmtime, strftime, sleep
import win32api
import win32con
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtWidgets import QMessageBox
import argparse
import configparser
import cv2
import re
import pyaudio
import pickle
import os
import struct
import zlib
import wave

sys.path.append("../video/")
from video.vchat import Video_Server, Video_Client
from video.achat import Audio_Server, Audio_Client

from UI import untitled, ip, Dialog


class Messager(Thread):
    def __init__(self, ip, port, version):
        super().__init__()
        self.connect_end = False
        self.ip = ip
        self.port = port
        if version == 4:
            self.sock = socket(AF_INET, SOCK_STREAM)
        else:
            self.sock = socket(AF_INET6, SOCK_STREAM)

    def __del__(self):
        self.sock.close()

    def win_close(self):
        # 窗口的关闭事件
        # 向服务端发送一个关闭信号，并且关闭本地服务
        # self.sock.send(bytes('SESSION_END_DISCONNECT',encoding='utf-8'))
        print('window closing...')
        try:
            self.client.send(bytes('SESSION_END_DISCONNECT', encoding='utf-8'))
        except:
            print('Try to send close signal, but failed')
        finally:
            print('Is closing the connection')
            self.conn.close()
            self.client.close()
            sys.exit(0)

        print('ok!')

    def msg_receiver(self, vdo_req):
        self.ui.textBrowser.append('---> 等待对方确认...')
        self.sock.bind(('', self.port))
        self.sock.listen(5)
        self.conn, self.addr = self.sock.accept()
        nick_name = self.conn.recv(1024).decode('utf-8')
        self.ui.label.setText(nick_name)
        while not self.connect_end:
            recv_data = self.conn.recv(1024).decode('utf-8')
            if recv_data == "VIDEO_REQUEST":
                vdo_req()
                # self.video_request()
            elif recv_data == 'SESSION_END_DISCONNECT':
                print('received close signal, try to exit.')
                try:
                    self.conn.close()
                    self.client.close()
                except:
                    print('signal received and try to close connection, but failed')
                finally:
                    sys.exit(0)
            elif recv_data == "VIDEO_RESPONED":
                parser = argparse.ArgumentParser()
                parser.add_argument('--host', type=str, default=self.receiverIP)
                parser.add_argument('--port', type=int, default=8087)
                parser.add_argument('--level', type=int, default=1)
                parser.add_argument('-v', '--version', type=int, default=4)
                args = parser.parse_args()
                IP = args.host
                PORT = args.port
                VERSION = args.version
                LEVEL = args.level

                vclient = Video_Client(IP, PORT, LEVEL, VERSION)
                vserver = Video_Server(PORT, VERSION)
                vclient.start()
                sleep(1)  # make delay to start server
                vserver.start()
                # while True:
                #     sleep(1)
                #     if not vserver.isAlive() or not vclient.isAlive():
                #         print("Video connection lost...")
                #         sys.exit(0)
                # break
            elif recv_data:
                self.ui.textBrowser.append(
                    '<font color="gray">{}    {}<font>'.format(nick_name, strftime("%H:%M:%S", gmtime())))
                # print('\b\b\b\b{} >>: {}\t{}\n\n>>: '.format(self.receiverIP, recv_data,
                #                                              strftime("%Y/%m/%d %H:%M:%S", gmtime())), end="")
                self.ui.textBrowser.append('{}\n'.format(recv_data))
                self.ui.textBrowser.moveCursor(self.ui.textBrowser.textCursor().End)

    def main_window(self):
        # 生成窗口
        self.window = Dialog.Dialog()
        self.window.set_close_callback(self.win_close)
        self.ui = untitled.Ui_MainWindow()  # 使用QTdesigner自动创建的类
        self.ui.setupUi(self.window)
        self.window.setWindowIcon(self.icon)  # 设置图标
        self.window.show()
        #设置昵称，尚未收到昵称时用IP显示
        self.ui.label.setText(self.receiverIP)

        self.ui.textBrowser.append('---> 初始化服务中...')
        self.client = socket(AF_INET, SOCK_STREAM)
        server = Thread(target=self.msg_receiver, args=(self.video_request, ))
        # server.setDaemon(True)
        server.start()
        self.client.connect((self.receiverIP, self.port))
        self.client.send(bytes(self.nick_name, encoding='utf-8'))
        self.ui.textBrowser.append('---> 连接成功')

        self.ui.pushButton.disconnect()#取消所有绑定
        self.ui.pushButton.clicked.connect(self.send_message)#将按钮与send_massage方法绑定
        self.ui.pushButton.setShortcut("return")
        self.ui.pushButton_2.clicked.connect(self.video_launch)  # 点击视频聊天按钮触发video_connect方法

    # 接受到聊天，调用该方法
    def video_request(self):
        reply = QMessageBox.question(self.window,
                                     '视频聊天',
                                     "是否接受？",
                                     QMessageBox.Yes | QMessageBox.No,
                                     QMessageBox.No)

        if reply == QMessageBox.Yes:
            parser = argparse.ArgumentParser()
            parser.add_argument('--host', type=str, default=self.receiverIP)
            parser.add_argument('--port', type=int, default=8087)
            parser.add_argument('--level', type=int, default=1)
            parser.add_argument('-v', '--version', type=int, default=4)
            args = parser.parse_args()
            IP = args.host
            PORT = args.port
            VERSION = args.version
            LEVEL = args.level
            print('Is trying to start the client and server.')
            vclient = Video_Client(IP, PORT, LEVEL, VERSION)
            vserver = Video_Server(PORT, VERSION)

            vclient.start()
            sleep(1)  # make delself.sock.connectay to start server
            vserver.start()
            self.client.send(bytes("VIDEO_RESPONED", encoding='utf-8'))
        else:
            pass

    # 发起视频调用
    def video_launch(self):
        self.client.send(bytes("VIDEO_REQUEST", encoding='utf-8'))

    def send_message(self):
        try:
            msg = self.ui.lineEdit.text()
            if msg:
                self.client.send(bytes(msg, encoding='utf-8'))
                self.ui.textBrowser.append(
                    '<font color="gray">{}    {}<font>'.format(self.nick_name, strftime("%H:%M:%S", gmtime())))
                self.ui.textBrowser.append('{}\n'.format(msg))
                self.ui.textBrowser.moveCursor(self.ui.textBrowser.textCursor().End)
                self.ui.lineEdit.clear()
            else:
                self.ui.textBrowser.append(
                    '<font color="gray">{}    {}<font>'.format("系统提示", strftime("%H:%M:%S", gmtime())))
                self.ui.textBrowser.append('{}\n'.format("消息不能为空哦"))
                self.ui.textBrowser.moveCursor(self.ui.textBrowser.textCursor().End)

        except:
            self.ui.textBrowser.append('---> 服务已断开...')
            self.sock.close()

    def run(self):
        QtCore.QCoreApplication.setAttribute(QtCore.Qt.AA_EnableHighDpiScaling)
        self.app = QtWidgets.QApplication(sys.argv)  # 生成应用
        self.window = QtWidgets.QMainWindow()  # 生成窗口q
        self.ui = ip.Ui_ip()  # 使用QTdesigner自动创建的类
        self.ui.setupUi(self.window)

        # 读取user.ini文件，获取记住的昵称和ip
        try:
            config = configparser.ConfigParser()
            config.read('UI/user.ini')
            config_dict = config.defaults()
            self.ui.lineEdit.setText(config_dict["nick_name"])
            self.ui.lineEdit_2.setText(config_dict["receiver_ip"])
        except:
            #读取失败
            pass

        # 图标
        self.icon = QtGui.QIcon()
        self.icon.addPixmap(QtGui.QPixmap("UI/logo.ico"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.window.setWindowIcon(self.icon)
        # 标题
        self.window.setWindowTitle("PyChat")

        # 按钮绑定事件:获取ip，昵称以及跳转到主窗口
        def get_ip():
            self.receiverIP = self.ui.lineEdit_2.text()
            self.nick_name = self.ui.lineEdit.text()

            # 记住昵称和ip，写入user.ini文件
            config["DEFAULT"] = {
                "nick_name": self.nick_name,
                "receiver_ip": self.receiverIP,
            }
            with open('UI/user.ini', 'w')as configfile:
                config.write(configfile)

            # 跳转到主窗口
            self.main_window()

        #给按钮绑定方法get_ip
        self.ui.pushButton.clicked.connect(get_ip)
        self.ui.pushButton.setShortcut('return')

        self.window.show()
        sys.exit(self.app.exec_())
