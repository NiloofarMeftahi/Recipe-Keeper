import os
import json
from datetime import datetime
import click
from flask.cli import with_appcontext

from flask import Flask, render_template, redirect, url_for, request,Response,make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import Engine
from sqlalchemy import event

from flask_restful import Resource, Api
from flask_caching import Cache
from jsonschema import validate, ValidationError, draft7_format_checker
from werkzeug.exceptions import NotFound, Conflict, BadRequest, UnsupportedMediaType
from constants import *

from flask import Flask,Blueprint

#app = Flask(__name__)
app = Flask(__name__, instance_relative_config=True)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///RecipeKeeper.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["CACHE_TYPE"] = "FileSystemCache"
app.config["CACHE_DIR"] = "cache"
db = SQLAlchemy(app)
api = Api(app)
cache = Cache(app)
#api_bp = Blueprint("api", __name__, url_prefix="/api")
#api = Api(api_bp)

JSON = "application/json"



class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), nullable=False, unique=True)
    password = db.Column(db.String(128), nullable=False)

    recipe = db.relationship('Recipes',cascade="all, delete-orphan", backref='user')
    comments = db.relationship('Comment',cascade="all, delete-orphan", backref='user')

    recipes = db.relationship("Recipes", secondary='Favorites', back_populates="users")

    def serialize(self, short_form=False):
        #print('trying',request.json)
        print('serlize')

        return {
            "username": self.username,
            "password" : self.password,
            #"recipe" : self.recipe,
        }
        """
        data = RecipeBuilder(
            username= self.username,
            password= self.password,
        )
        return data
        """
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
    users = db.relationship("Users", secondary='Favorites', back_populates="recipes")
    categories = db.relationship("Categories", secondary='Category_Recipe', back_populates="recipes")


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
    recipes = db.relationship("Recipes", secondary='Category_Recipe', back_populates="categories")


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

"""
class Category_Recipe(db.Model):
    Cat_id = db.Column(db.Integer, db.ForeignKey("categories.id"),primary_key=True)
    Recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"),primary_key=True)

class Favorites(db.Model):
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"),primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey("recipes.id"),primary_key=True)
"""
Category_Recipe = db.Table("Category_Recipe",
    db.Column("Cat_id", db.Integer, db.ForeignKey("categories.id"), primary_key=True),
    db.Column("Recipe_id", db.Integer, db.ForeignKey("recipes.id"), primary_key=True)
)

Favorites = db.Table("Favorites",
    db.Column("user_id", db.Integer, db.ForeignKey("users.id"), primary_key=True),
    db.Column("recipe_id", db.Integer, db.ForeignKey("recipes.id"), primary_key=True)
)




def create_app(test_config=None):
    #app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY="dev",
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(app.instance_path, "RecipeKeepertest_test.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False
    )

    if test_config is None:
        app.config.from_pyfile("config.py", silent=True)
    else:
        app.config.from_mapping(test_config)



    try:
        os.makedirs(app.instance_path)
    except OSError as e:

        pass

    db.init_app(app)
    #import model
    import api
    app.cli.add_command(init_db_command)
    app.cli.add_command(generate_test_data)
    #app.register_blueprint(api.api_bp)


    @app.route(LINK_RELATIONS_URL)
    def send_link_relations():
        return "link relations"

    @app.route("/profiles/<profile>/")
    def send_profile(profile):
        return "you requests {} profile".format(profile)

    @app.route("/admin/")
    def admin_site():
        return app.send_static_file("html/admin.html")

    return app


@click.command("init-db")
@with_appcontext
def init_db_command():
    db.create_all()

@click.command("testgen")
@with_appcontext
def generate_test_data():
    from model import db,Users,Recipes,Categories,Comment

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


    recipe2.comments.append(comment1)
    recipe1.comments.append(comment2)

    user1.recipes.append(recipe2)
    user2.recipes.append(recipe1)
    recipe2.users.append(user2)
    recipe1.users.append(user1)


    db.session.add(comment1)
    db.session.add(comment2)
    cat1 = Categories(cat_name = "Soups")
    cat2 = Categories(cat_name = "main dishes")
    cat3 = Categories(cat_name = "dessert")

    recipe2.categories.append(cat3)
    recipe1.categories.append(cat1)
    cat2.recipes.append(recipe1)
    cat3.recipes.append(recipe1)



    db.session.add(cat1)
    db.session.add(cat2)
    db.session.add(cat3)

    db.session.commit()