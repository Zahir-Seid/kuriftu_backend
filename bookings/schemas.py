from datetime import date as date_, time as time_, datetime as datetime_
from pydantic import BaseModel, Field, ConfigDict
from typing import Literal, Optional


class BookingBase(BaseModel):
    service_type: Literal['ROOM', 'SPA', 'RESTAURANT', 'EVENT'] = Field(..., description="Type of service being booked")
    date: date_ = Field(..., description="Booking date")  # Using date_ instead of date
    time: time_ = Field(..., description="Booking time")  # Using time_ instead of time
    guests: int = Field(default=1, ge=1, description="Number of guests (minimum 1)")
    pickup_required: bool = Field(default=False, description="Whether pickup service is needed")
    pickup_location: Optional[str] = Field(default=None, description="Pickup location if required")
    notes: Optional[str] = Field(default=None, description="Additional booking notes")

    model_config = ConfigDict(from_attributes=True)


class BookingCreate(BookingBase):
    service_id: Optional[str] = Field(
        default=None,
        description="ID of the specific service being booked"
    )


class BookingOut(BaseModel):
    id: int = Field(..., description="Booking ID")
    service_type: Literal['ROOM', 'SPA', 'RESTAURANT', 'EVENT']
    date: date_
    time: time_
    guests: int
    pickup_required: bool
    pickup_location: Optional[str] = None
    discount_applied: bool = Field(..., description="Whether discount was applied")
    discount_amount: float = Field(..., description="Discount amount if applied")
    status: str = Field(..., description="Booking status")
    created_at: datetime_ = Field(..., description="Creation timestamp")

    model_config = ConfigDict(from_attributes=True)


class PaymentCreate(BaseModel):
    booking_id: int = Field(..., description="Associated booking ID")
    amount: float = Field(..., gt=0, description="Payment amount (must be positive)")
    payment_method: Literal['CHAPA', 'POS', 'CASH'] = Field(..., description="Payment method")
    tx_ref: str = Field(..., description="Transaction reference")

    model_config = ConfigDict(from_attributes=True)


class PaymentOut(BaseModel):
    id: int = Field(..., description="Payment ID")
    booking_id: int = Field(..., description="Associated booking ID")
    amount: float = Field(..., description="Payment amount")
    payment_method: str = Field(..., description="Payment method used")
    status: str = Field(..., description="Payment status")
    paid_at: Optional[datetime_] = Field(None, description="When payment was completed")
    tx_ref: str = Field(..., description="Transaction reference")

    model_config = ConfigDict(from_attributes=True)


class TransactionLogOut(BaseModel):
    id: int = Field(..., description="Transaction log ID")
    event: str = Field(..., description="Event description")
    amount: float = Field(..., description="Transaction amount")
    timestamp: datetime_ = Field(..., description="When transaction occurred")
    metadata: Optional[dict] = Field(None, description="Additional transaction data")

    model_config = ConfigDict(from_attributes=True)