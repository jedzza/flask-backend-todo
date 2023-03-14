import hashlib
import datetime

from bin.models.PasswordResetModel import PasswordResetModel
from bin.services.LoginChecker import login_required, reset_permitted
import os
from flask import Flask, request, jsonify, render_template
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, decode_token
from pymongo import MongoClient
from bin.resources.errors import EmailDoesNotExistError
from bin.models.ForgotModel import ForgotModel
from bin.models.ResetModel import ResetModel
from bin.models.LoginModel import LoginModel
from bin.models.TaskListModel import TaskListModel
from bin.models.ResetTokenModel import ResetTokenModel
from flask_pydantic import validate
from dotenv import load_dotenv, find_dotenv
from flask_mail import Mail
import random

load_dotenv(find_dotenv())
SECRET_KEY = os.getenv('SECRET_KEY')
CONNECTION_STRING = os.getenv('CONNECTION_STRING')
app = Flask(__name__)
app.config['MAIL_SERVER'] = os.getenv('MAIL_SERVER')
app.config['MAIL_PORT'] = os.getenv("MAIL_PORT")
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config['MAIL_USE_TLS'] = os.getenv("MAIL_USE_TLS")
app.config['MAIL_USE_SSL'] = os.getenv("MAIL_USE_SSL")
app.config['JWT_COOKIE_CSRF_PROTECT'] = True
mail = Mail()
# app.config.from_envvar('.env')
from bin.services.mail_service import send_email

mail.init_app(app)
jwt = JWTManager(app)
app.config['JWT_SECRET_KEY'] = SECRET_KEY
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = datetime.timedelta(days=1)
client = MongoClient(CONNECTION_STRING)
db = client.get_database("todoapp-dev")
users_collection = db["users"]
print(CONNECTION_STRING)


@app.route("/todo/register", methods=["POST", "OPTIONS"])
@validate()
def register(body: LoginModel):
    new_user = body  # store the json body request
    new_user.password = hashlib.sha256(body.password.encode("utf-8")).hexdigest()  # encrpt password

    doc = users_collection.find_one({"email": new_user.email})  # check if user exist
    if not doc:
        users_collection.insert_one(new_user.dict())
        return jsonify({'email': new_user.email, 'password': new_user.password}), 201
    else:
        return jsonify({'msg': 'Username already exists'}), 409


@app.route("/todo/login", methods=["POST", "OPTIONS"])
@validate()
def login(body: LoginModel):
    login_details = body  # store the json body request
    user_from_db = users_collection.find_one({'email': login_details.email})  # search for user in database

    if user_from_db:
        encrypted_password = hashlib.sha256(login_details.password.encode("utf-8")).hexdigest()
        if encrypted_password == user_from_db['password']:
            additional_claims = {"logged_in": "true"}
            access_token = create_access_token(identity=user_from_db['email'],
                                               additional_claims=additional_claims)  # create jwt token
            return jsonify(access_token=access_token), 200

    return jsonify({'msg': 'The username or password is incorrect'}), 401


@app.route("/todo/updatetasks", endpoint='updateTasks', methods=["PUT", "OPTIONS"])
@login_required()
@validate()
def updateTasks(body: TaskListModel):
    request_data = request.json
    current_user = get_jwt_identity()
    doc = users_collection.find_one({"email": current_user})
    if not doc:
        return jsonify({'msg': 'ERROR incorrect username'})
    else:
        query = {"email": doc["email"]}
        newvalues = {"$set": {"tasks": body.dict()}}
        users_collection.update_one(query, newvalues)
    return jsonify({'msg': 'tasks updated successfully'})


@app.route("/todo/returntasks", endpoint='returnTasks', methods=["GET"])
@login_required()
def returnTasks():
    current_user = get_jwt_identity()
    doc = users_collection.find_one({"email": current_user})
    tasks = doc.get("tasks")
    print(tasks)
    if tasks:
        tasks = tasks
    else:
        print("in the else statement!")
        tasks = jsonify({"tasks": [{"description": "this is an example task"}]})
    return tasks


@app.route("/todo/user", endpoint='user', methods=["GET"])
@login_required()
def profile():
    current_user = get_jwt_identity()  # Get the identity of the current user
    user_from_db = users_collection.find_one({'email': current_user})
    if user_from_db:
        del user_from_db['_id'], user_from_db['password']  # delete data we don't want to return
        return jsonify({'profile': user_from_db}), 200
    else:
        return jsonify({'msg': 'Profile not found'}), 404


@app.route("/todo/delete", endpoint="delete", methods=["GET"])
@login_required()
def delete():
    current_user = get_jwt_identity()
    user_from_db = users_collection.find_one({'email': current_user})
    if user_from_db:
        users_collection.delete_one({'email': current_user})
        return jsonify({'msg': "user successfully deleted"}), 200
    else:
        return jsonify({'msg': 'Profile not found'}), 404


@app.route("/todo/forgot", endpoint="forgot", methods=["POST"])
@validate()
def forgot(body: ForgotModel):
    user_from_db = users_collection.find_one({'email': body.email})
    if not user_from_db:
        raise EmailDoesNotExistError
    reset_string = ""
    for i in range(0, 5):
        reset_string += str(random.randrange(1, 9))
    hashed_reset_string = hashlib.sha256(reset_string.encode("utf-8")).hexdigest()
    expiry = datetime.datetime.utcnow()
    time_delay = datetime.timedelta(minutes=30)
    expiry = expiry + time_delay
    reset_token = ResetTokenModel(passcode=hashed_reset_string, expiry=expiry)
    query = {"email": user_from_db["email"]}
    new_values = {"$set": {"reset data": reset_token.dict()}}
    users_collection.update_one(query, new_values)
    send_email('[Lazy-Todo] Reset your password',
               sender='lazy@thelazy.company',
               recipients=user_from_db.get('email'),
               text_body=render_template("email/reset_password.txt",
                                         code=reset_string),
               html_body=render_template("email/reset_password.html",
                                         code=reset_string))
    additional_claims = {"logged_in": "false"}
    access_token = create_access_token(identity=user_from_db['email'],
                                       additional_claims=additional_claims)  # create jwt token
    return jsonify(access_token=access_token), 200


@app.route("/todo/code", endpoint="code", methods=["POST"])
@validate()
def check_code(body: ResetModel):
    current_user = body.email
    user_from_db = users_collection.find_one({'email': current_user})
    if not user_from_db:  # check user exists
        raise EmailDoesNotExistError
    # check token not already used
    if user_from_db["reset data"]["used"]:
        return jsonify(msg="code already used")
    # now check code is correct
    encrypted_code = hashlib.sha256(body.code.encode("utf-8")).hexdigest()
    if encrypted_code != user_from_db['reset data']['passcode']:
        return jsonify(msg="incorrect code")
    # check token has not expired
    now = datetime.datetime.utcnow()
    if now > user_from_db["reset data"]["expiry"]:
        return jsonify(msg="code expired")
    claims = {"logged_in": "true"}
    access_token = create_access_token(identity=user_from_db['email'],
                                       additional_claims=claims,
                                       expires_delta=datetime.timedelta(minutes=5))  # create jwt token
    return jsonify(access_token=access_token), 200


#  NB - if we get this far the code is valid and the user exists so no need as far as I can tell to return errors
@app.route("/todo/reset", endpoint="reset", methods=["POST"])
@login_required()
@validate()
def reset_password(body: PasswordResetModel):
    current_user = get_jwt_identity()
    user_from_db = users_collection.find_one({'email': current_user})
    query = {"email": user_from_db["email"]}
    code_used_update = {"$set": {"reset data": {"used": True}}}
    users_collection.update_one(query, code_used_update)
    new_password = hashlib.sha256(body.password.encode("utf-8")).hexdigest()
    new_values = {"$set": {"password": new_password}}
    users_collection.update_one(query, new_values)
    return jsonify({'msg': 'reset email sent'}), 200
