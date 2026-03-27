from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# import routers
from app.routers import auth, products, categories, outfit, admin

app = FastAPI(title="Fashion AI Stylist API")

# NOTE: restrict origins in production
origins = ["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# include routers
app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(products.router, prefix="/products", tags=["products"])
app.include_router(categories.router, prefix="/categories", tags=["categories"])
app.include_router(outfit.router, prefix="/outfit", tags=["outfit"])
app.include_router(admin.router, prefix="/admin", tags=["admin"])


@app.get("/health")
async def health_check():
    return {"status": "ok"}


# serve static files (images)
from fastapi.staticfiles import StaticFiles
import os

static_dir = os.path.join(os.getcwd(), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")