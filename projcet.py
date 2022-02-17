from flask import Flask
from flask_sqlalchemy import SQLAlchemy
app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///RecipeKeeper.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
class Users(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(128), nullable=False)
    password = db.Column(db.String(128), nullable=False)

    recipe = db.relationship('Recipes', backref='users')
    comment = db.relationship('Comments', backref='users')
class Recipes(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64), nullable=False)
    content = db.Column(db.String(400), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))

    comment = db.relationship('Comments', backref='recipes')

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


db.create_all()
user1=Users(username='testusername1',password='testpass1')
user2=Users(username='testusername2',password='testpass2')
db.session.add(user1)
db.session.add(user2)
recipe1=Recipes(title='food1',content='content1')
recipe2=Recipes(title='food2',content='content2')

user1.Recipes=recipe1
user2.Recipes=recipe2
db.session.add(recipe1)
db.session.add(recipe2)
comment1=Comments(comment_body='comment1')
comment2=Comments(comment_body='comment2')
user1.Comments=comment1
user2.Comments=comment2

db.session.add(comment1)
db.session.add(comment2)
db.session.commit()