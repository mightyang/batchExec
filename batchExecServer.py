#-*-coding:utf-8-*-

import win32serviceutil
import win32service
import win32event
import socket, subprocess, select, sys, os, time, tempfile, threading

class batchExecServer(win32serviceutil.ServiceFramework):
    """
    Usage: 'PythonService.py [options] install|update|remove|start [...]|stop|restart [...]|debug [...]'
    Options for 'install' and 'update' commands only:
     --username domain\username : The Username the service is to run under
     --password password : The password for the username
     --startup [manual|auto|disabled|delayed] : How the service starts, default = manual
     --interactive : Allow the service to interact with the desktop.
     --perfmonini file: .ini file to use for registering performance monitor data
     --perfmondll file: .dll file to use when querying the service for
       performance data, default = perfmondata.dll
    Options for 'start' and 'stop' commands only:
     --wait seconds: Wait for the service to actually start or stop.
                     If you specify --wait with the 'stop' option, the service
                     and all dependent services will be stopped, each waiting
                     the specified period.
    """
    #服务名
    _svc_name_ = "batchExecServer"
    #服务显示名称
    _svc_display_name_ = "batchExecServer"
    #服务描述
    _svc_description_ = "for receiving and executing cmds"

    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.hWaitStop = win32event.CreateEvent(None, 0, 0, None)
        self.logger, self.handler = self._getLogger()
        self.isAlive = True
        self.s = None
        self.host = "0.0.0.0"
        self.port = 10584
        self.BUFFER = 1024
        self.dirpath = None
        self.batFilePath = os.getenv("temp")
        self.inputs = []
        self.outputs = []
        self.process = None
        # self.isWatch = False
        self.feedbackFile = tempfile.TemporaryFile(mode="w+")
        
    def _getLogger(self):
        import logging
        import os
        import inspect

        logger = logging.getLogger('batchExecServer')
        
        this_file = inspect.getfile(inspect.currentframe())
        self.dirpath = os.path.abspath(os.path.dirname(this_file))
        handler = logging.FileHandler(os.path.join(self.dirpath, "service.log"), mode="w")

        formatter = logging.Formatter('%(asctime)s %(filename)s[line:%(lineno)d] %(levelname)s %(message)s')
        handler.setFormatter(formatter)

        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

        return logger, handler
    
    def sendData(self, connection, msg):
        length = len(msg)
        while True:
            self.logger.debug("send length: %d"%length)
            connection.send("%d"%length)
            self.logger.debug("makesure length")
            makesure = connection.recv(4)
            if makesure == "$%^0":
                self.logger.debug("send msg: %s"%msg)
                connection.send(msg)
                self.logger.debug("makesure msg")
                makesure = connection.recv(4)
                if makesure == "$%^0":
                    self.logger.debug("send data succeed")
                    break
            elif makesure == "$%^1":
                self.logger.debug("send length failed")
                continue

    
    def recvData(self, connection):
        data = None
        while True:
            self.logger.debug("=====================")
            length = connection.recv(1024)
            if not length:
                self.logger.debug("receive over")
                break
            self.logger.debug("receive length: %s"%str(length))
            try:
                length = int(length)
            except Exception, e:
                connection.send("$%^1")
                self.logger.debug("receive length failed")
                continue
            self.logger.debug("makesure length")
            connection.send("$%^0")
            data = connection.recv(length)
            # self.logger.debug("receive data: %s"%data)
            if len(data) != length:
                connection.send("$%^1")
                self.logger.debug("receive data failed")
                continue
            else:
                connection.send("$%^0")
                break
        return data

    # def watchOutput(self, connection):
        # if self.process == None:
            # self.logger.debug("start feedback watcher")
            # feedbackseek = 0
            # while self.isWatch:
                # if self.process != None:
                    # self.feedbackFile.seek(feedbackseek)
                    # output = self.feedbackFile[1].recv()
                    # self.logger.debug("feedbackseek: %d"%feedbackseek)
                    # if not output and self.process.poll() != None:
                        # self.sendData(connection, "endEndeNdenD")
                        # break
                    # feedbackseek += len(output)
                    
                    # self.logger.debug("get feedback: %s"%output)
                    # self.sendData(connection, output)
                    # if self.process.poll() == None:
                        # time.sleep(0.5)
                        # continue
                # time.sleep(0.5)
        # self.process = None
        # self.logger.debug("feedback watcher exit")
        # self.isWatch = False
        # connection.close()
    def SvcDoRun(self):
        self.logger.info("svc do run....")
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
        self.inputs.append(self.s)
        self.outputs.append(self.feedbackFile)
        readConnection = None
        try:
            self.s.bind((self.host,self.port))
        except socket.error, e:
            self.logger.error("Bind Socket Error: %s, errorCode=%s"%(e[1], e[0]))
            sys.exit(1)
        self.logger.info("bind succeed")
        self.s.listen(1)
        self.logger.info("server is licensing, wait for events")
        while self.isAlive:
            if self.process != None and self.process.poll() != None:
                self.logger.debug("process has exit, set process None")
                self.process = None
            self.logger.debug("start input watcher")
            readables, writeables, exceptionals = select.select(self.inputs, [], [])
            self.logger.debug("get a input operation")
            for readable in readables:
                self.logger.debug("input operation from %s"%readable.fileno())
                if readable is self.s:
                    self.logger.debug("entry accept process")
                    self.logger.debug("this is a connection request")
                    readConnection, readAddress = readable.accept()
                    readConnection.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
                    self.logger.debug("accept connection from %s:%s"%readAddress)
                    if self.process != None and self.process.poll() == None:
                        self.sendData(readConnection, "there is a processing is running, please wait until the processing has finished!\n")
                        continue
                    self.inputs.append(readConnection)
                    # self.isWatch = True
                    # watchTread = threading.Thread(target=self.watchOutput, args=(readConnection,))
                    # watchTread.setDaemon(True)
                    # watchTread.start()
                    self.logger.debug("create bat file: [%s] for this connection"%(self.batFilePath+"\\batchTemp.bat"))
                    batFile = open(self.batFilePath+"\\batchTemp.bat", "w")
                    data = ""
                    self.logger.debug("receive operation from %s over, connection is created"%readable.fileno())
                else:
                    self.logger.debug("entry receive data process")
                    receive = self.recvData(readable)
                    if receive == "endEndeNdenD":
                        self.inputs.remove(readable)
                        self.logger.debug("receive end")
                        # self.logger.debug("close connection: %s:%s"%readAddress)
                        if batFile:
                            batFile.write(data)
                            self.logger.debug("write data")
                            batFile.close()
                            self.logger.debug("close bat file")
                        self.process = subprocess.Popen("call %s\\batchTemp.bat"%self.batFilePath, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True)
                        self.logger.debug("start bat process: call %s\\batchTemp.bat"%self.batFilePath)
                        self.logger.debug("receive operation from file describe: %s, the processing is still running until exit by itself"%readable.fileno())
                        while True:
                            line = self.process.stdout.read()
                            if line:
                                self.sendData(readable, line)
                            elif self.process.poll() == None:
                                time.sleep(0.5)
                                continue
                            else:
                                self.sendData(readable, "endEndeNdenD")
                                self.process=None
                                readable.close()
                                break
                    elif not receive:
                        self.logger.debug("receive None")
                        continue
                    else:
                        self.logger.debug("receive data: %s"%receive)
                        data += receive

        # 等待服务被停止 
        #win32event.WaitForSingleObject(self.hWaitStop, win32event.INFINITE) 
            
    def SvcStop(self): 
        for i in self.inputs:
            i.close()
        if self.process != None and self.process.poll() ==None:
            self.process.terminate()
        # 先告诉SCM停止这个过程 
        self.logger.info("svc do stop....")
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING) 
        # 设置事件 
        win32event.SetEvent(self.hWaitStop)
        self.isWatch = False
        self.isAlive = False

if __name__=='__main__': 
    win32serviceutil.HandleCommandLine(batchExecServer)

			