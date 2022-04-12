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


class CommentCollection(Resource):

    def get(self, user, recipe):
        print("recipe :" , recipe)
        db_user = Users.query.filter_by(username=user).first()
        fetched_recp = Recipes.query.filter_by(title=recipe).first()

        if db_user is None:
            return create_error_response(
                404, "Not found",
                "No User was found with the name {}".format(user)
            )
        if fetched_recp is None:
            return create_error_response(
                404, "Not found",
                "No Recipe was found with the title {}".format(recipe)
            )

        body = utils.RecipeBuilder(
            items=[]
        )
        body.add_namespace("recipe", LINK_RELATIONS_URL)
        base_uri = api.url_for(CommentCollection, user=user, recipe=recipe)
        body.add_control("self", api.url_for(resources.user.UserItem, user=user))

        db_recipe = Recipes.query.filter_by(recipe=recipe).order_by("title")
        for comnt in db_recipe:
            item = utils.RecipeBuilder(
                comment_body=comnt.comment_body
            )
            body["items"].append(item)

        return Response(json.dumps(body), 200, mimetype=MASON)
    """
    def post(self, user, recipe):

        if not request.json:
            raise UnsupportedMediaType
            return 415
        try:
            validate(request.json, Comment.json_schema(), format_checker=draft7_format_checker)
        except ValidationError as e:
            raise BadRequest(description=str(e))
            return 400

        comment = Comment()
        comment.deserialize(request.json, user, recipe)

        try:
            db.session.add(comment)
            db.session.commit()

        except KeyError:
            abort(400)
        return "Posted", 201
    """