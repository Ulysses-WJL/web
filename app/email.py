import logging
from flask import render_template, current_app
from . import mail
from flask_mail import Message
from threading import Thread

logging.basicConfig(format='%(asctime)s%(message)s', level=logging.INFO)
def send_asyn_email(app, msg):
    # 应用上下文，对flask一切对象的封装
    with app.app_context():
        mail.send(msg)


def send_email(to, subject, template, **kwargs):
    # 作用是获取本线程的应用实例以作为参数传递给其他线程使用
    app = current_app._get_current_object()
    logging.info(f"sender:{app.config['FLASKY_MAIL_SENDER']}, recipient: {to}")
    msg = Message(app.config['FLASKY_MAIL_SUBJECT_PREFIX'] + ' '+subject,
                  sender=app.config['FLASKY_MAIL_SENDER'], recipients=[to])
    msg.body = render_template(template + '.txt', **kwargs)
    msg.html = render_template(template+ '.html', **kwargs)
    thr = Thread(target=send_asyn_email, args=[app, msg])
    thr.start()
    return thr
    # mail.send(msg)