from django.contrib import admin
from django.urls import path, include
from .views import  login_view, signup_view, send_verification_code, verify_code,create_inprogress_order, get_csrf_token,get_profile_info,logout_view,stripe_webhook_view

urlpatterns = [
    path("api/csrf_token/", get_csrf_token),
    path('api/login/',login_view),
    path('api/logout/',logout_view),
    path('api/sign_up/',signup_view),
    path('api/send_code/',send_verification_code),
    path('api/verify_code/',verify_code),
    path('api/submit_order/',create_inprogress_order),
    path('api/profile_info/', get_profile_info),
    path('webhook/stripe_payment', stripe_webhook_view)
]
