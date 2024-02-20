import uuid

from flask import Blueprint, request, json
from sqlalchemy import MetaData, Table, and_, delete, or_, insert, select, update
from utils import get_engine, run_query

# this means that you can group all endpoints with prefix "/categories" together
categories_bp = Blueprint("categories", __name__, url_prefix="/categories")

@categories_bp.route("", methods=["GET"])
def get_category():
    # IMPLEMENT THIS
    categories = Table("categories", MetaData(bind=get_engine()), autoload=True)
    category = run_query(select(categories).where(categories.c.deleted == False))

    data = []
    for i in range(len(category)):
        data_temp = {}
        data_temp["id"] = category[i]["id_category"]
        data_temp["title"] = category[i]["category_name"]
        data.append(data_temp)
    
    return {"data": data}, 200


@categories_bp.route("", methods=["POST"])
def create_category():
    # IMPLEMENT THIS
    header = request.headers
    token = header.get("Authentication")
    body = json.loads(request.data)
    category_name = body.get("category_name")

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    user = run_query(select(users).where(and_(users.c.token == token, users.c.type == "seller")))
    
    if len(user) == 0:
        return {"message": "error, user is invalid"}, 400
    else:
        categories = Table("categories", MetaData(bind=get_engine()), autoload=True)
        category = run_query(select(categories).where(and_(categories.c.category_name == category_name, categories.c.deleted == False)))
        if len(category) != 0:
            return {"message": "error, Category is already exists"}, 409
        else:
            body["id_category"] = str(uuid.uuid4())
            body["deleted"] = False
            run_query(insert(categories).values(body), commit=True)
            return {"message": "Category added"}, 201
    
    # CONDITION
    """
    - if user not seller or token invalid
        - {"message": "error, user is invalid"}, 400
    - if category name is alraedy exist
        - {"message": "error, Category is already exists"}, 409
    """


@categories_bp.route("/<category_id>", methods=["PUT"])
def update_category(category_id):
    # IMPLEMENT THIS
    header = request.headers
    token = header.get("Authentication")
    body = json.loads(request.data)
    category_name = body.get("category_name")

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    user = run_query(select(users).where(and_(users.c.token == token, users.c.type == "seller")))
    
    if len(user) == 0:
        return {"message": "error, user is invalid"}, 400
    else:
        categories = Table("categories", MetaData(bind=get_engine()), autoload=True)
        category = run_query(select(categories).where(and_(categories.c.category_name == category_name, categories.c.deleted == False)))
        if len(category) != 0:
            return {"message": "error, category is already exists"}, 409
        else :
            run_query(update(categories).values({"category_name": category_name}).where(categories.c.id_category == category_id), commit=True)
            return {"message": "Category updated"}, 200

     # CONDITION
    """
    - if user not seller or token invalid
        - {"message": "error, user is invalid"}, 400
    - if category_name is alraedy exist
        - {"message": "error, Category is already exists"}, 409
    """

@categories_bp.route("/<category_id>", methods=["DELETE"])
def delete_category(category_id):
    # IMPLEMENT THIS
    header = request.headers
    token = header.get("Authentication")

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    user = run_query(select(users).where(and_(users.c.token == token, users.c.type == "seller")))
    
    if len(user) == 0:
        return {"message": "error, user is invalid"}, 400
    else:
        categories = Table("categories", MetaData(bind=get_engine()), autoload=True)
        category = run_query(select(categories).where(categories.c.id_category == category_id))
        if len(category) == 0:
            return {"message": "error, id_category is invalid"}, 400
        else :
            run_query(update(categories).values({"deleted": True}).where(categories.c.id_category == category_id), commit=True)
            return {"message": "Category deleted"}, 200

    # CONDITION
    """
    - if user not seller or token invalid
        - {"message": "error, user is invalid"}, 400
    - if id_category doesn't exist then create new category
        - {"message": "error, id_category is invalid"}, 400
    - if everything is valid then delete category and update category_id in products
    """