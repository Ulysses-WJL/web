from flask import Flask, session, render_template, url_for, redirect
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms.validators import DataRequired,equal_to
from wtforms import SubmitField, StringField, PasswordField

app = Flask(__name__)
bootstrap = Bootstrap(app)
app.config['SECRET_KEY'] = 'login secret key'


class PassForm(FlaskForm):
    name = StringField('Input your name:', validators=[DataRequired()])
    passwd = PasswordField('Input your password:', validators=[DataRequired()])
    submit = SubmitField('Enter')
    
@app.route('/', methods=['GET', 'POST'])
def index():
    form = PassForm()
    if form.validate_on_submit():
        old_name = session.get('name')
        old_passwd = session.get('passwd')
        if not (old_name == 'admin') and (old_passwd == '123456') :
            flash('非admin')
        return redirect(urlfor('index'))
        
    session['name'] = form.name.data
    session['passwd'] = form.passwd.data
    
    return render_template('index.html', form=form)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)