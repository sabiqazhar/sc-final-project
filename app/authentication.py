import secrets
import uuid

import jwt
from flask import Blueprint, request
from passlib.hash import sha256_crypt
from sqlalchemy import MetaData, Table, insert, or_, select, update
from utils import get_engine, run_query

# this means that you can group all endpoints with prefix "/sign-up" together
signup_bp = Blueprint("signup", __name__, url_prefix="/sign-up")

@signup_bp.route("", methods=["POST"])
def sign_up():
    # IMPLEMENT THIS
    body = request.json
    name = body.get("name")
    password = body.get("password")
    email = body.get("email")

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    user = run_query(select(users).where(or_(users.c.name == name, users.c.email == email)))
    
    if len(password) < 8:
        return {"error": "Password must contain at least 8 characters"}, 400
    elif any(char.islower() for char in password) == False:
        return {"error": "Password must contain a lowercase letter"}, 400
    elif any(char.isupper() for char in password) == False:
        return {"error": "Password must contain an uppercase letter"}, 400
    elif any(char.isdigit() for char in password) == False:
        return {"error": "Password must contain a number"}, 400
    elif len(user) != 0:
        return {"message": "error, user already exists"}, 409
    else:
        password_hash = sha256_crypt.hash(password)
        body["id_user"] = str(uuid.uuid4())
        body["type"] = "buyer"
        body["password"] = password_hash
        body["balance"] = 0
        run_query(insert(users).values(body), commit=True)
        return {"message": "success, user created"}, 201

    # CONDITION
    """
    - Password needs to satisfy certain standard:
        - contains >= 8 characters
        - contains >= 1 lowercase letter
        - contains >= upercase letter 
        - contains a number
    - Cannot register existing user check by name and email
    """



# this means that you can group all endpoints with prefix "/sign-in" together
signin_bp = Blueprint("signin", __name__, url_prefix="/sign-in")

@signin_bp.route("", methods=["POST"])
def sign_in():
    # IMPLEMENT THIS
    body = request.json
    email = body.get("email")
    password = body.get("password")

    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    user = run_query(select(users).where(users.c.email == email))

    if (len(user) == 0):
        return {"message": "error, Email or password is incorrect"}, 401
    else:
        verify = sha256_crypt.verify(password, user[0]["password"])
        if verify == False:
            return {"message": "error, Email or password is incorrect"}, 401
        else:
            key = secrets.token_hex(16)
            token = str(jwt.encode({"email": user[0]['email'], "type:": user[0]['type']}, key, "HS256"))
            run_query(update(users).where(users.c.email == email).values({"token": token}), commit=True)
            return {
                "user_information":
                    {
                        "name": user[0]['name'],
                        "email": user[0]['email'],
                        "phone_number": user[0]['phone_number'],
                        "type": user[0]['type']
                    },
                "token": token,
                "message": "Login success"
            }, 200