from fastapi import FastAPI, HTTPException
import json
import logging
from pydantic import BaseModel
from typing import Optional
import os

app = FastAPI()

# Configure logging for traceability
logging.basicConfig(level=logging.INFO, filename='inventory.log', 
                    format='%(asctime)s %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# JSON file for storage
DATA_FILE = "inventory.json"

# Load products from JSON file or initialize empty
def load_products():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading products from {DATA_FILE}: {str(e)}")
            return {}
    return {}

# Save products to JSON file
def save_products(products):
    try:
        with open(DATA_FILE, 'w') as f:
            json.dump(products, f, indent=2)
        logger.info(f"Saved products to {DATA_FILE}")
    except Exception as e:
        logger.error(f"Error saving products to {DATA_FILE}: {str(e)}")

products = load_products()

# Pydantic model for product creation
class ProductCreate(BaseModel):
    product_id: str
    name: str
    stock_quantity: int
    min_threshold: int
    restock_quantity: int
    priority: str

# Pydantic model for purchase request
class PurchaseRequest(BaseModel):
    quantity: int

@app.post("/products")
async def add_product(product: ProductCreate):
    try:
        # Validate input
        if product.stock_quantity < 0 or product.min_threshold < 0 or product.restock_quantity <= 0:
            logger.error(f"Invalid input for product {product.product_id}: negative or zero values")
            raise HTTPException(status_code=400, detail="Invalid input: quantities must be positive")

        if product.priority not in ["high", "low"]:
            logger.error(f"Invalid priority for product {product.product_id}: {product.priority}")
            raise HTTPException(status_code=400, detail="Priority must be 'high' or 'low'")

        # Business rule: Adjust min_threshold for high-priority products
        min_threshold = product.min_threshold
        if product.priority == "high" and min_threshold < 10:
            min_threshold = 10
            logger.info(f"Adjusted min_threshold to 10 for high-priority product {product.product_id}")

        # Business rule: Assign category based on restock_quantity
        category = "high_volume" if product.restock_quantity > 50 else "low_volume"
        logger.info(f"Assigned category {category} to product {product.product_id}")

        # Store product
        products[product.product_id] = {
            "product_id": product.product_id,
            "name": product.name,
            "stock_quantity": product.stock_quantity,
            "min_threshold": min_threshold,
            "restock_quantity": product.restock_quantity,
            "priority": product.priority,
            "category": category
        }
        save_products(products)
        logger.info(f"Added product {product.product_id}: {products[product.product_id]}")
        return {"message": "Product added successfully", "product": products[product.product_id]}

    except Exception as e:
        logger.error(f"Error adding product {product.product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/products/{product_id}")
async def get_inventory_status(product_id: str):
    try:
        product = products.get(product_id)
        if not product:
            logger.error(f"Product {product_id} not found")
            raise HTTPException(status_code=404, detail="Product not found")

        # Determine status based on stock_quantity and min_threshold
        if product["stock_quantity"] == 0:
            status = "out_of_stock"
        elif product["stock_quantity"] < product["min_threshold"]:
            status = "below_threshold"
        else:
            status = "ok"

        response = {
            "product_id": product["product_id"],
            "stock_quantity": product["stock_quantity"],
            "status": status,
            "priority": product["priority"]
        }
        logger.info(f"Retrieved status for product {product_id}: {response}")
        return response

    except Exception as e:
        logger.error(f"Error retrieving product {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/products/{product_id}/purchase")
async def purchase_product(product_id: str, purchase: PurchaseRequest):
    try:
        if purchase.quantity <= 0:
            logger.error(f"Invalid purchase quantity for product {product_id}: {purchase.quantity}")
            raise HTTPException(status_code=400, detail="Quantity must be positive")

        product = products.get(product_id)
        if not product:
            logger.error(f"Product {product_id} not found for purchase")
            raise HTTPException(status_code=404, detail="Product not found")

        if product["stock_quantity"] < purchase.quantity:
            logger.error(f"Insufficient stock for product {product_id}: {product['stock_quantity']} available, {purchase.quantity} requested")
            raise HTTPException(status_code=400, detail="Insufficient stock")

        # Update stock
        product["stock_quantity"] -= purchase.quantity
        logger.info(f"Purchased {purchase.quantity} units of product {product_id}. New stock: {product['stock_quantity']}")

        # Restock logic: Automatically restock if below threshold, with priority-based adjustments
        if product["stock_quantity"] < product["min_threshold"]:
            restock_amount = product["restock_quantity"]
            if product["priority"] == "high":
                restock_amount = int(restock_amount * 1.5)  # 50% more for high-priority
            product["stock_quantity"] += restock_amount
            logger.info(f"Restocked product {product_id} by {restock_amount} units. New stock: {product['stock_quantity']}")

        save_products(products)
        return {"message": "Purchase successful", "product": product}

    except Exception as e:
        logger.error(f"Error processing purchase for product {product_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)