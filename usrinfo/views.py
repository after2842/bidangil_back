from django.shortcuts import render
from openai import OpenAI
from django.http import JsonResponse 
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
import json
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from rest_framework.decorators import api_view, permission_classes
# from .serializers import 
from django.contrib.auth.models import User
from .models import Profile, EmailVerification,InProgressOrder,InProgressOrderItem, PastOrder, PastOrderItem, Payment, Delivery, InProgressOrderSteps
from django.core.mail import send_mail
import random
from django.utils import timezone
import trackingmore
from datetime import datetime
from .helpers.exchange_rate import get_exchange_rate
from .webhooks.stripewebhook import handle_stripe_webhook
from django.conf import settings

@api_view(["GET"])
def get_csrf_token(request):
    """
    Returns a JSON with the current CSRF token.
    Also sets csrftoken cookie in the response.
    """
    print("Incoming Request Cookies:")
    for key, value in request.COOKIES.items():
        print(f"{key}: {value}")
    csrf_token = get_token(request)  # This sets the "csrftoken" cookie in response
    print('csrf_token',csrf_token)
    return JsonResponse({"csrfToken": csrf_token})


@api_view(["POST"])
def send_verification_code(request):
    data = json.loads(request.body)
    print('inside sending',data)
    email = data['email']
    print(f"email{email}")
    try:
        if not email:
            return 'noEmail'
        
        if User.objects.filter(username=email).exists():
            return JsonResponse({'msg':'existing_email'}, status= 400)
        
        
        code = (random.randint(100000,999999))
        print(f"code{code}")

        record, created = EmailVerification.objects.update_or_create(
            email=email,
            defaults = {'code' : code}
        )
        if not created: # When EmailVerification is updated => update created at to update expire time
            record.created_at = timezone.now()
            print(f"is created {record.created_at} {timezone.now()}  {code}")
            record.save()

        send_mail(
            '비단길 인증코드입니다.',
            f'회원님의 인증코드는 {code} 입니다',
            'no-reply@atozservice.net',
            [email],
            fail_silently=False,

        )
        return JsonResponse({'msg':'success'}, status= 200)
    except:
        return JsonResponse({'msg':'wrong'}, status= 500)



@api_view(["POST"])
def verify_code(request):
    data = json.loads(request.body)
    email = data['email']
    code = data['code']
    print(f"###########{email}####")
    print(f"###########{code}####")
    try:
        print("---- All EmailVerification records ----")
        for obj in EmailVerification.objects.all():
            print(f"email: {obj.email}, code: {obj.code}, verified: {obj.isVerified}, created_at: {obj.created_at}")

        record = EmailVerification.objects.get(email=email, code=code)
        print(f"created_at: {record.created_at} email:{record.email}")
        
        if record.is_expired():
            print('expired!!')
            return JsonResponse({'msg':'expired'}, status= 401)
        else:   
            record.isVerified = True
            record.save()
            print("---- All EmailVerification records ----")
            for obj in EmailVerification.objects.all():
                print(f"email: {obj.email}, code: {obj.code}, verified: {obj.isVerified}, created_at: {obj.created_at}")
            return JsonResponse({'msg':'success'}, status= 200)
        
    except EmailVerification.DoesNotExist:
        return 500



@api_view(["POST"])
def signup_view(request):
    """
    A simple signup view that creates a new user account.
    Expects JSON: { "username": "", "email": "", "password": "" }
    """
    print('INSIDE SIGN UP VIEW')
    try:
        data = json.loads(request.body)
        nickname = data.get("username")

        password = data.get("userpassword")
        username = data.get("useremail")
        
     
        # Validate required fields
        if not username or not nickname or not password:
            print(f"usr{username} no sufficient fields")
            return JsonResponse({"error": "All fields (username, email, password) are required."}, status=400)
  
        # Check if user already exists by username or email
        if User.objects.filter(username=username).exists():
            print(f"usr{username} alreqdy exists")
            return JsonResponse({"error": "Email already registered"}, status=401)
        
        #check if email is verified
        record = EmailVerification.objects.get(email=username)
        if record.isVerified == True:
            # Create the user
            user = User.objects.create_user(
                username= username,
                password=password,            
                )
            print(f"usr{username} is created!!!!!")
            profile = Profile.objects.create(
                user=user,
                nickname = nickname,

            )
            login(request, user)
    
            return JsonResponse({'msg': f"{nickname} is created!", "data":nickname}, safe=False, status=201)

            # (Optional) Log the user in immediately after signup:
            # login(request, user)
        else:
            return JsonResponse({'msg': f"Email not verified!"}, safe=False, status=402)
        

    except Exception as e:
        print(f"err{e}")
        return JsonResponse({"error": str(e)}, status=500)
    


@api_view(["POST"])
def login_view(request):
    data = request.data
    password = data.get("userpassword")
    email = data.get("useremail")
    print(password,email)
    users = User.objects.all()
    for user in users:
        print("--------")
        print("ID:", user.id)
        print("Username:", user.username)
        print("Email:", user.email)
        print("Date joined:", user.date_joined)
    user = authenticate(request, username=email, password=password)
    if not user:
        return JsonResponse({'error': 'wrong credentials'}, status = 404)
    print('succcessfully logged in!!!', user)
    login(request, user)
    print('log in session activated!!!')
    if user is not None:
        profile = Profile.objects.get(user=user)
        print('login nickname to front',user.username,profile.nickname)
        return JsonResponse({'msg': f"{email} is logged in!",'data': {'email':user.username, 'nickname':profile.nickname}}, safe=False)
    return JsonResponse({"error": "Invalid credentials"}, status=401)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def logout_view(request):
    user = request.user
    user_email = user.username
    logout(request)
    return JsonResponse({"msg": f"{user_email}Logged out"}, status=200)

@api_view(["POST"])
@permission_classes([IsAuthenticated]) 
def create_inprogress_order(request):   #api/submit_order/
    print('inside Create inprogress!!!')
    user = request.user
    print('user',user.username)
    data = request.data

    combined_address = f"{data['address']['addressLine1']}\n{data['address']['addressLine2']}\n{data['address']['city']}\n{data['address']['state']}\n{data['address']['zip']} "
    print(f"CombinedAddress\n{combined_address}")
    order =  InProgressOrder.objects.create(
        user=user,
        address = combined_address,
        exchange_rate = get_exchange_rate()
        )
    # allorders = InProgressOrder.objects.all()
    # for singleorder in allorders:
    #     print(f"singleorder {singleorder.order_created_at}\n {singleorder.user}\n {singleorder.address}")

    for item in data['orders']:
        InProgressOrderItem.objects.create(
            order=order,
            url=item['storeUrl'],
            description = item['productOptions'],
        )
    print(order.id)
    # allItemperorder = InProgressOrderItem.objects.all()
    # for singleitem in allItemperorder:
        # print(f"item {singleitem.url}\n {singleitem.description}")

    return JsonResponse({"order_id": order.id}, status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated]) 
def get_profile_info(request):
    ProfileDataList = []
    try:
        user = request.user
        inprogress_orders = InProgressOrder.objects.filter(user = user)

        for inprogress_order in inprogress_orders:
            inprogress_items = InProgressOrderItem.objects.filter(order = inprogress_order) #items requested per Order
            # Try to get Payment info
            try:
                payment_info = Payment.objects.get(order=inprogress_order)
                payment_data = {
                'item_price': float(payment_info.item_price) if payment_info.item_price is not None else None,
                'delivery_price': float(payment_info.delivery_fee) if payment_info.delivery_fee is not None else None,
                'total_price': float(payment_info.total_fee) if payment_info.total_fee is not None else None,
                'is_paid': payment_info.is_paid,
                'invoice_created_at': str(payment_info.invoice_created_at) if payment_info.invoice_created_at else None,
                'payment_url': str(payment_info.stripe_url) if payment_info.stripe_url else None,
                }
            except Payment.DoesNotExist:
                payment_data = None

            # Try to get Delivery info
            try:
                delivery_info = Delivery.objects.get(order=inprogress_order)
                delivery_data = {
                    'delivery_start_at': str(delivery_info.delivery_start_at),
                    'courier': delivery_info.courier,
                    'tracking_number': delivery_info.tracking_number,
                    'delivered_at': str(delivery_info.delivered_at),
                }
            except Delivery.DoesNotExist:
                delivery_data = None
            try:
                steps_info = InProgressOrderSteps.objects.get(order=inprogress_order)
                steps_data = [
                    {'label': '주문 접수 완료', 'isDone': steps_info.request_received},
                    {'label': '물건 구매 완료', 'isDone': steps_info.item_purchased},
                    {'label': '물건 도착', 'isDone': steps_info.item_received},
                    {'label': '구매/배송비 결제 완료', 'isDone': steps_info.payment_received},
                    {'label': '배송 시작', 'isDone':steps_info.delivery_started},
                ]
            except InProgressOrderSteps.DoesNotExist:
                steps_data = None

            ProfileData = {
                'id':inprogress_order.id,
                'address': inprogress_order.address,
                'order_created_at': str(inprogress_order.order_created_at),
                'exchange_rate': str(inprogress_order.exchange_rate),
                'items':make_inprogress_items(inprogress_items),
                'Payment':payment_data,
                'Delivery':delivery_data,
                'Steps':steps_data,
            }
            print(f"ProfileDataList:{ProfileDataList}/// exchangerate {ProfileData['exchange_rate']}")
            ProfileDataList.append(ProfileData)
            print(json.dumps(ProfileDataList,indent=4))
        return JsonResponse({'msg': 'user inprogress data loaded!', 'data': ProfileDataList}, status = 200)
    except Exception as e:
        print(str(e))
        return JsonResponse({'err msg': str(e)}, status = 500)



def make_inprogress_items(inprogress_items):
    return [{'url': item.url, 'description': item.description} for item in inprogress_items]



def move_to_past_order(inprogress_order_id):
    # 1. Get the in-progress order
    inprogress_order = InProgressOrder.objects.get(id=inprogress_order_id)

    # 2. Create a new PastOrder with the same fields
    past_order = PastOrder.objects.create(
        user = inprogress_order.user,
        items_price = inprogress_order.items_price,
        delivery_price = inprogress_order.delivery_price,
        is_paid = inprogress_order.is_paid,
        tracking_number = inprogress_order.tracking_number,
        order_created_at = inprogress_order.order_created_at,
        delivery_started_at = inprogress_order.delivery_started_at,
        delivery_ended_at = timezone.now()  # or the final timestamp
    )

    # 3. Copy each InProgressOrderItem to PastOrderItem
    for item in inprogress_order.items.all():
        PastOrderItem.objects.create(
            order = past_order,
            url = item.url,
            description = item.description
        )

    # 4. Remove the old in-progress order 
    inprogress_order.delete()

    return past_order



def get_tracking_status(tracking_number = '771809733171'): #call when user click the userprofile

    trackingmore.api_key = '56r7vls8-an4v-octa-i1sc-bhtgqbryhuwl'

    tracking_history = []
    try:

        params = {'tracking_numbers': f"{tracking_number}", 'courier_code': 'fedex'}
        tracking_status = trackingmore.tracking.get_tracking_results(params)

        tracking_data = tracking_status['data'][0]['origin_info']['trackinfo']
        trackinfo_sorted = sorted(tracking_data, key=lambda x: datetime.fromisoformat(x['checkpoint_date']))

        for i, status in enumerate(trackinfo_sorted):
            tracking_checkpoint = {
                'date':status.get('checkpoint_date'),
                'status' : status.get('checkpoint_delivery_status'),
                'location' : status.get('location')
            }
            print(f"{i+1}th update: \n DATE: {tracking_checkpoint['date']}\n STATUS:{tracking_checkpoint['status']}\n LOCATION:{tracking_checkpoint['location']}")
            tracking_history.append(tracking_checkpoint)
        return tracking_history

           

    except trackingmore.exception.TrackingMoreException as ce:
        print(ce)
    except Exception as e:
        print("other error:", e) 


    
@csrf_exempt
@api_view(["POST"])
def stripe_webhook_view(request):
    response = handle_stripe_webhook(request=request)
    session_id = response['id']
    did_pay = response['did_pay']

    if did_pay:
        try:
            user_payment_object = Payment.objects.filter(stripe_id = session_id)
            user_payment_object.is_paid = True
            user_payment_object.save()
            steps = InProgressOrderSteps.objects.get(order = user_payment_object.order)
            steps.payment_received = True
            steps.save()


            user_nickname =  Profile.objects.get(user = user_payment_object.order.user)
            email = user_payment_object.order.user.username

            send_mail(
                subject=f'비단길에서 알려드립니다. Order #{user_payment_object.order.id}',
                message=(
                    f'안녕하세요 {user_nickname}님 결제해주셔서 감사합니다,\n\n'
                    f'고객님의 결제가 정상적으로 처리되었습니다.\n\n'
                    f'곧 고객님의 물건이 발송될 예정이오니, 추후 안내 드리겠습니다..\n'
                    f'상세한 주문 정보는 비단길 (웹사이트 -> 내 정보)에서 확인 가능합니다.'
                    '비단길을 이용해주셔서 감사합니다'
                ),
                from_email=None,
                recipient_list=[email],
                fail_silently=False,
            )
            print('payment successful!')
        except Exception as e:
            print(e)
    else:
        print('user payment not completed')













