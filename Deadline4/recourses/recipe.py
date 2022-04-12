import json
from jsonschema import validate, ValidationError, draft7_format_checker
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from model import Recipes,Users,db,api
import resources.user
import utils
from constants import *

JSON = "application/json"

#class RecipeItem():

class RecipesCollection(Resource):

        def get(self,user):

            db_user = Users.query.filter_by(username=user).first()
            if db_user is None:
                return utils.create_error_response(
                    404, "Not found",
                    "No User was found with the name {}".format(user)
                )

            body = utils.RecipeBuilder(
                items=[]
            )
            body.add_namespace("recipe", LINK_RELATIONS_URL)
            base_uri = api.url_for(RecipesCollection, user=user)
            body.add_control("self", api.url_for(resources.user.UserItem, user=user))

            db_recipes = Recipes.query.filter_by(user=db_user).order_by("title")
            #db_recipe = Recipes.query.filter_by(title=rec).order_by("title")

            for recp in db_recipes:
                item = utils.RecipeBuilder(
                    title=recp.title,
                    content=recp.content
                )
                body["items"].append(item)
            #body.add_control_get_comments(user=user, recipe=recipe)


            return Response(json.dumps(body), 200, mimetype=MASON)



        def post(self,user):

            if not request.json:
                return utils.create_error_response(415, "Unsupported media type", "Use JSON")

            try:
                validate(
                    request.json,
                    Recipes.json_schema(),
                    format_checker=draft7_format_checker,
                )
            except ValidationError as e:
                return utils.create_error_response(400, "Invalid JSON document", str(e))

            fetched_user = Users.query.filter_by(username=user).first()

            recp = Recipes(
                user_id=fetched_user.id,
                title=request.json["title"],
                content=request.json["content"]

            )
            try:
                db.session.add(recp)
                db.session.commit()

            except IntegrityError:
                return utils.create_error_response(
                    409, "Already exists",
                    "Recipe with title '{}' already exists.".format(request.json["title"])
                )
            except:
                return utils.create_error_response(500, "Database error")

            return Response(
                status=201,
                headers={"Location": api.url_for(resources.user.UserItem, user=user)}
            )
        