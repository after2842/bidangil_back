from celery import shared_task
from .helpers.gpt_helper import process_websearch 
from .models import InProgressOrderItem
from usrinfo.models import InProgressOrder, InProgressOrderSteps, Delivery, DeliveryStatus, User, Profile, Avatar
from django.utils import timezone
from .helpers.delivery_status_update import get_fedex_status, get_secret_key
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.response import Response
from .helpers.s3 import upload_png
import base64, re
from openai import OpenAI
from django.conf import settings

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



@shared_task
def generate_avatar(prompt, user_id):
    
    user = User.objects.get(id = user_id)
    profile=  Profile.objects.get(user=user)
    


    

    client = OpenAI(api_key= settings.GPT_SECRET)
    print('sending request to gpt')
    img = client.images.generate(
        model="gpt-image-1",
        prompt= prompt,
        background="transparent",  # Set background to transparent
        output_format="png",
        n=1 ,
        quality = 'high',
        size="1024x1024",
    )
    
    image_bytes = base64.b64decode(img.data[0].b64_json)


    #match = re.match(r"data:image/\\w+;base64,(.*)", image_bytes)
    #png_bytes = base64.b64decode(match.group(1) if match else image_bytes)
    print('uploading to s3')
    url = upload_png(image_bytes, folder="profiles", extention='png', content_type='image/png')
    print('uploaded to s3')
    # save on the profile
    print('url by gpt',url)
    profile.avatar = url
    profile.save()    

    obj, created = Avatar.objects.update_or_create(
    profile=profile,              # lookup
    defaults={"avatar_image_url": url},  # applied as UPDATE or on INSERT
    )
    print('avatar',url)
   

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {
            "type": "avatar_ready",
            "avatar_url": url,
        }
    )

    return {"avatar_url": url}
    
