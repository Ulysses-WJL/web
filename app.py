from flask import Flask, request, make_response, redirect, abort

app = Flask(__name__)


@app.route('/')
def hello_world():
    # request 请求对象 封装了HTTP请求中的内容
    # 获取request Header中的内容
    user_agent = request.headers.get('User-Agent')
    host = request.headers.get('Host')
    remote_addr_ = request.remote_addr
    resp = make_response(f"""<h1>Hello World!</h1>
           <p>Your browser is {user_agent}</p>
           <p>The host is {host}</p>
           <p>The remote addr is {remote_addr_}</p>""")
    resp.status_code = 200

    # return '<h1>Hello World!</h1>' \
    #        f'<p>Your browser is {user_agent}</p>' \
    #        f'<p>The host is {host}</p>' \
    #        f'<p>The remote addr is {remote_addr_}</p>', 200
    return resp


# 动态路由
@app.route('/<name>')
def hello_1(name):
    return f'<h1>Hello, {name}!</h1>'


@app.route('/<int:id_>')
def hello_id(id_):
    if id_ == 325608:
        return redirect('https://www.baidu.com')
    elif id_ == 404:
        abort(404)
    return f'<h1>Welcome: {id_}</h1>'


if __name__ == '__main__':

    app.run(debug=True)
