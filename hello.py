from flask import render_template, Flask

app = Flask(__name__)


@app.route('/')
def index():
    # 渲染模板
    return render_template('index.html')


@app.route('/user/<name>')
def hello(name):
    return render_template('user.html', name=name)


if __name__ == '__main__':
    app.run(debug=True, port=8888)
