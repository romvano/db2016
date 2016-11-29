from flask import Flask, request, g
import MySQLdb as db
from common.common import common
from User.user import User
from Forum.forum import Forum
from Thread.thread import Thread
from Post.post import Post

BASE = '/db/api/'

app = Flask(__name__)
app.config.from_object('config')
app.register_blueprint(common, url_prefix=BASE)
app.register_blueprint(User, url_prefix=BASE+'user/')
app.register_blueprint(Forum, url_prefix=BASE+'forum/')
app.register_blueprint(Thread, url_prefix=BASE+'thread/')
app.register_blueprint(Post, url_prefix=BASE+'post/')

@app.before_request
def connect():
    g.connection = db.connect(
        host = '127.0.0.1',
        user = 'dbapi',
        passwd = 'dbapi',
        db = 'dbapi',
        charset = 'utf8'
    )
    g.cursor = g.connection.cursor()

@app.teardown_request
def disconnect(e):
    g.connection.close()

if __name__ == '__main__':
    app.run()
