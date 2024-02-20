from flask import Blueprint
from sqlalchemy import MetaData, Table, and_, select, desc
from utils import get_engine, run_query

# this means that you can group all endpoints with prefix "/home" together
home_bp = Blueprint("home", __name__, url_prefix="/home")

@home_bp.route("/banner", methods=["GET"])
def get_banner():
    # IMPLEMENT THIS
    products = Table("products", MetaData(bind=get_engine()), autoload=True)
    most_sold_products = run_query(select(products).where(products.c.deleted == False).limit(3).order_by(desc(products.c.sold)))

    product_images = Table("product_images", MetaData(bind=get_engine()), autoload=True)
    data = []
    for i in range(len(most_sold_products)):
        product_image = run_query(select(product_images).where(product_images.c.product_id == most_sold_products[i]["id_product"]))
        if len(product_image) == 0 :
            img = "/image/image.jpg"
        else :
            img = product_image[0]["image"]
        data_temp = {}
        data_temp["id"] = most_sold_products[i]["id_product"]
        data_temp["image"] = img
        data_temp["title"] = most_sold_products[i]["product_name"]
        data.append(data_temp)
    
    return {"data": data}, 200


@home_bp.route("/category", methods=["GET"])
def get_category():
    # IMPLEMENT THIS
    categories = Table("categories", MetaData(bind=get_engine()), autoload=True)
    category = run_query(select(categories).where(categories.c.deleted == False))

    products = Table("products", MetaData(bind=get_engine()), autoload=True)
    product_images = Table("product_images", MetaData(bind=get_engine()), autoload=True)

    data = []
    for i in range(len(category)):
        product = run_query(select(products).where(and_(products.c.category_id == category[i]["id_category"], products.c.deleted == False)))
        if len(product) == 0 :
            img = "/image/image.jpg"
        else :
            product_image = run_query(select(product_images).where(product_images.c.product_id == product[0]["id_product"]))
            if len(product_image) == 0 :
                img = "/image/image.jpg"
            else :
                img = product_image[0]["image"]
        data_temp = {}
        data_temp["id"] = category[i]["id_category"]
        data_temp["image"] = img
        data_temp["title"] = category[i]["category_name"]
        data.append(data_temp)
    
    return {"data": data}, 200
