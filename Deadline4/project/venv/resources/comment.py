import json
from jsonschema import validate, ValidationError, draft7_format_checker
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from model import Comment,Recipes,Users, api , db
import resources.user
import resources.recipe

import utils
from constants import *

JSON = "application/json"


class CommentItem(Resource):
     
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


class CommentsCollection(Resource):

    def get(self, recipe,user=None):

        body = utils.RecipeBuilder(
            items=[]
        )
        db_user = Users.query.filter_by(username=user).first()
        db_recipe = Recipes.query.filter_by(title=recipe).first()
        if db_recipe is None:
            return utils.create_error_response(404, "Recipe not found")
        db_comments = Comment.query.filter_by(recipe_id=db_recipe.id)

        if user is None:
            base_uri = url_for("recipe_comments",recipe=recipe)

        else:
            #db_comments = Comment.query.filter_by(recipe_id=db_recipe.id, user_id=db_user.id)
            base_uri = url_for("user_comment",recipe=recipe,user=db_user)


        body.add_namespace("recipe", LINK_RELATIONS_URL)
        #base_uri = url_for("user_comment", user=user , recipe=recipe)
        body.add_control("self", href=request.path)
        body.add_control_add_comments(user=db_user,recipe= db_recipe)
        body.add_control_get_comments(user=db_user,recipe=db_recipe)

        #Recipes.query.join(Users).filter(
        #    Users.username == user, Recipes.title == recipe
        #).first()

        for comnt in db_comments:
            item = utils.RecipeBuilder(
                comment_body=comnt.comment_body,
            )
            body["items"].append(item)
        # body.add_control_get_comments(user=user, recipe=recipe)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self, recipe,user=None):

        if not request.json:
            return utils.create_error_response(415, "Unsupported media type", "Use JSON")

        try:
            validate(
                request.json,
                Comment.json_schema(),
                format_checker=draft7_format_checker,
            )
        except ValidationError as e:
            return utils.create_error_response(400, "Invalid JSON document", str(e))


        db_recipe = Recipes.query.filter_by(title=recipe).first()
        if not db_recipe:
            return utils.create_error_response(404, "Recipe not found")

        if user is not None:
            db_user = Users.query.filter_by(username=user).first()
        else:
            return utils.create_error_response(404, "User is Needed to post a comment")


        comnt = Comment(
            #user_id=db_user.id,
            comment_body=request.json["comment_body"],
            #recipe_id=db_recipe.id,
        )
        db_user.comments.append(comnt)
        db_recipe.comments.append(comnt)

        try:
            db.session.add(comnt)
            db.session.commit()
        except:
            return utils.create_error_response(500, "Database error")

        return Response(
            status=201,
            headers={"Location": api.url_for(resources.user.UserItem, user=user)}
        )
