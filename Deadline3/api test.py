import json
import os
import pytest
import random
from jsonschema import validate
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, StatementError
from app import app, db
from app import Users,Recipes,Category_Recipe,Categories,Comments

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# based on http://flask.pocoo.org/docs/1.0/testing/
# we don't need a client for database testing, just the db handle
@pytest.fixture
def client():
    db_fd, db_fname = tempfile.mkstemp()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_fname
    app.config["TESTING"] = True

    db.create_all()
    _populate_db()
    yield app.test_client()

    db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)

    ########################################################
def _populate_db():
    from app import db,Users,Recipes,Category_Recipe,Categories,Comments

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
    #########################################################

    
def _get_user_json(number=1):
    """
    Creates a valid user JSON object to be used for PUT and POST tests.
    """
    
    return {"username": "extra-user-{}".format(number), "password": "extrapass"}
    ##############################################################
class TestUsersCollection(object): # user collection get method test
    RESOURCE_URL = "/api/login/"
    def test_get(self, client):
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert len(body["items"]) == 2
        for item in body["items"]:
            assert "username" in item
            assert "password" in item
   ############################################################
    def test_post(self, client):
        """
        Tests the POST method. Checks all of the possible error codes, and 
        also checks that a valid request receives a 201 response with a 
        location header that leads into the newly created resource.
        """
        
        valid = _get_user_json()
        
        # test with wrong content type
        resp = client.post(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        # test with valid and see that it exists afterward
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 201
        assert resp.headers["login.html"].endswith(self.RESOURCE_URL + valid["name"] + "/")
        resp = client.get(resp.headers["login.html"])
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["username"] == "extra-user-1"
        assert body["password"] == "extrapass"
        
        # send same data again for 409
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        
        # remove password field for 400
        valid.pop("password")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
############################################################
class TestUserItem(object):
    
    RESOURCE_URL = "/api/users/testusername1/"
    INVALID_URL = "/api/users/nonuserx/"
    MODIFIED_URL = "/api/users/extra-user-1/"
    
    def test_get(self, client):
        """
        Tests the GET method. Checks that the response status code is 200, and
        then checks that all of the expected attributes and controls are
        present, and the controls work. Also checks that all of the items from
        the DB popluation are present, and their controls.
        """

        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["users"] == "testusername1"
        assert body["password"] == "testpass1"
        resp = client.get(self.INVALID_URL)
        assert resp.status_code == 404

    def test_put(self, client):
        """
        Tests the PUT method. Checks all of the possible erroe codes, and also
        checks that a valid request receives a 204 response. Also tests that
        when username is changed, the user can be found from a its new URI. 
        """
        
        valid = _get_user_json()
        
        # test with wrong content type
        resp = client.put(self.RESOURCE_URL, data=json.dumps(valid))
        assert resp.status_code == 415
        
        resp = client.put(self.INVALID_URL, json=valid)
        assert resp.status_code == 404
        
        # test with another username
        valid["username"] = "testuserename2"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
        
        # test with valid (only change model)
        valid["username"] = "testuserename1"
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 204
        
        # remove field for 400
        valid.pop("password")
        resp = client.put(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
        
        valid = _get_user_json()
        resp = client.put(self.RESOURCE_URL, json=valid)
        resp = client.get(self.MODIFIED_URL)
        assert resp.status_code == 200
        body = json.loads(resp.data)
        assert body["password"] == valid["password"]
        
    def test_delete(self, client):
        """
        Tests the DELETE method. Checks that a valid request reveives 204
        response and that trying to GET the sensor afterwards results in 404.
        Also checks that trying to delete a sensor that doesn't exist results
        in 404.
        """
        
        resp = client.delete(self.RESOURCE_URL)
        assert resp.status_code == 204
        resp = client.get(self.RESOURCE_URL)
        assert resp.status_code == 404
        resp = client.delete(self.INVALID_URL)
        assert resp.status_code == 404
                    


#######################################################

 
