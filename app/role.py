from app import db
from .models import Role
from flask import Blueprint, render_template, redirect,request,url_for,session
import logging
#logging.basicConfig(filename='role.log', filemode='a', level=logging.INFO, format='%(asctime)s:%(message)s')

role_bp = Blueprint('role', __name__, url_prefix='/role')


@role_bp.route('/index')
def index():
    return render_template('role/index.html')


@role_bp.route('/add/', methods=['GET', 'POST'])
def add():
    # 添加user数据
    if request.method == 'POST':
        # 没有则为None
        old_name=session.get('name')
        p_name = request.form.get('role_name')
        if p_name is not None and p_name != old_name:
            role = Role.query.filter_by(role_name=p_name).first()
            if role is None:
                # logging.info(f'name:{p_name}')
                # role_id 主键数据库自动生成
                newobj = Role(role_name=p_name)
                
                db.session.add(newobj)
                db.session.commit()
                session['name'] = p_name
        # roles = Role.query.all()
            # add界面
        # 指定一个蓝本名称作为端点的一部分
        return redirect(url_for('role.add'))
        
        # return redirect(url_for('/add/'), roles=roles)
    roles = Role.query.order_by('role_id')
    return render_template('role/add.html', roles=roles)


@role_bp.route('/show')
def show():
    return 'role_show'