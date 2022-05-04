import json
from datetime import datetime

import utils
from flask import Flask, render_template, redirect, url_for, request,Response,make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import Engine
from sqlalchemy import event
from werkzeug.routing import BaseConverter

from flask_restful import Resource, Api
from jsonschema import validate, ValidationError, draft7_format_checker
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType
from  constants import *

#import utils
#from constants import *

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///RecipeKeeper.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
api = Api(app)

JSON = "application/json"

class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)

    recipe = db.relationship('Recipes',cascade="all, delete-orphan", backref='user')
    comments = db.relationship('Comment',cascade="all, delete-orphan", backref='user')

    def serialize(self, short_form=False):
        #print('trying',request.json)
        print('serlize')

        return {
            "username": self.username,
            "password" : self.password,
            #recipe = self.recipe
        }
    def deserialize(self, doc):
        self.username = doc.get('username')
        self.password = doc.get('password')

    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["username", "password"]
        }
        props = schema["properties"] = {}
        props["username"] = {
            "description": "User Uniqe Name",
            "type": "string"
        }
        props["password"] = {
            "description": "User password",
            "type": "string"
        }
        return schema


#################################################################
class Recipes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False,unique=True)
    content = db.Column(db.String(400), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    comments = db.relationship('Comment',cascade="all, delete-orphan", backref='recipe')


    def serialize(self, short_form=False):
        return {
            "title": self.title,
            "content": self.content,
        }
    def deserialize(self, doc,usr):
        print('Im in Measurement deserlization')
        fetched_user = Users.query.filter_by(username=usr).first()

        self.user_id = fetched_user.id
        self.title = doc.get("title")
        self.content = doc.get('content')


    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["title", "content"]
        }
        props = schema["properties"] = {}
        props["title"] = {
            "description": "Recipe head title/Name",
            "type": "string"
        }
        props["content"] = {
            "description": "Recipe details and steps",
            "type": "string"
        }
        return schema




#####################################################################

class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment_body = db.Column(db.String(400), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"))

    def serialize(self, short_form=False):
        return {
            "comment_body": self.comment_body,
        }
    def deserialize(self, doc,usr,recipe):
        print('Im in Measurement deserlization')
        self.user_id = usr.id
        self.recipe_id = recipe.id
        self.comment_body = doc.get('comment_body')


    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["comment_body"]
        }
        props = schema["properties"] = {}
        props["comment_body"] = {
            "description": "comment_body",
            "type": "string"
        }
        return schema



class UserItem(Resource):

    def delete(self, user):
        fetched_user = Users.query.filter_by(username=user).first()
        if not fetched_user:
            return create_error_response(404, "User not found")
        try:
            db.session.delete(fetched_user)
            db.session.commit()
        except:
            return create_error_response(500, "Database error")

        return Response(status=204, mimetype=MASON)

    def get(self, user):

        fetched_user = Users.query.filter_by(username=user).first()
        if fetched_user is None:
            return create_error_response(
                404, "Not found",
                "No User was found with the name {}".format(user)
            )

        body = RecipeBuilder(
            username=fetched_user.username,
            password=fetched_user.password,
            # recipe=fetched_user.recipe
        )
        body.add_namespace("recipe", LINK_RELATIONS_URL)
        body.add_control("profile", href=PRODUCT_PROFILE)
        body.add_control("self", api.url_for(UserItem, user=fetched_user))

        body.add_control("collection", api.url_for(UsersCollection))
        print("good")

        body.add_control_delete_user(user=fetched_user)
        print("good")

        body.add_control_edit_user(user=fetched_user)
        body.add_control_add_recipe(user=fetched_user)
        body.add_control_get_recipe(user=fetched_user)

        body.add_control(
            "recipe:recipes-first",
            api.url_for(UsersCollection, user=fetched_user)
        )
        # add fetched_user.comments here

        return Response(json.dumps(body), 200, mimetype=MASON)

    def put(self, user):
        fetched_user = Users.query.filter_by(username=user).first()
        if not fetched_user:
            return create_error_response(404, "User not found")
        if not request.json:
            return create_error_response(415, "Unsupported media type", "Use JSON")

        try:
            validate(
                request.json,
                fetched_user.json_schema(),
                format_checker=draft7_format_checker,
            )
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

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
        print("xxxx : ", fetched_user.username)
        try:
            db.session.commit()
        except:
            return create_error_response(500, "Database error")

        return Response(status=204)


class UsersCollection(Resource):

    def get(self):
        print("mm")

        users = Users.query.all()

        data = RecipeBuilder()
        data.add_namespace("recipe", LINK_RELATIONS_URL)
        data.add_control("profile", href=PRODUCT_PROFILE)
        data.add_control_all_users()
        data.add_control_add_user()
        data["items"] = []

        for user in Users.query.all():
            item = MasonBuilder(user.serialize(short_form=True))
            item.add_control("self", api.url_for(UserItem, user=user))
            data["items"].append(item)

        return Response(json.dumps(data), 200, mimetype=MASON)

    def post(self):

        if not request.json:
            return create_error_response(415, "Unsupported media type", "Use JSON")

        try:
            validate(
                request.json,
                Users.json_schema(),
                format_checker=draft7_format_checker,
            )
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

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
            return create_error_response(500, "Database error")

        return Response(
            status=201,
            headers={"Location": api.url_for(UserItem, user=user)}
        )

class RecipesCollection(Resource):

    def get(self, user):

        db_user = Users.query.filter_by(username=user).first()
        if db_user is None:
            return create_error_response(
                404, "Not found",
                "No User was found with the name {}".format(user)
            )

        body = RecipeBuilder(
            items=[]
        )
        body.add_namespace("recipe", LINK_RELATIONS_URL)
        base_uri = api.url_for(RecipesCollection, user=user)
        body.add_control("self", api.url_for(UserItem, user=user))

        db_recipes = Recipes.query.filter_by(user=db_user).order_by("title")
        # db_recipe = Recipes.query.filter_by(title=rec).order_by("title")

        for recp in db_recipes:
            item = RecipeBuilder(
                title=recp.title,
                content=recp.content
            )
            body["items"].append(item)
        # body.add_control_get_comments(user=user, recipe=recipe)

        return Response(json.dumps(body), 200, mimetype=MASON)

    def post(self, user):

        if not request.json:
            return create_error_response(415, "Unsupported media type", "Use JSON")

        try:
            validate(
                request.json,
                Recipes.json_schema(),
                format_checker=draft7_format_checker,
            )
        except ValidationError as e:
            return create_error_response(400, "Invalid JSON document", str(e))

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
            return create_error_response(
                409, "Already exists",
                "Recipe with title '{}' already exists.".format(request.json["title"])
            )
        except:
            return create_error_response(500, "Database error")

        return Response(
            status=201,
            headers={"Location": api.url_for(UserItem, user=user)}
        )

class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.

    Note that child classes should set the *DELETE_RELATION* to the application
    specific relation name from the application namespace. The IANA standard
    does not define a link relation for deleting something.
    """

    DELETE_RELATION = ""

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.
        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.
        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.
        : param str ns: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.
        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md
        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href

    def add_control_post(self, ctrl_name, title, href, schema):
        """
        Utility method for adding POST type controls. The control is
        constructed from the method's parameters. Method and encoding are
        fixed to "POST" and "json" respectively.

        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        : param str title: human-readable title for the control
        : param dict schema: a dictionary representing a valid JSON schema
        """

        self.add_control(
            ctrl_name,
            href,
            method="POST",
            encoding="json",
            title=title,
            schema=schema
        )

    def add_control_put(self, title, href, schema):
        """
        Utility method for adding PUT type controls. The control is
        constructed from the method's parameters. Control name, method and
        encoding are fixed to "edit", "PUT" and "json" respectively.

        : param str href: target URI for the control
        : param str title: human-readable title for the control
        : param dict schema: a dictionary representing a valid JSON schema
        """

        self.add_control(
            "edit",
            href,
            method="PUT",
            encoding="json",
            title=title,
            schema=schema
        )

    def add_control_delete(self, title, href):
        """
        Utility method for adding PUT type controls. The control is
        constructed from the method's parameters. Control method is fixed to
        "DELETE", and control's name is read from the class attribute
        *DELETE_RELATION* which needs to be overridden by the child class.

        : param str href: target URI for the control
        : param str title: human-readable title for the control
        """

        self.add_control(
            "storage:delete",
            href,
            method="DELETE",
            title=title,
        )


class RecipeBuilder(MasonBuilder):

    def add_control_all_users(self):
        self.add_control(
            "recipe:users-all",
            # "/api/products/",
            api.url_for(UsersCollection)
            # title="All artists"
        )

    def add_control_delete_user(self, user):
        self.add_control_delete(
            "Delete the User",
            api.url_for(UserItem, user=user)
        )

    def add_control_add_user(self):
        self.add_control_post(
            "recipe:add-user",
            "Add a new user",
            api.url_for(UsersCollection),
            Users.json_schema()
        )

    def add_control_edit_user(self, user):
        self.add_control_put(
            "edit",
            api.url_for(UserItem, user=user),
            Users.json_schema()
        )

    def add_control_add_recipe(self, user):
        print("here ja yere")
        self.add_control(
            "recipe:add_recipe",
            api.url_for(RecipesCollection, user=user),
            method="POST",
            encoding="json",
            title="Add a new Recipe for this User",
            schema=Recipes.json_schema()
        )

    def add_control_get_recipe(self, user):
        # base_uri = api.url_for(resources.recipe.RecipesCollection, sensor=sensor)
        # uri = base_uri + "?start={index}"
        self.add_control(
            "recipe:recipes",
            #api.url_for(resources.recipe.RecipesCollection, user=user),
            isHrefTemplate=True,
        )

    """
    def add_control_get_comments(self,user , recipe):
        self.add_control(
            "recipe:comments",
            api.url_for(resources.Comment.CommentCollection, user=user, recipe=recipe),
            isHrefTemplate=True,
        )
    """




def create_error_response(status_code, title, message=None):
    resource_url = request.path
    data = MasonBuilder(resource_url=resource_url)
    data.add_error(title, message)
    data.add_control("profile", href=ERROR_PROFILE)
    return Response(json.dumps(data), status_code, mimetype=MASON)


api.add_resource(UserItem, "/api/user/<user>/")
api.add_resource(UsersCollection, "/api/user/")

if __name__ == '__main__':
    app.run(debug=True)

