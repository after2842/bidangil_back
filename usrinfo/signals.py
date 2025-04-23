from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Payment, InProgressOrder, Delivery, Profile, InProgressOrderItem,InProgressOrderSteps
from django.db.models.signals import pre_save, post_save
from .helpers.payment_session import create_delivery_payment, create_item_payment
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
                f"곧 접수된 주문의 통관정보와 결제 링크를 안내드리겠습니다!\n"
            ),
            from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings.py
            recipient_list=[user_email],
            fail_silently=False,
        )
_PREVIOUS_DELIVERY_VALUES = {}
@receiver(pre_save, sender=Delivery)
def store_previous_delivery_fields(sender, instance, **kwargs):
  
    if instance.pk:
        try:
            previous = Delivery.objects.get(pk=instance.pk)
            _PREVIOUS_DELIVERY_VALUES[instance.pk] = {
                'delivered_at': previous.delivered_at,
            }
        except Delivery.DoesNotExist:
            _PREVIOUS_DELIVERY_VALUES[instance.pk] = {
                'delivered_at': None,
            }

@receiver(post_save, sender=Delivery) #when the delivery object is created with tracking num.courier
def delivery_started(sender, instance, created, **kwargs):
    previous_values = _PREVIOUS_DELIVERY_VALUES.pop(instance.pk, {'delivered_at': None})
    is_delivered = previous_values.get('delivered_at')        
    courier = instance.courier
    tracking_num = instance.tracking_number

    order = instance.order

    user = order.user
    user_email = user.username
    profile = Profile.objects.get(user = user)
    user_nickname = profile.nickname
    if not is_delivered:
        print('is delivered false')
    else:
        print('is delivered true')

    if created:
        print('delivery start email')


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
    elif not created and not is_delivered:
        print('delivery complete email')
        send_mail(
            subject=f'{user_nickname}님, 배송은 잘 받으셨나요? #{instance.id}',
            message=(
                f'안녕하세요 {user_nickname} 님,\n\n'
                f'고객님의 배송이 완료되었습니다!!\n\n'
                f'운송사:{courier} \n\n'
                f'조회번호:{tracking_num} \n\n'
                f'배송조회:{make_tracking_url(courier, tracking_num)} \n\n'
                f"저희 비단길을 이용해주셔서 감사합니다. 다음에는 더 쉽고 빠른 서비스로 찾아뵙겠습니다.\n"

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
        url = "{courier} 홈페이지에서 배송 조회 번호를 입력해 주세요."
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
_PREVIOUS_PROGRESS_VALUES = {}
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
    if created:
        print('when the payment object is initially created! after every inprogressitems price is filled')
        stripe_payment_id, payment_url, paymentcreated = create_item_payment(order)
        if paymentcreated:
            progressItems = order.items.all()
            detailed_message = detailed_price_message(progressItems)
            send_mail(
                    subject=f'비단길에서 알려드립니다. Order #{order.id}',
                    message=(
                        f'안녕하세요 {user_nickname}님,\n\n'
                        f'고객님의 주문을 접수 받았습니다.'
                        f'결제 완료 후 비단길에서 상품의 구매를 시작합니다.\n'
                        f'{detailed_message}\n'
                        f'결제: {payment_url}\n\n'
                        f'비단길 웹사이트 -> 내 정보에서 결제하실 수도 있습니다.'
                        f'더욱 상세한 주문 정보는 비단길 (웹사이트 -> 내 정보)에서 확인 가능합니다.\n'
                        '비단길을 이용해주셔서 감사합니다'
                    ),
                    from_email=None,
                    recipient_list=[user_email],
                    fail_silently=False,
                )
             #same as InProgressItem.object.filter(order=order) | this is called 'using reverse relationship'

            total_item_price = 0

            for item in progressItems:
                total_item_price += item.price
            #update Paymnet objects' stripe data
            instance.stripe_item_id = stripe_payment_id
            instance.stripe_item_url = payment_url
            instance.item_invoice_created_at = datetime.fromtimestamp(created, tz=timezone.utc)

            #update/calculate Payment object's item_price(total item price)
            instance.item_price = total_item_price
            instance.save()

            
        else:
            print('no item payment session created')


    # Case 2: Existing Payment updated with delivery_fee now set or changed (send delivery_fee email)
    elif not created:
        print('payment delivery update email////////')
        old_delivery_fee = previous_values.get('delivery_fee')
        new_delivery_fee = instance.delivery_fee        
        
        if old_delivery_fee != new_delivery_fee and new_delivery_fee is not None:
            order_steps = InProgressOrderSteps.objects.get(order = order)
            order_steps.delivery_ready = True
            order_steps.save()

            instance.total_fee = instance.item_price + instance.delivery_fee
            instance.save()

            stripe_payment_id, payment_url, paymentcreated = create_delivery_payment(instance)#create custom paymnt session
            if paymentcreated:
                send_mail(
                    subject=f'비단길에서 알려드립니다. Order #{order.id}',
                    message=(
                        f'안녕하세요 {user_nickname}님,\n\n'
                        f'고객님의 주문이 배송대기 중입니다.'
                        f'아래의 링크로 배송비를 결제해주세요.\n\n'
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

                instance.stripe_delivery_id = stripe_payment_id
                instance.stripe_delivery_url = payment_url
                instance.delivery_invoice_created_at = datetime.fromtimestamp(created, tz=timezone.utc)
                instance.save()

@receiver(pre_save, sender=InProgressOrderSteps)
def store_previous_payment_fields(sender, instance, **kwargs):

    if instance.pk:
        try:
            previous = InProgressOrderSteps.objects.get(pk=instance.pk)
            _PREVIOUS_PROGRESS_VALUES[instance.pk] = {
                'item_purchased': previous.item_purchased,
            }
        except InProgressOrderSteps.DoesNotExist:
            _PREVIOUS_PROGRESS_VALUES[instance.pk] = {
                'item_purchased': None,
            }            

@receiver(post_save, sender=InProgressOrderSteps)
def send_payment_update_emails(sender, instance, created, **kwargs):
    order = instance.order
    user = order.user
    user_email = user.username
    profile = Profile.objects.get(user = user)
    
    user_nickname = profile.nickname

    previous_values = _PREVIOUS_PROGRESS_VALUES.pop(instance.pk, {'item_purchased': None})

    #send clients' that we've purchased the item. WHEN the admin check 'item_purchased'
    if instance.item_purchased and (not previous_values.get('item_purchased')):        
        print('let user know item is purchased')
        progressItems = order.items.all() #same as InProgressItem.object.filter(order=order) | this is called 'using reverse relationship'


        detailed_message = detailed_price_message(progressItems)


        

        send_mail(
            subject=f'비단길에서 알려드립니다. Order #{order.id}',
            message=(
                f'안녕하세요 {user_nickname}님,\n\n'
                f'고객님이 주문하신 상품들을 비단길에서 구매하였습니다.'
                f'더욱 상세한 주문 정보는 비단길 (웹사이트 -> 내 정보)에서 확인 가능합니다.'
                f'배송준비가 완료되면 최종적인 안내와 배송비 결제 링크를 보내드립니다.'
                '비단길을 이용해주셔서 감사합니다'
            ),
            from_email=None,
            recipient_list=[user_email],
            fail_silently=False,
        )


def detailed_price_message(progressItems):
    urls=[]
    descriptions =[]
    prices = []

    for item in progressItems:
        urls.append(item.url)
        descriptions.append(item.description)
        prices.append(item.price)

    return order_message(urls, descriptions, prices)


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