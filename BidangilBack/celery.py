# proj/proj/celery.py
import os
from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BidangilBack.settings")

app = Celery("BidangilBack")                               # Celery application object
app.config_from_object("django.conf:settings",     # read DJANGO settings
                       namespace="CELERY")         # only keys starting CELERY_
app.autodiscover_tasks()                          # scan installed app ,usrinfo and find target func
                                                                                        # [
                                                                                        #     'usrinfo.scheduled.delivery_update'
                                                                                        #     'usrinfo.tasks.process_websearch_task'
                                                                                        # ]
@app.task(bind=True)
def debug_task(self):                              # quick sanity check
    print(f"Request: {self.request!r}")
