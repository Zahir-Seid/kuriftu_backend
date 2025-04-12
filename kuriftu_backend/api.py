from ninja import NinjaAPI
from user.views import router as user_router
from bookings.views import router as booking_router

api = NinjaAPI(title="Kuriftu API")

api.add_router("/user", user_router)
api.add_router("/booking", booking_router)