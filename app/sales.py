from flask import Blueprint, request
from sqlalchemy import MetaData, Table, and_, delete, insert, select, update
from utils import get_engine, run_query

# this means that you can group all endpoints with prefix "/sales" together
sales_bp = Blueprint("sales", __name__, url_prefix="/sales")


@sales_bp.route("", methods=["GET"])
def get_total_sales():
    # IMPLEMENT THIS
    headers = request.headers
    token = headers.get("Authentication")

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    user = run_query(select(users).where(
        and_(users.c.token == token, users.c.type == "seller")))

    if len(user) == 0:
        return {"message": "error, user is invalid"}, 400
    else :
        return {
            "data": {
                "total": user[0]["balance"]
            }
        }, 200