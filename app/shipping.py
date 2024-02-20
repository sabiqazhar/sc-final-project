import uuid

from flask import Blueprint, request
from sqlalchemy import MetaData, Table, insert, select
from utils import get_engine, run_query


# this means that you can group all endpoints with prefix "/shipping_price" together
shipping_price_bp = Blueprint("shipping_price", __name__, url_prefix="/shipping_price")


@shipping_price_bp.route("", methods=["GET"])
def get_shipping_price():
    # IMPLEMENT THIS
    header = request.headers
    token = header.get("Authentication")

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    carts = Table("carts", MetaData(bind=get_engine()), autoload=True)
    products = Table("products", MetaData(bind=get_engine()), autoload=True)

    user = run_query(select(users).where(users.c.token == token))

    if len(user) == 0:
        return {"message": "error, user is invalid"}, 400
    else:
        cart_in = run_query(select(carts).where(carts.c.user_id == user[0]['id_user']))
        if len(cart_in) == 0:
            return {"message": "error, Cart is empty"}
        else:
            price_pay = run_query(select(carts, products).join(products, carts.c.product_id == products.c.id_product)
                          .where(carts.c.user_id == user[0]['id_user']))
            total_price = 0
            for row in price_pay:
                total_price+=int(row['price'])*int(row['quantity'])
            
            reg_price = 0
            if total_price < 200000:
                reg_price += 0.15 * total_price
            else:
                reg_price += 0.2 * total_price

            nextday_price = 0
            if total_price < 300000:
                nextday_price += 0.2 * total_price
            else:
                nextday_price += 0.25 * total_price

            return {
                "data" : [
                    {
                        "name":"regular",
                        "price":reg_price
                    },
                    {
                        "name":"next day",
                        "price":nextday_price
                    }
                ]
            }, 200
