from django.contrib import admin
from .models import Booking, Payment, TransactionLog

# Register your models here.
admin.site.register(Booking)
admin.site.register(Payment)
admin.site.register(TransactionLog)