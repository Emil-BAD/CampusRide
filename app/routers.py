from app.features.create_trip.handlers import router as create_trip_router
# from features.search_trip.handlers import router as search_trip_router

def setup_routers(dp):
    dp.include_router(create_trip_router)
    # dp.include_router(search_trip_router)