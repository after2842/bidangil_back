from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json


def karrio_webhook(request):
    if request.method == 'POST':
        payload = json.loads(request.body)
        
        print("Received webhook payload:", payload)

        # Do something: update your order tracking info
        # payload['tracking_number'], payload['status'], etc.

        return JsonResponse({'message': 'Webhook received'})
    else:
        return JsonResponse({'error': 'Invalid request'}, status=400)