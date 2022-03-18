import json
import os
import pytest
import random
rom jsonschema import validate
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, StatementError
from model import db,Users,Recipes,Category_Recipe,Categories,Comments

# based on http://flask.pocoo.org/docs/1.0/testing/
# we don't need a client for database testing, just the db handle
@pytest.fixture
def client():
    db_fd, db_fname = tempfile.mkstemp()
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///" + db_fname
    app.config["TESTING"] = True

    db.create_all()
    createDB()
    yield app.test_client()

    db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)

    ########################################################
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
    #########################################################
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


#######################################################
    def test_post_missing_field(self, client): # test for missing fields
        valid = _get_user_json()
        valid.pop("username")
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 400
#########################################

    def test_post_valid_request(self, client):  # test for conflict
        valid = _get_user_json()
        valid["username"] = "testusername1"
        resp = client.post(self.RESOURCE_URL, json=valid)
        assert resp.status_code == 409
