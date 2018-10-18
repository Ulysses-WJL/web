from flask import request, session, redirect, url_for, render_template
from . import user_bp
from .. import db
from ..models import User

@user_bp.route('/add/', methods=['GET', 'POST'])
def add():
    # 添加user数据
    if request.method == 'POST':
        # 没有则为None
        old_name = session.get('name')
        p_name = request.form.get('user_name', None)
        p_passwd = request.form.get('user_passwd', None)
        p_roleid = request.form.get('role_id', None)
        
        if p_name is not None and p_name != old_name:
            user = User.query.filter_by(user_name=p_name).first()
            if user is None:
                # logging.info(f'name:{p_name}')
                # role_id 主键数据库自动生成
                newobj = User(user_name=p_name, password=p_passwd, role_id=p_roleid)
                
                db.session.add(newobj)
                db.session.commit()
                session['name'] = p_name
        # roles = Role.query.all()
        # add界面
        # 指定一个蓝本名称作为端点的一部分
        return redirect(url_for('user_bp.add'))
    users = User.query.order_by('user_id')
    return render_template('user/add.html', users=users)
