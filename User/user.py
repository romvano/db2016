from flask import Blueprint, request, g, jsonify
import MySQLdb as db
from itertools import chain
import bisect
from common.common import *

User = Blueprint('user', __name__)

user_fields = ['id', 'username', 'about', 'name', 'email', 'isAnonymous']

def select_from_user_where(key, value):
    return select_from_where('User', user_fields, key, value)

def select_followers(user):
    query = 'SELECT follower FROM Followee WHERE name = "' + user + '";'
    return list(chain.from_iterable(select(query)))

def select_followees(user):
    query = 'SELECT followee FROM Follower WHERE name = "' + user + '";'
    return list(chain.from_iterable(select(query)))

def select_subscriptions(user):
    query = 'SELECT thread FROM Subscription WHERE name = %s;'
    return list(chain.from_iterable(select(query, (user,))))

@User.route('create/', methods = ['POST']) 
def user_create():
    data = get_post_data(request)
    if not {'username', 'about', 'name', 'email'} <= set(data.keys()):
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    data['isAnonymous'] = data.get('isAnonymous', False)
    return jsonify(create('User', data, user_fields, 'email', data['email']))

def get_user_where(key, value):
    response = select_from_user_where(key, value)
    if not response:
        return None
    response['followers'] = select_followers(response['email'])
    response['following'] = select_followees(response['email'])
    response['subscriptions'] = select_subscriptions(response['email'])
    return response


@User.route('details/', methods=['GET'])
def user_details():
    data = get_get_data(request)
    if 'user' not in data.keys():
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    try:
        response = get_user_where('email', data['user'])
    except db.Error as e:
        return jsonify({ 'code': 4, 'response': str(e) })
    else:
        if not response:
            return jsonify({ 'code': 1, 'response': 'User not found' })
        return jsonify({ 'code': 0, 'response': response })

@User.route('follow/', methods=['POST'])
@User.route('unfollow/', methods=['POST'])
def set_following():
    url = request.url_rule.rule
    action = url.rsplit('/', 2)[1] # follow or unfollow
    follower = request.json.get('follower').encode('utf-8')
    followee = request.json.get('followee').encode('utf-8')
    if not follower or not followee:
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    try:
        if action == 'follow':
            g.cursor.execute('INSERT INTO Follower(name, followee) VALUES ("%s", "%s"); ' % (follower, followee))
            g.cursor.execute('INSERT INTO Followee(name, follower) VALUES ("%s", "%s"); ' % (followee, follower))
        elif action == 'unfollow':
            g.cursor.execute('DELETE FROM Follower WHERE name = "%s" AND followee = "%s";' % (follower, followee))
            g.cursor.execute('DELETE FROM Followee WHERE name = "%s" AND follower = "%s";' % (followee, follower))
    except db.IntegrityError:
        g.connection.rollback()
    else:
        g.connection.commit()
    finally:
        return jsonify({ 'code': 0, 'response': select_from_user_where('email', follower) })

@User.route('updateProfile/', methods=['POST'])
def update_user():
    data = get_post_data(request)
    if not {'about', 'user', 'name'} <= set(data.keys()):
        return jsonify({ 'code': 2, 'response': 'json error' })
    return jsonify(update(
        'User',
        { 'about': data['about'].join('""'), 'name': data['name'].join('""') },
        { 'email': data['user'].join('""') },
        lambda: (select_from_user_where('email', data['user']))
    ))

@User.route('listFollowers/', methods=['GET'])
@User.route('listFollowing/', methods=['GET'])
def list_followers():
    url = request.url_rule.rule
    action = url.rsplit('/', 2)[1] # which list?
    data = get_get_data(request)
    if not 'user' in data.keys():
        return jsonify({ 'code': 2, 'response': 'json error' })
    (table, email) = ('Followee', 'follower') if action == 'listFollowers' else ('Follower', 'followee')
    return list_users_where_email(table, email, data, { 'name': data['user'] })

