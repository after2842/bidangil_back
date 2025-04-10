from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from ..models import Payment, InProgressOrder, Delivery, Profile, InProgressOrderItem
from django.db.models.signals import pre_save, post_save

@receiver(post_save, sender=InProgressOrder)
def send_new_order_email(sender, instance, created, **kwargs):
    if created:
        print('///////////new order created!!!!!///////////')
        user = instance.user
        user_email = user.username
        profile = Profile.objects.get(user = user)
        items = InProgressOrderItem.objects.filter(order = instance)
        user_nickname = profile.nickname
        send_mail(
            subject=f'{user_nickname}의 주문이 접수되었습니다! #{instance.id}',
            message=(
                f'안녕하세요 {user_nickname} 님,\n\n'
                f'비단길을 이용해주셔서 감사합니다.\n\n'
                f'고객님의 주문요청이 접수되었습니다.\n\n'
                f"더 자세한 사항은 '홈페이지 -> 내 정보'에서 확인하실 수 있습니다.\n"
                f"고객님의 물건을 구매한 뒤에 다시 연락드리겠습니다!\n"
            ),
            from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings.py
            recipient_list=[user_email],
            fail_silently=False,
        )




_PREVIOUS_PAYMENT_VALUES = {}

@receiver(pre_save, sender=Payment)
def store_previous_payment_fields(sender, instance, **kwargs):
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
    order = instance.order
    user = order.user
    user_email = user.email
    user_nickname = user.profile.nickname if hasattr(user, 'profile') else user.username

    previous_values = _PREVIOUS_PAYMENT_VALUES.pop(instance.pk, {'item_price': None, 'delivery_fee': None})

    # Case 1: Newly created Payment with item_price set (send item_price email)
    if created and instance.item_price is not None:
        send_mail(
            subject=f'Item Price Determined for Order #{order.id}',
            message=(
                f'Hello {user_nickname},\n\n'
                'The item price for your order has been determined.\n\n'
                f'Order ID: #{order.id}\n'
                f'Item Price: ${instance.item_price}\n\n'
                'Thank you for shopping with us!'
            ),
            from_email=None,
            recipient_list=[user_email],
            fail_silently=False,
        )

    # Case 2: Existing Payment updated with delivery_fee now set or changed (send delivery_fee email)
    if not created:
        old_delivery_fee = previous_values.get('delivery_fee')
        new_delivery_fee = instance.delivery_fee
        if old_delivery_fee != new_delivery_fee and new_delivery_fee is not None:
            send_mail(
                subject=f'Delivery Fee Determined for Order #{order.id}',
                message=(
                    f'Hello {user_nickname},\n\n'
                    'The delivery fee for your order has been determined.\n\n'
                    f'Order ID: #{order.id}\n'
                    f'Delivery Fee: ${new_delivery_fee}\n\n'
                    'Thank you for shopping with us!'
                ),
                from_email=None,
                recipient_list=[user_email],
                fail_silently=False,
            )


@receiver(post_save, sender=Delivery)
def send_payment_email(sender, instance, created, **kwargs):
    if created:
        order = instance.order
        user = order.user
        user_email = user.username
        user_nickname = user.profile.nickname if hasattr(user, 'profile') else user.username

        send_mail(
            subject=f'Payment Received for Order #{order.id}',
            message=(
                f'Hello {user_nickname},\n\n'
                f'We received your payment!\n\n'
                f'Order ID: #{order.id}\n'
                f'Item Price: ${instance.item_price}\n'
                f'Delivery Fee: ${instance.delivery_fee}\n'
                f'Total: ${instance.total_fee}\n\n'
                'Thank you for shopping with us!'
            ),
            from_email=None,  # Uses DEFAULT_FROM_EMAIL from settings.py
            recipient_list=[user_email],
            fail_silently=False,
        )