import json
from jsonschema import validate, ValidationError, draft7_format_checker
from flask import Response, request, url_for
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError
from model import Favorites, api , db, Users, Recipes

import utils
from constants import *


