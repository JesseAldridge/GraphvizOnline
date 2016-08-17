import os, json, glob
from datetime import datetime, timedelta
from functools import wraps

import flask
from flask import request

import secrets


app = flask.Flask(__name__)
port = int(os.environ.get('PORT', 3000))

def check_auth(username, password):
    return username == secrets.username and password == secrets.password

def authenticate():
    return flask.Response(
    'Could not verify your access level for that URL.\n'
    'You have to login with proper credentials', 401,
    {'WWW-Authenticate': 'Basic realm="Login Required"'})

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return authenticate()
        return f(*args, **kwargs)
    return decorated


@app.route('/')
@requires_auth
def index():
    res = flask.render_template('index.html')
    return res

@app.route('/get_latest')
@requires_auth
def latest_text():
    paths = list(sorted(glob.glob('versions/*.dot')))
    if not paths:
        return 'digraph G {\n\n}'
    with open(paths[-1]) as f:
        return f.read()

@app.route('/update_text', methods=['POST'])
@requires_auth
def update_text():
    text = json.loads(request.data)['text']
    if not os.path.exists('versions'):
        os.mkdir('versions')
    out_path = os.path.join('versions/{}.dot'.format(datetime.now()))
    prev_paths = glob.glob('versions/*.dot')
    if prev_paths:
        prev_dt_str = prev_paths[-1].rsplit('.dot', 1)[0].split('versions/', 1)[1]
        prev_dt = datetime.strptime(prev_dt_str, '%Y-%m-%d %H:%M:%S.%f')
        if datetime.now() - prev_dt < timedelta(minutes=5):
            out_path = prev_paths[-1]
    with open(out_path, 'w') as f:
        f.write(text)
    return 'ok'

if __name__ == '__main__':
    # Bind to PORT if defined, otherwise default to 3000.
    port = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=port, debug=(port==3000))
