from flask import Blueprint
main_bp = Blueprint('main_bp', __name__)
user_bp = Blueprint('user_bp', __name__, url_prefix='/user')
role_bp = Blueprint('role_bp',__name__, url_prefix='/role')
from . import views