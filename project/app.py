import model
from flask import Flask, render_template, redirect, url_for, request,Response
from model import *
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from sqlalchemy.engine import Engine
from sqlalchemy import event
from flask_restful import Resource, Api


#from flask import Flask, render_template
# Route for handling the login page logic


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///RecipeKeeper.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
api = Api(app)


# Use Resource instead of routing
#from flask_restful import Resource
####
#get all sensors
# put that code in the model
'''
#In order for anything to work in Flask-RESTful we need to initialize an API object
''''''in a single file app the process is very simple: import Api from flask_restul, and create an instance of it.'''
'''
db = SQLAlchemy(app)
api = Api(app
'''
##Assuming your resource classes are in the same file
'''
api.add_resource(SensorCollection, "/api/sensors/")
api.add_resource(SensorItem, "/api/sensors/<sensor>/")

Now you could send GET and POST to /api/sensors/, and likewise GET, PUT and DELETE 
to e.g. /api/sensors/uo-donkeysensor-4451/. 
Not that they'd do much (except for POST to sensors collection which we just implemented). 


'''

#@app.route('/')
class home(Resource):
    def get(self):
        return "Hello, World!"  # return a string
# Route for handling the login page logic
class login(Resource):

    def get(self):
        error = None
        headers = {'Content-Type': 'text/html'}
        return Response(render_template('login.html', error=error),200,headers)
    def post(self):
        error = None

        if request:
            #user = Users(username=request.form['username'], password=request.form['password'])
            UsersCollection()
        return Response(render_template('login.html', error=error),200,headers)

    '''
    
    if  request.form['username'] and request.form['password']:
        if request.method == 'POST':
            #UsersCollection(request.json)
            user = Users(username=request.form['username'],password=request.form['password'])
            #api.add_resource(UsersCollection, "/api/Users/")

            #db.session.add(user)
            #db.session.commit()
            #if request.form['username'] != 'admin' or request.form['password'] != 'admin':
    else:
        error = 'Invalid Credentials. Please try again.'
            #else:
                #return redirect(url_for('home'))
    '''

api.add_resource(home, '/')

api.add_resource(login, "/api/login/")
#api.add_resource(UserItem, "/api/User/<User>/")


# start the server with the 'run()' method
if __name__ == '__main__':
    app.run(debug=True)
