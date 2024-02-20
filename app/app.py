from authentication import signin_bp, signup_bp
from cart import cart_bp
from categories import categories_bp
from flask import Flask, jsonify, send_file
from flask_cors import CORS
from home import home_bp
from order import order_bp, orders_bp
from product import products_bp
from sales import sales_bp
from shipping import shipping_price_bp
from sqlalchemy import (Column, Integer, Boolean, MetaData, String, Table, delete,
                        inspect)
from user import user_bp
from utils import get_engine, run_query


def create_app():
    app = Flask(__name__)
    CORS(app)

    # always register your blueprint(s) when creating application
    blueprints = [signin_bp, signup_bp, cart_bp, categories_bp, home_bp, order_bp, orders_bp,
                  products_bp, sales_bp, shipping_price_bp, user_bp]
    for blueprint in blueprints:
        app.register_blueprint(blueprint)

    engine = get_engine()

    # - create necessary tables

    if not inspect(engine).has_table('users'):
        meta = MetaData()
        Table(
            'users',
            meta,
            Column('id_user', String, primary_key=True, unique=True),
            Column('name', String(128), unique=True),
            Column('email', String(128), unique=True),
            Column('password', String(128)),
            Column('phone_number', String(128)),
            Column('token', String, unique=True),
            Column('type', String(12)),
            Column('balance', Integer)
        )
        meta.create_all(engine)
    else:
        users = Table("users", MetaData(bind=get_engine()), autoload=True)
        run_query(delete(users), commit=True)

    if not inspect(engine).has_table('shipping_addresses'):
        meta = MetaData()
        Table(
            'shipping_addresses',
            meta,
            Column('id_address', String, primary_key=True, unique=True),
            Column('user_id', String(128), unique=True),
            Column('name', String(128)),
            Column('phone_number', String(128)),
            Column('address', String(128)),
            Column('city', String(128))
        )
        meta.create_all(engine)
    else:
        shipping_addresses = Table("shipping_addresses", MetaData(bind=get_engine()), autoload=True)
        run_query(delete(shipping_addresses), commit=True)

    if not inspect(engine).has_table('categories'):
        meta = MetaData()
        Table(
            'categories',
            meta,
            Column('id_category', String, primary_key=True, unique=True),
            Column('category_name', String(128)),
            Column('deleted', Boolean, default=False)
        )
        meta.create_all(engine)
    else:
        categories = Table("categories", MetaData(bind=get_engine()), autoload=True)
        run_query(delete(categories), commit=True)

    if not inspect(engine).has_table('products'):
        meta = MetaData()
        Table(
            'products',
            meta,
            Column('id_product', String, primary_key=True, unique=True),
            Column('category_id', String(128)),
            Column('product_name', String(128)),
            Column('description', String(128)),
            Column('condition', String(128)),
            Column('price', Integer),
            Column('size', String(128)),
            Column('sold', Integer),
            Column('deleted', Boolean, default=False)
        )
        meta.create_all(engine)
    else:
        products = Table("products", MetaData(bind=get_engine()), autoload=True)
        run_query(delete(products), commit=True)

    if not inspect(engine).has_table('product_images'):
        meta = MetaData()
        Table(
            'product_images',
            meta,
            Column('id_product_images', String, primary_key=True, unique=True),
            Column('product_id', String(128)),
            Column('image', String(128))
        )
        meta.create_all(engine)
    else:
        product_images = Table("product_images", MetaData(bind=get_engine()), autoload=True)
        run_query(delete(product_images), commit=True)

    if not inspect(engine).has_table('carts'):
        meta = MetaData()
        Table(
            'carts',
            meta,
            Column('id_cart', String, primary_key=True, unique=True),
            Column('user_id', String(128)),
            Column('product_id', String(128)),
            Column('quantity', Integer),
            Column('size', String(128)),
            Column('deleted', Boolean, default=False),
            Column('order_id', String(128))
        )
        meta.create_all(engine)
    else:
        carts = Table("carts", MetaData(bind=get_engine()), autoload=True)
        run_query(delete(carts), commit=True)

    if not inspect(engine).has_table('orders'):
        meta = MetaData()
        Table(
            'orders',
            meta,
            Column('id_order', String, primary_key=True, unique=True),
            Column('user_id', String(128)),
            Column('shipping_method', String(64)),
            Column('shipping_price', Integer),
            Column('total_product_price', Integer),
            Column('created_at', String(128)),
            Column('status', String(128)),
        )
        meta.create_all(engine)
    else:
        orders = Table("orders", MetaData(bind=get_engine()), autoload=True)
        run_query(delete(orders), commit=True)

    # Universal Endpoints
    @app.route("/image/<image_name>", methods=["GET"])
    def get_image(image_name):
        extension = image_name.split(".")
        extension = extension[len(extension)-1]
        return send_file(f"img/{image_name}", mimetype=f'image/{extension}')

    @app.errorhandler(Exception)
    def invalid_enpoint(e):
        return jsonify({"message": str(e)})

    return app


app = create_app()


# Uncomment this before deploy
if __name__ == "__main__":
    app.run(debug=True)