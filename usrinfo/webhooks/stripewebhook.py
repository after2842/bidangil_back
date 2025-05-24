import stripe
from django.http import JsonResponse, HttpResponse
from django.conf import settings

endpoint_secret = settings.STRPIE_WEBHOOK_SEC

def handle_stripe_webhook(request):
    print('inside the function')
    payload = request.body   #payload is just a raw byte    
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    # session = payload.data
    # session_id = session.object.id
    # print(f"payload :{payload}")

    try:
        # 1) Construct the event with Stripe's helper => verify its authecticity && resolve the byte data to dictionary 
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=endpoint_secret
        )

    except ValueError:
        # Invalid JSON
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError:
        # Invalid signature
        return HttpResponse(status=400)

    
    try:
        if event['type'] == "checkout.session.completed":
            session = event["data"]["object"]  
            session_id = session['id']
            payment_type = session['metadata']['payment_type']

            return {'did_pay': True, 'id': session_id, 'type': payment_type}
        
        elif event['type'] == "checkout.session.expired":
            print('expired')
            return False
        
        elif event['type'] == "checkout.session.async_payment_succeeded":
            print('async payment succeded')
            return False
        
        elif event['type'] == "checkout.session.async_payment_failed":
            print('async paymnet failed')
            return False
        

    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    # 🔔 Handle different event types
    # if event["type"] == "payment_intent.succeeded":
    #     payment_intent = event["data"]["object"]
    #     print("✅ Payment succeeded:", payment_intent["id"])
    #     # Handle your logic (update models, send email, etc.)

    # elif event["type"] == "payment_intent.payment_failed":
    #     print("❌ Payment failed")

    return {"status": "received"}

#listens these four events
# checkout.session.async_payment_failed
# checkout.session.async_payment_succeeded
# checkout.session.completed
# checkout.session.expired