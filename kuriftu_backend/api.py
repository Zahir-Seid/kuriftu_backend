from ninja import NinjaAPI
from user.views import router as user_router

api = NinjaAPI(title="Kuriftu API")

api.add_router("/user", user_router)