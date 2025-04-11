from ninja import Router
from ninja.errors import HttpError
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.http import HttpRequest
from datetime import datetime

from .models import User, Newsletter, Tier, PasswordResetCode
from .schemas import (
    UserRegisterSchema, UserLoginSchema, UserOutSchema,
    UserUpdateSchema, NewsletterToggleSchema,
    NewsletterStatusSchema, TierOutSchema, PasswordResetConfirmSchema, PasswordResetRequestSchema
)

from .utils import send_password_reset_email
from django.utils import timezone

User = get_user_model()

router = Router(tags=["User account"])



@router.post("/register", response=UserOutSchema)
def register_user(request: HttpRequest, data: UserRegisterSchema):
    if User.objects.filter(email=data.email).exists():
        raise HttpError(400, "User with this email already exists.")

    referred_by = None
    if data.referred_by_code:
        referred_by = User.objects.filter(referral_code=data.referred_by_code).first()

    user = User.objects.create_user(
        email=data.email,
        password=data.password,
        first_name=data.first_name,
        middle_name=data.middle_name,
        last_name=data.last_name,
        birthdate=data.birthdate,
        referred_by=referred_by
    )

    # Create newsletter subscription
    Newsletter.objects.create(
        user=user,
        is_subscribed=True,
        subscribed_at=timezone.now()
    )

    login(request, user)
    return {"message": "Registration successful."} 


@router.post("/login") #, response=UserOutSchema | add this if user info is wanted 
def login_user(request: HttpRequest, data: UserLoginSchema):
    user = authenticate(request, email=data.email, password=data.password)
    if not user:
        raise HttpError(401, "Invalid credentials")
    login(request, user)
    return {"message": "Login successful"}

@router.post("/logout")
async def logout_user(request: HttpRequest):
    if not request.user.is_authenticated:
        raise HttpError(401, "Not logged in.")
    logout(request)
    return {"message": "Logged out successfully"}


@router.post("/password-reset/request")
def request_password_reset(request, data: PasswordResetRequestSchema):
    user = User.objects.filter(email=data.email).first()
    if not user:
        raise HttpError(404, "No user found with this email.")

    send_password_reset_email(user, request)
    return {"success": True, "message": "Reset instructions sent to your email."}


@router.post("/password-reset/confirm")
def confirm_password_reset(request, data: PasswordResetConfirmSchema):
    reset = PasswordResetCode.objects.filter(code=data.code).first()

    if not reset:
        raise HttpError(400, "Invalid reset code.")

    if reset.is_expired():
        reset.delete()
        raise HttpError(400, "Reset code expired.")

    user = reset.user
    user.set_password(data.password)
    user.save()
    reset.delete()

    return {"success": True, "message": "Password has been reset successfully."}


@router.get("/profile", response=UserOutSchema)
def get_profile(request: HttpRequest):
    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")
    return request.user


@router.put("/profile", response=UserOutSchema)
def update_profile(request: HttpRequest, data: UserUpdateSchema):
    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")
    for field, value in data.dict(exclude_unset=True).items():
        setattr(request.user, field, value)
    request.user.save()
    return request.user

@router.delete("/profile/", response={200: dict, 401: dict})
def delete_profile(request):
    if not request.user.is_authenticated:
        return 401, {"error": "Authentication required"}
    
    request.user.delete()
    return 200, {"message": "Your account has been deleted successfully."}

@router.get("/newsletter/status", response=NewsletterStatusSchema)
def get_newsletter_status(request: HttpRequest):
    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")
    newsletter = Newsletter.objects.filter(user=request.user).first()
    return {
        "email": request.user.email,
        "is_subscribed": newsletter.is_subscribed if newsletter else False,
        "subscribed_at": newsletter.subscribed_at if newsletter else None,
    }

@router.post("/newsletter/unsubscribe", response=NewsletterStatusSchema)
def unsubscribe_newsletter(request: HttpRequest):
    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")

    newsletter = Newsletter.objects.filter(user=request.user).first()
    if not newsletter:
        return {
            "email": request.user.email,
            "is_subscribed": False,
            "subscribed_at": None,
        }

    newsletter.is_subscribed = False
    newsletter.save()

    return {
        "email": request.user.email,
        "is_subscribed": False,
        "subscribed_at": newsletter.subscribed_at,
    }


@router.get("/tier", response={200: TierOutSchema, 401: dict})
def get_user_tier(request):
    if not request.user.is_authenticated:
        return 401, {"error": "Authentication required"}
    
    if not request.user.tier:
        raise HttpError(404, "No tier assigned to this user.")

    return request.user.tier