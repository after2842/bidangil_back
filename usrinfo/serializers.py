# serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    InProgressOrder,
    InProgressOrderItem,
    PastOrder,
    PastOrderItem,
    Payment,
    Delivery,
    Profile,
    EmailVerification,
    PostComment
)

# ------------------------------------------
# 1. InProgressOrder & InProgressOrderItem
# ------------------------------------------

class InProgressOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = InProgressOrderItem
        fields = "__all__"


class InProgressOrderSerializer(serializers.ModelSerializer):
    # If you want to see the items nested under the order:
    items = InProgressOrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = InProgressOrder
        fields = "__all__"
        # or list only the fields you want:
        # fields = ("id", "user", "order_created_at", "address", "items", "exchange_rate")

# ------------------------------------------
# 2. PastOrder & PastOrderItem
# ------------------------------------------

class PastOrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PastOrderItem
        fields = "__all__"


class PastOrderSerializer(serializers.ModelSerializer):
    # Optionally show nested items
    past_items = PastOrderItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = PastOrder
        fields = "__all__"

# ------------------------------------------
# 3. Payment
# ------------------------------------------

class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = "__all__"
        # If you want to hide certain fields or make them read-only, consider:
        # read_only_fields = ("is_paid", )

# ------------------------------------------
# 4. Delivery
# ------------------------------------------

class DeliverySerializer(serializers.ModelSerializer):
    class Meta:
        model = Delivery
        fields = "__all__"

# ------------------------------------------
# 5. Profile
# ------------------------------------------

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = "__all__"

# ------------------------------------------
# 6. Email Verification
# ------------------------------------------

class EmailVerificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmailVerification
        fields = "__all__"

# ------------------------------------------
# 7. (Optional) User Serializer
# ------------------------------------------
# If you need to serialize Django's built-in User.

class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "profile"]



from .models import Post, PostImage, PostLikes










class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model  = PostImage
        fields = ["image_url"]


class ReviewSerializer(serializers.ModelSerializer):
    images = PostImageSerializer(source="post_images", many=True)  #nested inline(child) model
    avatar = serializers.SerializerMethodField()
    user_nickname = serializers.SerializerMethodField()

    def get_avatar(self, obj):
        try:
            profile = obj.user.profile
            return profile.avatar
        except Profile.DoesNotExist:
            return None  
        
    def get_user_nickname(self, obj):
        try:
            profile = obj.user.profile
            return profile.nickname
        except Profile.DoesNotExist:
            return None   

    class Meta:
        model  = Post
        fields = ["id", "user", "title", "content", "created_at", "images", 'avatar', 'user_nickname']

class PostSerializer(serializers.ModelSerializer):
    images = PostImageSerializer(source = 'post_images', many=True)
    avatar = serializers.SerializerMethodField()
    user_community_address = serializers.SerializerMethodField()
    user_nickname = serializers.SerializerMethodField()
    post_like = serializers.SerializerMethodField()

    class Meta:
        
        model  = Post
        fields = ["id", "user", "title", "content", "created_at", "images", 'avatar', 'user_nickname', 'slug', 'subcategory', 'state', 'county', 'meetuptype' ,'category','user_community_address', 'restaurant_address','post_like']

    def get_avatar(self, obj):
        try:
            profile = obj.user.profile
            return profile.avatar
        except Profile.DoesNotExist:
            return None    
        
    def get_user_community_address(self, obj):
        try:
            profile = obj.user.profile
            return profile.community_address
        except Profile.DoesNotExist:
            return None   
        
    def get_user_nickname(self, obj):
        try:
            profile = obj.user.profile
            return profile.nickname
        except Profile.DoesNotExist:
            return None   
        
    def get_post_like(self, obj):
        request = self.context.get("request", None)
        print('inside serializer,')
        try:
            if request and request.user.is_authenticated:
                print('inside serializer, user_auth ok')
                liked_profiles = obj.post_likes.all()
                liked_avatars = [single.liked_users.avatar for single in liked_profiles]
                liked_nickname = [single.liked_users.nickname for single in liked_profiles]
                payload = {"liked_avatars": liked_avatars, "liked_nickname": liked_nickname}
                print("liked_avatar:", liked_avatars)
                return payload
            return False
        except Exception as e:
            print("err" , e)

            return False
    
class CommunityInfoByOthersSerializer(serializers.ModelSerializer):
    liked_posts = serializers.SerializerMethodField()
    target_posts = serializers.SerializerMethodField()

    def get_liked_posts(self, obj):
        try:
            print('retrieving liked posts')
            postlikes = obj.post_likes_users.all()
            posts = [single.post for single in postlikes]
            data = PostSerializer(posts, many=True).data
            return data
            
        except PostLikes.DoesNotExist:
            return None
        except Exception as e:
            print(e)
            return None
        

    def get_target_posts(self, obj):
        try:
            print("retrieving the posts")
            target_user = obj.user
            posts =  target_user.posts.all().order_by("-created_at")
            
            data = PostSerializer(posts, many=True).data
            return data
        except Post.DoesNotExist:
            return None
        except Exception as e:
            print(e)
            return None
        

    class Meta:
        model = Profile
        fields = ["nickname","community_address", "avatar", "liked_posts", "target_posts", "likes"]


class CommentTreeSerializer(serializers.ModelSerializer):
    # -------- extra, friendly fields --------
    user_name = serializers.CharField(source="user.profile.nickname", read_only=True)
    avatar    = serializers.CharField(source="user.profile.avatar",   read_only=True)
    depth = serializers.IntegerField() 

    # -------- recursion entry point --------
    children  = serializers.SerializerMethodField()

    class Meta:
        model  = PostComment
        # keep it lightweight: no giant user/post objects in every node
        fields = (
            "id",
            "user_name",
            "avatar",
            "content",
            "created_at",
            "likes",
            "children",
            "depth",
        )
        read_only_fields = fields   # comments are not created through this serializer

    # ---------------------------------------
    # Recursively pull child comments
    # ---------------------------------------
    def get_children(self, obj):
        """
        Return a list (possibly empty) of nested CommentTreeSerializer data
        for all direct replies to *obj*, ordered newest → oldest.

        Uses:
        1) obj.replies_cache    (if the view attached it)
        2) obj.replies.all()    (if .prefetch_related("replies") ran)
        3) executes a fresh query only if neither of the above exist.
        """

        # 1) Fast path: in-memory cache attached by the view -> we stored this in our memory(python dict) from views
        cached = getattr(obj, "replies_cache", None)
        if cached is not None:
            children_qs = sorted(cached, key=lambda c: c.created_at, reverse=True)

    ##### in case it has a problem with storing in memory -> more costs, but good have backups
        # # 2) Prefetched queryset (no SQL)
        # elif obj.replies._prefetch_done:
        #     children_qs = obj.replies.all().order_by("created_at")

        # 3) Fallback: hits DB (only if you forgot to prefetch)
        else:
            children_qs = obj.replies.order_by("-created_at")

        # Recursively serialise each child
        return CommentTreeSerializer(children_qs, many=True, context=self.context).data

