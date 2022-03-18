import json
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request,Response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import Engine
from sqlalchemy import event
from werkzeug.routing import BaseConverter

from flask_restful import Resource, Api
from jsonschema import validate, ValidationError, draft7_format_checker
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType

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

    recipe = db.relationship('Recipes',  cascade="all, delete-orphan",backref='user')
    comment = db.relationship('Comments',  cascade="all, delete-orphan",backref='user')

    def serialize(self, short_form=False):
        #print('trying',request.json)
        print('serlize')

        return {
            "username": self.username,
            "password": self.password,
        }

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
class UserConverter(BaseConverter):

    def to_python(self, user_name):
        db_user = Users.query.filter_by(username=user_name).first()

        if db_user is None:
            raise NotFound
        return db_user

    def to_url(self, db_user):
        #print('I am in to_url sensor')
        return db_user.username

# get one User
class UserItem(Resource):

    def get(self, user):
        return user.serialize()

    def put(self, user):
        if not request.json:
            raise UnsupportedMediaType

        try:
            #print('request json :', request.json)
            validate(request.json, Users.json_schema())
        except ValidationError as e:
            raise BadRequest(description=str(e))

        user.deserialize(request.json)
        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            raise Conflict(
                409,
                description="User with name '{username}' already exists.".format(
                    **request.json
                )
            )

        #return Response(status=204)
        return (render_template('login.html'),204,headers)

class UsersCollection(Resource):

        def get(self):
            print('I;m get')
            body = {"items": []}
            for db_User in Users.query.all():
                item = db_User.serialize(short_form=True)
                body["items"].append(item)

            return Response(json.dumps(body), 200, mimetype=JSON)
           # return Response(render_template('login.html'))

        def post(self):

            if not request.json:
                raise UnsupportedMediaType
                return 415
            try:
                user = Users(
                    username=request.json['username'],
                    password=request.json["password"],
                )
                db.session.add(user)
                db.session.commit()

            except IntegrityError:
                raise Conflict(
                    description="User with name '{username}' already exists.".format(
                       **request.json
                    )
                )
                abort(409)
            except KeyError:
                abort(400)
            return "Posted", 201
           #headers = {'Content-Type': 'text/html'}

            #return Response(render_template('login.html'), 201, headers)

#################################################################
class Recipes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False)
    content = db.Column(db.String(400), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    comment = db.relationship('Comments',  cascade="all, delete-orphan",backref='recipe',uselist=False)


    def serialize(self, short_form=False):
        return {
            "title": self.title,
            "content": self.content,
        }
    def deserialize(self, doc,usr):
        print('Im in Measurement deserlization')
        self.user_id = usr.id
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

class RecipesCollection(Resource):

        def get(self,user):
            body = {"items": []}
            for db_recipe in user.recipe:
                item = db_recipe.serialize(short_form=True)
                body["items"].append(item)

            return Response(json.dumps(body), 200, mimetype=JSON)

        # return Response(render_template('login.html'))

        def post(self,user):

            if not request.json:
                raise UnsupportedMediaType
                return 415
            try:
                validate(request.json, Recipes.json_schema(), format_checker=draft7_format_checker)
            except ValidationError as e:
                raise BadRequest(description=str(e))
                return 400

            recipe = Recipes()
            recipe.deserialize(request.json, user)

            try:
                db.session.add(recipe)
                db.session.commit()

            except IntegrityError:
                raise Conflict(
                    description="recipe with name '{title}' already exists.".format(
                        **request.json
                    )
                )
                abort(409)
            except KeyError:
                abort(400)
            return "Posted", 201


#####################################################################

class Comments(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    comment_body = db.Column(db.String(400), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"))

class Categories(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False, unique=True)

class Category_Recipe(db.Model):
    Cat_id = db.Column(db.Integer, db.ForeignKey("categories.id"),primary_key=True)
    Recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"),primary_key=True)

class Favorites(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"),primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"),primary_key=True)


#api.add_resource("/api/login/")
#api.ro(render_template('login.html'), "/api/login/")
app.url_map.converters["user"] = UserConverter

api.add_resource(UsersCollection, "/api/user/")
#still in progress
#api.add_resource(UserItem, "/api/user/<User>/")
api.add_resource(RecipesCollection, "/api/users/<user:user>/recipes/")



# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True)



def createDB():
    from model import db,Users,Recipes,Category_Recipe,Categories,Comments

    db.create_all()
    user1=Users(username='testusername1',password='testpass1')
    user2=Users(username='testusername2',password='testpass2')
    db.session.add(user1)
    db.session.add(user2)
    recipe1=Recipes(title='food1',content='content1')
    recipe2=Recipes(title='food2',content='content2')

    user1.recipe=recipe1
    user2.recipe=recipe2
    db.session.commit()
    db.session.add(recipe1)
    db.session.add(recipe2)
    comment1=Comments(comment_body='comment1')
    comment2=Comments(comment_body='comment2')
    user1.comment=comment1
    user2.comment=comment2

    db.session.add(comment1)
    db.session.add(comment2)
    db.session.commit()