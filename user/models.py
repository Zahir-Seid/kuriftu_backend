from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from django.utils import timezone
import uuid


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('Email must be provided')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.referral_code = str(uuid.uuid4())[:8]  # Generate unique referral code
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(email, password, **extra_fields)


class Tier(models.Model):
    name = models.CharField(max_length=50, unique=True)
    min_points = models.IntegerField()
    perks = models.TextField(blank=True)

    def __str__(self):
        return self.name


class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    profile_image = models.URLField(blank=True, null=True)
    identity_card = models.URLField(blank=True, null=True)
    birthdate = models.DateField(null=True, blank=True)

    referral_code = models.CharField(max_length=20, unique=True, blank=True, null=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')

    points = models.IntegerField(default=0)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    tier = models.ForeignKey(Tier, on_delete=models.SET_NULL, null=True, blank=True)

    preferred_location = models.CharField(max_length=100, blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

    @property
    def is_birthday_today(self):
        if not self.birthdate:
            return False
        today = timezone.now().date()
        return self.birthdate.month == today.month and self.birthdate.day == today.day

class PasswordResetCode(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    code = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        return timezone.now() > self.created_at + timedelta(minutes=30)


class BirthdayRewardLog(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    last_rewarded = models.DateField()

    def __str__(self):
        return f"{self.user.email} birthday rewarded on {self.last_rewarded}"

class Newsletter(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="newsletter")
    is_subscribed = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {'Subscribed' if self.is_subscribed else 'Unsubscribed'}"

class EngagementLog(models.Model):
    ACTION_REFERRAL = "referral_signup"
    ACTION_BOOKING = "completed_booking"
    ACTION_FAMILY = "family_booking"  
    ACTION_COMBO = "combo_experience"
    ACTION_BIRTHDAY = "birthday_claim"
    ACTION_LOTTERY = "lottery_play"

    ACTION_CHOICES = [
        (ACTION_REFERRAL, "Referral Signup"),
        (ACTION_BOOKING, "Completed Booking"),
        (ACTION_COMBO, "Combo Experience"),
        (ACTION_BIRTHDAY, "Birthday Claim"),
        (ACTION_LOTTERY, "Lottery Play"),
        (ACTION_FAMILY, "Family Booking")
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.action}"

    @staticmethod
    def get_points_for_action(action):
        """
        Return how many points the given engagement action is worth.
        This can be used in views or services to apply the point logic.
        """
        return {
            EngagementLog.ACTION_REFERRAL: 100,
            EngagementLog.ACTION_BOOKING: 50,
            EngagementLog.ACTION_COMBO: 80,
            EngagementLog.ACTION_BIRTHDAY: 70,
            EngagementLog.ACTION_LOTTERY: 40,
            EngagementLog.ACTION_FAMILY: 100,
        }.get(action, 0)
