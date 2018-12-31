import threading
import time

import schedule

from src.resources.task_instance_resources import create_time_triggered_task_instances


class Scheduler:
    """
    Starts scheduled jobs on initialization.
    """

    def __init__(self):
        self.start_time_triggered_tasks()
        self.run_continuously()

        # Run all jobs - maybe the server was down for maintainance during regular run time at 00:01
        schedule.run_all()

    def start_time_triggered_tasks(self):
        """
        Checks for time triggered tasks that have to be started.
        """
        schedule.every().day.at('00:01').do(create_time_triggered_task_instances)

    def run_continuously(self, interval=1):
        """Continuously run, while executing pending jobs at each elapsed
        time interval.
        @return cease_continuous_run: threading.Event which can be set to
        cease continuous run.
        Please note that it is *intended behavior that run_continuously()
        does not run missed jobs*. For example, if you've registered a job
        that should run every minute and you set a continuous run interval
        of one hour then your job won't be run 60 times at each interval but
        only once.
        """
        cease_continuous_run = threading.Event()

        class ScheduleThread(threading.Thread):
            @classmethod
            def run(cls):
                while not cease_continuous_run.is_set():
                    schedule.run_pending()
                    time.sleep(interval)

        continuous_thread = ScheduleThread()
        continuous_thread.start()
        return cease_continuous_run
