import base64
from io import BytesIO
import random
import string
import uuid

from flask import Blueprint, request, json
from sqlalchemy import (MetaData, Table, and_, asc, or_, delete, desc, insert,
                        select, update)
from utils import get_engine, run_query
from PIL import Image
from model.main import Main

# this means that you can group all endpoints with prefix "/products" together
products_bp = Blueprint("products", __name__, url_prefix="/products")


@products_bp.route("", methods=["GET"])
def get_product():
    # IMPLEMENT THIS
    args = request.args
    sort_by = args.get("sort_by")
    category = args.get("category")
    product_name = args.get("product_name")
    condition = args.get("condition")
    page = args.get("page")
    page_size = args.get("page_size")
    price = args.get("price")

    products = Table("products", MetaData(bind=get_engine()), autoload=True)
    product_images = Table("product_images", MetaData(bind=get_engine()), autoload=True)

    if len(args) == 0 :
        product = run_query(select(products).where(products.c.deleted == False))
        data = []
        for i in range(len(product)):
            product_image = run_query(select(product_images).where(product_images.c.product_id == product[i]["id_product"]))
            if len(product_image) == 0 :
                img = "/image/image.jpg"
            else :
                img = product_image[0]["image"]
            data_temp = {}
            data_temp["id"] = product[i]["id_product"]
            data_temp["title"] = product[i]["product_name"]
            data_temp["price"] = product[i]["price"]
            data_temp["image"] = img
            data.append(data_temp)
        
        return {"data": data}, 200
    
    else :
        if category == None and product_name == "undefined" and condition == None and price == None:
            product_list = []

        elif product_name != None and condition != None:
            if product_name != "undefined":
                product_name = (products.c.product_name == product_name)
            else :
                product_name = (products.c.deleted == False)

            if condition != None:
                condition = condition.split(",")
                if len(condition) == 1:
                    condition = (products.c.condition == condition[0])
                else:
                    condition = (or_(products.c.condition == condition[0], products.c.condition == condition[1]))
            else :
                condition = (products.c.deleted == False)

            if category != None:
                product_list = []
                category = category.split(",")
                for i in range(len(category)):
                    product = run_query(select(products).where(and_(condition, product_name, products.c.category_id == category[i], products.c.deleted == False)))
                    for x in product:
                        product_list.append(x)
            else:
                product_list = run_query(select(products).where(and_(condition, product_name, products.c.deleted == False)))

            if sort_by == "Price a_z":
                product_list = sorted(product_list, key=lambda d: d['price']) 
            else:
                product_list = sorted(product_list, key=lambda d: d['price'], reverse=True)
                product_list[0:(int(page)*int(page_size))]
            
        else:
            if price != None:
                price = price.split(",")
                if category != None:
                    category = category.split(",")
                    product_list = []
                    for i in range(len(category)):
                        product = run_query(select(products).where(and_(products.c.category_id == category[i], products.c.price >= price[0], products.c.price <= price[1], products.c.deleted == False)))
                        for x in product:
                            product_list.append(x)
                else:
                    product_list = run_query(select(products).where(and_(products.c.price >= price[0], products.c.price <= price[1], products.c.deleted == False)))
                
                if sort_by == "Price a_z":
                    product_list = sorted(product_list, key=lambda d: d['price']) 
                else:
                    product_list = sorted(product_list, key=lambda d: d['price'], reverse=True)
                    product_list[0:(int(page)*int(page_size))]
            else:
                if category != None:
                    category = category.split(",")
                    product_list = []
                    for i in range(len(category)):
                        product = run_query(select(products).where(and_(products.c.category_id == category[i], products.c.deleted == False)))
                        for x in product:
                            product_list.append(x)
                else:
                    product_list = run_query(select(products).where(and_(products.c.deleted == False)))  

                if sort_by == "Price a_z":
                    product_list = sorted(product_list, key=lambda d: d['price']) 
                else:
                    product_list = sorted(product_list, key=lambda d: d['price'], reverse=True)
                    product_list[0:(int(page)*int(page_size))]

        data = []
        for i in range(len(product_list)):
            dict = {}

            image = run_query(select(product_images).where(product_images.c.product_id == product_list[i]["id_product"]))

            if len(image) == 0 :
                img = "/image/imgage.jpg"
            else :
                dict["image"] = image[0]["image"]

            dict["id"] = product_list[i]["id_product"]
            dict["title"] = product_list[i]["product_name"]
            dict["price"] = product_list[i]["price"]

            data.append(dict)

        return {"data": data, "total_rows": len(product_list)}, 200


@products_bp.route("", methods=["POST"])
def create_product():
    # IMPLEMENT THIS
    header = request.headers
    token = header.get("Authentication")
    body = json.loads(request.data)
    product_name = body.get('product_name')
    description = body.get('description')
    images = body.get('images')
    condition = body.get('condition')
    category_id = body.get('category')
    price = body.get('price')

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    user = run_query(select(users).where(and_(users.c.token == token, users.c.type == "seller")))

    if len(user) == 0:
        return {"message": "error, user is invalid"}, 400
    else:
        products = Table("products", MetaData(bind=get_engine()), autoload=True)
        product = run_query(select(products).where(and_(products.c.category_id == category_id, products.c.product_name == product_name, products.c.condition == condition, products.c.deleted == False)))
        if len(product) != 0 :
            return {"message": "error, Product is already exists"}, 409
        else:
            categories = Table("categories", MetaData(bind=get_engine()), autoload=True)
            category = run_query(select(categories.c.id_category).where(categories.c.id_category == category_id))
            if len(category) == 0:
                return {"message": "error, id_category is invalid"}, 400
            else :
                data = {
                    'id_product': str(uuid.uuid4()),
                    'category_id': category_id,
                    'product_name': product_name,
                    'description': description,
                    'condition': condition,
                    'price': price,
                    'size': "S, M, L, XL",
                    'sold': 0,
                    'deleted': False
                }
                run_query(insert(products).values(data), commit=True)

                if images :
                    product_images = Table("product_images", MetaData(bind=get_engine()), autoload=True)
                    for image in images:
                        base64_bytes = image.split(',')
                        imag = bytes(base64_bytes[1], encoding="ascii")
                        file_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20)) + f".{base64_bytes[0].split('/')[1].split(';')[0]}"

                        img = Image.open(BytesIO(base64.b64decode(imag)))
                        img.save('img/'+f'{file_name}')
        
                        run_query(insert(product_images).values({'id_product_images': str(uuid.uuid4()), "product_id": data["id_product"], "image": f"/image/{file_name}"}), commit=True)
                        
                return {"message": "Product added"}, 201
    # CONDITION
    """
    - if user not seller or token invalid
        - {"message": "error, user is invalid"}, 400
    - if product is alraedy exist (check product_name, product_category, condition)
        - {"message": "error, product is already exists"}, 409
    - if category_id is invalid
        - {"message": "error, id_category is invalid"}, 400
    """


@products_bp.route("", methods=["PUT"])
def update_product():
    # IMPLEMENT THIS
    header = request.headers
    token = header.get("Authentication")
    body = json.loads(request.data)
    product_name = body.get('product_name')
    description = body.get('description')
    images = body.get('images')
    condition = body.get('condition')
    category_id = body.get('category')
    price = body.get('price')
    product_id = body.get("product_id")

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    user = run_query(select(users).where(and_(users.c.token == token, users.c.type == "seller")))

    if len(user) == 0:
        return {"message": "error, user is invalid"}, 400
    else:
        products = Table("products", MetaData(bind=get_engine()), autoload=True)
        product = run_query(select(products).where(and_(products.c.category_id == category_id, products.c.product_name == product_name, products.c.condition == condition, products.c.deleted == False)))
        if len(product) != 0 :
            return {"message": "error, Product is already exists"}, 409
        else:
            products = Table("products", MetaData(bind=get_engine()), autoload=True)
            product = run_query(select(products).where(products.c.id_product == product_id))
            if len(product) == 0 :
                return {"message": "error, id_product is invalid"}, 400
            else :
                data = {
                    'id_product': product_id,
                    'category_id': category_id,
                    'product_name': product_name,
                    'description': description,
                    'condition': condition,
                    'price': price
                }
                run_query(update(products).values(data).where(products.c.id_product == product_id), commit=True)
                
                if images :
                        product_images = Table("product_images", MetaData(bind=get_engine()), autoload=True)
                        for image in images:
                            try:
                                base64_bytes = image.split(',')
                                imag = bytes(base64_bytes[1], encoding="ascii")
                                file_name = ''.join(random.choices(string.ascii_lowercase + string.digits, k=20)) + f".{base64_bytes[0].split('/')[1].split(';')[0]}"

                                img = Image.open(BytesIO(base64.b64decode(imag)))
                                img.save('img/'+f'{file_name}')
                                
                                run_query(delete(product_images).where(product_images.c.product_id == product_id), commit=True)
                                run_query(insert(product_images).values({'id_product_images': str(uuid.uuid4()), "product_id": product_id, "image": f"/image/{file_name}"}), commit=True)
                            except:
                                images == None
                return {"message": "Product updated"}, 200
    # CONDITION
    """
    - if user not seller or token invalid
        - {"message": "error, user is invalid"}, 400
    - if product is alraedy exist (check product_name, product_category, condition)
        - {"message": "error, product is already exists"}, 409
    - if category_id is invalid
        - {"message": "error, id_category is invalid"}, 400
    - if product_id is invalid
        - {"message": "error, id_product is invalid"}, 400
    """


@products_bp.route("/<product_id>", methods=["GET"])
def get_product_details(product_id):
    # IMPLEMENT THIS
    products = Table("products", MetaData(bind=get_engine()), autoload=True)
    product = run_query(select(products).where(products.c.id_product == product_id))

    categories = Table("categories", MetaData(bind=get_engine()), autoload=True)
    category = run_query(select(categories).where(categories.c.id_category == product[0]["category_id"]))

    product_images = Table("product_images", MetaData(bind=get_engine()), autoload=True)
    product_image = run_query(select(product_images).where(product_images.c.product_id == product_id))

    list_image = []

    for i in range(len(product_image)):
        list_image.append(product_image[i]["image"])

    size = str(product[0]["size"])
    list_size = size.split(", ")

    return {
        "data": {
            "id": product[0]["id_product"],
            "title": product[0]["product_name"],
            "size": list_size,
            "product_detail": product[0]["description"],
            "price": product[0]["price"],
            "images_url": list_image,
            "category_id": product[0]["category_id"],
            "category_name": category[0]["category_name"],
        }
    }, 200

@products_bp.route("/search_image", methods=["POST"])
def search_image():
    # IMPLEMENT THIS
    # body = json.loads(request.data)
    body = request.json
    image = body.get('image')

    model_img = Main(img_input=image)
    result = model_img.get_results
    return {"data": result}, 200

@products_bp.route("/<product_id>", methods=["DELETE"])
def delete_product(product_id):
    # IMPLEMENT THIS
    header = request.headers
    token = header.get("Authentication")

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    user = run_query(select(users).where(and_(users.c.token == token, users.c.type == "seller")))

    if len(user) == 0:
        return {"message": "error, user is invalid"}, 400
    else:
        products = Table("products", MetaData(bind=get_engine()), autoload=True)
        product = run_query(select(products).where(products.c.id_product == product_id))
        if len(product) == 0 :
            return {"message": "error, Product is not exists"}, 400
        else:
            run_query(update(products).values({"deleted": True}).where(products.c.id_product == product_id), commit=True)
            return {"message": "Product deleted"}, 200

    # CONDITION
    """
    - if user not seller or token invalid
        - {"message": "error, user is invalid"}, 400
    - if product is not exist
        - {"message": "error, Product is not exists"}, 400
    """
