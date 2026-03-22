from fastapi import FastAPI, Query, HTTPException, Response
from pydantic import BaseModel, Field
from typing import Optional
import math

app = FastAPI()

# ── Data ─────────────────────────────────────────────

menu = [
    {'id': 1, 'name': 'Veg Burger', 'price': 70, 'category': 'Burger', 'is_available': True},
    {'id': 2, 'name': 'Farmhouse Pizza', 'price': 399, 'category': 'Pizza', 'is_available': True},
    {'id': 3, 'name': 'Coca Cola', 'price': 30, 'category': 'Drink', 'is_available': True},
    {'id': 4, 'name': 'Choco Lava Cake', 'price': 90, 'category': 'Dessert', 'is_available': True},
    {'id': 5, 'name': 'Sourdough Pizza', 'price': 320, 'category': 'Pizza', 'is_available': False},
    {'id': 6, 'name': 'Sprite', 'price': 20, 'category': 'Drink', 'is_available': False},
    {'id': 7, 'name': 'Cupcake', 'price': 40, 'category': 'Dessert', 'is_available': True},
    {'id': 8, 'name': 'Chicken Burger', 'price': 120, 'category': 'Burger', 'is_available': False},
]

orders = []
order_counter = 1
cart = []

# ── Helper Functions ─────────────────────────────────

def find_menu_item(item_id):
    for item in menu:
        if item['id'] == item_id:
            return item
    return None

def calculate_bill(price, quantity, order_type):
    total = price * quantity
    if order_type == "delivery":
        total += 30
    return total

def filter_menu_logic(category=None, max_price=None, is_available=None):
    result = menu

    if category is not None:
        result = [i for i in result if i['category'] == category]

    if max_price is not None:
        result = [i for i in result if i['price'] <= max_price]

    if is_available is not None:
        result = [i for i in result if i['is_available'] == is_available]

    return result

# ── Models ───────────────────────────────────────────

class OrderRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    item_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0, le=20)
    delivery_address: str = Field(..., min_length=10)
    order_type: str = "delivery"

class NewMenuItem(BaseModel):
    name: str = Field(..., min_length=2)
    price: int = Field(..., gt=0)
    category: str = Field(..., min_length=2)
    is_available: bool = True

class CheckoutRequest(BaseModel):
    customer_name: str = Field(..., min_length=2)
    delivery_address: str = Field(..., min_length=10)

# ── Basic Endpoints ─────────────────────────────────

@app.get('/')
def home():
    return {'message': 'Welcome to QuickBite Food Delivery'}

@app.get('/menu')
def get_menu():
    return {'items': menu, 'total': len(menu)}

# ── Menu Summary ─────────────────────────────────────

@app.get('/menu/summary')
def menu_summary():
    available = sum(1 for i in menu if i['is_available'])
    categories = list(set(i['category'] for i in menu))

    return {
        "total_items": len(menu),
        "available_items": available,
        "unavailable_items": len(menu) - available,
        "categories": categories
    }

# ── Menu Filter ─────────────────────────────────────

@app.get('/menu/filter')
def filter_menu(category: str = Query(None), max_price: int = Query(None), is_available: bool = Query(None)):
    result = filter_menu_logic(category, max_price, is_available)
    return {"filtered_items": result, "count": len(result)}

# ── Menu Search ─────────────────────────────────────

@app.get('/menu/search')
def search_menu(keyword: str = Query(...)):
    result = [i for i in menu if keyword.lower() in i['name'].lower() or keyword.lower() in i['category'].lower()]
    if not result:
        return {"message": "No matching items found"}
    return {"items": result, "total": len(result)}

# ── Menu Sort ───────────────────────────────────────

@app.get('/menu/sort')
def sort_menu(sort_by: str = Query('price'), order: str = Query('asc')):
    if sort_by not in ['price', 'name', 'category']:
        raise HTTPException(status_code=400, detail="Invalid sort_by")
    if order not in ['asc', 'desc']:
        raise HTTPException(status_code=400, detail="Invalid order")

    return {
        "items": sorted(menu, key=lambda x: x[sort_by], reverse=(order == 'desc'))
    }

# ── Menu Pagination ─────────────────────────────────

@app.get('/menu/page')
def paginate(page: int = Query(1, ge=1), limit: int = Query(3, ge=1, le=10)):
    total = len(menu)
    start = (page - 1) * limit
    return {
        "page": page,
        "limit": limit,
        "total": total,
        "total_pages": math.ceil(total / limit),
        "items": menu[start:start+limit]
    }

# ── Smart Browse ───────────────────────────────────

@app.get('/menu/browse')
def browse(keyword: str = None, sort_by: str = 'price', order: str = 'asc', page: int = 1, limit: int = 4):
    result = menu

    if keyword:
        result = [i for i in result if keyword.lower() in i['name'].lower() or keyword.lower() in i['category'].lower()]

    result = sorted(result, key=lambda x: x[sort_by], reverse=(order == 'desc'))

    start = (page - 1) * limit
    total = len(result)

    return {
        "page": page,
        "total_pages": math.ceil(total / limit) if total else 1,
        "items": result[start:start+limit]
    }

# ── Menu CRUD ───────────────────────────────────────

@app.post('/menu')
def add_item(item: NewMenuItem, response: Response):
    for i in menu:
        if i['name'].lower() == item.name.lower():
            response.status_code = 400
            return {"error": "Duplicate item"}

    new_item = {"id": len(menu)+1, **item.dict()}
    menu.append(new_item)
    response.status_code = 201
    return new_item

@app.put('/menu/{item_id}')
def update_item(item_id: int, price: int = None, is_available: bool = None):
    item = find_menu_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")

    if price is not None:
        item['price'] = price
    if is_available is not None:
        item['is_available'] = is_available

    return item

@app.delete('/menu/{item_id}')
def delete_item(item_id: int):
    item = find_menu_item(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Not found")

    menu.remove(item)
    return {"message": f"{item['name']} deleted"}

@app.get('/menu/{item_id}')
def get_item(item_id: int):
    item = find_menu_item(item_id)
    if not item:
        return {"error": "Item not found"}
    return item

# ── Orders ─────────────────────────────────────────

@app.post('/orders')
def place_order(order: OrderRequest):
    global order_counter

    item = find_menu_item(order.item_id)
    if not item or not item['is_available']:
        return {"error": "Item unavailable"}

    total = calculate_bill(item['price'], order.quantity, order.order_type)

    new_order = {
        "order_id": order_counter,
        "customer_name": order.customer_name,
        "item_name": item['name'],
        "quantity": order.quantity,
        "total_price": total
    }

    orders.append(new_order)
    order_counter += 1

    return new_order

@app.get('/orders')
def get_orders():
    return {"orders": orders}

@app.get('/orders/search')
def search_orders(customer_name: str):
    result = [o for o in orders if customer_name.lower() in o['customer_name'].lower()]
    if not result:
        return {"message": "No matching orders found"}
    return result

@app.get('/orders/sort')
def sort_orders(order: str = 'asc'):
    return sorted(orders, key=lambda x: x['total_price'], reverse=(order == 'desc'))

# ── Cart ───────────────────────────────────────────

@app.post('/cart/add')
def add_cart(item_id: int, quantity: int = 1):
    item = find_menu_item(item_id)
    if not item or not item['is_available']:
        return {"error": "Item unavailable"}

    for c in cart:
        if c['item_id'] == item_id:
            c['quantity'] += quantity
            return c

    cart.append({
        "item_id": item_id,
        "name": item['name'],
        "quantity": quantity,
        "total_price": item['price'] * quantity
    })

    return {"message": "Added"}

@app.get('/cart')
def view_cart():
    total = sum(i['total_price'] for i in cart)
    return {"cart": cart, "total": total}

@app.delete('/cart/{item_id}')
def remove_cart(item_id: int):
    for i in cart:
        if i['item_id'] == item_id:
            cart.remove(i)
            return {"message": "Removed"}
    return {"error": "Not found"}

@app.post('/cart/checkout')
def checkout(data: CheckoutRequest):
    global order_counter

    if not cart:
        return {"error": "Cart empty"}

    placed = []
    total = 0

    for c in cart:
        total += c['total_price']
        new_order = {
            "order_id": order_counter,
            "customer_name": data.customer_name,
            "item_name": c['name'],
            "quantity": c['quantity'],
            "total_price": c['total_price']
        }
        orders.append(new_order)
        placed.append(new_order)
        order_counter += 1

    cart.clear()

    return {"orders": placed, "total": total}