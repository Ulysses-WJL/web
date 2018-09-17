from flask import render_template, redirect, session, url_for, current_app, request
from datetime import datetime
from . import main_bp
from ..models import User
from .forms import NameForm
from .. import db
from ..email import send_email
import logging
logging.basicConfig(format="%(asctime)s%(message)s", level=logging.INFO)


@main_bp.route('/', methods=['GET', 'POST'])
def index():
    # name = None
    form = NameForm()
    # Call :meth:`validate` only if the form is submitted.
    #  This is a shortcut for ``form.is_submitted() and form.validate()``.
    # 当表单被提交时，调用验证函数， 返回 是否提交了表单&内容是否为空
    if form.validate_on_submit():
        # name = form.name.data # 表单的数据，空则为''
        user = User.query.filter_by(user_name=form.name.data).first()
        if user is None:
            user = User(user_name=form.name.data)
            user.password = '123456'
            db.session.add(user)
            db.session.commit()
            session['know'] = False
            # flask 邮件发送
            # ogging.info(f"admin:{app.config['FLASK_ADMIN']}, user: {user}, sender:{mail_user}")
            if current_app.config['FLASK_ADMIN']:
                # 向admin（2276777056@qq.com）发送邮件
                logging.info(f"admin: {current_app.config['FLASK_ADMIN']}, user:{user}")
                send_email(current_app.config['FLASK_ADMIN'], 'New User', 'mail/new_user', user=user)
        else:
            session['know'] = True
        session['name'] = form.name.data
        form.name.data = ''
        return redirect(url_for('main_bp.index'))  # 提交数据后，回到index页面，数据被保存在session中
        # form.name.data = ''
    # 渲染模板
    return render_template(
        'index.html',
        url=url_for(
            'static',
            filename='favicron.ico'),
        form=form,
        name=session.get('name'),
        current_time=datetime.utcnow(),
        know=session.get('know', False))
    # 静态文件favicron.ico
