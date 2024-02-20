import base64
import traceback
import uuid
from functools import wraps

from passlib.hash import sha256_crypt
from sqlalchemy import MetaData, Table, delete, insert, select, update
from utils import get_engine, run_query

##############################################################################################
# Helpers
##############################################################################################


def test(f: callable):
    @wraps(f)
    def dec(*args, **kwargs):
        print("-" * 100)
        print(f.__name__)
        print("-" * 100)
        global MAX_SCORE, FINAL_SCORE
        MAX_SCORE, FINAL_SCORE = 0, 0
        try:
            f(*args, **kwargs)
        finally:
            res = FINAL_SCORE, MAX_SCORE
            # reset final score before returning
            FINAL_SCORE = 0
            return res

    return dec


def assert_eq_dict(expression, expected: dict) -> bool:
    if not isinstance(expression, dict):
        return False

    for k in expected:
        if k not in expression:
            return False

    for k, v in expression.items():
        if k not in expected:
            return False
        if v != expected[k]:
            return False

    return True


def assert_eq(
    expression, expected, exc_type=AssertionError, hide: bool = False, err_msg=None
):
    try:
        if isinstance(expected, dict):
            if assert_eq_dict(expression, expected):
                return
        elif expression == expected:
            return

        errs = [err_msg] if err_msg else []
        if hide:
            expected = "<hidden>"
        err = "\n".join(
            [*errs, f"> Expected: {expected}", f"> Yours: {expression}"])
        raise exc_type(err)
    except Exception:
        raise


# https://www.lihaoyi.com/post/BuildyourownCommandLinewithANSIescapecodes.html
class COL:
    PASS = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    BLUE = "\033[94m"
    UNDERLINE = "\033[4m"


# special exception when something should've been printed, but wasn't
class DisplayError(Exception):
    pass


class Scorer:
    def __enter__(self):
        pass

    def __init__(self, score: float, desc: str):
        self.score = score
        global MAX_SCORE
        MAX_SCORE += score
        print(f"{COL.BOLD}{desc}{COL.ENDC} ({self.score} pts)")

    def __exit__(self, exc_type, exc_value, exc_tb):
        # add maximum score when passing these statements, otherwise 0
        if not exc_type:
            global FINAL_SCORE
            FINAL_SCORE += self.score
            print(COL.PASS, f"\tPASS: {self.score} pts", COL.ENDC)
        else:
            err_lines = [exc_type.__name__, *str(exc_value).split("\n")]
            errs = [
                "\t" + (" " * 4 if index else "") + line
                for index, line in enumerate(err_lines)
            ]
            print("{}{}".format(COL.WARNING, "\n".join(errs)))
            print(f"\t{COL.FAIL}FAIL: 0 pts", COL.ENDC)

        # skip throwing the exception
        return True


class safe_init:
    def __enter__(self):
        pass

    def __init__(self, max_score: int):
        self.max_score = max_score

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type:
            print(traceback.format_exc())
            global MAX_SCORE
            MAX_SCORE = self.max_score
            return False

        return True


##############################################################################################
# Actual Tests
##############################################################################################


def assert_response(
    c,
    method: str,
    endpoint: str,
    json: dict = None,
    exp_json=None,
    exp_code: int = None,
    headers: dict = None,
):
    if not headers:
        headers = {}

    response = getattr(c, method)(endpoint, json=json, headers=headers)
    assert_eq(response.json, exp_json)
    assert_eq(response.status_code, exp_code)
    return response.json


class IsString:
    def __eq__(self, other):
        return isinstance(other, str)

    def __repr__(self):
        return "<must_be_a_string>"


def gen_uuid():
    # representative from each
    id = uuid.uuid4()
    return id


@test
def test_end_to_end():
    with safe_init(100):
        from app import app

        app.config.update({"TESTING": True})
        c = app.test_client()
    
    ##############################################################################################
    # Inserting Data Dummy For Testing Part 1
    ##############################################################################################
    
    # Delete seed
    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    run_query(delete(users), commit=True)
    categories = Table("categories", MetaData(bind=get_engine()), autoload=True)
    run_query(delete(categories), commit=True)
    products = Table("products", MetaData(bind=get_engine()), autoload=True)
    run_query(delete(products), commit=True)
    product_images = Table("product_images", MetaData(bind=get_engine()), autoload=True)
    run_query(delete(product_images), commit=True)

    # Table Users
    users = Table("users", MetaData(bind=get_engine()), autoload=True)
    user_data = {
            "id_user": f"{gen_uuid()}",
            "name": "Tristan Hans Pratama",
            "email": "tristanpratama7@gmail.com",
            "phone_number": "087734738379", 
            "password": f"{sha256_crypt.hash('Password123')}",
            "type" : "seller",
            "balance" : 100000
        }
    run_query(insert(users).values(user_data), commit=True)


    # Table Categories
    categories = Table("categories", MetaData(bind=get_engine()), autoload=True)
    categories_data = [
        {   
            "id_category": f"{gen_uuid()}",
            "category_name": "Jacket",
            "deleted": False,
        },
        {   
            "id_category": f"{gen_uuid()}",
            "category_name": "Hoodie",
            "deleted": False,
        },
        {   
            "id_category": f"{gen_uuid()}",
            "category_name": "Shirt",
            "deleted": False,
        },
        {   
            "id_category": f"{gen_uuid()}",
            "category_name": "T-Shirt",
            "deleted": False,
        }
    ]
    run_query(insert(categories).values(categories_data), commit=True)

    # Tabel Product
    categories = Table("categories", MetaData(bind=get_engine()), autoload=True)
    category = run_query(select(categories))
    products = Table("products", MetaData(bind=get_engine()), autoload=True)
    for i in range(len(category)):
        products_data = [
            {
                "id_product": f"{gen_uuid()}",
                "category_id": f"{category[i]['id_category']}",
                "product_name": f"Product {i+1} {category[i]['category_name']}",
                "description": f"This is description of Product {i+1}",
                "condition": "new",
                "price": 75000,
                "size": "S, M, L, XL",
                "sold": i+1,
                "deleted": False,
            },
            {
                "id_product": f"{gen_uuid()}",
                "category_id": f"{category[i]['id_category']}",
                "product_name": f"Product {i+1} {category[i]['category_name']}",
                "description": f"This is description of Product {i+1}",
                "condition": "used",
                "price": 175000,
                "size": "S, M, L, XL",
                "sold": i+1,
                "deleted": False,
            },
        ]
        run_query(insert(products).values(products_data), commit=True)

    # Tabel Product Images
    products = Table("products", MetaData(bind=get_engine()), autoload=True)
    product = run_query(select(products))
    product_images = Table("product_images", MetaData(bind=get_engine()), autoload=True)
    for i in range(len(product)):
        product_images_data = {
            "id_product_images": f"{gen_uuid()}",
            "product_id": f"{product[i]['id_product']}",
            "image": f"/image/img_product{i+1}.jpg"
        }
        run_query(insert(product_images).values(product_images_data), commit=True)


    ##############################################################################################
    # Start Testing Each Endpoint
    ##############################################################################################

    IP_ADDRESS = "http://34.142.244.100:5000"

    with Scorer(1, "Testing for Get Image"):
        image_name = "img_product8.jpg"
        assert_response(
            c,
            "get",
            f"{IP_ADDRESS}/image/{image_name}",
            exp_code=200,
        )

    with Scorer(1, "Testing for Get Banner"):
        assert_response(
            c,
            "get",
            f"{IP_ADDRESS}/home/banner",
            exp_json={
                'data': [
                    {
                        'id': IsString(), 
                        'image': '/image/img_product7.jpg',
                        'title': 'Product 4 T-Shirt'
                    }, 
                    {
                        'id': IsString(),
                        'image': '/image/img_product8.jpg',
                        'title': 'Product 4 T-Shirt'
                    }, 
                    {
                        'id': IsString(),
                        'image': '/image/img_product3.jpg',
                        'title': 'Product 3 Shirt'
                    }
                ]
            },
            exp_code=200,
        )

    with Scorer(1, "Testing for Get Category"):
        assert_response(
            c,
            "get",
            f"{IP_ADDRESS}/home/category",
            exp_json={
                'data': [
                    {
                        'id': IsString(),
                        'image': '/image/img_product1.jpg',
                        'title': 'Jacket'
                    }, 
                    {
                        'id': IsString(),
                        'image': '/image/img_product5.jpg',
                        'title': 'Hoodie'
                    }, 
                    {
                        'id': IsString(),
                        'image': '/image/img_product3.jpg',
                        'title': 'Shirt'
                    },
                    {
                        'id': IsString(),
                        'image': '/image/img_product7.jpg',
                        'title': 'T-Shirt'
                    }
                ]
            },
            exp_code=200,
        )

    with Scorer(1, "Testing for Sign-up"):
        # valid case
        assert_response(
            c,
            "post",
            f"{IP_ADDRESS}/sign-up",
            json={"name": "Raihan Parlaungan", "email": "raihan@gmail.com",
                  "phone_number": "081380737126", "password": "Password1234"},
            exp_json={
                "message": "success, user created"},
            exp_code=201,
        )
        # valid case
        assert_response(
            c,
            "post",
            f"{IP_ADDRESS}/sign-up",
            json={"name": "Raymond Christoper", "email": "raymond@gmail.com",
                  "phone_number": "081280737123", "password": "Password5678"},
            exp_json={
                "message": "success, user created"},
            exp_code=201,
        )
        # error password less than 8
        assert_response(
            c,
            "post",
            f"{IP_ADDRESS}/sign-up",
            json={"name": "Raihan Parlaungan", "email": "raihan7@gmail.com",
                  "phone_number": "081380737126", "password": "Pasw12"},
            exp_json={
                "error": "Password must contain at least 8 characters"},
            exp_code=400,
        )
        # error password no upppercase
        assert_response(
            c,
            "post",
            f"{IP_ADDRESS}/sign-up",
            json={"name": "Raihan Parlaungan", "email": "raihan7@gmail.com",
                  "phone_number": "081380737126", "password": "password1234"},
            exp_json={
                "error": "Password must contain an uppercase letter"},
            exp_code=400,
        )
        # error password no lowercase
        assert_response(
            c,
            "post",
            f"{IP_ADDRESS}/sign-up",
            json={"name": "Raihan Parlaungan", "email": "raihan7@gmail.com",
                  "phone_number": "081380737126", "password": "PASSWORD1234"},
            exp_json={
                "error": "Password must contain a lowercase letter"},
            exp_code=400,
        )
        # error password no number
        assert_response(
            c,
            "post",
            f"{IP_ADDRESS}/sign-up",
            json={"name": "Raihan Parlaungan", "email": "raihan7@gmail.com",
                  "phone_number": "081380737126", "password": "Passworddd"},
            exp_json={
                "error": "Password must contain a number"},
            exp_code=400,
        )
        # duplicat name case
        assert_response(
            c,
            "post",
            f"{IP_ADDRESS}/sign-up",
            json={"name": "Raihan Parlaungan", "email": "raihan7@gmail.com",
                  "phone_number": "081380737126", "password": "Password1234"},
            exp_json={
                "message": "error, user already exists"},
            exp_code=409,
        )
        # duplicat email case
        assert_response(
            c,
            "post",
            f"{IP_ADDRESS}/sign-up",
            json={"name": "Raihan Parlaungan I", "email": "raihan@gmail.com",
                  "phone_number": "081380737126", "password": "Password1234"},
            exp_json={
                "message": "error, user already exists"},
            exp_code=409,
        )

    buyer_token = []
    seller_token = []

    with Scorer(1, "Testing for Sign-in"):
        # error email
        response = assert_response(
            c,
            "post",
            f"{IP_ADDRESS}/sign-in",
            json={"email": "raihan99@gmail.com", "password": "Password1233"},
            exp_json={"message": "error, Email or password is incorrect"},
            exp_code=401,
        )
        # error password
        response = assert_response(
            c,
            "post",
            f"{IP_ADDRESS}/sign-in",
            json={"email": "raihan@gmail.com", "password": "password1233"},
            exp_json={"message": "error, Email or password is incorrect"},
            exp_code=401,
        )
        # valid case
        response = assert_response(
            c,
            "post",
            f"{IP_ADDRESS}/sign-in",
            json={"email": "raihan@gmail.com", "password": "Password1234"},
            exp_json={
                "message": "Login success",
                "token": IsString(),
                "user_information":
                    {
                        "email": "raihan@gmail.com",
                        "name": "Raihan Parlaungan",
                        "phone_number": "081380737126",
                        "type": "buyer"
                    }
            },
            exp_code=200,
        )
        buyer_token.append(response["token"])
        # valid case
        response = assert_response(
            c,
            "post",
            f"{IP_ADDRESS}/sign-in",
            json={"email": "raymond@gmail.com", "password": "Password5678"},
            exp_json={
                "message": "Login success",
                "token": IsString(),
                "user_information":
                    {
                        "email": "raymond@gmail.com",
                        "name": "Raymond Christoper",
                        "phone_number": "081280737123",
                        "type": "buyer"
                    }
            },
            exp_code=200,
        )
        buyer_token.append(response["token"])
        # valid case
        response = assert_response(
            c,
            "post",
            f"{IP_ADDRESS}/sign-in",
            json={"email": "tristanpratama7@gmail.com", "password": "Password123"},
            exp_json={
                "message": "Login success",
                "token": IsString(),
                "user_information":
                    {
                        "email": "tristanpratama7@gmail.com",
                        "name": "Tristan Hans Pratama",
                        "phone_number": "087734738379",
                        "type": "seller"
                    }
            },
            exp_code=200,
        )
        seller_token.append(response["token"])

    # with Scorer(1, "Testing for Get Product List"):
    #     products = Table("products", MetaData(bind=get_engine()), autoload=True)
    #     product = run_query(select(products))
    #     product_id = product[0]["id_product"]
    #     product_category = product[0]["category_id"]
    #     sort_bies = ["Price a_z", "Price z_a"]
    #     prices = [0, 10000]
    #     for sort_by in sort_bies:
    #         for price in prices:
    #             assert_response(
    #                 c,
    #                 "get",
    #                 f"{IP_ADDRESS}/products",
    #                 f"/products?page=1&page_size=100&sort_by={sort_by}&category=id category b&price={price}&condition=used&product_name=Item B",
    #                 exp_json={
    #                     "message": "error, Item is not available"},
    #                 exp_code=400,
    #             )

    #             assert_response(
    #                 c,
    #                 "get",
    #                 f"{IP_ADDRESS}/products?page=1&page_size=100&sort_by={sort_by}&category=id category b&price={price}&condition=used&product_name=Item A",
    #                 exp_json={
    #                     "message": "error, Item is not available"},
    #                 exp_code=400,
    #             )

    #             assert_response(
    #                 c,
    #                 "get",
    #                 "/products",
    #                 f"{IP_ADDRESS}/products?page=1&page_size=100&sort_by={sort_by}&category={product_category}&price={price}&condition=used&product_name=Item B",
    #                 exp_json={
    #                     "message": "error, Item is not available"},
    #                 exp_code=400,
    #             )

    #             assert_response(
    #                 c,
    #                 "get",
    #                 f"{IP_ADDRESS}/products?page=1&page_size=100&sort_by={sort_by}&category={product_category}&price={price}&condition=used&product_name=Item A",
    #                 exp_json={
    #                     "data": [
    #                         {
    #                             "id": product_id,
    #                             "image": "/image/img_product.png",
    #                             "title": "Item A",
    #                             "price": 15000
    #                         }
    #                     ],
    #                     "total_rows": 1
    #                 },
    #                 exp_code=200,
    #             )

    # with Scorer(1, "Testing for Search Product by Image"):
    #     image_name = "/image/img_product.png"
    #     sample_string = image_name
    #     sample_string_bytes = sample_string.encode("ascii")
    #     base64_bytes = base64.b64encode(sample_string_bytes)
    #     base64_string = base64_bytes.decode("ascii")
    #     products = Table("products", MetaData(bind=get_engine()), autoload=True)
    #     product = run_query(select(products))
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/products/search_image?image={base64_string}",
    #         exp_json={"category_id": product[0]["category_id"]},
    #         exp_code=200,
    #     )

    # with Scorer(2, "Testing for Add to Cart"):
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/cart",
    #         json={"id": "item_id", "quantity": 10, "size": "M"},
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={"message": "Item added to cart"},
    #         exp_code=201,
    #     )

    # with Scorer(0.5, "Testing for Get User's Carts"):
    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/cart",
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={
    #             "data": [
    #                 {
    #                     "id": "uuid",
    #                     "details": {
    #                         "quantity": 100,
    #                         "size": "M"
    #                     },
    #                     "price": 10000,
    #                     "image": "/url/image.jpg",
    #                     "name": "Product a"
    #                 }
    #             ],
    #             "total_rows": 10
    #         },
    #         exp_code=200,
    #     )

    # with Scorer(2, "Testing for Get Shipping Price"):
    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/shipping_price",
    #         headers={"Authentication": "12345678"},
    #         exp_json={"message": "error, Unauthorized user"},
    #         exp_code=403,
    #     )

    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/shipping_price",
    #         headers={"Authentication": buyer_token[1]},
    #         exp_json={"message": "error, Cart is empty"},
    #         exp_code=400,
    #     )

    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/shipping_price",
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={
    #             "data": [
    #                 {
    #                     "name": "regular",
    #                     "price": 30000
    #                 },
    #                 {
    #                     "name": "next day",
    #                     "price": 20000
    #                 }
    #             ]
    #         },
    #         exp_code=200,
    #     )

    # with Scorer(1.5, "Testing for Create Order"):
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/order",
    #         json={"shipping_method": "Same day", "shipping_address":         {
    #             "name": "address name",
    #             "phone_number": "082713626",
    #             "address": "22, ciracas, east jakarta",
    #             "city": "Jakarta"
    #         }},
    #         headers={"Authentication": "12345678"},
    #         exp_json={"message": "error, Unauthorized user"},
    #         exp_code=403,
    #     )

    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/order",
    #         json={"shipping_method": "Same day", "shipping_address":         {
    #             "name": "address name",
    #             "phone_number": "082713626",
    #             "address": "22, ciracas, east jakarta",
    #             "city": "Jakarta"
    #         }},
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={"message": "error, Please top up 50000"},
    #         exp_code=400,
    #     )

    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/user/balance?amount=50000",
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={"message": "Top Up balance success"},
    #         exp_code=200,
    #     )

    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/order",
    #         json={"shipping_method": "Same day", "shipping_address":         {
    #             "name": "address name",
    #             "phone_number": "082713626",
    #             "address": "22, ciracas, east jakarta",
    #             "city": "Jakarta"
    #         }},
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={
    #             "data": [
    #                 {
    #                     "name": "regular",
    #                     "price": 30000
    #                 },
    #                 {
    #                     "name": "next day",
    #                     "price": 20000
    #                 }
    #             ]
    #         },
    #         exp_code=200,
    #     )

    # with Scorer(1, "Testing for Delete Cart Item"):
    #     assert_response(
    #         c,
    #         "delete",
    #         f"{IP_ADDRESS}/cart/cart_id",
    #         headers={"Authentication": "12345678"},
    #         exp_json={"message": "error, Unauthorized user"},
    #         exp_code=403,
    #     )

    #     assert_response(
    #         c,
    #         "delete",
    #         f"{IP_ADDRESS}/cart/cart_id",
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={"message": "Cart deleted"},
    #         exp_code=200,
    #     )

    # with Scorer(1, "Testing for User Details"):
    #     # valid case
    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/user",
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={
    #             "data":
    #                 {
    #                     "email": "raihan@gmail.com",
    #                     "name": "Raihan Parlaungan",
    #                     "phone_number": "081380737126"
    #                 }
    #         },
    #         exp_code=200,
    #     )
    #     # valid case
    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/user",
    #         headers={"Authentication": buyer_token[1]},
    #         exp_json={
    #             "data":
    #                 {
    #                     "email": "raymond@gmail.com",
    #                     "name": "Raymond Christoper",
    #                     "phone_number": "081280737123",
    #                 }
    #         },
    #         exp_code=200,
    #     )
    #     # # valid case
    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/user",
    #         headers={"Authentication": seller_token[0]},
    #         exp_json={
    #             "data":
    #                 {
    #                     "email": "tristanpratama7@gmail.com",
    #                     "name": "Tristan Hans Pratama",
    #                     "phone_number": "087734738379",
    #                 }
    #         },
    #         exp_code=200,
    #     )
    #     # invalid case
    #     token = f"{gen_uuid()}"
    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/user",
    #         headers={"Authentication": token},
    #         exp_json={"message": "error, user is invalid"},
    #         exp_code=400,
    #     )

    # ##############################################################################################
    # # Inserting Data Dummy For Testing Part 2
    # ##############################################################################################
    
    # # Table Shipping Address
    # users = Table("users", MetaData(bind=get_engine()), autoload=True)
    # user = run_query(select(users).where(users.c.type == "buyer"))

    # shipping_addresses = Table("shipping_addresses", MetaData(bind=get_engine()), autoload=True)
    # shipping_addresses_data = [
    #     {
    #         "id_address": f"{gen_uuid()}",
    #         "user_id": user[0]["id_user"],
    #         "name": user[0]["name"],
    #         "phone_number" : user[0]["phone_number"],
    #         "address": "22, ciracas, east jakarta",
    #         "city": "Jakarta",
    #     },
    #     {
    #         "id_address": f"{gen_uuid()}",
    #         "user_id": user[1]["id_user"],
    #         "name": user[1]["name"],
    #         "phone_number" : user[1]["phone_number"],
    #         "address": "02, wonokromo, south Surabaya",
    #         "city": "Surabaya",
    #     },
    # ]
    # run_query(insert(shipping_addresses).values(shipping_addresses_data), commit=True)

    # ##############################################################################################


    # with Scorer(0.5, "Testing for Get User's Shipping Address"):
    #     # valid case
    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/user/shipping_address",
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={
    #             "data":
    #                 {
    #                     "address": "22, ciracas, east jakarta",
    #                     "city": "Jakarta",
    #                     "id": IsString(),
    #                     "name": "Raihan Parlaungan",
    #                     "phone_number": "081380737126",
    #                 }
    #         },
    #         exp_code=200,
    #     )
    #     # valid case
    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/user/shipping_address",
    #         headers={"Authentication": buyer_token[1]},
    #         exp_json={
    #             "data":
    #                 {
    #                     "address": "02, wonokromo, south Surabaya",
    #                     "city": "Surabaya",
    #                     "id": IsString(),
    #                     "name": "Raymond Christoper",
    #                     "phone_number": "081280737123",
    #                 }
    #         },
    #         exp_code=200,
    #     )
    #     # invalid case
    #     token = f"{gen_uuid()}"
    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/user/shipping_address",
    #         headers={"Authentication": token},
    #         exp_json={"message": "error, user is invalid"},
    #         exp_code=400,
    #     )

    # with Scorer(1, "Testing for Change Shipping Address"):
    #     # change name in shipping address
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/user/shipping_address",
    #         headers={"Authentication": buyer_token[1]},
    #         json={
    #             "address": "02, wonokromo, south Surabaya",
    #             "city": "Surabaya",
    #             "name": "Christoper Raymond",
    #             "phone_number": "081280737123",
    #         },
    #         exp_json={
    #             "address": "02, wonokromo, south Surabaya",
    #             "city": "Surabaya",
    #             "name": "Christoper Raymond",
    #             "phone_number": "081280737123",
    #         },
    #         exp_code=200,
    #     )
    #     # change phone_number in shipping address
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/user/shipping_address",
    #         headers={"Authentication": buyer_token[1]},
    #         json={
    #             "address": "02, wonokromo, south Surabaya",
    #             "city": "Surabaya",
    #             "name": "Christoper Raymond",
    #             "phone_number": "087734738379",
    #         },
    #         exp_json={
    #             "address": "02, wonokromo, south Surabaya",
    #             "city": "Surabaya",
    #             "name": "Christoper Raymond",
    #             "phone_number": "087734738379",
    #         },
    #         exp_code=200,
    #     )
    #     # change address and city in shipping address
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/user/shipping_address",
    #         headers={"Authentication": buyer_token[1]},
    #         json={
    #             "address": "22, ciracas, east jakarta",
    #             "city": "Jakarta",
    #             "name": "Christoper Raymond",
    #             "phone_number": "087734738379",
    #         },
    #         exp_json={
    #             "address": "22, ciracas, east jakarta",
    #             "city": "Jakarta",
    #             "name": "Christoper Raymond",
    #             "phone_number": "087734738379",
    #         },
    #         exp_code=200,
    #     )
    #     # change address and city in shipping address
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/user/shipping_address",
    #         headers={"Authentication": seller_token[0]},
    #         json={
    #             "address": "09, pekalongan, central Java",
    #             "city": "Java",
    #             "name": "Tristan Hans Pratama",
    #             "phone_number": "087734738379",
    #         },
    #         exp_json={
    #             "address": "09, pekalongan, central Java",
    #             "city": "Java",
    #             "name": "Tristan Hans Pratama",
    #             "phone_number": "087734738379",
    #         },
    #         exp_code=200,
    #     )
    #     # invalid case
    #     token = f"{gen_uuid()}"
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/user/shipping_address",
    #         headers={"Authentication": token},
    #         json={
    #             "address": "09, pekalongan, central Java",
    #             "city": "Java",
    #             "name": "Tristan Hans Pratama",
    #             "phone_number": "087734738379",
    #         },
    #         exp_json={"message": "error, user is invalid"},
    #         exp_code=400,
    #     )

    # with Scorer(1, "Testing for Top-up Balance"):
    #     # valid case
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/user/balance?amount=100000",
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={"message": "Top Up balance success"},
    #         exp_code=200,
    #     )
    #     # valid case
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/user/balance?amount=100000",
    #         headers={"Authentication": buyer_token[1]},
    #         exp_json={"message": "Top Up balance success"},
    #         exp_code=200,
    #     )
    #     # invalid case
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/user/balance?amount=RP100000",
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={"message": "error, amount must be an integer"},
    #         exp_code=400,
    #     )
    #     # invalid case
    #     token = f"{gen_uuid()}"
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/user/balance?amount=100000",
    #         headers={"Authentication": token},
    #         exp_json={"message": "error, user is invalid"},
    #         exp_code=400,
    #     )

    # with Scorer(1, "Testing for Get User Balance"):
    #     # valid case
    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/user/balance",
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={
    #             "data":
    #                 {
    #                     "balance": 100000
    #                 }
    #         },
    #         exp_code=200,
    #     )
    #     # valid case
    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/user/balance",
    #         headers={"Authentication": buyer_token[1]},
    #         exp_json={
    #             "data":
    #                 {
    #                     "balance": 100000
    #                 }
    #         },
    #         exp_code=200,
    #     )
    #     # invalid case
    #     token = f"{gen_uuid()}"
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/user/balance?amount=100000",
    #         headers={"Authentication": token},
    #         exp_json={"message": "error, user is invalid"},
    #         exp_code=400,
    #     )
    #     # valid case top-up balance
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/user/balance?amount=100000",
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={"message": "Top Up balance success"},
    #         exp_code=200,
    #     )
    #     # valid case top-up balance
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/user/balance?amount=100000",
    #         headers={"Authentication": buyer_token[1]},
    #         exp_json={"message": "Top Up balance success"},
    #         exp_code=200,
    #     )
    #     # valid case
    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/user/balance",
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={
    #             "data":
    #                 {
    #                     "balance": 200000
    #                 }
    #         },
    #         exp_code=200,
    #     )
    #     # valid case
    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/user/balance",
    #         headers={"Authentication": buyer_token[1]},
    #         exp_json={
    #             "data":
    #                 {
    #                     "balance": 200000
    #                 }
    #         },
    #         exp_code=200,
    #     )
    
    # with Scorer(1, "Testing for Get Total Sales"):
    #     # invalid user case
    #     token = f"{gen_uuid()}"
    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/sales",
    #         headers={"Authentication": token},
    #         exp_json={"message": "error, user is invalid"},
    #         exp_code=400,
    #     )
    #     # invalid user case
    #     token = f"{gen_uuid()}"
    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/sales",
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={"message": "error, user is invalid"},
    #         exp_code=400,
    #     )
    #     # valid case
    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/sales",
    #         headers={"Authentication": seller_token[0]},
    #         exp_json={
    #             "data": {
    #                 "total": 100000
    #             }
    #         },
    #         exp_code=200,
    #     )

    # with Scorer(1, "Testing for User Orders"):
    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/order",
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={
    #             "data": [
    #                 {
    #                     "id": "uuid",
    #                     "created_at": "Mon, 22 august 2022",
    #                     "products": [
    #                         {
    #                             "id": "uuid",
    #                             "details": {
    #                                 "quantity": 100,
    #                                 "size": "M"
    #                             },
    #                             "price": 10000,
    #                             "image": "/url/image.jpg",
    #                             "name": "Product a"
    #                         }
    #                     ],
    #                     "shipping_method": "same day",
    #                     "status": "waiting",
    #                     "shipping_address": {
    #                         "name": "address name",
    #                         "phone_number": "082713626",
    #                         "address": "22, ciracas, east jakarta",
    #                         "city": "Jakarta"
    #                     }
    #                 }
    #             ]
    #         },
    #         exp_code=200,
    #     )

    # with Scorer(1, "Testing for Get Orders and Get Product"):
    #     for sort_by in sort_bies:
    #         assert_response(
    #             c,
    #             "get",
    #             f"{IP_ADDRESS}/orders?sort_by={sort_by}&page=1&page_size=25&is_admin=False",
    #             headers={"Authentication": buyer_token[0]},
    #             exp_json={"message": "error, user is not admin"},
    #             exp_code=400,
    #         )

    #         assert_response(
    #             c,
    #             "get",
    #             f"{IP_ADDRESS}/orders?sort_by={sort_by}&page=1&page_size=25&is_admin=True",
    #             headers={"Authentication": seller_token[0]},
    #             exp_json={
    #                 "data": [
    #                     {
    #                         "id": "uuid",
    #                         "created_at": "Mon, 22 august 2022",
    #                         "products": [
    #                             {
    #                                 "id": "uuid",
    #                                 "details": {
    #                                     "quantity": 100,
    #                                     "size": "M"
    #                                 },
    #                                 "price": 10000,
    #                                 "image": "/url/image.jpg",
    #                                 "name": "Product a"
    #                             }
    #                         ],
    #                         "shipping_method": "same day",
    #                         "status": "waiting",
    #                         "shipping_address": {
    #                             "name": "address name",
    #                             "phone_number": "082713626",
    #                             "address": "22, ciracas, east jakarta",
    #                             "city": "Jakarta"
    #                         }
    #                     }
    #                 ]
    #             },
    #             exp_code=200,
    #         )
    #         for price in prices:
    #             assert_response(
    #                 c,
    #                 "get",
    #                 f"{IP_ADDRESS}/products",
    #                 f"{IP_ADDRESS}/products?page=1&page_size=100&sort_by={sort_by}&category='id category c'&price={price}&condiction='used'&product_name='name'",
    #                 exp_json={
    #                     "message": "error, Item is not available"},
    #                 exp_code=400,
    #             )

    #             assert_response(
    #                 c,
    #                 "get",
    #                 f"{IP_ADDRESS}/products",
    #                 f"{IP_ADDRESS}/products?page=1&page_size=100&sort_by={sort_by}&category='id category c'&price={price}&condiction='used'&product_name='name1'",
    #                 exp_json={
    #                     "message": "error, Item is not available"},
    #                 exp_code=400,
    #             )
    #             for price in prices:
    #                 assert_response(
    #                     c,
    #                     "get",
    #                     f"{IP_ADDRESS}/products",
    #                     f"{IP_ADDRESS}/products?page=1&page_size=100&sort_by={sort_by}&category={category}&price={price}&condiction='used'&product_name='name1'",
    #                     exp_json={
    #                         "message": "error, Item is not available"},
    #                     exp_code=400,
    #                 )

    #                 assert_response(
    #                     c,
    #                     "get",
    #                     f"{IP_ADDRESS}/products?page=1&page_size=100&sort_by={sort_by}&category={category}&price={price}&condiction='used'&product_name='name'",
    #                     exp_json={
    #                         "data": [
    #                             {
    #                                 "id": "uuid",
    #                                 "image": "/something/image.png",
    #                                 "title": "Item A",
    #                                 "price": 15000
    #                             }
    #                         ],
    #                         "total_rows": 10
    #                     },
    #                     exp_code=200,
    #                 )

    # with Scorer(1, "Testing for Get Product Details"):
    #     products = Table("products", MetaData(bind=get_engine()), autoload=True)
    #     product = run_query(select(products))
    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/products/{product[0]['id_product']}",
    #         exp_json={
    #             "id": product[0]["id_product"],
    #             "category_id": product[0]["category_id"],
    #             "category_name": "Category A",
    #             "images_url": ["/image/img_product.png"],
    #             "price": 15000,
    #             "product_detail": "This is description of Item A",
    #             "size": ["XL", "S", "M"],
    #             "title": "Item A",
    #         },
    #         exp_code=200,
    #     )

    # with Scorer(2, "Testing for Create Product"):
    #     categories = Table("categories", MetaData(bind=get_engine()), autoload=True)
    #     category = run_query(select(categories))
    #     # valid case
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/products",
    #         json={"product_name": "Product 1", "description": "Lorem ipsum", "images": [
    #             "image_1", "image_2", "image_3"], "condition": "new", "size": "XL, S, M", "category": category[0]["id_category"], "price": 10000},
    #         headers={"Authentication": seller_token[0]},
    #         exp_json={"message": "Product added"},
    #         exp_code=201,
    #     )
    #     # invalid user case
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/products",
    #         json={"product_name": "Product 1", "description": "Lorem ipsum", "images": [
    #             "image_1", "image_2", "image_3"], "condition": "new", "category": category[0]["id_category"], "price": 10000},
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={"message": "error, user is invalid"},
    #         exp_code=400,
    #     )
    #     # invalid category_id case
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/products",
    #         json={"product_name": "Product 1", "description": "Lorem ipsum", "images": [
    #             "image_1", "image_2", "image_3"], "condition": "new", "category": "category_id", "price": 10000},
    #         headers={"Authentication": seller_token[0]},
    #         exp_json={"message": "error, id_category is invalid"},
    #         exp_code=400,
    #     )
    #     # invalid product case
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/products",
    #         json={"product_name": "Product 1", "description": "Lorem ipsum", "images": [
    #             "image_1", "image_2", "image_3"], "condition": "new", "category": category[0]["id_category"], "price": 10000},
    #         headers={"Authentication": seller_token[0]},
    #         exp_json={"message": "error, Product is already exists"},
    #         exp_code=409,
    #     )

    # with Scorer(1, "Testing for Update Product"):
    #     categories = Table("categories", MetaData(bind=get_engine()), autoload=True)
    #     category = run_query(select(categories))
    #     # invalid category_id case
    #     assert_response(
    #         c,
    #         "put",
    #         f"{IP_ADDRESS}/products",
    #         json={"product_name": "Product 1", "description": "Lorem ipsum", "images": [
    #             "image_1", "image_2", "image_3"], "condition": "new", "category": "category_id", "price": 12000, "product_id": "product_id"},
    #         headers={"Authentication": seller_token[0]},
    #         exp_json={"message": "error, id_category is invalid"},
    #         exp_code=400,
    #     )
    #     # invalid product already exist case
    #     assert_response(
    #         c,
    #         "put",
    #         f"{IP_ADDRESS}/products",
    #         json={"product_name": "Product 1", "description": "Lorem ipsum", "images": [
    #             "image_1", "image_2", "image_3"], "condition": "new", "category": category[0]["id_category"], "price": 12000, "product_id": "product_id"},
    #         headers={"Authentication": seller_token[0]},
    #         exp_json={"message": "error, Product is already exists"},
    #         exp_code=409,
    #     )
    #     # invalid procudct_id case
    #     assert_response(
    #         c,
    #         "put",
    #         f"{IP_ADDRESS}/products",
    #         json={"product_name": "Product 1", "description": "Lorem ipsum", "images": [
    #             "image_1", "image_2", "image_3"], "condition": "used", "category": category[0]["id_category"], "price": 12000, "product_id": "product_id"},
    #         headers={"Authentication": seller_token[0]},
    #         exp_json={"message": "error, id_product is invalid"},
    #         exp_code=400,
    #     )
    #     products = Table("products", MetaData(bind=get_engine()), autoload=True)
    #     product = run_query(select(products))
    #     # invalid user case
    #     assert_response(
    #         c,
    #         "put",
    #         f"{IP_ADDRESS}/products",
    #         json={"product_name": "Product 1", "description": "Lorem ipsum", "images": [
    #             "image_1", "image_2", "image_3"], "condition": "used", "category": category[0]["id_category"], "price": 12000, "product_id": product[0]["id_product"]},
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={"message": "error, user is invalid"},
    #         exp_code=400,
    #     )
    #     # valid case
    #     assert_response(
    #         c,
    #         "put",
    #         f"{IP_ADDRESS}/products",
    #         json={"product_name": "Item B", "description": "Lorem ipsum", "images": [
    #             "image_1", "image_2", "image_3"], "condition": "used", "category": category[0]["id_category"], "price": 12000, "size": "S, M, L", "product_id": product[0]["id_product"]},
    #         headers={"Authentication": seller_token[0]},
    #         exp_json={"message": "Product updated"},
    #         exp_code=200,
    #     )
    #     # Testing detail Product after update data
    #     products = Table("products", MetaData(bind=get_engine()), autoload=True)
    #     product = run_query(select(products))
    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/products/{product[1]['id_product']}",
    #         exp_json={
    #             "id": product[1]["id_product"],
    #             "category_id": product[1]["category_id"],
    #             "category_name": "Category A",
    #             "images_url": ["image_1", "image_2", "image_3"],
    #             "price": 12000,
    #             "product_detail": product[1]["description"],
    #             "size": ["S", "M", "L"],
    #             "title": product[1]["product_name"],
    #         },
    #         exp_code=200,
    #     )
        

    # with Scorer(1, "Testing for Delete Product"):
    #     products = Table("products", MetaData(bind=get_engine()), autoload=True)
    #     product = run_query(select(products))
    #     # invalid user case
    #     assert_response(
    #         c,
    #         "delete",
    #         f"{IP_ADDRESS}/products/{product[0]['id_product']}",
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={"message": "error, user is invalid"},
    #         exp_code=400,
    #     )
    #     # valid case
    #     assert_response(
    #         c,
    #         "delete",
    #         f"{IP_ADDRESS}/products/{product[0]['id_product']}",
    #         headers={"Authentication": seller_token[0]},
    #         exp_json={"message": "Product deleted"},
    #         exp_code=200,
    #     )

    # with Scorer(0.5, "Testing for Get Category"):
    #     assert_response(
    #         c,
    #         "get",
    #         f"{IP_ADDRESS}/categories",
    #         exp_json={
    #             "data": [
    #                 {
    #                     "id": categories_data[0]["id_category"],
    #                     "title": "Category A"
    #                 },
    #                 {   
    #                     "id": categories_data[1]["id_category"],
    #                     "title": "Category B"
    #                 }
    #             ]
    #         },
    #         exp_code=200,
    #     )

    # with Scorer(1, "Testing for Create Category"):
    #     # valid case
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/categories",
    #         json={"category_name": "Category C"},
    #         headers={"Authentication": seller_token[0]},
    #         exp_json={"message": "Category added"},
    #         exp_code=201,
    #     )
    #     # category already exist case
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/categories",
    #         json={"category_name": "Category A"},
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={"message": "error, user is invalid"},
    #         exp_code=400,
    #     )
    #     # category already exist case
    #     assert_response(
    #         c,
    #         "post",
    #         f"{IP_ADDRESS}/categories",
    #         json={"category_name": "Category A"},
    #         headers={"Authentication": seller_token[0]},
    #         exp_json={"message": "error, Category is already exists"},
    #         exp_code=409,
    #     )

    # with Scorer(1, "Testing for Update Category"):
    #     categories = Table("categories", MetaData(bind=get_engine()), autoload=True)
    #     category = run_query(select(categories))
    #     category_id = category[0]['id_category']
    #     # valid case
    #     assert_response(
    #         c,
    #         "put",
    #         f"{IP_ADDRESS}/categories/{category_id}",
    #         json={"category_name": "Category D", "category_id": category_id},
    #         headers={"Authentication": seller_token[0]},
    #         exp_json={"message": "Category updated"},
    #         exp_code=200,
    #     )
    #     # name category already exist
    #     assert_response(
    #         c,
    #         "put",
    #         f"{IP_ADDRESS}/categories/{category_id}",
    #         json={"category_name": "Category D",
    #               "category_id": category_id},
    #         headers={"Authentication": seller_token[0]},
    #         exp_json={"message": "error, Category is already exists"},
    #         exp_code=409,
    #     )
    #     # id category doesn't exist
    #     category_id = f"{gen_uuid()}"
    #     assert_response(
    #         c,
    #         "put",
    #         f"{IP_ADDRESS}/categories/{category_id}",
    #         json={"category_name": "Category A",
    #               "category_id": category_id},
    #         headers={"Authentication": seller_token[0]},
    #         exp_json={"message": "Category added"},
    #         exp_code=201,
    #     )
    #     # invalid user token
    #     category_id = f"{gen_uuid()}"
    #     assert_response(
    #         c,
    #         "put",
    #         f"{IP_ADDRESS}/categories/{category_id}",
    #         json={"category_name": "Category A",
    #               "category_id": category_id},
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={"message": "error, user is invalid"},
    #         exp_code=400,
    #     )

    # with Scorer(1, "Testing for Delete Category"):
    #     categories = Table("categories", MetaData(bind=get_engine()), autoload=True)
    #     category = run_query(select(categories))
    #     category_id = category[0]['id_category']
    #     # invalid user
    #     assert_response(
    #         c,
    #         "delete",
    #         f"{IP_ADDRESS}/categories/{category_id}",
    #         headers={"Authentication": buyer_token[0]},
    #         exp_json={"message": "error, user is invalid"},
    #         exp_code=400,
    #     )
    #     # valid case
    #     assert_response(
    #         c,
    #         "delete",
    #         f"{IP_ADDRESS}/categories/{category_id}",
    #         headers={"Authentication": seller_token[0]},
    #         exp_json={"message": "Category deleted"},
    #         exp_code=200,
    #     )
    #     # invalid id_category check, if category already deleted
    #     assert_response(
    #         c,
    #         "delete",
    #         f"{IP_ADDRESS}/categories/{category_id}",
    #         headers={"Authentication": seller_token[0]},
    #         exp_json={"message": "error, id_category is invalid"},
    #         exp_code=400,
    #     )


##############################################################################################


def highlight(s: str):
    print("=" * 100 + "\n")
    print(s)
    print("\n" + "=" * 100)


if __name__ == "__main__":
    highlight("Testing for Final Project...")
    tests = [test_end_to_end]

    final_score = 0
    perfect_score = 0
    for test_f in tests:
        total_score, total_weight = test_f()
        final_score += total_score
        perfect_score += total_weight

    perc = round(final_score / perfect_score * 100, 1)
    highlight(
        f"{COL.BOLD}FINAL PROJECT PROGRESS:{COL.ENDC} "
        + f"{COL.BLUE}{final_score}/{perfect_score} ({perc}%){COL.ENDC}"
    )
