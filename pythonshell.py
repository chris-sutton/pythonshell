#!/usr/bin/python3
import os
import glob
import sys
import re
import resource
import signal
from time import sleep

USER = os.getenv("USER")
AOSENV = {
    "AOSPATH": ["/bin", "/usr/bin"],
    "AOSHOME": os.getenv("HOME"),
    "AOSCWD": os.getcwd()
}
foreground = []
background = []  # has background processes too


def childHandler(signum, frame):
    global foreground, background
    pid, status = os.waitpid(-1, os.WNOHANG)
    b = findPid(pid, background)
    if pid in foreground:
        foreground.clear()
    elif b is not None:
        background.pop(b)


def findPid(pid, lst):
    for i, proc in enumerate(lst):
        if pid in proc:
            return i
    return None


def sigIntHandler(signum, frame):
    if len(foreground) > 0:
        try:
            os.kill(foreground[0], signal.SIGKILL)
            foreground.clear()
        except:
            pass


def suspendHandler(signum, frame):
    global foreground, background
    # os.setpgid(foreground[0], 0)
    if len(foreground) > 0:
        os.kill(foreground[0], signal.SIGTSTP)
        print("\nsuspended {}".format(foreground[0]))
        foreground[1] = "suspended"
        background.append(foreground.copy())
        foreground.clear()


def killChildrenExceptBackground():
    global background, foreground
    for j in background:
        try:
            #print("if {} exists".format(j[0]))
            os.kill(j[0], 0)
        except OSError:
            pass
        else:
            # if "suspended" in j:
            #print("killing {}".format(j[0]))
            os.kill(j[0], signal.SIGKILL)
    if len(foreground) > 0:
        try:
            os.kill(j[0], 0)
        except OSError:
            pass
        else:
            os.kill(foreground[0], signal.SIGKILL)


def prepStatement(statement):
    statements = statement.split("#")[0].split(" ")
    statements = [x.strip() for x in statements if x != ""]
    return statements


def processStatement(statement=None, statementList=None):
    global AOSENV, USER, foreground, background
    statements = []
    if statement is None:
        statements = statementList
    else:
        statements = prepStatement(statement)

    if statements[0] == "exit":
        sys.exit(0)
        return True

    elif statements[0] in ["envset", "set"]:
        AOSENV[statements[1]] = statements[2]
        return True

    elif statements[0] == "envprt":
        for key, val in AOSENV.items():
            print(key + "=", end="")
            if isinstance(val, list):
                print(':'.join(val))
            else:
                print(val)
        return True

    elif statements[0] in ["envunset", "unset"]:
        try:
            del AOSENV[statements[1]]
        except KeyError:
            pass
        return True

    elif statements[0] == "prt":
        for txt in statements[1:]:
            print(txt, end=" ")
        print()
        return True

    elif statements[0] == "witch":
        found = witch(statements[1])
        if found is not None:
            print(found)
        return True

    elif statements[0] == "pwd":
        print(AOSENV["AOSCWD"])
        return True

    elif statements[0] == "cd":
        os.chdir(statements[1])
        AOSENV["AOSCWD"] = os.getcwd()
        return True
    elif statements[0] == "lim":
        if len(statements) == 3:
            resource.setrlimit(resource.RLIMIT_CPU,
                               (int(statements[1]), int(statements[1])))
            resource.setrlimit(resource.RLIMIT_AS, (int(
                statements[2])*1000000, int(statements[2])*1000000))
        else:
            _, cpumax = resource.getrlimit(resource.RLIMIT_CPU)
            _, memmax = resource.getrlimit(resource.RLIMIT_AS)
            print(cpumax, memmax, sep=" ")
        return True
    elif statements[0] == "jobs":
        printJobs()
        return True
    elif statements[0] == "fg":
        procnum = 0
        if len(statements) == 2:
            procnum = int(statements[1])
        if procnum < len(background):
            foreground = background.pop(procnum)
            # os.setpgid(foreground[0], os.getgid())
            foreground[1] = "foreground"
            os.kill(foreground[0], signal.SIGCONT)
        return True
    elif statements[0] == "bg":
        procnum = 0
        if len(statements) == 2:
            procnum = int(statements[1])
        if procnum < len(background):
            background[procnum][1] = "background"
            os.kill(background[procnum][0], signal.SIGCONT)
        return True
    return False


def printJobs():
    global background
    for i in range(len(background)):
        print('[{}] {} process {} -> "{}"'.format(i, background[i][1],
                                                  background[i][0], background[i][2]))


def witch(cmd):
    global AOSENV
    for path in AOSENV["AOSPATH"]:
        tmp = os.path.join(path, cmd)
        if os.access(tmp, os.X_OK):
            return tmp
    return None


##########################################################
#####################   Start Main   #####################
##########################################################
signal.signal(signal.SIGCHLD, childHandler)
signal.signal(signal.SIGTSTP, suspendHandler)
signal.signal(signal.SIGINT, sigIntHandler)
count = 0

def main():
    global AOSENV, USER, foreground, background, count
    tty = os.isatty(0)
    while True:
        sleep(0.05)
        try:
            if len(foreground) > 0:
                signal.pause()
            if tty:
                statement = input(USER + "_sh> ")
            else:
                statement = input()
            # implement everything...basically
            statement = statement.strip()
            if statement.isspace() or not statement:
                continue
            for var, val in AOSENV.items():
                if isinstance(val, list):
                    tempVal = ':'.join(val)
                else:
                    tempVal = val
                temp = "$" + var
                statement = statement.replace(temp, tempVal)

            statement = re.sub("\\$[a-zA-Z]+[a-zA-Z0-9]*", "", statement)

            # check for pipes |
            if "|" in statement:
                r, w = os.pipe()

                pipeStatements = statement.split('|')
                pid = os.fork()
                if pid:
                    # in parent
                    pid2 = os.fork()
                    if pid2:
                        # in parent again
                        # wait for both
                        os.close(r)
                        os.close(w)
                        # id1, ex1 = os.waitpid(pid, 0)
                        id2, ex2 = os.waitpid(pid2, 0)
                    else:

                        # in child 2...confusing I know
                        os.close(w)
                        os.dup2(r, 0)
                        success2 = processStatement(pipeStatements[1])
                        if not success2:
                            stmts2 = prepStatement(pipeStatements[1])
                            exe2 = witch(stmts2[0])

                            if exe2 is not None and os.access(exe2, os.X_OK):
                                os.execv(exe2, stmts2)
                                sys.exit(0)
                            elif os.access(stmts2[0], os.X_OK):
                                os.execv(stmts2[0], stmts2)
                                sys.exit(0)
                        else:
                            sys.exit(0)
                else:

                    # in child 1
                    os.close(r)
                    os.dup2(w, 1)
                    success = processStatement(pipeStatements[0])
                    if not success:
                        stmts = prepStatement(pipeStatements[0])
                        exe = witch(stmts[0])

                        if exe is not None and os.access(exe, os.X_OK):
                            os.execv(exe, stmts)
                            sys.exit(0)
                        elif os.access(stmts[0], os.X_OK):
                            os.execv(stmts[0], stmts)
                            sys.exit(0)
                    else:
                        sys.exit(0)
                    # in child

                # we  have a pipe
                # so fork one process and use each side of the pipe in processStatement
                # make sure to wait for both children before leaving this part as parent.

            # check for background run &
            elif "&" in statement:
                # this will be a background statement. we should continue on if this happens
                statement = statement.replace("&", "")
                pid = os.fork()
                if pid:
                    # in parent
                    background.append([int(pid), "background", statement])
                else:
                    os.setpgid(os.getpid(), 0)
                    # in child
                    success = processStatement(statement)
                    if not success:
                        stmts = prepStatement(statement)
                        exe = witch(stmts[0])
                        if exe is not None and os.access(exe, os.X_OK):
                            os.execv(exe, stmts)

                        elif os.access(stmts[0], os.X_OK):
                            os.execv(stmts[0], stmts)
                        sys.exit(0)
                    else:
                        sys.exit(0)
                # remove the & before continuing
                # I should handle SIGCHILD but only for background ones such as this
                # fork one process and call processStatement
            else:
                # attempt to process builtins
                # otherwise check if it can be found
                success = processStatement(statement)
                if not success:
                    stmts = prepStatement(statement)
                    exe = witch(stmts[0])

                    if exe is not None and os.access(exe, os.X_OK):
                        pid = os.fork()
                        if pid:
                            proc = [pid, "foreground", statement]
                            foreground = proc

                            # pid2, ex = os.waitpid(pid, 0)
                            pass
                        else:
                            os.execv(exe, stmts)
                            sys.exit(0)

                    elif os.access(stmts[0], os.X_OK):

                        pid = os.fork()
                        if pid:
                            proc = [pid, "foreground", statement]
                            foreground = proc
                        else:
                            os.execv(stmts[0], stmts)
                            sys.exit(0)

            ##################################

        except EOFError:
            killChildrenExceptBackground()
            sys.exit(0)
#############################################
if __name__ == "__main__":
    main()
