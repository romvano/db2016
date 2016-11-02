from flask import Flask, request, g
import MySQLdb as db
from common.common import common
from User.user import User

BASE = '/db/api/'

app = Flask(__name__)
app.config.from_object('config')
app.register_blueprint(common, url_prefix=BASE)
app.register_blueprint(User, url_prefix=BASE+'user/')

@app.before_request
def connect():
    g.connection = db.connect(
        host = '127.0.0.1',
        user = 'tpdb',
        passwd = 'tpdb',
        db = 'dbforumtry1',
        charset = 'utf8'
    )
    g.cursor = g.connection.cursor()

@app.teardown_request
def disconnect(e):
    g.connection.close()

if __name__ == '__main__':
    app.run()
