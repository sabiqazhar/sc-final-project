import uuid

from flask import Blueprint, request
from sqlalchemy import MetaData, Table, and_, delete, insert, select, update
from utils import get_engine, run_query

# this means that you can group all endpoints with prefix "/user" together
user_bp = Blueprint("user", __name__, url_prefix="/user")

@user_bp.route("", methods=["GET"])
def user_details():
    # IMPLEMENT THIS
    header = request.headers
    token = header.get("Authentication")

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    user = run_query(select(users).where(users.c.token == token))
    
    if len(user) == 0:
        return {"message": "error, user is invalid"}, 400
    else:
        return {
            "data":
                {
                    "name": user[0]["name"],
                    "email": user[0]["email"],
                    "phone_number": user[0]["phone_number"]
                }
        }, 200


@user_bp.route("/balance", methods=["GET"])
def get_user_balance():
    # IMPLEMENT THIS
    header = request.headers
    token = header.get("Authentication")

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    user = run_query(select(users).where(users.c.token == token))
    
    if len(user) == 0:
        return {"message": "error, user is invalid"}, 400
    else:
        return {
            "data":
                {
                    "balance": user[0]["balance"]
                }
        }, 200


@user_bp.route("/balance", methods=["POST"])
def top_up_balance():
    # IMPLEMENT THIS
    body = request.json
    header = request.headers
    token = header.get("Authentication")

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    user = run_query(select(users).where(users.c.token == token))

    if len(user) == 0:
        return {"message": "error, user is invalid"}, 400
    else:
        try:
            amount = int(body.get("amount"))
            new_balance = amount + user[0]["balance"]
            run_query(update(users).values({"balance": new_balance}).where(users.c.token == token), commit=True)
            return {"message": "Top Up balance success"}, 200
        except:
            return {"message": "error, amount must be an integer"}, 400


@user_bp.route("/shipping_address", methods=["GET"])
def get_user_sa():
    # IMPLEMENT THIS
    header = request.headers
    token = header.get("Authentication")

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    user = run_query(select(users).where(users.c.token == token))
    
    if len(user) == 0:
        return {"message": "error, user is invalid"}, 400
    else:
        shipping_addresses = Table("shipping_addresses", MetaData(bind=get_engine()), autoload=True)
        shipping_address = run_query(select(shipping_addresses).where(shipping_addresses.c.user_id == user[0]["id_user"]))

        return {
            "data":
                {
                    "id": shipping_address[0]["id_address"],
                    "name": shipping_address[0]["name"],
                    "phone_number": shipping_address[0]["phone_number"],
                    "address": shipping_address[0]["address"],
                    "city": shipping_address[0]["city"]
                }
        }, 200


@user_bp.route("/shipping_address", methods=["POST"])
def change_sa():
    # IMPLEMENT THIS
    header = request.headers
    token = header.get("Authentication")
    body = request.json

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    user = run_query(select(users).where(users.c.token == token))
    
    if len(user) == 0:
        return {"message": "error, user is invalid"}, 400
    else:
        shipping_addresses = Table("shipping_addresses", MetaData(bind=get_engine()), autoload=True)
        shipping_address = run_query(select(shipping_addresses).where(shipping_addresses.c.user_id == user[0]["id_user"]))
        
        if len(body) == 0:
            return {"message": "error, request body cannot be null"}, 400
        elif len(shipping_address) == 0:
            body["id_address"] = str(uuid.uuid4())
            body["user_id"] = user[0]["id_user"]
            run_query(insert(shipping_addresses).values(body), commit=True)   
        else :
            run_query(update(shipping_addresses).values(body).where(shipping_addresses.c.user_id == user[0]["id_user"]), commit=True)
        
        result_shipping_address = run_query(select(shipping_addresses).where(shipping_addresses.c.user_id == user[0]["id_user"]))
        return {
                "name": result_shipping_address[0]["name"],
                "phone_number": result_shipping_address[0]["phone_number"],
                "address": result_shipping_address[0]["address"],
                "city": result_shipping_address[0]["city"]
        }, 200

        # CONDITION
        """
        - if user not token invalid
            - {"message": "error, user is invalid"}, 400
        - if request body is null
            - {"message": "error, request body cannot be null"}, 400
        - if shipping address doesn't exist then create
        """

@user_bp.route("/order", methods=["GET"])
def user_orders():
    # IMPLEMENT THIS
    header = request.headers
    token = header.get("Authentication")

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    shipping_addresses = Table("shipping_addresses", MetaData(bind=get_engine()), autoload=True)
    products = Table("products", MetaData(bind=get_engine()), autoload=True)
    product_images = Table("product_images", MetaData(bind=get_engine()), autoload=True)
    carts = Table("carts", MetaData(bind=get_engine()), autoload=True)
    orders = Table("orders", MetaData(bind=get_engine()), autoload=True)

    user = run_query(select(users).where(users.c.token == token))
    
    if len(user) == 0:
        return {"message": "error, user is invalid"}, 400
    else:
        order = run_query(select(orders).where(orders.c.user_id == user[0]["id_user"]))
        if len(order) == 0:
            return {"data": []}, 200
        else :
            shipping_address = run_query(select(shipping_addresses).where(shipping_addresses.c.user_id == user[0]["id_user"]))
            data_address = {
                    "name": shipping_address[0]["name"],
                    "phone_number": shipping_address[0]["phone_number"],
                    "address": shipping_address[0]["address"],
                    "city": shipping_address[0]["city"]
                }
            data = []
            for i in range(len(order)):
                dict = {}
                dict["id"] = order[i]["id_order"]
                dict["created_at"] = order[i]["created_at"]

                cart = run_query(select(carts, products).join(products, carts.c.product_id == products.c.id_product).where(and_(carts.c.order_id == order[i]["id_order"], carts.c.deleted == True)))
                dict["products"] = []
                for row in cart:
                    product_image = run_query(select(product_images).where(product_images.c.product_id == row['product_id']))
                    if len(product_image) == 0 :
                        continue
                    product = {
                        "id": row['id_product'],
                        "details": {
                            "quantity": row['quantity'],
                            "size": row['size'],
                        },
                        "price": row['price'],
                        "image": product_image[0]['image'],
                        "name": row['product_name']
                    }
                    dict["products"].append(product)


                dict["shipping_method"] = order[i]["shipping_method"]
                dict["shipping_address"] = data_address

                data.append(dict)

            return {"data": data}, 200
