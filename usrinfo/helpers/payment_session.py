import stripe
from decimal import Decimal
from django.conf import settings

stripe.api_key = settings.STRIPE_API


def create_delivery_payment(payment):
    inprogress_order = payment.order

    exchange_rate = Decimal(inprogress_order.exchange_rate)
    
    
    delivery_fee = payment.delivery_fee

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='payment',
        line_items=[
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
                    'unit_amount': int((  round(( (delivery_fee/exchange_rate))  *  Decimal(0.04),2))*100),  
                    'product_data': {
                        'name': '카드 수수료 4%',
                    },
                },
                'quantity': 1,
            },          
        ],
        success_url='https://bidangil.co',
        cancel_url='https://google.com',
                metadata={
            'payment_type': 'delivery',        # <--- Custom data you add
            'inprogress_order_id': str(inprogress_order.id),  # or anything else
        }
    )

    return session.id, session.url, session.created



def create_item_payment(order):
    

    exchange_rate = order.exchange_rate
    
    items = order.items.all()
    prices = []
    total = Decimal('0.0')
    for item in items:
        prices.append(item.price)
        total +=item.price
     
    payment_desc = [            {
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int(round(item_price/exchange_rate, 2)*100), 
                    'product_data': {
                        'name': f'상품{index+1}',
                    },
                },
                'quantity': 1,
            } for index, item_price in enumerate(prices)]
    payment_desc.extend([            {
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': int((  round( (total/exchange_rate)  *  Decimal(0.04),2))*100),  
                    'product_data': {
                        'name': '카드 수수료',
                    },
                },
                'quantity': 1,
            }, {
                'price_data': {
                    'currency': 'usd',
                    'unit_amount': 0, #int(round((item_price/exchange_rate) * Decimal(0.04),2)*100),  
                    'product_data': {
                        'name': '대행 수수료 4%',
                    },
                },
                'quantity': 1,
            },])

    session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        mode='payment',
        line_items=payment_desc,
        success_url='https://bidangil.co',
        cancel_url='https://google.com',
                        metadata={
            'payment_type': 'items',        # <--- Custom data you add
            'inprogress_order_id': str(order.id),  # or anything else
        }
    )

    return session.id, session.url, session.created