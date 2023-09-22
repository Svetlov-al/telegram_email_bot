from api.email_routes import router_email
from api.filter_routers import router_filter
from api.user_routes import router_user
from ninja import NinjaAPI

api = NinjaAPI(title='EmailTelegramBot')

api.add_router('/users', router_user)
api.add_router('/emailboxes', router_email)
api.add_router('/filters', router_filter)
