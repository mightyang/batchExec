#-*-coding:utf-8-*-
import wmi, os, sys, time
reload(sys)
sys.setdefaultencoding("utf-8")

##argvList = sys.argv
argvList = [sys.argv[0], "-cFile", r"E:\lzy_info\materials\computers.txt", "-bat", r"E:\lzy_info\materials\netuse.bat", "-u", "administrator", "-p", "abc123@123"]
# argvList = [sys.argv[0], "-host", r"192.168.86.118", "-bat", r"E:\lzy_info\materials\python_install.bat", "-u", "administrator", "-p", "abc123@123"]
argvDict = {}
cmdMode = True
argvDict["hosts"] = []
watcher = {}
autoStartPath=r"%AppData%\Microsoft\Windows\Start Menu\Programs\Startup"
if (len(argvList)-1)%2!=0:
    print "there is something wrong in argvs"
    sys.exit(1)

for i in range(1,len(argvList)/2+1):
    if argvList[i*2-1]=="-u":
        argvDict["user"]=argvList[i*2]
    if argvList[i*2-1]=="-p":
        argvDict["password"]=argvList[i*2]
    if argvList[i*2-1]=="-cFile":
        cf = open(argvList[i*2], "r")
        cs = cf.readlines()
        cs = [j.strip() for j in cs]
        cf.close()
        argvDict["hosts"]+=cs
    if argvList[i*2-1]=="-host":
        argvDict["hosts"]=[argvList[i*2],]
    if argvList[i*2-1]=="-cmd":
        argvDict["cmd"]=argvList[i*2]
    if argvList[i*2-1]=="-bat":
        argvDict["bat"]=argvList[i*2]
        cmdMode = False

if "user" not in argvDict.keys():
    print "please entry user"
if "password" not in argvDict.keys():
    print "please entry password"

if cmdMode:
    cmd = argvDict["cmd"]
    for c in argvDict["hosts"]:
        if c == "localhost":
            session = wmi.WMI()
            process = session.Win32_Process.Create(CommandLine="cmd.exe /c %s"%cmd)
        else:
            try:
                session = wmi.WMI(c, user=argvDict["user"], password=argvDict["password"])
            except wmi.x_wmi, e:
                raise e
            process = session.Win32_Process.Create(CommandLine="cmd.exe /c %s"%cmd)
else:
    batFile = open(argvDict["bat"], "r")
    #write bat
    new = True
    print "starting transmit"
    batCmd = ""
    for line in batFile:
        line=line.strip()
        for dosSC in ["^","%","\"","&","<",">","|","'","`",",",";","=","(",")"]:
            line=line.replace(dosSC, "^"+dosSC)
        if new == True:
            if not line:
                continue
            batCmd += "cmd.exe /c echo %s>\"%s\"\\batchTemp.bat"%(line,autoStartPath)
            new = False
        else:
            if not line:
                continue
            batCmd +="&&echo %s>>\"%s\"\\batchTemp.bat"%(line,autoStartPath)
    print batCmd
    for c in argvDict["hosts"]:
        print "--------------%s----------------"%c
        if c == "localhost":
            session = wmi.WMI()
        else:
            try:
                session = wmi.WMI(c, user=argvDict["user"], password=argvDict["password"])
                print "connection successful"
            except wmi.x_wmi, e:
                print "connect failed"
                continue
                
        pid, result = session.Win32_Process.Create(CommandLine=batCmd)
        print str(pid)+": "+str(result)
        print "watch transmition"
        try:
            watcher[c] = session.Win32_Process.watch_for()
            feedback=watcher[c]()
        except Exception, e:
            print e
        if not result:
            print "transmit over"
        else:
            print "errorCode: %s"%result
            
        # print "run"
        # process_startup = session.Win32_ProcessStartup.new()
        # process_startup.ShowWindow = 1
        # pid, result = session.Win32_Process.Create(CommandLine="cmd /c copy /Y \"\\\\192.168.88.195\\installer\\Nuke7.0v4_install.bat\" \"%temp%\">C:\log.txt")
        # restartComputer = wmi.WMI(c, privileges=["RemoteShutdown"])
        
        print "restart %s"%c
        try:
            os=session.Win32_OperatingSystem(Primary=1)[0]
            os.Reboot()
        except Exception, e:
            print e
            
        # print pid,result
        # create watcher
        # print "create watcher"
        # watcher[c] = session.Win32_Process.watch_for(delay_secs=1)
        # feedback = watcher[c]()
        print "--------------over-----------------"
    batFile.close()