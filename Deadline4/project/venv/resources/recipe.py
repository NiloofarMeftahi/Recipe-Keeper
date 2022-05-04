import json
from jsonschema import validate, ValidationError, draft7_format_checker
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from model import Recipes,Users, api , db
import resources.user
import utils
from constants import *

JSON = "application/json"

class RecipeItem(Resource):
    def get(self, recipe , user=None):

        fetched_user = Users.query.filter_by(username=user).first()
        db_recipe = Recipes.query.filter_by(title=recipe).first()
        """
        if fetched_user is None:
            return utils.create_error_response(
                404, "Not found",
                "No User was found with the name {}".format(user)
            )
        """
        if db_recipe is None:
            return utils.create_error_response(
                404, "Not found",
                "No Recipe was found with the name {}".format(recipe)
            )

        body = utils.RecipeBuilder(
            title=db_recipe.title,
            content=db_recipe.content,
            # recipe=fetched_user.recipe
        )
        print("out here ")

        body.add_namespace("recipe", LINK_RELATIONS_URL)
        body.add_control("profile", href=PRODUCT_PROFILE)

        base_uri = url_for("single_recipe", recipe=db_recipe)
        body.add_control("self", url_for("single_recipe", recipe=db_recipe.title, user = None))
        """
        else :
            print("again ")

            base_uri = url_for("User_recipe", recipe=db_recipe , user = fetched_user)
        """

        body.add_control("collection", url_for("recipes"))
        body.add_control_delete_recipe(recipe=db_recipe, user=fetched_user )
        body.add_control_edit_recipe(recipe = db_recipe,user=fetched_user)

        body.add_control_add_comments(user=fetched_user, recipe=recipe)
        body.add_control_get_comments(user=fetched_user, recipe=recipe)
        body.add_control_edit_comment(user=fetched_user, recipe=recipe)
        body.add_control_delete_comment(user=fetched_user, recipe=recipe)


        """
        body.add_control_get_recipe(user=fetched_user)

        body.add_control(
            "recipe:recipes-first",
            api.url_for(UsersCollection, user=fetched_user)
        )
        # add fetched_user.comments here
        """
        return Response(json.dumps(body), 200, mimetype=MASON)

    def delete(self, user, recipe):
        fetched_user = Users.query.filter_by(username=user).first()
        db_recipe = Recipes.query.join(Users).filter(
            Users.username == user, Recipes.title == recipe
        ).first()

        if not fetched_user:
            return utils.create_error_response(404, "User not found")

        if not db_recipe:
            return utils.create_error_response(404, "Recipe not found")
        try:
            db.session.delete(db_recipe)
            db.session.commit()
        except:
            return utils.create_error_response(500, "Database error")

        return Response(status=204, mimetype=MASON)

    def put(self, user, recipe):
        fetched_user = Users.query.filter_by(username=user).first()
        db_recipe = Recipes.query.join(Users).filter(
            Users.username == user, Recipes.title == recipe
        ).first()
        if not fetched_user:
            return utils.create_error_response(404, "User not found")

        if not db_recipe:
            return utils.create_error_response(404, "Recipe not found")

        if not request.json :
            return utils.create_error_response(415, "Unsupported media type", "Use JSON")

        try:
            validate(
                request.json,
                db_recipe.json_schema(),
                format_checker=draft7_format_checker,
            )
        except ValidationError as e:
            return utils.create_error_response(400, "Invalid JSON document", str(e))

        if db_recipe.title != request.json["title"]:
            n = Recipes.query.filter(
                Recipes.title.ilike(request.json["title"].lower())
            ).count() - 1
            if n:
                name = db_recipe.title.lower() + "_f" + str(n)
            else:
                name = db_recipe.title.lower()
            db_recipe.title = name

        db_recipe.title = request.json["title"]
        db_recipe.content = request.json["content"]

        try:
            db.session.commit()
        except:
            return utils.create_error_response(500, "Database error")

        return Response(status=204)


class RecipesCollection(Resource):

    def get(self, user=None):
        body = utils.RecipeBuilder(
            items=[]
        )
        if user is None:
            db_recipes = Recipes.query.all()
            base_uri = url_for("recipes")

        else:
            db_user = Users.query.filter_by(username=user).first()
            db_recipes = Recipes.query.filter_by(user=db_user).order_by("title")
            base_uri = url_for("userrecipes", user=user)


        body.add_namespace("recipe", LINK_RELATIONS_URL)
        #body.add_control("self", api.url_for(resources.user.UserItem, user=user))
        #db_recipes = Recipes.query.filter_by(user=db_user).order_by("title")
        # db_recipe = Recipes.query.filter_by(title=rec).order_by("title")

        for recp in db_recipes:
            item = utils.RecipeBuilder(
                title=recp.title,
                content=recp.content
            )
            body.add_control("self", href=request.path)
            body.add_control("profile", href=PRODUCT_PROFILE)

            body["items"].append(item)
        # body.add_control_get_comments(user=user, recipe=recipe)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self, user):

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
