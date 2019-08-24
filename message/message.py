# coding:utf-8
from threading import Thread
from socket import *

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


    def msg_receiver(self):
        print('---> 正在连接服务器...')
        self.sock.bind(('', self.port))
        self.sock.listen(5)
        self.conn, self.addr = self.sock.accept()
        while not self.connect_end:
            recv_data = self.conn.recv(1024).decode('utf-8')
            print('\n{} >>: {}\n'.format(self.ip, recv_data))

    def run(self):
        print('---> 初始化服务中...')
        server = Thread(target=self.msg_receiver)
        server.start()
        
        client = socket(AF_INET, SOCK_STREAM)
        ip = input('---> 请输入联系人的ip: ')
        client.connect((ip, self.port))
        print('---> 连接成功')
        try:
            while True: 
                # 发送
                msg = input('>>：')
                if msg == '##':
                    client.close()
                    self.sock.close()
                    self.connect_end = True
                    break
                client.send(bytes(msg, encoding='utf-8'))
                # self.conn.send(bytes(msg, encoding='utf-8'))
        except:
            print('---> 服务已断开...')
            self.sock.close()

