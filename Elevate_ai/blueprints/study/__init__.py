from flask import Blueprint

study_bp = Blueprint('study', __name__)

from . import routes