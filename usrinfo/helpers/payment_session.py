import stripe
from decimal import Decimal
from django.conf import settings
stripe.api_key = settings.STRIPE_API


def create_payment_session(payment):
    inprogress_order = payment.order

    exchange_rate = inprogress_order.exchange_rate
    
    item_price = payment.item_price
    delivery_fee = payment.delivery_fee

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='payment',
        line_items=[
            {
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(round(item_price/exchange_rate, 2)*100), 
                    'product_data': {
                        'name': '구매 대금',
                    },
                },
                'quantity': 1,
            },
            {
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(round((delivery_fee/exchange_rate) ,2)*100), 
                    'product_data': {
                        'name': '배송비',
                    },
                },
                'quantity': 1,
            },
            {
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int((  round(((item_price/exchange_rate)  + (delivery_fee/exchange_rate))  *  Decimal(0.04),2))*100),  
                    'product_data': {
                        'name': '카드 수수료',
                    },
                },
                'quantity': 1,
            },            {
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': 0, #int(round((item_price/exchange_rate) * Decimal(0.04),2)*100),  
                    'product_data': {
                        'name': '대행 수수료 4%',
                    },
                },
                'quantity': 1,
            },
        ],
        success_url='https://naver.com',
        cancel_url='https://google.com',
    )

    return session.id, session.url, session.created