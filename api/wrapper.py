from subprocess import *

class Wrapper:
    def jarWrapper(self, *args):
        process = Popen(['java', '-jar']+list(args), stdout=PIPE, stderr=PIPE, stdin=subprocess.PIPE)
        stdin = process.communicate()
        return stdin
    
    def serverManagementCommand(self, sid, command):
        
        if command == "stop":
            pass
        if command == "":
            pass
        if command == "":
            pass
        if command == "":
            pass
    
    #args = ['myJarFile.jar', 'arg1', 'arg2', 'argN'] # Any number of args to be passed to the jar file
    
    #result = jarWrapper(*args)
    
    #print result