#!/usr/bin/python3
import os
import sys
import re

def main():
    tty = os.isatty(0)
    USER = os.getenv("USER")
    AOSENV = {
        "AOSPATH" : ["/bin","/usr/bin"],
        "AOSHOME" : os.getenv("HOME"),
        "AOSCWD" : os.getcwd()
        

    }
    while True:
        try: 


            if tty:
                statement = input(USER + "_sh> ")
            else:
                statement = input()
            
            
            # implement everything...basically
            statement = statement.strip()

            for var, val in AOSENV.items():
                if isinstance(val, list):
                    tempVal = ':'.join(val)
                else:
                    tempVal = val
                temp = "$" + var
                statement = statement.replace(temp, tempVal)

            statement = re.sub("\\$[a-zA-Z]+[a-zA-Z0-9]*", "", statement)

            # check for pipes |
            # check for background run &


            statements = statement.split(" ")
            statements = [x.strip() for x in statements if x != ""]
            

            if statements[0] == "exit":
                sys.exit(0)
            elif statements[0] in ["envset", "set"]:
                AOSENV[statements[1]] = statements[2]
            elif statements[0] == "envprt":
                for key, val in AOSENV.items():
                    print(key + "=", end="")
                    if isinstance(val, list):
                        print(':'.join(val))
                    else:
                        print(val)
            elif statements[0] in ["envunset", "unset"]:
                try:
                    del AOSENV[statements[1]]
                except KeyError:
                    pass
            elif statements[0] == "prt":
                for txt in statements[1:]:
                    print(txt, end=" ")
                print()
            elif statements[0] == "witch":
                for path in AOSENV["AOSPATH"]:
                    for root, d, files in os.walk(path):
                        if statements[1] in files:
                            print(os.path.join(root, statements[1]))
            elif statements[0] == "pwd":
                print(AOSENV["AOSCWD"])
            elif statements[0] == "cd":
                os.chdir(statements[1])
                AOSENV["AOSCWD"] = os.getcwd()
            ##################################



        except EOFError:
            sys.exit(0)

if __name__ == "__main__":
    main()