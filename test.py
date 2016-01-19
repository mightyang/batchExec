#-*-coding:utf-8-*-
import socket


def sendData(connection, msg):
    length = len(msg)
    while True:
        # print "send length: %d"%length
        connection.send("%d"%length)
        # print "makesure length"
        makesure = connection.recv(4)
        if makesure == "$%^0":
            # print "send msg: %s"%msg
            connection.send(msg)
            # print "makesure msg"
            makesure = connection.recv(4)
            if makesure == "$%^0":
                # print "send data succeed"
                break
        elif makesure == "$%^1":
            # print "send length failed"
            continue

def recvData(connection):
    data = None
    while True:
        length = connection.recv(1024)
        if not length:
            # print "receive over"
            break
        # print "receive length: %s"%str(length)
        try:
            length = int(length)
        except:
            connection.send("$%^1")
            # print "receive length failed"
            continue
        # print "makesure length"
        connection.send("$%^0")
        data = connection.recv(length)
        # self.logger.debug("receive data: %s"%data)
        if len(data) != length:
            connection.send("$%^1")
            # print "receive data failed"
            continue
        else:
            connection.send("$%^0")
            break
    return data


cs = "E:\lzy_info\materials\computers.txt"
o = open(cs, "r")
hosts = o.readlines()
for i in hosts:
    i = i.strip()
    print "host is %s"%i
    port = 10584
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((i, port))
    bat = open(r"E:\lzy_info\materials\batchExecServer.bat","r")
    data = bat.read()
    bat.close()
    print "send data"
    sendData(s, data)
    data = "endEndeNdenD"
    print "send end"
    sendData(s, data)
    while True:
        r = recvData(s)
        if r=="endEndeNdenD":
            break
        print r
    s.close()
