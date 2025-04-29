from django.contrib import admin
from .models import (
    InProgressOrder, InProgressOrderItem,
    PastOrder, PastOrderItem,
    Payment, Delivery,
    Profile, EmailVerification, InProgressOrderSteps, Post,PostImage
)
from django.db.models import Sum
from django.utils.html import format_html

class InProgressOrderItemInline(admin.TabularInline):  # or admin.StackedInline
    model = InProgressOrderItem
    extra = 0  # Don't show extra blank rows
    fields = ('url_truncated', 'description', 'price', 'gpt_product_name')  # only show these fields
    readonly_fields = ('url_truncated', 'description')  # optional if you want read-only

    def url_truncated(self, obj):
        if obj.url:
            return format_html(
                '''
                <a href="{0}" target="_blank" style="color:blue; text-decoration:underline; onmouseover="this.style.color='gray'" onmouseout="this.style.color='blue'">
                    {1}... (열기)
                </a>
                ''',
                obj.url,
                obj.url[:30]
            )

        return "-"

class InProgressPaymentInline(admin.TabularInline):  # or admin.StackedInline
    model = Payment
    extra = 1  # Don't show extra blank rows∂
    fields = ('item_price', 'delivery_fee', 'total_fee',
        'stripe_item_url_c', 'stripe_delivery_url_c',
        'stripe_item_id_c', 'stripe_delivery_id_c',
        'item_is_paid', 'delivery_is_paid',
        'item_invoice_created_at', 'delivery_invoice_created_at')  # only show these fields
    readonly_fields = ('item_price', 'total_fee',
        'stripe_item_url_c', 'stripe_delivery_url_c',
        'stripe_item_id_c', 'stripe_delivery_id_c',
        'item_is_paid', 'delivery_is_paid',
        'item_invoice_created_at', 'delivery_invoice_created_at') 
        
    def stripe_item_url_c(self, obj):
        if obj.stripe_item_url:
            return format_html(
                '''
                <span style="cursor:pointer; color:blue;" onclick="navigator.clipboard.writeText('{}')">
                    {}... (복사)
                </span>
                ''',
                obj.stripe_item_url,
                obj.stripe_item_url[:30]
            )
        return "-"

    def stripe_delivery_url_c(self, obj):
        if obj.stripe_delivery_url:
            return format_html(
                '''
                <span style="cursor:pointer; color:blue;" onclick="navigator.clipboard.writeText('{}')">
                    {}... (복사)
                </span>
                ''',
                obj.stripe_delivery_url,
                obj.stripe_delivery_url[:30]
            )
        return "-"

    def stripe_item_id_c(self, obj):
        if obj.stripe_item_id:
            return format_html(
                '''
                <span style="cursor:pointer; color:blue;" onclick="navigator.clipboard.writeText('{}')">
                    {}... (복사)
                </span>
                ''',
                obj.stripe_item_id,
                obj.stripe_item_id[:10]
            )
        return "-"

    def stripe_delivery_id_c(self, obj):
        if obj.stripe_delivery_id:
            return format_html(
                '''
                <span style="cursor:pointer; color:blue;" onclick="navigator.clipboard.writeText('{}')">
                    {}... (복사)
                </span>
                ''',
                obj.stripe_delivery_id,
                obj.stripe_delivery_id[:10]
            )
        return "-"
    
    

 # optional if you want read-only

class InProgressDeliveryInline(admin.TabularInline):  # or admin.StackedInline
    model = Delivery
    extra = 1  
    fields = ('delivery_start_at', 'delivered_at','courier', 'tracking_number')  # only show these fields
    readonly_fields = ('delivery_start_at', 'delivered_at')  # optional if you want read-only

class InProgressOrderStepsInline(admin.TabularInline):
    model = InProgressOrderSteps
    extra = 0
    fields = ('request_received', 'item_fee_paid','item_purchased','delivery_ready','delivery_fee_paid','delivery_started','delivery_completed')
    readonly_fields = ('request_received', 'item_fee_paid','delivery_ready','delivery_fee_paid','delivery_started','delivery_completed')

class PostImagesInline(admin.TabularInline):
    model = PostImage
    extra = 0
    fields = ['image_url']
    readonly_fields = ['image_url']

@admin.register(InProgressOrder)
class InProgressOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order_created_at', 'exchange_rate')
    readonly_fields = ('user', 'exchange_rate','address') 
    inlines = [InProgressOrderItemInline, InProgressPaymentInline, InProgressDeliveryInline,InProgressOrderStepsInline]
    # The reason why I override the save_formet,
    # I want to create a new Payment Object, when EVERY InProgressOrderItem are saved.
    # However, the receiver in signals.py won't wait untill the iteration of InProgressOrderItem.save() is finished'
    # So, I had to modify save_format:
    # First, when django call save_formset for formset.model == InProgressOrderItem, I want it to save every instances
    # Then, I will create a Payment object after all instances are saved for formset.model == InProgressOrderItem
    def save_formset(self, request, form, formset, change):
        """
        This method is called after all inlines have been validated & saved.
        """
        # collects all changes withoug auto saving to DB
        instances = formset.save(commit=False)  
        #instances are the number of objects that are inlined in InProgressOrder. 
        # Unlike signals, we can listen to the inline objectcs of a certain InProgressOrder and control each objects
        # (if we have 4 InProgressOrderItem inlined in a InProgressOrder, the save_format for InProgressOrderItemInline will have four instances)

        # Save each changed inline
        for obj in instances:
            # If you want to do custom logic per item, do it here
            obj.save()

        # If some items are deleted, handle them:
        for deleted_obj in formset.deleted_objects:
            deleted_obj.delete()

        


        # Only do summation if it's the InProgressOrderItem inline
        if formset.model == InProgressOrderItem:
            # If NO objects changed or were added, skip summation
            if not instances and not formset.deleted_objects:
                # means no real changes to InProgressOrderItem
                super().save_formset(request, form, formset, change) #even though I've called obj.save() above. django still expects super()
                return

            # Otherwise, do summation
            inprogress_order = form.instance
            # total_item_price = inprogress_order.items.aggregate(total=Sum('price'))['total'] or 0

            # Create the Payment object ONCE: after all InProgressOrderItems.price are updated
            Payment.objects.create(order=inprogress_order)
            #payment.item_price = total_item_price
            # payment.save()

        # Finally, call super so Django can finish up
        super().save_formset(request, form, formset, change)

# admin.site.register(InProgressOrderItem)
admin.site.register(PastOrder)
admin.site.register(PostImage)
# admin.site.register(Payment)
# admin.site.register(Delivery)

admin.site.register(Profile)
# admin.site.register(Post)

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'title', 'content','avatar')
    readonly_fields = ('user', 'category', 'title', 'content') 
    inlines = [PostImagesInline]

# when admin changes InProgressOrderItem's value, and hit save. django calls'
# 'InProgressOrderAdmin.save_formset(
#     request=request, 
#     form=the_parent_form,
#     formset=the_inprogressorderitem_formset,
#     change=True
# )

# However, as we want to catch the event that triggers upon ALL items' value is updated. (signals's post save will catch only item#1's change <=> listens only a single form)