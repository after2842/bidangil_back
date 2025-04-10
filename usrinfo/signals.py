from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Payment, InProgressOrder, Delivery, Profile, InProgressOrderItem,InProgressOrderSteps
from django.db.models.signals import pre_save, post_save
from .helpers.payment_session import create_payment_session
from datetime import datetime, timezone

def order_message(urls, descriptions, prices):
    message = ""
    for i in range (len(urls)):
        message += f"\n상품{i+1}\n{urls[i]}\n옵션: {descriptions[i]} \n가격: {prices[i]}\n"

    return message

@receiver(post_save, sender=InProgressOrder)
def send_new_order_email(sender, instance, created, **kwargs):
    if created:
        print('//////inprogress//////email')
        user = instance.user
        user_email = user.username
        profile = Profile.objects.get(user = user)
        
        user_nickname = profile.nickname
        InProgressOrderSteps.objects.create(order=instance, request_received = True)
        send_mail(
            subject=f'{user_nickname}의 주문이 접수되었습니다! #{instance.id}',
            message=(
                f'안녕하세요 {user_nickname} 님,\n\n'
                f'비단길을 이용해주셔서 감사합니다.\n\n'
                f'고객님의 주문요청이 접수되었습니다.\n\n'
                f"더 자세한 사항은 '홈페이지 -> 내 정보'에서 확인하실 수 있습니다.\n"
                f"곧 접수된 주문의 통관정보와 가격을 안내드리겠습니다!\n"
            ),
            from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings.py
            recipient_list=[user_email],
            fail_silently=False,
        )

@receiver(post_save, sender=Delivery)
def delivery_started(sender, instance, created, **kwargs):
    if created:
        courier = instance.courier
        tracking_num = instance.tracking_number

        order = instance.order

        user = order.user
        user_email = user.username
        profile = Profile.objects.get(user = user)
        user_nickname = profile.nickname

        steps = InProgressOrderSteps.objects.get(order = order)
        steps.delivery_started = True
        steps.save()

        send_mail(
            subject=f'{user_nickname}님의 배송이 시작되었습니다. #{instance.id}',
            message=(
                f'안녕하세요 {user_nickname} 님,\n\n'
                f'고객님의 배송이 시작되었습니다.\n\n'
                f'운송사:{courier} \n\n'
                f'조회번호:{tracking_num} \n\n'
                f'배송조회:{make_tracking_url(courier, tracking_num)} \n\n'
                f"더 자세한 사항은 '홈페이지 -> 내 정보'에서 확인하실 수 있습니다.\n"

            ),
            from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings.py
            recipient_list=[user_email],
            fail_silently=False,
        )

def make_tracking_url(courier, tracking_num):
    if courier.lower() == 'fedex':
        url = f"https://www.fedex.com/fedextrack/?trknbr={tracking_num}"
    elif courier.lower() =='ems':
        url =  f"https://service.epost.go.kr/trace.RetrieveEmsRigiTraceList.comm?POST_CODE={tracking_num}"
    else:
        url = "{courier}홈페이지에서 배송 조회 번호를 입력해 주세요."
    return url

# @receiver(post_save, sender=InProgressOrderItem)   ===================> this will cause a multiple execution of Paymnet.objects.create(), because the 'instance' could be multiple (more than one InProgressOrderItem is updated and receiver listens to those events seperately)
# def create_payment_instance(sender, instance, created, **kwargs):
#     if not created:
#         total_item_price = 0
#         order = instance.order
#         progress_itmes = order.items.all()

#         for item in progress_itmes:
#             total_item_price+=item.price

#         Payment.objects.create(order=order, item_price = total_item_price)

#         order_steps = InProgressOrderSteps.objects.get(order = order)
#         order_steps.item_purchased = True
#         order_steps.save()

_PREVIOUS_PAYMENT_VALUES = {}

@receiver(pre_save, sender=Payment)
def store_previous_payment_fields(sender, instance, **kwargs):
    print('//////////inside payment email//////')
    if instance.pk:
        try:
            previous = Payment.objects.get(pk=instance.pk)
            _PREVIOUS_PAYMENT_VALUES[instance.pk] = {
                'item_price': previous.item_price,
                'delivery_fee': previous.delivery_fee,
            }
        except Payment.DoesNotExist:
            _PREVIOUS_PAYMENT_VALUES[instance.pk] = {
                'item_price': None,
                'delivery_fee': None,
            }

@receiver(post_save, sender=Payment)
def send_payment_update_emails(sender, instance, created, **kwargs):
    print('//////payment update email///////')
    order = instance.order
    user = order.user
    user_email = user.username
    profile = Profile.objects.get(user = user)
    
    user_nickname = profile.nickname

    previous_values = _PREVIOUS_PAYMENT_VALUES.pop(instance.pk, {'item_price': None, 'delivery_fee': None})
#when admin put a wrong item_price
#when admin put a wrong delivery_price
#when admin create a table with delivery_price
#when admin create a table with delivery and item prcie



    # Case 2: Existing Payment updated with delivery_fee now set or changed (send delivery_fee email)
    if not created:
        print('payment delivery update email////////')
        old_delivery_fee = previous_values.get('delivery_fee')
        new_delivery_fee = instance.delivery_fee        
        
        old_item_fee = previous_values.get('item_price')
        new_item_fee = instance.item_price
        if old_delivery_fee != new_delivery_fee and new_delivery_fee is not None:
            order_steps = InProgressOrderSteps.objects.get(order = order)
            order_steps.item_received = True
            order_steps.save()

            instance.total_fee = instance.item_price + instance.delivery_fee
            instance.save()

            stripe_payment_id, payment_url, created = create_payment_session(instance)#create custom paymnt session
            send_mail(
                subject=f'비단길에서 알려드립니다. Order #{order.id}',
                message=(
                    f'안녕하세요 {user_nickname}님,\n\n'
                    f'고객님의 주문이 배송대기 중입니다.'
                    f'아래의 결제를 통해 배송을 시작해주세요.\n\n'
                    f'결제 완료 후 배송이 시작됩니다.\n'
                    f'결제: {payment_url}\n\n'
                    f'비단길 웹사이트 -> 내 정보에서 결제하실 수도 있습니다.'
                    f'더욱 상세한 주문 정보는 비단길 (웹사이트 -> 내 정보)에서 확인 가능합니다.\n'
                    f'추후 배송이 시작되면 배송 조회 번호를 보내드립니다.\n'
                    '비단길을 이용해주셔서 감사합니다'
                ),
                from_email=None,
                recipient_list=[user_email],
                fail_silently=False,
            )

            #update corresponding Payment object (invoice created/ stripe ID / paymenturl)
            instance.stripe_id = stripe_payment_id
            instance.stripe_url = payment_url
            instance.invoice_created_at = datetime.fromtimestamp(created, tz=timezone.utc)
            instance.save()


        elif old_item_fee != new_item_fee and new_item_fee is not None:        
            print('////paymnet item price update email')
            order_steps = InProgressOrderSteps.objects.get(order = order)
            order_steps.item_purchased = True
            order_steps.save()
            progressItems = order.items.all() #same as InProgressItem.object.filter(order=order) | this is called 'using reverse relationship'

            urls=[]
            descriptions =[]
            prices = []

            for item in progressItems:
                urls.append(item.url)
                descriptions.append(item.description)
                prices.append(item.price)

            detailed_message = order_message(urls, descriptions, prices)


            

            send_mail(
                subject=f'비단길에서 알려드립니다. Order #{order.id}',
                message=(
                    f'안녕하세요 {user_nickname}님,\n\n'
                    f'고객님이 주문하신 상품들의 통관정보와 가격을 알려드립니다.'
                    f'{detailed_message}'
                    f'더욱 상세한 주문 정보는 비단길 (웹사이트 -> 내 정보)에서 확인 가능합니다.'
                    f'배송준비가 완료되면 최종적인 안내와 결제 링크를 보내드립니다.'
                    '비단길을 이용해주셔서 감사합니다'
                ),
                from_email=None,
                recipient_list=[user_email],
                fail_silently=False,
            )





# @receiver(post_save, sender=Delivery)
# def send_payment_email(sender, instance, created, **kwargs):
#     if created:
#         order = instance.order
#         user = order.user
#         user_email = user.email
#         profile = Profile.objects.get(user = user)
        
#         user_nickname = profile.nickname

#         send_mail(
#             subject=f'Payment Received for Order #{order.id}',
#             message=(
#                 f'Hello {user_nickname},\n\n'
#                 f'We received your payment!\n\n'
#                 f'Order ID: #{order.id}\n'
#                 f'Item Price: ${instance.item_price}\n'
#                 f'Delivery Fee: ${instance.delivery_fee}\n'
#                 f'Total: ${instance.total_fee}\n\n'
#                 'Thank you for shopping with us!'
#             ),
#             from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings.py
#             recipient_list=[user_email],
#             fail_silently=False,
#         )