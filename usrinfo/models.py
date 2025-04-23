# models.py
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from datetime import timedelta
from datetime import datetime

class InProgressOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='inprogress_orders')
    order_created_at = models.DateTimeField(auto_now_add=True)
    address = models.TextField()
    exchange_rate = models.DecimalField(max_digits=10, decimal_places=2, default=None)
    name = models.CharField(max_length=20, default='', null=True)
    phone = models.CharField(max_length=12, default='', null=True)


    # any other overall fields for the entire order

    def __str__(self):
        return f"InProgressOrder #{self.id} for {self.user.username}"

class InProgressOrderItem(models.Model):
    order = models.ForeignKey(
        InProgressOrder, 
        on_delete=models.CASCADE, 
        related_name='items'
    )
    url = models.URLField()
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, blank=True)
    gpt_product_name = models.CharField(max_length=50,null=True, blank=True)


    def __str__(self):
        return f"Item in Order #{self.order.id}: {self.url}"

class InProgressOrderSteps(models.Model):
    order = models.OneToOneField(
        InProgressOrder, 
        on_delete=models.CASCADE, 
        related_name='steps'
    )
    request_received = models.BooleanField(default=False)

    item_fee_paid = models.BooleanField(default=False)
    item_purchased = models.BooleanField(default=False) #manually....

    delivery_ready = models.BooleanField(default=False) 
    delivery_fee_paid = models.BooleanField(default=False)

    delivery_started = models.BooleanField(default=False) # when tracking number in hand
    delivery_completed= models.BooleanField(default=False) # when the items are at customer's front door


class PastOrder(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='past_orders')

    items_price = models.DecimalField(max_digits=10, decimal_places=2, default=None)
    delivery_price = models.DecimalField(max_digits=10, decimal_places=2, default=None)
    
    is_paid = models.BooleanField(default=False)

    tracking_number = models.CharField(max_length=12, blank=True, default=None)

    # Timestamps
    order_created_at = models.DateTimeField()
    delivery_started_at = models.DateTimeField(null=True, blank=True)
    delivery_ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"PastOrder #{self.id} for {self.user.username}"

class PastOrderItem(models.Model):
    order = models.ForeignKey(
        PastOrder,
        on_delete=models.CASCADE,
        related_name='past_items'
    )
    url = models.URLField()
    description = models.TextField()
    price = models.DecimalField(max_digits=10,decimal_places=2,default=0, blank=True )

    def __str__(self):
        return f"PastOrderItem #{self.order.id}: {self.url}"
    



class Payment(models.Model):
    order = models.OneToOneField(
        InProgressOrder, 
        on_delete=models.CASCADE, 

        related_name='payment',
        null=True,  # Allow database to store NULL
        blank=True  # Allow forms to leave it blank
    )

    item_price = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)
    delivery_fee = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)



    total_fee = models.DecimalField(max_digits=10, decimal_places=2,null=True,blank=True)


    stripe_item_url = models.URLField(null=True, blank=True)
    stripe_item_id = models.CharField(max_length=200,null=True, blank=True)

    stripe_delivery_url = models.URLField(null=True, blank=True)
    stripe_delivery_id = models.CharField(max_length=200,null=True, blank=True)

    item_is_paid = models.BooleanField(default=False)
    delivery_is_paid= models.BooleanField(default=False)

    item_invoice_created_at = models.DateTimeField(null=True, blank=True)
    delivery_invoice_created_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment: {self.order.user.username} "

class Delivery(models.Model):
    COURIER_CHOICES = [
        ('fedex', 'FedEx'),
        ('dhl', 'DHL'),
        ('ups', 'UPS'),
        ('usps', 'USPS'),
        ('ems', 'EMS'),
    ]
    order = models.OneToOneField(
        InProgressOrder,
        on_delete=models.CASCADE,
        related_name='delivery'
    )
    delivery_start_at = models.DateTimeField(auto_now_add=True)
    delivered_at = models.DateTimeField(null=True, default=None)
    courier = models.CharField(max_length=10, choices = COURIER_CHOICES, default=None, blank=True)
    tracking_number = models.CharField(max_length=50, blank=True, default=None)

class DeliveryStatus(models.Model):
    delivery = models.ForeignKey(Delivery, on_delete=models.CASCADE, related_name = 'tracking')
    status = models.CharField(max_length=20, blank=True, default=None)
    timestamp = models.DateTimeField(auto_now=True)


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    nickname = models.CharField(max_length=40, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)
    signup_date = models.DateTimeField(auto_now_add=True)
    last_address = models.TextField(max_length=255, blank = True)

    def __str__(self):
        return f"Name:{self.nickname} || Email:{self.user.username}"
    
    
class EmailVerification(models.Model):
    email = models.EmailField()
    code = models.IntegerField()
    isVerified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add = True)
    
    def is_expired(self):
        return self.created_at < (timezone.now() - timedelta(minutes=10))
    
class Foo(models.Model):
    name = models.CharField(max_length=50)