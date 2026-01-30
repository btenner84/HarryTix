from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from app.api.deps import get_db
from app.models.inventory import Inventory
from app.models.listing import ListingSnapshot
from app.schemas.inventory import InventoryCreate, InventoryUpdate, InventoryResponse, InventoryWithMarketData

router = APIRouter()


@router.get("/", response_model=list[InventoryWithMarketData])
async def list_inventory(db: AsyncSession = Depends(get_db)):
    """List all inventory items with current market data"""
    result = await db.execute(select(Inventory).order_by(Inventory.event_id, Inventory.section))
    inventory_items = result.scalars().all()

    # Get latest listings for market comparison (last 2 hours)
    cutoff = datetime.utcnow() - timedelta(hours=2)

    items_with_market = []
    for item in inventory_items:
        # Find comparable listings (same event, same/similar section)
        listings_query = select(ListingSnapshot).where(
            ListingSnapshot.event_id == item.event_id,
            ListingSnapshot.fetched_at >= cutoff,
            ListingSnapshot.section.ilike(f"%{item.section.split()[0]}%")  # Match section prefix
        )
        listings_result = await db.execute(listings_query)
        listings = listings_result.scalars().all()

        # Calculate market stats
        if listings:
            prices = [float(l.price_per_ticket) for l in listings]
            avg_price = Decimal(str(sum(prices) / len(prices)))
            min_price = Decimal(str(min(prices)))
            max_price = Decimal(str(max(prices)))
            expected_revenue = avg_price * item.quantity
            expected_profit = expected_revenue - item.total_cost
        else:
            avg_price = min_price = max_price = None
            expected_revenue = expected_profit = None

        item_data = InventoryWithMarketData(
            **{k: v for k, v in item.__dict__.items() if not k.startswith('_')},
            current_market_price=avg_price,
            expected_revenue=expected_revenue,
            expected_profit=expected_profit,
            comparable_listings_count=len(listings),
            min_market_price=min_price,
            max_market_price=max_price,
            avg_market_price=avg_price,
        )
        items_with_market.append(item_data)

    return items_with_market


@router.get("/{inventory_id}", response_model=InventoryWithMarketData)
async def get_inventory_item(inventory_id: int, db: AsyncSession = Depends(get_db)):
    """Get a specific inventory item with market data"""
    result = await db.execute(select(Inventory).where(Inventory.id == inventory_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    # Get market data
    cutoff = datetime.utcnow() - timedelta(hours=2)
    listings_query = select(ListingSnapshot).where(
        ListingSnapshot.event_id == item.event_id,
        ListingSnapshot.fetched_at >= cutoff,
        ListingSnapshot.section.ilike(f"%{item.section.split()[0]}%")
    )
    listings_result = await db.execute(listings_query)
    listings = listings_result.scalars().all()

    if listings:
        prices = [float(l.price_per_ticket) for l in listings]
        avg_price = Decimal(str(sum(prices) / len(prices)))
        min_price = Decimal(str(min(prices)))
        max_price = Decimal(str(max(prices)))
        expected_revenue = avg_price * item.quantity
        expected_profit = expected_revenue - item.total_cost
    else:
        avg_price = min_price = max_price = None
        expected_revenue = expected_profit = None

    return InventoryWithMarketData(
        **{k: v for k, v in item.__dict__.items() if not k.startswith('_')},
        current_market_price=avg_price,
        expected_revenue=expected_revenue,
        expected_profit=expected_profit,
        comparable_listings_count=len(listings),
        min_market_price=min_price,
        max_market_price=max_price,
        avg_market_price=avg_price,
    )


@router.post("/", response_model=InventoryResponse)
async def create_inventory_item(item: InventoryCreate, db: AsyncSession = Depends(get_db)):
    """Add a new ticket to inventory"""
    db_item = Inventory(**item.model_dump())
    db.add(db_item)
    await db.commit()
    await db.refresh(db_item)
    return db_item


@router.put("/{inventory_id}", response_model=InventoryResponse)
async def update_inventory_item(inventory_id: int, item: InventoryUpdate, db: AsyncSession = Depends(get_db)):
    """Update an inventory item"""
    result = await db.execute(select(Inventory).where(Inventory.id == inventory_id))
    db_item = result.scalar_one_or_none()
    if not db_item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    update_data = item.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_item, field, value)

    await db.commit()
    await db.refresh(db_item)
    return db_item


@router.delete("/{inventory_id}")
async def delete_inventory_item(inventory_id: int, db: AsyncSession = Depends(get_db)):
    """Remove a ticket from inventory"""
    result = await db.execute(select(Inventory).where(Inventory.id == inventory_id))
    db_item = result.scalar_one_or_none()
    if not db_item:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    await db.delete(db_item)
    await db.commit()
    return {"message": "Inventory item deleted"}
