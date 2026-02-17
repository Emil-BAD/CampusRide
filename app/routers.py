from app.features.create_trip.handlers import router as create_trip_router
from app.features.search_trip.handlers import router as search_trip_router
from app.features.my_trips.handlers import router as my_trips_router
from app.features.profile.handlers import router as profile_router
from app.features.support.handlers import router as support_router


def setup_routers(dp):
    dp.include_router(create_trip_router)
    dp.include_router(search_trip_router)
    dp.include_router(my_trips_router)
    dp.include_router(profile_router)
    dp.include_router(support_router)