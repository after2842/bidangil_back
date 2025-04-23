from celery import shared_task
from .helpers.gpt_helper import process_websearch 
from .models import InProgressOrderItem
from usrinfo.models import InProgressOrder, InProgressOrderSteps, Delivery, DeliveryStatus
from django.utils import timezone
from .helpers.delivery_status_update import get_fedex_status, get_secret_key

@shared_task
def run_and_update():
    print('hitted!!!')
    secrete_key = get_secret_key()

    # find Deliveries that is not done yet
    inprogress_deliveries = Delivery.objects.filter(delivered_at = None)
    print('len of inprogress deliveires', len(inprogress_deliveries))
    for inprogress_delivery in inprogress_deliveries:
        tracking_num = inprogress_delivery.tracking_number
        status_info = get_fedex_status(tracking_num, secrete_key)
        print(inprogress_delivery.tracking_number, status_info)
        if not status_info:
            print('status info null')
            continue

        #when delivery is completed
        if status_info.get('statusByLocale') == 'Delivered' or status_info.get('description') == 'Delivered':
            inprogress_delivery.delivered_at = timezone.now()
            inprogress_delivery.save()

            order = inprogress_delivery.order
            steps = InProgressOrderSteps.objects.get(order = order)
            steps.delivery_completed = True
            steps.save()
            print('svae step complete')

        # when delivery is still inprogress -> record the status caught
        else:
            delivery_status = DeliveryStatus.objects.create(delivery = inprogress_delivery)
            delivery_status.status = str(status_info.get('statusByLocale') + " " + status_info.get('description'))
            delivery_status.save()
            print('svae step not complete')


@shared_task(name="usrinfo.process_websearch_task")
def process_websearch_task(obj_id, url):
    name = process_websearch(url)
    order_item = InProgressOrderItem.objects.get(id = obj_id)
    order_item.gpt_product_name = name
    order_item.save()
    print('gpt name saved')

    
