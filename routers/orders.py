from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from database import get_db
from models import Product, Order, OrderItem
from schemas import OrderCreate, OrderOut

router = APIRouter()


@router.post("/orders", response_model=OrderOut)
def create_order(order_data: OrderCreate, db: Session = Depends(get_db)):

    # --- IDEMPOTENCY CHECK ---
    # If this key was already used, return the existing order (don't create a duplicate)
    existing_order = db.query(Order).filter(
        Order.idempotency_key == order_data.idempotency_key
    ).first()
    if existing_order:
        return existing_order

    # --- CONCURRENCY: Lock rows with SELECT FOR UPDATE ---
    # This prevents two requests from reading the same stock simultaneously
    skus = [item.sku for item in order_data.items]
    products = (
        db.execute(
            select(Product)
            .where(Product.sku.in_(skus))
            .with_for_update()          # <-- DATABASE ROW LOCK
        )
        .scalars()
        .all()
    )

    product_map = {p.sku: p for p in products}

    # --- STOCK VALIDATION ---
    for item in order_data.items:
        if item.sku not in product_map:
            raise HTTPException(
                status_code=404, detail=f"SKU {item.sku} not found")
        if product_map[item.sku].stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {item.sku}. Available: {product_map[item.sku].stock}"
            )

    # --- CREATE ORDER + DEDUCT STOCK (atomic) ---
    new_order = Order(idempotency_key=order_data.idempotency_key)
    db.add(new_order)
    db.flush()  # get the order.id without committing yet

    for item in order_data.items:
        product_map[item.sku].stock -= item.quantity   # deduct stock
        order_item = OrderItem(
            order_id=new_order.id,
            sku=item.sku,
            quantity=item.quantity
        )
        db.add(order_item)

    db.commit()
    db.refresh(new_order)
    return new_order


@router.get("/orders/{id}", response_model=OrderOut)
def get_order(id: int, db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order
