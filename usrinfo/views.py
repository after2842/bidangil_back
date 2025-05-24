from django.shortcuts import render
from openai import OpenAI
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from rest_framework.permissions import IsAuthenticated
import json
from django.contrib.auth import authenticate, login, logout
from django.middleware.csrf import get_token
from rest_framework.decorators import api_view, permission_classes, parser_classes
# from .serializers import 
from django.contrib.auth.models import User
from .models import Profile, EmailVerification,InProgressOrder,InProgressOrderItem, PastOrder, PastOrderItem, Payment, Delivery, InProgressOrderSteps, Post, PostImage, PostLikes, UserLikes, PostComment, CommentLikes
from django.core.mail import send_mail
import random
from django.utils import timezone
from datetime import datetime, date
import calendar
from .tasks import process_websearch_task, generate_avatar
from .helpers.exchange_rate import get_exchange_rate
from .helpers.s3 import upload_png
from .webhooks.stripewebhook import handle_stripe_webhook
from .webhooks.trackingwebhook import karrio_webhook
from django.conf import settings
from rest_framework.parsers import MultiPartParser, FormParser
import requests
from .serializers import ReviewSerializer, PostSerializer, CommunityInfoByOthersSerializer, CommentTreeSerializer
from django.core.mail import EmailMultiAlternatives
from .helpers.send_sms import send_sms
from .helpers.email_template import render_item_payment_confirm_email, render_delivery_payment_confirm_email
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

def session_ping(request):
    if request.user.is_authenticated:
        return JsonResponse({"authenticated": True})
    return JsonResponse({"authenticated": False}, status=401)

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
            subject ='비단길 인증코드입니다.',
            message = f'회원님의 인증코드는 {code} 입니다',
            from_email='support@bidangil.co',
            recipient_list=[email],
            
            fail_silently=False,

        )
        return JsonResponse({'msg':'success'}, status= 200)
    except Exception as e:
        print(e)
        return JsonResponse({'msg':'wrong'}, status= 500)



@api_view(["POST"])
def verify_code(request):
    data = json.loads(request.body)
    email = data['email']
    code = data['code']
    # print(f"###########{email}####")
    # print(f"###########{code}####")
    try:
        # print("---- All EmailVerification records ----")
        # for obj in EmailVerification.objects.all():
        #     print(f"email: {obj.email}, code: {obj.code}, verified: {obj.isVerified}, created_at: {obj.created_at}")

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
        return JsonResponse({'msg': f"{email} is logged in!",'data': {'email':user.username, 'nickname':profile.nickname}}, status=200)
    return JsonResponse({"error": "Invalid credentials"}, status=401)




@api_view(["POST"])
def logout_view(request):
    try:
        user = request.user
        user_email = user.username
        logout(request)
        return JsonResponse({"msg": f"{user_email}Logged out"}, status=200)
    except Exception as e:
        print("logoutview err",e)
        return JsonResponse({"err": str(e)}, status=400)

@api_view(["POST"])
@permission_classes([IsAuthenticated]) 
def create_inprogress_order(request):   #api/submit_order/
    print('inside Create inprogress!!!')
    user = request.user
    print('user',user.username)
    data = request.data

    combined_address = f"{data['address']['addressLine1']}\n{data['address']['addressLine2']}\n{data['address']['city']}\n{data['address']['state']}\n{data['address']['zip']} "
    print(f"CombinedAddress\n{combined_address}")
    name = data['address']['name']
    phone = data['address']['phone']
    order =  InProgressOrder.objects.create(
        user=user,
        address = combined_address,
        name = name,
        phone = phone,
        exchange_rate = get_exchange_rate()
        )
    # allorders = InProgressOrder.objects.all()
    # for singleorder in allorders:
    #     print(f"singleorder {singleorder.order_created_at}\n {singleorder.user}\n {singleorder.address}")

    for item in data['orders']:

        order_item = InProgressOrderItem.objects.create(
            order=order,
            url=item['url'],
            description = item['desc'],
            
            
        )
        print('process websearch!')
        process_websearch_task.delay(obj_id = order_item.id, url = item['url'])
        print('process websearch2!')
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
        nickname = user.profile.nickname
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
                'item_is_paid': payment_info.item_is_paid,
                'delivery_is_paid':payment_info.delivery_is_paid,
                'stripe_item_url': str(payment_info.stripe_item_url) if payment_info.stripe_item_url else None,
                'stripe_delivery_url':str(payment_info.stripe_delivery_url) if payment_info.stripe_delivery_url else None,
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
                    {'label': '물건 도착', 'isDone': steps_info.delivery_ready},
                    {'label': '배송 시작', 'isDone':steps_info.delivery_started},
                    {'label': '배송 완료', 'isDone':steps_info.delivery_completed},
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
        return JsonResponse({'msg': 'user inprogress data loaded', 'data': ProfileDataList,'nickname' : str(nickname)}, status = 200)
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


    
@csrf_exempt
@api_view(["POST"])
def stripe_webhook_view(request):
    response = handle_stripe_webhook(request=request)
    session_id = response['id']
    did_pay = response['did_pay']
    payment_type = response['type']

    if did_pay:
        try:
            if payment_type == 'delivery':
                #find the corresponding Payment object
                user_payment_object = Payment.objects.filter(stripe_delivery_id = session_id)
                user_payment_object.delivery_fee_paid = True
                user_payment_object.save()

                #update the order step object
                steps = InProgressOrderSteps.objects.get(order = user_payment_object.order)
                steps.delivery_fee_paid = True

                steps.save()

                usr_phone = user_payment_object.order.phone

                user_nickname =  Profile.objects.get(user = user_payment_object.order.user)
                email = user_payment_object.order.user.username
                subject = f'비단길에서 안내드립니다 – 주문번호 #{user_payment_object.order.id}'

                # Fallback text version for clients that don’t support HTML
                text_content = (
                    f'안녕하세요 {user_nickname}님 결제해주셔서 감사합니다,\n\n'
                    f'고객님의 상품 결제가 정상적으로 처리되었습니다.\n\n'
                    f'비단길에서 고객님의 상품을 대신 구매하여 배송을 준비할 예정입니다.\n'
                    f'상세한 주문 정보는 비단길 (웹사이트 -> 내 정보)에서 확인 가능합니다.'
                    '비단길을 이용해주셔서 감사합니다'
                )

                # Render HTML with your helper function
                html_content = render_delivery_payment_confirm_email(
                    user_nickname=user_nickname,
                )

                # Send the email
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send()

                send_sms(phone_num='9492997512', country_code='1', nickname=f"", content=f"배송비 결제 완료 #{user_payment_object.order.id}")
                send_sms(phone_num='01083413311', country_code='82', nickname=f"", content=f"배송비 결제 완료 #{user_payment_object.order.id}")

                send_sms(phone_num=usr_phone, country_code='1', nickname=user_nickname, content=f"[비단길 알림]\n고객님의 결제가 정상 처리되었습니다.\n 자세한 사항은 이메일을 확인해주세요.")

            elif payment_type == 'items':

                #find corresponding Payment object with its id
                user_payment_object = Payment.objects.filter(stripe_item_id = session_id)
                user_payment_object.item_fee_paid = True
                user_payment_object.save()
                user_nickname =  Profile.objects.get(user = user_payment_object.order.user)
                email = user_payment_object.order.user.username
                usr_phone = user_payment_object.order.phone

                #update the order step (to show clients)
                steps = InProgressOrderSteps.objects.get(order = user_payment_object.order)
                steps.item_fee_paid = True
                steps.save()
                subject = f'비단길에서 안내드립니다 – 주문번호 #{user_payment_object.order.id}'

                # Fallback text version for clients that don’t support HTML
                text_content = (
                    f'안녕하세요 {user_nickname}님 결제해주셔서 감사합니다,\n\n'
                    f'고객님의 결제가 정상적으로 처리되었습니다.\n\n'
                    f'고객님의 물건이 발송될 예정입니다. 곧 배송 정보와 함께 연락드리겠습니다! \n'
                    f'상세한 주문 정보는 비단길 (웹사이트 -> 내 정보)에서 확인 가능합니다.'
                    '비단길을 이용해주셔서 감사합니다'
                )

                # Render HTML with your helper function
                html_content = render_item_payment_confirm_email(
                    user_nickname=user_nickname,
                )

                # Send the email
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    to=[email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send()

                send_sms(phone_num='9492997512', country_code='1', nickname=f"", content=f"물건대금 결제 완료 #{user_payment_object.order.id}")
                send_sms(phone_num='01083413311', country_code='82', nickname=f"", content=f"물건대금 결제 완료 #{user_payment_object.order.id}")         
                send_sms(phone_num=usr_phone, country_code='1', nickname=user_nickname, content=f"[비단길 알림]\n고객님의 결제가 정상 처리되었습니다.\n 자세한 사항은 이메일을 확인해주세요.")
       
            print('payment successful!')
        except Exception as e:
            print(e)
    else:
        print('user payment not completed')




@api_view(["POST"])
def validate_address(request):
    print('inside validate address')
    data = request.data
    print('data',data)

    addressLine1 = data['addressLine1']
    addressLine2 = data['addressLine2']
    city = data['city']
    state = data['state']
    zip =data['zip']

    address_google = {'address':{
        'regionCode':'US',
        'addressLines':[addressLine1,addressLine2,city,state,zip]
    }}
    try:
        response = requests.post(
            url = f'https://addressvalidation.googleapis.com/v1:validateAddress?key={settings.GOOGLE_API}',
            headers = {"Content-Type": "application/json"},
            json = address_google

        )
        response.raise_for_status()

        result_data = response.json()
        print(json.dumps(result_data,indent=4))
        return JsonResponse({'result':result_data},status =200)
    except requests.exceptions.RequestException as e:
        return JsonResponse({'result':str(e)}, status=400)




@api_view(["POST"])
@permission_classes([IsAuthenticated])
def store_new_avatar(request):
    data = request.data
    print('data', data)

    personality= ','.join(data['personality'])
    species = data['species']


    prompt = f'''Draw a cute little chibi character. You must not include text in the image.
    species: {species}\n
    personality:{personality}\n 
    '''
    print('delay()')
    generate_avatar.delay(prompt, request.user.id)
    import time
    time.sleep(5)
    print('deplay() is completed')

    return JsonResponse({"msg": 'success'},status=200)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_others_community_profile(request):
    print('inside others comm profile')
    print("user:", request.user)
    print("auth:", request.auth)
    print("is_authenticated:", request.user.is_authenticated)
    try:
        target_nickname = request.GET.get("usr", '')
        target_profile = Profile.objects.get(nickname = target_nickname)

        data = CommunityInfoByOthersSerializer(target_profile).data
        
        return JsonResponse({"result": data}, status =200)
    except Profile.DoesNotExist:
        return JsonResponse({"err": "no such usr"}, status =400)

    except Exception as e:
        print("other info",e)
        return JsonResponse({"err":str(e)}, status = 500)

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def community_profile(request):
    print('inside get profile info')
    try:
        user = request.user
        print(user.username)
        usr_profile = Profile.objects.get(user=user)

        liked_users = UserLikes.objects.filter(liked_users = usr_profile)

        liked_users_nickname = [single.user.profile.nickname for single in liked_users]
        liked_users_avatars = [single.user.profile.avatar for single in liked_users]
        print("liked_users_avaars, ", liked_users_avatars[0])
        avatar_url = usr_profile.avatar
        address = usr_profile.community_address
        likes = usr_profile.likes
        nickname = usr_profile.nickname
        print('avatarurl...////',avatar_url)
        return JsonResponse({'avatar': avatar_url, 'nickname':nickname, 'address':address, 
                             'likes':likes, "liked_users_nickname": liked_users_nickname, 
                             "liked_users_avatars":liked_users_avatars}, status =200)

    except Exception as e:
        print('comm profile',e)
        return JsonResponse({'err':str(e)}, status = 400)



@api_view(["POST"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def post_new(request):
    print('post new in herre!!!')
    try:
        print('1')
        category = request.POST.get('category')
        print('2')
        title = request.POST.get('title')
        print('3')
        content = request.POST.get('content')
        print('title',title)

        uploaded_files = request.FILES #request.FILES is an dict of UploadedFile object
        print('4')
        urls=[]

        user = request.user
        post = Post.objects.create(user=user, title = title)

        if category == 'review':

            for key, obj in uploaded_files.items():#to extract raw byte to send to s3
                print('here!')
                file_byte = obj.read()
                content_type = obj.content_type
                print(content_type,'contenttype')
                extention = ''

                if content_type == 'image/png': # for browsers and servers
                    extention='png' # for humans and os to recognize the file type
                elif content_type == 'image/jpeg':
                    extention = 'jpeg'
                elif content_type=='image/jpg':
                    extention = 'jpg'
                else:
                    raise Exception('unsupported file format!')
                url = upload_png(file_byte, folder='posts/review', extention = extention, content_type=content_type)
                urls.append(url)

        if category == 'share':
            state = request.POST.get('state','')
            county = request.POST.get('county','')

            post.state = state
            post.county = county
            post.save()
            for key, obj in uploaded_files.items():#to extract raw byte to send to s3
                print('here!')
                file_byte = obj.read()
                content_type = obj.content_type
                print(content_type,'contenttype')
                extention = ''

                if content_type == 'image/png': # for browsers and servers
                    extention='png' # for humans and os to recognize the file type
                elif content_type == 'image/jpeg':
                    extention = 'jpeg'
                elif content_type=='image/jpg':
                    extention = 'jpg'
                else:
                    raise Exception('unsupported file format!')
                url = upload_png(file_byte, folder='posts/share', extention = extention, content_type=content_type)
                urls.append(url)
        if category == 'fun':
            if request.POST.get('funcategory') == 'food':
                restaurant_address = request.POST.get('restaurantaddress','')
                post.restaurant_address = restaurant_address
                post.subcategory = 'food'
                post.save()
                print('inside food!!')

            if request.POST.get('funcategory') == 'meetup':
                meetup_state = request.POST.get('state','')
                meetup_county = request.POST.get('county', '')
                meetup_type = request.POST.get('meetupcategory','')
                print('inside meetup!!!')
                print('meetup loc', meetup_county,meetup_state)

                post.state = meetup_state
                post.county = meetup_county
                post.meetuptype = meetup_type
                post.subcategory = 'meetup'
                post.save()

            if request.POST.get('funcategory') == 'chat':

                post.subcategory = 'chat'
                post.save()

            
            for key, obj in uploaded_files.items():#to extract raw byte to send to s3
                print('here!')
                file_byte = obj.read()
                content_type = obj.content_type
                print(content_type,'contenttype')
                extention = ''

                if content_type == 'image/png': # for browsers and servers
                    extention='png' # for humans and os to recognize the file type
                elif content_type == 'image/jpeg':
                    extention = 'jpeg'
                elif content_type=='image/jpg':
                    extention = 'jpg'
                else:
                    raise Exception('unsupported file format!')
                url = upload_png(file_byte, folder='posts/fun', extention = extention, content_type=content_type)
                urls.append(url)

        

        profile = Profile.objects.get(user=user)
        nickname =profile.nickname
        avatar = profile.avatar

        
        post.category = category
        post.content=content
        post.nickname = nickname
        post.avatar = avatar
        post.save()
        print('6')

        for url in urls:
            PostImage.objects.create(post = post, image_url = url )
            print('url is here:', url)

        return JsonResponse({'msg': 'new post created!'}, status =200)

    except Exception as e:
        return JsonResponse({'err':str(e)}, status = 400)

@api_view(["GET"])
def get_reviews(request):
    print('//////inside get reviews')
    try:
        qs = Post.objects.filter(category="review").order_by("-created_at")  # newest first
        #print('@@@@@test',qs[0].avatar. qs[0].category)
        images_urls = []
        print(f"len of qs{len(qs)}")

        

        page  = int(request.GET.get("page", 1))
        size  = int(request.GET.get("size", 10))
        start = (page - 1) * size
        end   = start + size

        total   = qs.count()
        total_pages = total//size
        slice_q = qs[start:end]

        data = ReviewSerializer(slice_q, many=True).data
        has_next = end < total
        

        return JsonResponse({
            "results":  data,
            "page":     page,
            "page_size": size,
            "has_next": has_next,
            "total_pages":    total_pages,
        }, status =200)
    except Exception as e:
        print('e',e)
    

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_my_posts (request):
    try:
        print('getmypost!!')
        user = request.user
        my_posts = Post.objects.filter(user=user)
        serializer = PostSerializer(my_posts, many=True, context={"request":request})
        return JsonResponse({'results':serializer.data}, status=200)
    except User.DoesNotExist:
        return JsonResponse({'resuls':"not_user"}, status=400)
    except Exception as e:
        return JsonResponse({'results':str(e)}, status = 500)


@api_view(['GET'])
def get_post_list(request):
    page  = int(request.GET.get("page", 1))
    size  = int(request.GET.get("size", 10))
    filter = str(request.GET.get("filter", 'all'))

    print(f"filter: {filter}")

    start = (page - 1) * size
    end   = start + size

    if filter == '':
        posts = Post.objects.exclude(category = 'review').order_by("-created_at")
        total = posts.count()
        total_pages = total//size
        has_next = end < total
        
        slice_posts = posts[start:end]
    else:    
        if filter =='share':
            posts = Post.objects.exclude(category = 'review').filter(category = 'share').order_by("-created_at")
        else:
            posts = Post.objects.exclude(category = 'review').filter(category = 'fun', subcategory = filter).order_by("-created_at")
    
        
        total = posts.count()
        total_pages = total//size
        has_next = end < total
        
        slice_posts = posts[start:end]

    
    serializer = PostSerializer(slice_posts, many=True).data
    return JsonResponse({
            "results":  serializer,
            "page":     page,
            "page_size": size,
            "has_next": has_next,
            "total_pages": total_pages,
        }, status =200)

@api_view(['GET'])
def get_post_detail(request, slug):
   
    print('got slug!!!', slug)
    try:
        post = Post.objects.get(slug=slug)
        did_like=False

        if request.user.is_authenticated:
            did_like = post.post_likes.filter(liked_users = request.user.profile).exists()

        print('category slug',post.category)
        print('rest add', post.restaurant_address)
        #print('target post retrieved', 'len of post:',len(post))
    except Post.DoesNotExist:
        return JsonResponse({"detail": "Not found."}, status=400)

    serializer = PostSerializer(post, context={"request":request})
    return JsonResponse({'results':serializer.data, 'did_like':did_like}, status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def validate_nickname(request):
    try:
        data = request.data
        candidate_nickname = data.get("nickname")
        print('candidatenick', candidate_nickname)

        obj = Profile.objects.get(nickname = candidate_nickname)
        print('nickname TAKEN')

        return JsonResponse({'result': False}, status = 200)
    except Profile.DoesNotExist:
        print('nickname USABLE')
        return JsonResponse({'result': True}, status = 200)
    except Exception as e:
        return JsonResponse({"err":str(e)}, status=400)
    

@api_view(["POST"])    
@permission_classes([IsAuthenticated])
def update_community_profile(request):
    user = request.user
    data = request.data
    new_nickname = data.get('nickname')
    print(new_nickname, 'newnickname')
    new_community_address = data['address']
    profile = Profile.objects.get(user=user)
    profile.nickname = new_nickname
    profile.community_address = new_community_address
    profile.save()
    return JsonResponse({'results':'updated'},status=200)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def like_post(request):
    print('likepost___')
    try:
        user = request.user
        data = request.data
        slug = data.get('slug', '')

        post = Post.objects.get(slug=slug)
        print('1')

        # Check if the user has already liked the post
        existing_like = PostLikes.objects.filter(post=post, liked_users=user.profile).first()
        print('2')
        if existing_like:
            # User already liked → unlike
            print('already liked, so will unlike')
            existing_like.delete()
            print('3')
            return JsonResponse({'result': 'unliked'}, status=200)
        else:
            # Not liked yet → like it
            print('not liked yet, will like it')
            PostLikes.objects.create(post=post, liked_users=user.profile)
            return JsonResponse({'result': 'liked'}, status=200)
        
    except Post.DoesNotExist:
        return JsonResponse({'err': 'Post not found'}, status=400)
    except Exception as e:
        print('4')
        return JsonResponse({'err': str(e)}, status=500)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def like_profile(request):
    print('likeProfile')
    try:
        user = request.user
        data = request.data
        nickname = data.get('nickname', '')
        profile = Profile.objects.get(nickname = nickname)


        # Check if the user has already liked the profile
        existing_like = UserLikes.objects.filter(user=user, liked_users=profile).first()
        print('2')
        if existing_like:
            # User already liked → unlike
            print('already liked, so will unlike')
            existing_like.delete()
            profile.likes -=1
            profile.save()
            print('3')
            return JsonResponse({'result': 'unliked'}, status=200)
        else:
            # Not liked yet → like it
            print('not liked yet, will like it')
            UserLikes.objects.create(user=user, liked_users=profile)
            profile.likes +=1
            profile.save()
            return JsonResponse({'result': 'liked'}, status=200)
        
    except Post.DoesNotExist:
        return JsonResponse({'err': 'User not found'}, status=400)
    except Exception as e:
        print('4')
        print(e)
        return JsonResponse({'err': str(e)}, status=500)
    
@api_view(["POST"])
@permission_classes([IsAuthenticated])
def write_comment(request):
    try:
        print('add commnet!!!')
        slug  = request.GET.get("slug", '')
        user = request.user
        data = request.data
        content = data.get('content', '')
        reply_to = data.get('parent_id', None)
        target_post = Post.objects.get(slug=slug)



        if reply_to == None:
            PostComment.objects.create(user = user, post=target_post, content = content, reply_to=None)
        else:
            reply_to_post = PostComment.objects.get(id=reply_to)
            PostComment.objects.create(user = user, post=target_post, content = content, reply_to=reply_to_post)
        return JsonResponse({"result":'created'}, status=200)
    except Post.DoesNotExist:
        return JsonResponse({"err":'profile dne'}, status=400)
    except Exception as e:
        print('write comment err', e)
        return JsonResponse({"err":str(e)}, status=500)


@api_view(["GET"])
def get_comments(request):
    print("GET COMMENTS")
    try:

        # data = request.data
        # slug = data.get('slug', '')
        slug = request.GET.get("slug",'')
        print('slug = ',slug)
        target_post = Post.objects.get(slug=slug)
        comments = (
        PostComment.objects
        .filter(post=target_post)
        .select_related("user")           # user.username in 1 query
        .prefetch_related("replies")      # to fetch all the children replies in one extra query (instead of doing comment.replies)
        .order_by("-created_at")
        )
        comment_lookup = {c.id: c for c in comments}

        roots = []
        for c in comments:
            c.depth = 1

        for c in comments:
            if c.reply_to_id:
                parent = comment_lookup[c.reply_to_id]
                c.depth = parent.depth + 1   
                # access .replies cache without DB hit
                parent.replies_cache = getattr(parent, "replies_cache", [])
                parent.replies_cache.append(c)
            else:
                roots.append(c)

        # Serializer sees replies via .replies_cache fallback
        data = CommentTreeSerializer(roots, many=True).data
        print("comment data: ",data)
        return JsonResponse({"results" : data}, status = 200)
    except Post.DoesNotExist:
        return JsonResponse({"err":'profile dne'}, status=400)
    except Exception as e:
        print('err/////$$$', e)
        return JsonResponse({"err":str(e)}, status=500)
    

@api_view(["POST"])
@permission_classes([IsAuthenticated])
def like_comment(request):
    try:
        data= request.data
        user = request.user
        target_commnet_id = data.get("id", "")
        target_comment = PostComment.objects.get(id=target_commnet_id)

        existing_like = CommentLikes.objects.filter(comment = target_comment, liked_users = user.profile).first()

        if existing_like:
            existing_like.delete()
            target_comment.likes -=1
            target_comment.save()
            return JsonResponse({"msg":"unliked"},status=200)
        else:
            CommentLikes.objects.create(comment = target_comment, liked_users = user.profile)  
            target_comment.likes +=1
            target_comment.save()
            return JsonResponse({"msg":"liked"},status=200)
        
    except Exception as e :
        print(f"err occured! {e}")
        return JsonResponse({"err": str(e)},status=500)

@api_view(["GET"])
def get_summarize_reliable(request):
    print('get summary')
    try:
        reviews = Post.objects.filter(category = "review")

        num_usrs = User.objects.count()
        num_review = reviews.count()

        JsonResponse({'results':{'reviews': num_review, "usrs":num_usrs}}, status = 200)
    except Exception as e:
        print(e)
        JsonResponse({"err":str(e)},status=500)
  