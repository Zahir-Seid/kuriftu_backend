from pydantic import BaseModel, EmailStr, Field, constr
from typing import Optional, List
from datetime import date, datetime


class UserRegisterSchema(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    first_name: str
    middle_name: Optional[str] = None
    last_name: str
    birthdate: Optional[date] = None
    referred_by_code: Optional[str] = None  # referral code (optional)


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str


class UserUpdateSchema(BaseModel):
    first_name: Optional[str]
    middle_name: Optional[str]
    last_name: Optional[str]
    birthdate: Optional[date]
    profile_image: Optional[str]
    preferred_location: Optional[str]


class UserOutSchema(BaseModel):
    id: int
    email: EmailStr
    first_name: str
    middle_name: Optional[str]
    last_name: str
    profile_image: Optional[str]
    birthdate: Optional[date]
    points: int
    total_spent: float
    tier: Optional[str]
    referral_code: str
    preferred_location: Optional[str]

    class Config:
        from_attributes = True


class BirthdayRewardOutSchema(BaseModel):
    message: str
    rewarded: bool


class NewsletterToggleSchema(BaseModel):
    is_subscribed: bool


class NewsletterStatusSchema(BaseModel):
    email: EmailStr
    is_subscribed: bool
    subscribed_at: Optional[datetime]

class TierOutSchema(BaseModel):
    id: int
    name: str
    min_points: int
    perks: Optional[str]

    class Config:
        from_attributes = True


class PasswordResetRequestSchema(BaseModel):
    email: EmailStr

class PasswordResetConfirmSchema(BaseModel):
    code: str
    password: constr(min_length=6, max_length=68)