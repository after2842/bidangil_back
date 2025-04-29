from django.contrib import admin
from django.urls import path, include
from .views import  login_view, signup_view, send_verification_code, verify_code,create_inprogress_order, get_csrf_token,get_profile_info,logout_view,stripe_webhook_view,validate_address, store_new_avatar, community_profile, post_new, get_reviews

urlpatterns = [
    path("api/csrf_token/", get_csrf_token),
    path('api/login/',login_view),
    path('api/logout/',logout_view),
    path('api/sign_up/',signup_view),
    path('api/send_code/',send_verification_code),
    path('api/verify_code/',verify_code),
    path('api/submit_order/',create_inprogress_order),
    path('api/profile_info/', get_profile_info),    
    path('api/validate_address/', validate_address),
    path('api/community_profile/', community_profile),
    path('webhook/stripe_payment', stripe_webhook_view),
    path('api/create_avatar/', store_new_avatar),
    path('api/community/post/', post_new),
    path('api/get_reviews/', get_reviews)

]
# from django.urls import resolve
# print("★ loaded urls, get_reviews resolves to:",
#       resolve("/api/get_reviews/"))