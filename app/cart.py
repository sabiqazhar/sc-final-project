import uuid
from flask import Blueprint, request, json
from sqlalchemy import (MetaData, Table, and_, asc, delete, desc, insert,
                        select, update)
from utils import get_engine, run_query

# this means that you can group all endpoints with prefix "/cart" together
cart_bp = Blueprint("cart", __name__, url_prefix="/cart")

@cart_bp.route("", methods=["GET"])
def get_user_cart():
    # IMPLEMENT THIS
    headers = request.headers
    token = headers.get("Authentication")

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    carts = Table("carts", MetaData(bind=get_engine()), autoload=True)
    products = Table("products", MetaData(bind=get_engine()), autoload=True)
    product_images = Table("product_images", MetaData(bind=get_engine()), autoload=True)

    user = run_query(select(users).where(and_(users.c.token == token, users.c.type == "buyer")))

    if len(user) == 0:
        return {"message": "error, user is invalid"}, 400
    else :
        cart = run_query(select(carts).where(and_(carts.c.user_id == user[0]["id_user"], carts.c.deleted == False)))

        data = []
        for i in range(len(cart)):
            dict = {}
            dict["id"] = cart[i]["id_cart"]
            dict["details"] = {
                "quantity": cart[i]["quantity"],
                "size": cart[i]["size"]
            }

            product = run_query(select(products).where(products.c.id_product == cart[i]["product_id"]))
            dict["price"] = product[0]["price"]
            dict["name"] = product[0]["product_name"]

            product_image = run_query(select(product_images).where(product_images.c.product_id == cart[i]["product_id"]))
            if len(product_image) == 0 :
                continue
            elif len(product_image) == 1:
                dict["image"] = product_image[0]["image"]
            else :
                dict["image"] = []
                for j in range(len(product_image)):
                    dict["image"].append(product_image[j]["image"])

            data.append(dict)

        return {
            "data": data,
            "total_rows": len(data)
        }, 200


@cart_bp.route("", methods=["POST"])
def add_to_cart():
    # IMPLEMENT THIS
    header = request.headers
    body = request.json
    token = header.get("Authentication")
    product_id = body.get('id')
    quantity = body.get('quantity')
    size = body.get('size')

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    carts = Table("carts", MetaData(bind=get_engine()), autoload=True)

    user = run_query(select(users).where(and_(users.c.token == token, users.c.type == "buyer")))

    if len(user) == 0:
        return {"message": "error, user is invalid"}, 400
    else :
        cart = run_query(select(carts).where(and_(carts.c.size == size, carts.c.product_id == product_id, carts.c.user_id == user[0]["id_user"])))
        if len(cart) != 0:
            run_query(update(carts).values({"quantity": cart[0]["quantity"]+int(quantity)}).where(and_(carts.c.product_id == product_id, carts.c.size == size, carts.c.user_id == user[0]["id_user"], carts.c.deleted == False)), commit=True)
        else:
            data = {
                'id_cart': str(uuid.uuid4()),
                'user_id': user[0]['id_user'],
                'product_id': product_id,
                'quantity': quantity,
                'size': size,
                'deleted' : False
            }
            run_query(insert(carts).values(data), commit=True)

        return {"message": "success, item added to cart"}, 201


@cart_bp.route("/<cart_id>", methods=["DELETE"])
def delete_cart_item(cart_id):
    # IMPLEMENT THIS
    header = request.headers
    token = header.get("Authentication")

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    carts = Table("carts", MetaData(bind=get_engine()), autoload=True)

    user = run_query(select(users).where(and_(users.c.token == token, users.c.type == "buyer")))

    if len(user) == 0:
        return {"message": "error, user is invalid"}, 400
    else:
        run_query(delete(carts).where(carts.c.id_cart == cart_id), commit=True)
        return {"message": "Cart deleted"}, 200

