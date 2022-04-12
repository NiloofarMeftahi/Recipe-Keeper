import json
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request,Response,make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import Engine
from sqlalchemy import event
from werkzeug.routing import BaseConverter

from flask_restful import Resource, Api
from jsonschema import validate, ValidationError, draft7_format_checker
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType

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

        data = InventoryBuilder(
            username= self.username,
            password= self.password,
            #recipe = self.recipe
        )
        return data
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


class Categories(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    cat_name = db.Column(db.String(64), nullable=False, unique=True)

    def serialize(self, short_form=False):
        return {
            "cat_name": self.cat_name,
        }
    def deserialize(self, doc):
        self.cat_name = doc.get('cat_name')


    @staticmethod
    def json_schema():
        schema = {
            "type": "object",
            "required": ["cat_name"]
        }
        props = schema["properties"] = {}
        props["cat_name"] = {
            "description": "cat_name",
            "type": "string"
        }
        return schema
class Category_Recipe(db.Model):
    Cat_id = db.Column(db.Integer, db.ForeignKey("categories.id"),primary_key=True)
    Recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"),primary_key=True)

class Favorites(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"),primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"),primary_key=True)




#api.add_resource("/api/login/")
#api.ro(render_template('login.html'), "/api/login/")
#app.url_map.converters["user"] = UserConverter
#app.url_map.converters["recipe"] = RecipeConverter

#api.add_resource(UsersCollection, "/api/user/",endpoint="users")
#still in progress
#api.add_resource(UserItem, "/api/user/<user:user>/")
#api.add_resource(UserItem, "/api/user/<user>/",endpoint="user")

#api.add_resource(RecipesCollection, "/api/users/<user:user>/recipes/")
#api.add_resource(CommentCollection, "/api/users/<user:user>/<recipe:recipe>/comment/")



# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True)



def createDB():
    from model import db,Users,Recipes,Category_Recipe,Categories,Comment

    db.create_all()
    user1=Users(username='testusername1',password='testpass1')
    user2=Users(username='testusername2',password='testpass2')
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()

    recipe1=Recipes(title='food1',content='content1')
    recipe2=Recipes(title='food2',content='content2')

    user1.recipe.append(recipe1)
    user2.recipe.append(recipe2)
    db.session.commit()
    db.session.add(recipe1)
    db.session.add(recipe2)
    comment1=Comment(comment_body='comment1')
    comment2=Comment(comment_body='comment2')
    user1.comments.append(comment1)
    user2.comments.append(comment2)

    db.session.add(comment1)
    db.session.add(comment2)
    db.session.commit()