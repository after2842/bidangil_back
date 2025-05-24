from django.urls import path
from .views import  login_view, signup_view, send_verification_code, verify_code,create_inprogress_order, get_csrf_token,get_profile_info,logout_view,stripe_webhook_view,validate_address, store_new_avatar, community_profile, post_new, get_reviews, get_post_list,get_post_detail, validate_nickname, update_community_profile, get_my_posts, like_post, get_others_community_profile, like_profile, write_comment,get_comments, like_comment,get_summarize_reliable,session_ping

urlpatterns = [
    path("api/csrf_token/", get_csrf_token),
    path('api/login/',login_view),

    path('api/logout/',logout_view),
    path('api/session_ping/',session_ping),
    path('api/sign_up/',signup_view),
    path('api/send_code/',send_verification_code),
    path('api/verify_code/',verify_code),
    path('api/submit_order/',create_inprogress_order),
    path('api/profile_info/', get_profile_info),    
    path('api/validate_address/', validate_address),
    path('api/community_profile/', community_profile),
    path('api/community_profile/like/', like_profile),
    path('api/others_profile/', get_others_community_profile),
    path('api/summarize_reliable/', get_summarize_reliable),
    path('webhook/stripe_payment', stripe_webhook_view),
    path('api/create_avatar/', store_new_avatar),
    path('api/community/post/', post_new),
    path('api/get_reviews/', get_reviews),
    path("api/posts/", get_post_list),               
    path("api/posts/get_my_posts/", get_my_posts),  
    path("api/post/write_comments/", write_comment)  ,
    path("api/post/like_comment/", like_comment),
    path("api/post/get_comments/",get_comments),
    path("api/post/like/", like_post),  
    path("api/post/<slug:slug>/", get_post_detail), 
    path("api/validate_nickname/", validate_nickname),
    path("api/community/update_profile/", update_community_profile),

   

]
