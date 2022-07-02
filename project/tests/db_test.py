import os
import pytest
import tempfile
import time
from datetime import datetime
from sqlalchemy.engine import Engine
from sqlalchemy import event
from sqlalchemy.exc import IntegrityError, StatementError

from model import Users, Recipes, Category_Recipe, Categories, Comment, create_app, db


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

# based on http://flask.pocoo.org/docs/1.0/testing/
# we don't need a client for database testing, just the db handle
@pytest.fixture
def app():
    db_fd, db_fname = tempfile.mkstemp()
    config = {
        "SQLALCHEMY_DATABASE_URI": "sqlite:///" + db_fname,
        "TESTING": True
    }
    
    app = create_app(config)
    
    with app.app_context():
        db.create_all()
        
    yield app

    db.session.remove()
    os.close(db_fd)
    os.unlink(db_fname)


def _get_user():
    return Users(
        username="testusername1",
        password="testpass1",
    )


def _get_recipe():
    return Recipes(
        title="food1",
        content="content1",
    )
def _get_comment():
    return Comment(
        comment_body="comment1",
    )
def _get_Category():
    return Categories(
        cat_name="cat_1",
    )

def test_create_instances(app):
    """
    Tests that we can create one instance of each model and save them to the
    database using valid values for all columns. After creation, test that
    everything can be found from database, and that all relationships have been
    saved correctly.
    """

    with app.app_context():
        # Create everything
        user = _get_user()
        recipe = _get_recipe()
        comment = _get_comment()
        category = _get_Category()
        
        user.recipe.append(recipe)
        recipe.users.append(user)
        user.comments.append(comment)
        recipe.comments.append(comment)

        db.session.add(recipe)
        db.session.add(user)
        db.session.add(comment)

        recipe.categories.append(category)
        #category.recipes.append(recipe)

        db.session.add(category)

        db.session.commit()

        # Check that everything exists
        assert Recipes.query.count() == 1
        assert Users.query.count() == 1
        assert Comment.query.count() == 1
        assert Categories.query.count() == 1


        db_recipe = Recipes.query.first()
        db_user = Users.query.first()
        db_comment = Comment.query.first()
        db_cat = category.query.first()


        # Check all relationships (both sides)
        assert db_recipe.user == db_user
        assert db_recipe in db_user.recipes
        assert db_comment in db_recipe.comments
        assert db_comment in db_user.comments
        assert db_cat in db_recipe.categories

def test_user_columns(app):
    """
    Tests user columns' restrictions. username must be unique, and username and password
    must be mandatory.
    """

    with app.app_context():
        user1 = _get_user()
        user2 = _get_user()
        db.session.add(user1)
        db.session.add(user2)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        user = _get_user()
        user.username = None
        db.session.add(user)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        user = _get_user()
        user.password = None
        db.session.add(user)
        with pytest.raises(IntegrityError):
            db.session.commit()

def test_recipe_columns(app):
    """
    Tests recipe columns' restrictions. title must be unique, and title and content
    must be mandatory.
    """

    with app.app_context():
        recipe1 = _get_recipe()
        recipe2 = _get_recipe()
        db.session.add(recipe1)
        db.session.add(recipe2)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        recipe = _get_recipe()
        recipe.title = None
        db.session.add(recipe)
        with pytest.raises(IntegrityError):
            db.session.commit()

        db.session.rollback()

        recipe = _get_recipe()
        recipe.content = None
        db.session.add(recipe)
        with pytest.raises(IntegrityError):
            db.session.commit()

def test_recipe_ondelete_user(app):
    """
    Tests that recipe's user are deleted when the user
    is deleted.
    """

    with app.app_context():
        recipe = _get_recipe()
        user = _get_user()
        user.recipe.append(recipe)
        db.session.add(recipe)
        db.session.commit()
        db.session.delete(user)
        db.session.commit()
        assert  Recipes.query.count() == 0

def test_comments_ondelete_recipe(app):
    """
    Tests that all comments of the recipe are deleted when the recipe
    is deleted.
    """

    with app.app_context():
        recipe = _get_recipe()
        comment = _get_comment()
        recipe.comments.append(comment)
        db.session.add(comment)
        db.session.commit()
        db.session.delete(recipe)
        db.session.commit()
        assert  Comment.query.count() == 0
