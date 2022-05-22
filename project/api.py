from flask import Flask,Blueprint
from flask_restful import Api

from resources.user import UserItem, UsersCollection
from resources.recipe import RecipesCollection , RecipeItem
from resources.comment import CommentsCollection,CommentItem
from model import db,api,app#,api_bp
from constants import *
#from sensorhub.resources.location import LocationItem, LocationSensorPairing
#from sensorhub.resources.measurement import MeasurementCollection
#from model import app


#app.register_blueprint(api_bp)


api.add_resource(UsersCollection, "/api/user/", endpoint = "user")
#still in progress
api.add_resource(UserItem, "/api/user/<user>/")
#api.add_resource(UserItem, "/api/user/<user>/favorits/", endpoint = "user_favorits")

api.add_resource(RecipesCollection, "/api/user/<user>/recipes/", endpoint = "userrecipes")
api.add_resource(RecipesCollection, "/api/recipes/", endpoint = "recipes")
api.add_resource(RecipeItem, "/api/recipes/<recipe>/",endpoint = "single_recipe")


#api.add_resource(RecipeItem, "/api/user/<user>/<recipe>/",endpoint = "User_recipe")
api.add_resource(CommentsCollection, "/api/user/<user>/<recipe>/comment/", endpoint="user_comment")
api.add_resource(CommentsCollection, "/api/<recipe>/comment/" , endpoint="recipe_comments")
#doesn't have use now
api.add_resource(CommentItem, "/api/user/<recipe>/comment/", endpoint="user_comment_Item")


@app.route(LINK_RELATIONS_URL)
def send_link_relations():
    return "link relations"

@app.route("/profiles/<profile>/")
def send_profile(profile):
    return "you requests {} profile".format(profile)

@app.route("/recipes/")
def admin_site():
    return app.send_static_file("html/all_recpies.html")

if __name__ == '__main__':
    app.run(debug=True)




