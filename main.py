from fastapi import FastAPI
from database import Base, engine
from routers import products, orders

# Create all tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Inventory API")

app.include_router(products.router)
app.include_router(orders.router)


@app.get("/")
def root():
    return {"message": "Inventory API is running"}
