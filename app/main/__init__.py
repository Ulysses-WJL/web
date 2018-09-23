from flask import Blueprint
main_bp = Blueprint('main_bp', __name__)
from . import views, errors
from ..models import Permission

@main_bp.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
