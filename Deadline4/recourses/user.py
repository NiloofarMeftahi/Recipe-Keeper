import json
from jsonschema import validate, ValidationError, draft7_format_checker
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from model import Users, api , db

import utils
from constants import *

# get one User
class UserItem(Resource):

    def delete(self, user):
        fetched_user = Users.query.filter_by(username=user).first()
        if not fetched_user:
            return utils.create_error_response(404, "User not found")
        try:
            db.session.delete(fetched_user)
            db.session.commit()
        except:
            return utils.create_error_response(500, "Database error")

        return Response(status=204, mimetype=MASON)


    def get(self, user):

        fetched_user = Users.query.filter_by(username=user).first()
        if fetched_user is None:
            return utils.create_error_response(
                404, "Not found",
                "No User was found with the name {}".format(user)
            )

        body = utils.RecipeBuilder(
            username=fetched_user.username,
            password=fetched_user.password,
            #recipe=fetched_user.recipe
        )
        body.add_namespace("recipe", LINK_RELATIONS_URL)
        body.add_control("profile", href=PRODUCT_PROFILE)
        body.add_control("self", api.url_for(UserItem, user=fetched_user))


        body.add_control("collection", api.url_for(UsersCollection))
        print("good")

        body.add_control_delete_user(user=fetched_user)
        print("good")

        body.add_control_edit_user  (user=fetched_user)
        body.add_control_add_recipe (user=fetched_user)
        body.add_control_get_recipe (user=fetched_user)

        body.add_control(
            "recipe:recipes-first",
            api.url_for(UsersCollection, user=fetched_user)
        )
        #add fetched_user.comments here
        
        return Response(json.dumps(body), 200, mimetype=MASON)


    def put(self, user):
        fetched_user = Users.query.filter_by(username=user).first()
        if not fetched_user:
            return utils.create_error_response(404, "User not found")
        if not request.json :
            return utils.create_error_response(415, "Unsupported media type", "Use JSON")

        try:
            validate(
                request.json,
                fetched_user.json_schema(),
                format_checker=draft7_format_checker,
            )
        except ValidationError as e:
            return utils.create_error_response(400, "Invalid JSON document", str(e))

        if fetched_user.username != request.json["username"]:
            n = Users.query.filter(
                Users.username.ilike(request.json["username"].lower())
            ).count() - 1
            if n:
                name = fetched_user.username.lower() + "_f" + str(n)
            else:
                name = fetched_user.username.lower()
            fetched_user.username = name

        fetched_user.username = request.json["username"]
        fetched_user.password = request.json["password"]
        print("xxxx : ",fetched_user.username)
        try:
            db.session.commit()
        except:
            return utils.create_error_response(500, "Database error")

        return Response(status=204)

class UsersCollection(Resource):
    def get(self):
        users = Users.query.all()

        data = utils.RecipeBuilder()
        data.add_namespace("recipe", LINK_RELATIONS_URL)
        data.add_control("profile", href=PRODUCT_PROFILE)
        data.add_control_all_users()
        data.add_control_add_user()
        data["items"] = []

        for user in Users.query.all():
            item = utils.MasonBuilder(user.serialize(short_form=True))
            item.add_control("self", api.url_for(UserItem, user=user))
            data["items"].append(item)

        return Response(json.dumps(data), 200, mimetype=MASON)

    def post(self):

        if not request.json:
            return utils.create_error_response(415, "Unsupported media type", "Use JSON")

        try:
            validate(
                request.json,
                Users.json_schema(),
                format_checker=draft7_format_checker,
            )
        except ValidationError as e:
            return utils.create_error_response(400, "Invalid JSON document", str(e))

        user = Users(
            username=request.json['username'],
            password=request.json["password"]
        )

        try:
            db.session.add(user)
            db.session.commit()

        except IntegrityError:
            return create_error_response(
                409, "Already exists",
                "Sensor with name '{}' already exists.".format(request.json["name"])
            )
        except:
            return utils.create_error_response(500, "Database error")


        return Response(
            status=201,
            headers={"Location": api.url_for(UserItem, user=user)}
        )