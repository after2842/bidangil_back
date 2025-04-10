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










# [
#     {
#     'address': 'some address',
#      'created_at': 'Whenever it was created',
#      'exchange_rate': 'somenumber',
#      'items':[{'url':'someurl', 'description': 'some description'},
#               {'url':'someurl', 'description': 'some description'},
#               {'url':'someurl', 'description': 'some description'}
#               ],
#      'Payment':{
#         'item_price': 'someprice',
#         'Delivery_price': 'some delivery price',
#         'total_price':'some total price',
#         'ispaid':'true or false',
#         'invoice_created':'when user paid through stripe zelle or whatever',

#      }
#      'Delivery':{
#          'delivery_start_at':'some day ',
#          'tracking_number':'some number tracking',
#          'courier':'courier',
#      }
#      },
#          {
#     'address': 'some address',
#      'created_at': 'Whenever it was created',
#      'exchange_rate': 'somenumber',
#     'items':[{'url':'someurl', 'description': 'some description'},
#         {'url':'someurl', 'description': 'some description'},
#         {'url':'someurl', 'description': 'some description'}
#         ],
#      'Payment':{
#         'item_price': 'someprice',
#         'Delivery_price': 'some delivery price',
#         'total_price':'some total price',
#         'ispaid':'true or false',
#         'invoice_created':'when user paid through stripe zelle or whatever',

#      }
#      'Delivery':{
#          'delivery_start_at':'some day ',
#          'tracking_number':'some number tracking',
#          'courier':'courier',
#      }
#      },
     
     
# ]