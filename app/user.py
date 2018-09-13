from app import db
from .models import User
from flask import Blueprint, render_template, redirect,request
# 蓝图名称， 蓝图所在模块
#  url_prefix指定了这个蓝图的URL前缀
user_bp = Blueprint('user', __name__, url_prefix='/user' )

@user_bp.route('/')
def index():
    return render_template('user/index.html')

@user_bp.route('/add/', methods=['GET', 'POST'])
def add():
    # 添加user数据
    if request.method == 'POST':
        # 没有则为None
        p_name = request.form.get('user_name', None)
        p_passwd = request.form.get('user_passwd', None)
        p_roleid = request.form.get('role_id', None)
        
        if not p_name or not p_passwd or not p_roleid:
            return 'input error'
        # user_id 主键数据库自动生成
        newobj = User(user_name=p_name, pass_wd=p_passwd, role_id=p_roleid)
        
        db.session.add(newobj)
        db.session.commit()
        users = User.query.all()
        # add界面
        return render_template('user/add.html',users=users)
    users = User.query.all()
    return render_template('user/add.html', users=users)
@user_bp.route('/show')
def show():
    return 'user_show'