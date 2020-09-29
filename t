#!/usr/bin/python3
from os import getpid
from time import sleep
for i in range(5):
    print("{} second(s) pid: {}".format(i, getpid()))
    sleep(1)
