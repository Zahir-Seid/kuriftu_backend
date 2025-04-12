from ninja import Router
from django.http import JsonResponse
from .models import *
from .schemas import BookingCreate, BookingOut
from django.db import IntegrityError
from datetime import datetime
from django.shortcuts import get_object_or_404
from ninja.errors import HttpError
from django.http import HttpRequest
from dotenv import load_dotenv
from Crypto.Cipher import AES
from Crypto.Util.Padding import unpad
import base64
import os
import uuid
import json
import hmac
import hashlib
from django.utils import timezone
from ninja import Header

router = Router(tags=["Bookings and Payment"])


# Environment Variables
CHAPA_SECRET_KEY = os.getenv("CHAPA_SECRET_KEY")
CHAPA_INIT_URL = os.getenv("CHAPA_INIT_URL")
CHAPA_VERIFY_URL = os.getenv("CHAPA_VERIFY_URL")
BACKEND_URL = os.getenv("BACKEND_URL")
FRONTEND_URL = os.getenv("FRONTEND_URL")
CHAPA_WEBHOOK_SECRET = os.getenv("CHAPA_WEBHOOK_SECRET")
DECIPH_KEY = os.getenv("Deciphkey")

@router.post("/bookings/", response={201: BookingOut})
def create_booking(request, booking: BookingCreate):
    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")

    try:
        # Create a new booking instance
        new_booking = Booking.objects.create(
            user=request.user,
            service_type=booking.service_type,
            service_id=booking.service_id,
            date=booking.date,
            time=booking.time,
            guests=booking.guests,
            pickup_required=booking.pickup_required,
            pickup_location=booking.pickup_location,
            notes=booking.notes or "",  # optional
        )
        
        return JSONResponse(status_code=201, content=new_booking)

    except IntegrityError as e:
        return JsonResponse({'error': f'Error creating booking: {e}'}, status=400)


@router.get("/bookings/", response=BookingOut)
def list_bookings(request):
    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")

    bookings = Booking.objects.filter(user=request.user) 
    return JSONResponse(bookings)


@router.post("/bookings/get/", response={200: BookingOut})
def get_booking(request, booking_data: BookingCreate):
    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")

    booking_id = booking_data.booking_id
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    return JSONResponse(booking)



@router.put("/bookings/update/", response={200: BookingOut})
def update_booking(request, booking_data: BookingCreate):
    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")

    # Extract booking_id from the request body
    booking_id = booking_data.booking_id
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    # Update fields
    booking.service_type = booking_data.service_type
    booking.service_id = booking_data.service_id
    booking.date = booking_data.date
    booking.time = booking_data.time
    booking.guests = booking_data.guests
    booking.pickup_required = booking_data.pickup_required
    booking.pickup_location = booking_data.pickup_location
    booking.notes = booking_data.notes or ""

    booking.save()

    return JSONResponse(booking)


@router.delete("/bookings/delete/", response={204: None})
def delete_booking(request, booking_data: BookingCreate):
    if not request.user.is_authenticated:
        raise HttpError(401, "Authentication required")

    # Extract booking_id from the request body
    booking_id = booking_data.booking_id
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    # Delete the booking
    booking.delete()

    return JSONResponse(status_code=204, content={"message": "Booking deleted successfully"})


# Function to decrypt the encrypted amount
def decrypt_amount(encrypted_amount: str) -> float:
    try:
        # Convert hex key to bytes
        key = bytes.fromhex(DECIPH_KEY)

        # Decode base64-encoded encrypted string
        encrypted_bytes = base64.b64decode(encrypted_amount)

        # Create AES cipher in ECB mode
        cipher = AES.new(key, AES.MODE_ECB)

        # Decrypt and unpad the data
        decrypted_bytes = unpad(cipher.decrypt(encrypted_bytes), BLOCK_SIZE)

        # Convert the decrypted bytes back to a float
        return float(decrypted_bytes.decode('utf-8'))

    except Exception as e:
        raise ValueError(f"Decryption failed: {str(e)}")


@router.post("/pay-initialize/")
def initialize_payment(request, amount: str, currency: str = "ETB"):
    """Initialize Chapa payment with vending machine format"""
    try:
        # Decrypt the amount (assuming you have a decrypt function)
        amount = decrypt_amount(amount)

        # Read the entire request body
        body = request.data
        meta = body.get("meta", {})  # Extract meta object from the body

        # Generate a tx_ref that is unique for each transaction
        tx_ref = f"order_{uuid.uuid4()}"

        # Prepare Chapa payment payload
        payload = {
            "amount": str(amount),
            "currency": currency,
            "tx_ref": tx_ref,
            "callback_url": f"{BACKEND_URL}/api/payment/callback/",
            "return_url": f"{FRONTEND_URL}/payment-complete/",
            "meta": meta
        }

        # Make request to Chapa API to initiate payment
        response = requests.post(
            CHAPA_INIT_URL,
            json=payload,
            headers={
                'Authorization': f'Bearer {CHAPA_SECRET_KEY}',
                'Content-Type': 'application/json'
            }
        )

        data = response.json()
        if data.get("status") == "success":
            # Save payment to the database (use tx_ref here)
            payment = Payment.objects.create(
                booking_id=meta.get("booking_id"),
                amount=amount,
                payment_method="CHAPA",
                status="PENDING",
                tx_ref=tx_ref
            )

            return JsonResponse({
                "status": "success",
                "checkout_url": data["data"]["checkout_url"],
                "tx_ref": tx_ref
            })
        else:
            return JsonResponse({"status": "error", "message": data.get("message")}, status=400)

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)


@router.post("/callback/")
def payment_callback(request, chapa_signature: str = Header(None), x_chapa_signature: str = Header(None)):    
    try:
        # Get raw request body
        body_bytes = request.body

        # Verify Chapa signature
        if not chapa_signature and not x_chapa_signature:
            return JsonResponse({"status": "error", "message": "Missing signature"}, status=401)

        expected_signature = hmac.new(
            CHAPA_WEBHOOK_SECRET.encode(),
            body_bytes,
            hashlib.sha256
        ).hexdigest()

        if expected_signature not in [chapa_signature, x_chapa_signature]:
            return JsonResponse({"status": "error", "message": "Invalid signature"}, status=401)

        # Parse the body data
        data = json.loads(body_bytes.decode())
        tx_ref = data.get("tx_ref")

        # Verify transaction with Chapa
        verify_response = requests.get(
            f"{CHAPA_VERIFY_URL}/{tx_ref}",
            headers={'Authorization': f'Bearer {CHAPA_SECRET_KEY}'}
        )
        verify_data = verify_response.json()

        if verify_data.get("status") != "success":
            return JsonResponse({"status": "error", "message": "Payment verification failed"}, status=400)

        transaction_status = verify_data.get("data", {}).get("status")
        if transaction_status != "success":
            return JsonResponse({"status": "error", "message": f"Transaction not successful: {transaction_status}"}, status=400)

        # Extract metadata (any additional data from Chapa)
        meta = verify_data.get("data", {}).get("meta", {})
        booking_id = meta.get("booking_id")

        # Find payment by tx_ref
        payment = get_object_or_404(Payment, tx_ref=tx_ref)

        # Update the payment status in the database after successful verification
        payment.status = "SUCCESS"
        payment.paid_at = timezone.now()
        payment.save()

        # Create a transaction log for the successful payment
        TransactionLog.objects.create(
            user=payment.booking.user,
            event="Payment Successful",
            amount=payment.amount,
            metadata={"tx_ref": tx_ref, "status": transaction_status}
        )

        return JsonResponse({"status": "success", "message": "Payment verified successfully"})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)
