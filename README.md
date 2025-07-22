# Mini Inventory Management System

A simple inventory management system built with FastAPI, supporting product addition, inventory status, purchasing, and automatic restocking.

## Setup
1. Install Python 3.10+
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `python inventory_system.py`
4. Access API at `http://localhost:8000/docs`

## Endpoints
- **POST /products**: Add a new product (e.g., `curl -X POST "http://localhost:8000/products" -H "Content-Type: application/json" -d '{"product_id":"P001","name":"Notebook","stock_quantity":50,"min_threshold":5,"restock_quantity":30,"priority":"high"}'`)
- **GET /products/{product_id}**: Check inventory status (e.g., `curl "http://localhost:8000/products/P001"`)
- **POST /products/{product_id}/purchase**: Purchase product and trigger restock if needed (e.g., `curl -X POST "http://localhost:8000/products/P001/purchase" -H "Content-Type: application/json" -d '{"quantity":45}'`)

## Features
- Adjusts `min_threshold` to 10 for high-priority products if < 10.
- Assigns `high_volume` or `low_volume` category based on `restock_quantity` (>50 or ≤50).
- Restocks automatically when `stock_quantity` < `min_threshold`, with 1.5x `restock_quantity` for high-priority products.
- Logs all operations to `inventory.log` for traceability.
- Stores data in `inventory.json` for persistence.
