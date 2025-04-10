from django.contrib import admin
from .models import (
    InProgressOrder, InProgressOrderItem,
    PastOrder, PastOrderItem,
    Payment, Delivery,
    Profile, EmailVerification, InProgressOrderSteps
)
from django.db.models import Sum


class InProgressOrderItemInline(admin.TabularInline):  # or admin.StackedInline
    model = InProgressOrderItem
    extra = 0  # Don't show extra blank rows
    fields = ('url', 'description', 'price')  # only show these fields
    readonly_fields = ('url', 'description')  # optional if you want read-only

class InProgressPaymentInline(admin.TabularInline):  # or admin.StackedInline
    model = Payment
    extra = 0  # Don't show extra blank rows
    fields = ('item_price', 'delivery_fee','total_fee', 'is_paid','invoice_created_at')  # only show these fields
    readonly_fields = ('item_price', 'total_fee', 'invoice_created_at','is_paid')  # optional if you want read-only

class InProgressDeliveryInline(admin.TabularInline):  # or admin.StackedInline
    model = Delivery
    extra = 1  
    fields = ('delivery_start_at', 'delivered_at','courier', 'tracking_number')  # only show these fields
    readonly_fields = ('delivery_start_at', 'delivered_at')  # optional if you want read-only

class InProgressOrderStepsInline(admin.TabularInline):
    model = InProgressOrderSteps
    extra = 0
    fields = ('request_received', 'item_purchased','item_received','payment_received','delivery_started')
    readonly_fields = ('request_received', 'item_purchased','item_received','payment_received','delivery_started')

@admin.register(InProgressOrder)
class InProgressOrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'order_created_at', 'exchange_rate')
    readonly_fields = ('user', 'exchange_rate','address') 
    inlines = [InProgressOrderItemInline, InProgressPaymentInline, InProgressDeliveryInline,InProgressOrderStepsInline]

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
                super().save_formset(request, form, formset, change)
                return

            # Otherwise, do summation
            inprogress_order = form.instance
            total_item_price = inprogress_order.items.aggregate(total=Sum('price'))['total'] or 0

            # You can do create if you want only 1 Payment object:
            payment= Payment.objects.create(order=inprogress_order)
            payment.item_price = total_item_price
            payment.save()

        # Finally, call super so Django can finish up
        super().save_formset(request, form, formset, change)

# admin.site.register(InProgressOrderItem)
admin.site.register(PastOrder)
admin.site.register(PastOrderItem)
admin.site.register(Payment)
admin.site.register(Delivery)

admin.site.register(Profile)
admin.site.register(EmailVerification)

# when admin changes InProgressOrderItem's value, and hit save. django calls'
# 'InProgressOrderAdmin.save_formset(
#     request=request, 
#     form=the_parent_form,
#     formset=the_inprogressorderitem_formset,
#     change=True
# )

# However, as we want to catch the event that triggers upon ALL items' value is updated. (signals's post save will catch only item#1's change <=> listens only a single form)