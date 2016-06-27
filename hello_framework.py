import logging
import uuid
import time
import sys
import os

from mesos.interface import Scheduler
from mesos.native import MesosSchedulerDriver
from mesos.interface import mesos_pb2

logging.basicConfig(level=logging.INFO)

TOTAL_TASKS = 5

class HelloWorldScheduler(Scheduler):

    def __init__(self, executor):
        self.launched_tasks = 0
        self.executor = executor

    def registered(self, driver, framework_id, master_info):
        logging.info("Registered with framework id: {}".format(framework_id))

    def resourceOffers(self, driver, offers):
        logging.info("Recieved resource offers: {}".format([o.id.value for o in offers]))
        # whenever we get an offer, we accept it and use it to launch a task that
        # just echos hello world to stdout
        for offer in offers:
            if self.launched_tasks <= TOTAL_TASKS:

                self.launched_tasks = self.launched_tasks + 1
                
                task = mesos_pb2.TaskInfo()
                id = uuid.uuid4()
                task.task_id.value = str(id)
                task.slave_id.value = offer.slave_id.value
                task.name = "task {}".format(str(id))
                task.executor.MergeFrom(self.executor)

                cpus = task.resources.add()
                cpus.name = "cpus"
                cpus.type = mesos_pb2.Value.SCALAR
                cpus.scalar.value = 1

                mem = task.resources.add()
                mem.name = "mem"
                mem.type = mesos_pb2.Value.SCALAR
                mem.scalar.value = 1

                time.sleep(2)
                logging.info("Launching task {task} "
                             "using offer {offer}.".format(task=task.task_id.value,
                                                           offer=offer.id.value))
                tasks = [task]

                driver.launchTasks(offer.id, tasks)

            else: 

                driver.stop()

if __name__ == '__main__':

    executor = mesos_pb2.ExecutorInfo()
    executor.executor_id.value = "default"
    executor.command.value = os.path.abspath("./test-executor.in") 
    executor.name = "Hello executor"
    executor.source = "python executor"

    # make us a framework
    framework = mesos_pb2.FrameworkInfo()
    framework.user = "zc"  # Have Mesos fill in the current user.
    framework.name = "hello-world"
    framework.checkpoint = True

    driver = MesosSchedulerDriver(
        HelloWorldScheduler(executor),
        framework,
        "127.0.0.1:5050/"  # assumes running on the master
    )

    sys.exit(0 if driver.run() == mesos_pb2.DRIVER_STOPPED else 1)
