import datetime
import uuid
from flask import Blueprint, request, json
from sqlalchemy import (MetaData, Table, and_, asc, delete, desc, insert,
                        select, update)
from utils import get_engine, run_query, created_at

# this means that you can group all endpoints with prefix "/orders" together
orders_bp = Blueprint("orders", __name__, url_prefix="/orders")


@orders_bp.route("", methods=["GET"])
def get_orders():
    # IMPLEMENT THIS
    header = request.headers
    token = header.get("Authentication")

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    orders = Table("orders", MetaData(bind=get_engine()), autoload=True)

    user = run_query(select(users).where(users.c.token == token))
    
    if len(user) == 0:
        return {"message": "error, user is invalid"}, 400
    else:
        order = run_query(select(orders))
        data = []
        for i in range(len(order)):
            buyer = run_query(select(users).where(users.c.id_user == order[i]["user_id"]))
            dict = {}
            dict["id"] = order[i]["id_order"]
            dict["user_name"] = buyer[0]["name"]
            dict["created_at"] = order[i]["created_at"]
            dict["user_id"] = order[i]["user_id"]
            dict["user_email"] = buyer[0]["email"]
            dict["total"] = order[i]["total_product_price"]
        
            data.append(dict)

        return {"data": data}, 200


# this means that you can group all endpoints with prefix "/order" together
order_bp = Blueprint("order", __name__, url_prefix="/order")

@order_bp.route("", methods=["POST"])
def create_order():
    # IMPLEMENT THIS
    headers = request.headers
    token = headers.get("Authentication")
    body = request.json
    shipping_method = body.get("shipping_method")

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    products = Table("products", MetaData(bind=get_engine()), autoload=True)
    carts = Table("carts", MetaData(bind=get_engine()), autoload=True)
    orders = Table("orders", MetaData(bind=get_engine()), autoload=True)

    user = run_query(select(users).where(and_(users.c.token == token, users.c.type == "buyer")))

    if len(user) == 0:
        return {"message": "error, user is invalid"}, 400
    else :
        cart = run_query(select(carts).where(and_(carts.c.user_id == user[0]["id_user"], carts.c.deleted == False)))
        
        if len(cart) == 0:
            return {"message": "error, Cart is empty"}
        else :
            price_pay = run_query(select(carts, products).join(products, carts.c.product_id == products.c.id_product)
                          .where(carts.c.user_id == user[0]['id_user']))
            total_product_price = 0
            for row in price_pay:
                total_product_price+=int(row['price'])*int(row['quantity'])

            if shipping_method == "regular" or shipping_method == "same day":
                if total_product_price < 200000:
                    shipping_price = 0.15 * total_product_price
                else:
                    shipping_price = 0.2 * total_product_price
            elif shipping_method == "next day":
                if total_product_price < 300000:
                    shipping_price = 0.2 * total_product_price
                else:
                    shipping_price = 0.25 * total_product_price

            total_price = total_product_price + shipping_price
            diff = total_price - user[0]["balance"]

            if diff > 0:
                return {"message": f"error, Please top up {diff}"}, 400
            else:
                data = {
                    'id_order': str(uuid.uuid4()),
                    'user_id': user[0]["id_user"],
                    'shipping_method': shipping_method,
                    'shipping_price': shipping_price,
                    'total_product_price': total_product_price,
                    'created_at': created_at(),
                    'status': "waiting"
                }
                run_query(insert(orders).values(data), commit=True)

                for i in range(len(cart)):
                    product = run_query(select(products).where(products.c.id_product == cart[i]["product_id"]))
                    run_query(update(products).values({"sold" : product[0]["sold"] + cart[i]["quantity"] }).where(products.c.id_product == cart[i]["product_id"]), commit=True)
                    run_query(update(carts).values({"deleted" : True, "order_id": data["id_order"]}).where(carts.c.id_cart == cart[i]["id_cart"]), commit=True)

                run_query(update(users).values({"balance" : abs(diff)}).where(and_(users.c.token == token, users.c.type == "buyer")), commit=True)
                seller = run_query(select(users).where(users.c.type == "seller"))
                run_query(update(users).values({"balance" : seller[0]["balance"] + total_product_price}).where(and_(users.c.id_user == seller[0]["id_user"], users.c.type == "seller")), commit=True)

                return {"message": "Order success"}, 201
