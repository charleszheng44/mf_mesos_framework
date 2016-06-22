import logging
import time
import os

from mesos.interface import Scheduler
from mesos.native import MesosSchedulerDriver
from mesos.interface import mesos_pb2

logging.basicConfig(level=logging.INFO)

FILE_RUN_TASKS = "task_to_run"
FILE_FINISH_TASKS = "finished_tasks"

def new_task(offer, task_id):
    task = mesos_pb2.TaskInfo()
    task.task_id.value = task_id
    task.slave_id.value = offer.slave_id.value
    task.name = "task {}".format(str(id))

    cpus = task.resources.add()
    cpus.name = "cpus"
    cpus.type = mesos_pb2.Value.SCALAR
    cpus.scalar.value = 1

    mem = task.resources.add()
    mem.name = "mem"
    mem.type = mesos_pb2.Value.SCALAR
    mem.scalar.value = 1

    return task

def get_new_task(task_list):
    logging.info(task_list)
    inp_fn = open(FILE_RUN_TASKS, "r")
    lines = inp_fn.readlines()
    processing = False
    new_task = False

    for line in lines:
        if line.strip(' \t\n\r') == "done":
            return ("done", None)

        words = line.split(':')
        # find new task
        if processing:
            if words[0] == "cmd":
                cmd = words[1].strip(' \t\n\r')
            if words[0] == "input files":
                inp_fns = words[1].strip(' \t\n\r').split(',')
                inp_fns.pop()
            if words[0] == "output files":
                oup_fns = words[1].strip(' \t\n\r').split(',')
                oup_fns.pop()
                processing = False
                break

        if (words[0] == "task_id") and (words[1].strip(' \t\n\r') not in task_list):
            task_id = words[1].strip(' \t\n\r')
            processing = True
            new_task = True
                
    inp_fn.close()

    if new_task:
        mf_task = MakeflowTask(task_id, cmd, inp_fns, oup_fns)
        return ("working", mf_task)
    else: 
        return ("working", None)

class MakeflowTask:

    def __init__(self, task_id, cmd, inp_fns, oup_fns):
        self.task_id = task_id
        self.cmd = cmd
        self.inp_fns = inp_fns
        self.oup_fns = oup_fns

class MakeflowScheduler(Scheduler):

    def __init__(self):
        self.task_list = []

    def registered(self, driver, framework_id, master_info):
        logging.info("Registered with framework id: {}".format(framework_id))

    def resourceOffers(self, driver, offers):
        logging.info("Recieved resource offers: {}".format([o.id.value for o in offers]))
        
        for offer in offers:
            state_and_task = get_new_task(self.task_list)            
            if state_and_task[0] == "done":
                driver.stop()
            if state_and_task[1] != None:
                mf_task = state_and_task[1]
                task = new_task(offer, mf_task.task_id)
                task.command.value = mf_task.cmd 
                for fn in mf_task.inp_fns:
                    uri = task.command.uris.add()
                    logging.info("input file is: {}".format(fn.strip(' \t\n\r')))
                    uri.value = fn.strip(' \t\n\r')
                    uri.executable = False
                    uri.extract = False
                time.sleep(2)
                logging.info("Launching task {task} "
                             "using offer {offer}.".format(task=task.task_id.value,
                                                        offer=offer.id.value))
                tasks = [task]
                self.task_list.append(mf_task.task_id)
                driver.launchTasks(offer.id, tasks)

    def statusUpdate(self, driver, update):
        print "Task {} is in state {}".format(update.task_id.value, update.state)

        if os.path.isfile(FILE_FINISH_TASKS): 
            oup_fn = open(FILE_FINISH_TASKS, "a")
        else:
            oup_fn = open(FILE_FINISH_TASKS, "w")

        if update.state == mesos_pb2.TASK_FAILED:
            oup_fn.write("{} is failed.\n".format(update.task_id.value))
        if update.state == mesos_pb2.TASK_FINISHED:
            oup_fn.write("{} is finished.\n".format(update.task_id.value))

        oup_fn.close()

if __name__ == '__main__':
    # make us a framework
    framework = mesos_pb2.FrameworkInfo()
    framework.user = ""  # Have Mesos fill in the current user.
    framework.name = "Makeflow"
    driver = MesosSchedulerDriver(
        MakeflowScheduler(),
        framework,
        "127.0.0.1:5050/"  # assumes running on the master
    )

    driver.run() 