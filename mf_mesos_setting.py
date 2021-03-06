#!/usr/bin/env python

# This module defined global variables and classes 
# used by mf_mesos_scheduler.py

import os
import Queue
import threading

# variables need to be synchronized between threads
tasks_info_dict = {}
executors_info_dict = {}
lock = threading.RLock()
offers_queue = Queue.Queue()
# default makeflow working directory
mf_wk_dir = "."
DEBUG_FILE = "debug_mesos"
SLEEP = 0

def print_task_id_state():
    if os.path.isfile(DEBUG_FILE):
        debug_fn = open(DEBUG_FILE, "a+")
    else:
        debug_fn = open(DEBUG_FILE, "w+")

    if len(tasks_info_dict) > 0:

        for value in tasks_info_dict.itervalues():
            debug_fn.write("{}:{},".format(value.task_id, value.action))

        debug_fn.write("================\n")

    debug_fn.close()
    

# Makeflow Mesos task info class
class MfMesosTaskInfo:

    def __init__(self, task_id, cmd, inp_fns, oup_fns, action):
        self.task_id = task_id
        self.cmd = cmd
        self.inp_fns = inp_fns
        self.oup_fns = oup_fns
        self.action = action
        self.executor_id = None

# Makeflow Mesos executor info class
class MfMesosExecutorInfo:

    def __init__(self, executor_id, slave_id, hostname):
        self.executor_id = executor_id
        self.slave_id = slave_id
        self.hostname = hostname
        self.state = "init"
        self.tasks = []
