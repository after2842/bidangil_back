from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from .models import Payment, InProgressOrder, Delivery, Profile, InProgressOrderItem,InProgressOrderSteps
from django.db.models.signals import pre_save, post_save
from .helpers.payment_session import create_delivery_payment, create_item_payment
from datetime import datetime, timezone
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from .helpers.email_template import render_order_email, order_message, render_delivery_email, purchase_confirm_email, render_delivery_info_email, render_delivery_complete_email,render_order_start_email
from .helpers.send_sms import send_sms
@receiver(post_save, sender=InProgressOrder)
def send_new_order_email(sender, instance, created, **kwargs):
    if created:
        print('//////inprogress//////email')
        user = instance.user
        user_email = user.username
        profile = Profile.objects.get(user = user)
        
        user_nickname = profile.nickname
        InProgressOrderSteps.objects.create(order=instance, request_received = True)
        subject = f'비단길에서 안내드립니다 – 주문번호 #{instance.id}'

        # Fallback text version for clients that don’t support HTML
        text_content = (
            f'안녕하세요 {user_nickname} 님,\n\n'
            f'비단길을 이용해주셔서 감사합니다.\n\n'
            f'고객님의 주문요청이 접수되었습니다. 주문버호: {instance.id}\n\n'
            f"더 자세한 사항은 '홈페이지 -> 내 정보'에서 확인하실 수 있습니다.\n"
            f"곧 접수된 주문의 통관정보와 결제 링크를 안내드리겠습니다\n"
        )

        # Render HTML with your helper function
        html_content = render_order_start_email(
            user_nickname=user_nickname,
            order_id=instance.id
        )

        # Send the email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        send_sms(phone_num='9492997512', country_code='1', nickname=f"", content=f"새 주문 #{instance.id}")
        send_sms(phone_num='01083413311', country_code='82', nickname=f"", content=f"새 주문 #{instance.id}")

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
    steps = order.steps
    user_nickname = profile.nickname

    if not is_delivered:
        print('is delivered false')
        print(f"courier: {instance.courier}")
        print(f"tracking_num: {instance.tracking_number}")
    else:
        print('is delivered true')

    if created:
        print('delivery start email')


        steps = InProgressOrderSteps.objects.get(order = order)
        steps.delivery_started = True
        steps.save()
        subject = f'비단길에서 안내드립니다. – 주문번호 #{order.id}'

        # Fallback text version for clients that don’t support HTML
        text_content = (
            f'안녕하세요 {user_nickname} 님,\n\n'
            f'고객님의 배송이 시작되었습니다.\n\n'
            f'운송사:{courier} \n\n'
            f'조회번호:{tracking_num} \n\n'
            f'배송조회:{make_tracking_url(courier, tracking_num)} \n\n'
            f"더 자세한 사항은 '홈페이지 -> 내 정보'에서 확인하실 수 있습니다.\n"
        )

        # Render HTML with your helper function
        html_content = render_delivery_info_email(
            user_nickname=user_nickname,
            courier=courier,
            tracking_num=tracking_num,
            tracking_url=make_tracking_url(courier, tracking_num),
        )

        # Send the email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        send_sms(phone_num=order.phone, country_code='1', nickname=user_nickname, content="[비단길 알림]\n 고객님의 배송이 시작되었습니다. \n이메일을 확인해주세요.")
        

    elif not created and not is_delivered and steps.delivery_completed:
        print('delivery complete email')
        subject = f'[비단길] {user_nickname}님, 배송은 잘 받으셨나요? #{instance.id}'

        # Fallback text version for clients that don’t support HTML
        text_content = (
            f'안녕하세요 {user_nickname} 님,\n\n'
            f'고객님의 배송이 완료되었습니다!!\n\n'
            f'고객님의 소중한 리뷰를 남겨주세요\n\n'
            f"https://bidangil.co/community/review\n"
            f"저희 비단길을 이용해주셔서 감사합니다. 다음에는 더 쉽고 빠른 서비스로 찾아뵙겠습니다.\n"
        )

        # Render HTML with yousr helper function
        html_content = render_delivery_complete_email(
            user_nickname=user_nickname,
        )

        # Send the email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()



def make_tracking_url(courier, tracking_num):
    if courier.lower() == 'fedex':
        url = f"https://www.fedex.com/fedextrack/?trknbr={tracking_num}"
    elif courier.lower() =='ems':
        url =  f"https://service.epost.go.kr/trace.RetrieveEmsRigiTraceList.comm?POST_CODE={tracking_num}"
    else:
        url = "{courier} 홈페이지에서 배송 조회 번호를 입력해 주세요."
    return url


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
            subject = f'비단길에서 안내드립니다 – 주문번호 #{order.id}'

            # Fallback text version for clients that don’t support HTML
            text_content = (
                f'안녕하세요 {user_nickname}님,\n\n'
                f'주문이 접수되었습니다.\n'
                f'{detailed_message}\n'
                f'결제: {payment_url if payment_url else "비단길 웹사이트 → 내 정보"}\n\n'
                f'비단길을 이용해주셔서 감사합니다.'
            )

            # Render HTML with your helper function
            html_content = render_order_email(
                user_nickname=user_nickname,
                order_id=order.id,
                detailed_message=detailed_message,
                payment_url=payment_url,
            )

            # Send the email
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user_email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
             #same as InProgressItem.object.filter(order=order) | this is called 'using reverse relationship'

            send_sms(phone_num=order.phone, country_code='1', nickname=user_nickname, content="[비단길 알림]\n고객님의 주문이 결제 대기중입니다.\n이메일을 확인해주세요.")
  

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

            detailed_message = order.address

            instance.total_fee = instance.item_price + instance.delivery_fee
            instance.save()

            stripe_payment_id, payment_url, paymentcreated = create_delivery_payment(instance)#create custom paymnt session
            if paymentcreated:
                subject = f'비단길에서 안내드립니다 – 주문번호 #{order.id}'

                # Fallback text version for clients that don’t support HTML
                text_content = (
                    f'안녕하세요 {user_nickname}님,\n\n'
                    f'고객님의 주문이 배송대기 중입니다.\n'
                    f'다음의 링크를 통해 결제를 해주시면, 비단길에서 다음의 주소로 배송을 시작합니다.'
                    f'{detailed_message}'
                    f'결제: {payment_url if payment_url else "비단길 웹사이트 → 내 정보"}\n\n'
                    f'비단길을 이용해주셔서 대단히 감사합니다.'
                )

                # Render HTML with your helper function
                html_content = render_delivery_email(
                    user_nickname=user_nickname,
                    order_id=order.id,
                    detailed_message=detailed_message,
                    payment_url=payment_url,
                )

                # Send the email
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[user_email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
                send_sms(phone_num=order.phone, country_code='1', nickname=user_nickname, content="[비단길 알림]\n고객님의 물건이 배송 대기중입니다.\n이메일을 확인해주세요.")

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

        subject = f'비단길에서 안내드립니다 – 주문번호 #{order.id}'

        # Fallback text version for clients that don’t support HTML
        text_content = (
            f'안녕하세요 {user_nickname}님,\n\n'
            f'고객님이 주문하신 상품들을 비단길에서 구매하였습니다.\n'
            f'배송준비가 완료되면 최종적인 안내와 배송비 결제 링크를 보내드립니다.'
            f'비단길을 이용해주셔서 감사합니다'
        )

        # Render HTML with your helper function
        html_content = purchase_confirm_email(
            user_nickname=user_nickname,
        )

        # Send the email
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user_email]
        )
        email.attach_alternative(html_content, "text/html")
        email.send()
        send_sms(phone_num=order.phone, country_code='1', nickname=user_nickname, content="[비단길 알림]\n비단길에서 주문하신 상품을 구매하였습니다.\n이메일을 확인해주세요.")
        




def detailed_price_message(progressItems):
    urls=[]
    descriptions =[]
    prices = []

    for item in progressItems:
        urls.append(item.url)
        descriptions.append(item.description)
        prices.append(item.price)

    return order_message(urls, descriptions, prices)

