import json
from flask import Response, request, url_for
from constants import *
from model import *
import resources.user
import resources.recipe
import resources.Comment


class MasonBuilder(dict):
    """
    A convenience class for managing dictionaries that represent Mason
    objects. It provides nice shorthands for inserting some of the more
    elements into the object but mostly is just a parent for the much more
    useful subclass defined next. This class is generic in the sense that it
    does not contain any application specific implementation details.

    Note that child classes should set the *DELETE_RELATION* to the application
    specific relation name from the application namespace. The IANA standard
    does not define a link relation for deleting something.
    """

    DELETE_RELATION = ""

    def add_error(self, title, details):
        """
        Adds an error element to the object. Should only be used for the root
        object, and only in error scenarios.
        Note: Mason allows more than one string in the @messages property (it's
        in fact an array). However we are being lazy and supporting just one
        message.
        : param str title: Short title for the error
        : param str details: Longer human-readable description
        """

        self["@error"] = {
            "@message": title,
            "@messages": [details],
        }

    def add_namespace(self, ns, uri):
        """
        Adds a namespace element to the object. A namespace defines where our
        link relations are coming from. The URI can be an address where
        developers can find information about our link relations.
        : param str ns: the namespace prefix
        : param str uri: the identifier URI of the namespace
        """

        if "@namespaces" not in self:
            self["@namespaces"] = {}

        self["@namespaces"][ns] = {
            "name": uri
        }

    def add_control(self, ctrl_name, href, **kwargs):
        """
        Adds a control property to an object. Also adds the @controls property
        if it doesn't exist on the object yet. Technically only certain
        properties are allowed for kwargs but again we're being lazy and don't
        perform any checking.
        The allowed properties can be found from here
        https://github.com/JornWildt/Mason/blob/master/Documentation/Mason-draft-2.md
        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        """

        if "@controls" not in self:
            self["@controls"] = {}

        self["@controls"][ctrl_name] = kwargs
        self["@controls"][ctrl_name]["href"] = href

    def add_control_post(self, ctrl_name, title, href, schema):
        """
        Utility method for adding POST type controls. The control is
        constructed from the method's parameters. Method and encoding are
        fixed to "POST" and "json" respectively.

        : param str ctrl_name: name of the control (including namespace if any)
        : param str href: target URI for the control
        : param str title: human-readable title for the control
        : param dict schema: a dictionary representing a valid JSON schema
        """

        self.add_control(
            ctrl_name,
            href,
            method="POST",
            encoding="json",
            title=title,
            schema=schema
        )

    def add_control_put(self, title, href, schema):
        """
        Utility method for adding PUT type controls. The control is
        constructed from the method's parameters. Control name, method and
        encoding are fixed to "edit", "PUT" and "json" respectively.

        : param str href: target URI for the control
        : param str title: human-readable title for the control
        : param dict schema: a dictionary representing a valid JSON schema
        """

        self.add_control(
            "edit",
            href,
            method="PUT",
            encoding="json",
            title=title,
            schema=schema
        )

    def add_control_delete(self, title, href):
        """
        Utility method for adding PUT type controls. The control is
        constructed from the method's parameters. Control method is fixed to
        "DELETE", and control's name is read from the class attribute
        *DELETE_RELATION* which needs to be overridden by the child class.

        : param str href: target URI for the control
        : param str title: human-readable title for the control
        """

        self.add_control(
            "storage:delete",
            href,
            method="DELETE",
            title=title,
        )
        
class RecipeBuilder(MasonBuilder):

    def add_control_all_users(self):
        self.add_control(
            "recipe:users-all",
            #"/api/products/",
            api.url_for(resources.user.UsersCollection)
            #title="All artists"
        )

    def add_control_delete_user(self, user):
        self.add_control_delete(
            "Delete the User",
            api.url_for(resources.user.UserItem, user=user)
        )

    def add_control_add_user(self):
        self.add_control_post(
            "recipe:add-user",
            "Add a new user",
            api.url_for(resources.user.UsersCollection),
            Users.json_schema()
        )

    def add_control_edit_user(self, user):
        self.add_control_put(
            "edit",
            api.url_for(resources.user.UserItem, user=user),
            Users.json_schema()
        )

    def add_control_add_recipe(self,user):
        print("here ja yere")
        self.add_control(
            "recipe:add_recipe",
            api.url_for(resources.recipe.RecipesCollection, user=user),
            method="POST",
            encoding="json",
            title="Add a new Recipe for this User",
            schema=Recipes.json_schema()
        )


    def add_control_get_recipe(self,user):
        #base_uri = api.url_for(resources.recipe.RecipesCollection, sensor=sensor)
        #uri = base_uri + "?start={index}"
        self.add_control(
            "recipe:recipes",
            api.url_for(resources.recipe.RecipesCollection, user=user),
            isHrefTemplate=True,
        )
    def add_control_get_comments(self,user , recipe):
        self.add_control(
            "recipe:comments",
            api.url_for(resources.Comment.CommentCollection, user=user, recipe=recipe),
            isHrefTemplate=True,
        )

def create_error_response(status_code, title, message=None):
    resource_url = request.path
    data = MasonBuilder(resource_url=resource_url)
    data.add_error(title, message)
    data.add_control("profile", href=ERROR_PROFILE)
    return Response(json.dumps(data), status_code, mimetype=MASON)
