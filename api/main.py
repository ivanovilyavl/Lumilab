from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routers import master, slots, bookings, tribute
from shared.config import settings

app = FastAPI(title="ЗАПИСЬ.БОТ API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(master.router)
app.include_router(slots.router)
app.include_router(bookings.router)
app.include_router(tribute.router)


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok", "version": "1.0.0"}
