from django.db import models
from django.conf import settings
from django.utils import timezone
from user.models import EngagementLog 

class Booking(models.Model):
    SERVICE_CHOICES = [
        ('ROOM', 'Room'),
        ('SPA', 'Spa'),
        ('RESTAURANT', 'Restaurant'),
        ('EVENT', 'Event'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONFIRMED', 'Confirmed'),
        ('CANCELLED', 'Cancelled'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    service_type = models.CharField(max_length=20, choices=SERVICE_CHOICES)
    service_id = models.CharField(max_length=100, blank=True, null=True)  # Optional for linking services
    date = models.DateField()
    time = models.TimeField()
    guests = models.PositiveIntegerField(default=1)
    pickup_required = models.BooleanField(default=False)
    pickup_location = models.CharField(max_length=255, blank=True, null=True)
    discount_applied = models.BooleanField(default=False)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.service_type} booking by {self.user.email} on {self.date}"



class Payment(models.Model):
    PAYMENT_METHODS = [
        ('CHAPA', 'Chapa'),
        ('POS', 'POS'),
        ('CASH', 'Cash'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SUCCESS', 'Success'),
        ('FAILED', 'Failed'),
    ]

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    paid_at = models.DateTimeField(null=True, blank=True)
    tx_ref = models.CharField(max_length=100, unique=True, null=False)  # Unique tx_ref per user

    class Meta:
        unique_together = ('tx_ref', 'booking')  

    def __str__(self):
        return f"Payment for Booking {self.booking.id} - {self.status}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Auto-log engagement if payment is successful
        if self.status == 'SUCCESS' and self.paid_at and not EngagementLog.objects.filter(
            user=self.booking.user,
            action='BOOKING_COMPLETED',
            metadata__contains={'booking_id': self.booking.id}
        ).exists():
            EngagementLog.objects.create(
                user=self.booking.user,
                action='BOOKING_COMPLETED',
                metadata={'booking_id': self.booking.id, 'service_type': self.booking.service_type}
            )


class TransactionLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transactions')
    event = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(blank=True, null=True)

    def __str__(self):
        return f"Transaction by {self.user.email} - {self.event} - {self.amount}"
