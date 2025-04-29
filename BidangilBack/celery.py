# Celery's app configuration file
# Celery reads this when loaded 
# So, we need to let celery know what celery conf in setting is, get_channel_layer, async_to_async ...etc
import os
import django  
from celery import Celery
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "BidangilBack.settings")
django.setup() 

app = Celery("BidangilBack")                               # Celery application object
app.config_from_object("django.conf:settings",     # read DJANGO settings
                       namespace="CELERY")         # only keys starting CELERY_
app.autodiscover_tasks()                          # scan installed app ,usrinfo and find target func

@app.task(bind=True)
def debug_task(self):                              # quick sanity check
    print(f"Request: {self.request!r}")
