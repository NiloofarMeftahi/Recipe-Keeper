from flask import Flask,Blueprint
from flask_restful import Api

from resources.user import UserItem, UsersCollection
from resources.recipe import RecipesCollection
from resources.Comment import CommentCollection
from model import db,api,app
#from sensorhub.resources.location import LocationItem, LocationSensorPairing
#from sensorhub.resources.measurement import MeasurementCollection
#from model import app


#api.add_resource(LocationItem, "/locations/<location>/")
#api.add_resource(MeasurementCollection, "/sensors/<sensor>/measurements/")
#api.add_resource(LocationSensorPairing, "/locations/<location>/<sensor>/")

api.add_resource(UsersCollection, "/api/user/")
#still in progress
#api.add_resource(UserItem, "/api/user/<user:user>/")
api.add_resource(UserItem, "/api/user/<user>/")
api.add_resource(RecipesCollection, "/api/user/<user>/recipes/", endpoint = "recipe")
#api.add_resource(CommentCollection, "/api/user/<user>/<recipe>/comment/")



# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True)


