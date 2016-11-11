from flask import Blueprint, request, g, jsonify
import MySQLdb as db
from itertools import chain
import bisect
from common.common import get_post_data, get_get_data, select, select_from_where, create, update

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

@User.route('create/', methods = ['POST']) 
def user_create():
    data = get_post_data(request)
    data['isAnonymous'] = data.get('isAnonymous', False)
    return create('User', data, 'email', data['email'])
    try:
        g.cursor.execute(
            'INSERT INTO User(username, about, name, email, isAnonymous) \
             VALUES ("%(username)s", "%(about)s", "%(name)s", "%(email)s", %(isAnonymous)s);' % data)
    except db.IntegrityError as ie:
        g.connection.rollback()
        return jsonify({ 'code': 5, 'response': str(ie)})
    except Exception as e:
        g.connection.rollback()
        return jsonify({ 'code': 2, 'response': str(e) })
    else:
        data['id'] = g.cursor.lastrowid
        g.connection.commit()
        return jsonify({ 'code': 0, 'response': data })

def get_user_where(key, value):
    response = select_from_user_where(key, value)
    if not response:
        return None
    response['followers'] = select_followers(response['email'])
    response['followees'] = select_followees(response['email'])
    # response['subscriptions'] = select_subscriptions(response['email'])
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
        return jsonify({ 'code': 2, 'response': 'json error' })
    try:
        if action == 'follow':
            g.cursor.execute('INSERT INTO Follower(name, followee) VALUES ("%s", "%s"); ' % (follower, followee))
            g.cursor.execute('INSERT INTO Followee(name, follower) VALUES ("%s", "%s"); ' % (followee, follower))
        elif action == 'unfollow':
            g.cursor.execute('DELETE FORM Follower WHERE name = "%s" AND followee = "%s";' % (follower, followee))
            g.cursor.execute('DELETE FORM Followee WHERE name = "%s" AND follower = "%s";' % (followee, follower))
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
    return update(
        'User',
        { 'about': data['about'], 'name': data['name'] },
        { 'email': data['user'] },
        select_from_user_where('email', data['user'])
    )

def minimize_response(response, ls):
    # TODO add subscriptions
    (first, second) = ('followers', 'following') if ls == 'listFollowers' else ('following', 'followers')
    response = list(dict(zip(user_fields + ['followers', 'following'], l)) for l in response)
    new_response = response.pop()
    new_response[first] = [] if new_response[first] is None else [new_response[first]]
    new_response[second] = [] if new_response[second] is None else [new_response[second]]
    new_response = [new_response]
    for d in response:
        # followers - first index
        # following - second index
        if new_response[-1]['email'] == d['email']: # email remains the same
            new_response[-1][first].append(d[first]) # 1st index
            if bisect.bisect_left(new_response[-1][second], d[second]) == len(new_response[-1][second]):
                new_response[-1][second].append(d[second])
        else:
            new_response.append(d)
            new_response[-1][first] = [new_response[-1][first]]
            new_response[-1][second] = [new_response[-1][second]]
    return new_response

@User.route('listFollowers/', methods=['GET'])
@User.route('listFollowing/', methods=['GET'])
def list_followers():
    url = request.url_rule.rule
    action = url.rsplit('/', 2)[1] # which list?
    data = get_get_data(request)
    if not 'user' in data.keys():
        return jsonify({ 'code': 2, 'response': 'json error' })
    # add subscription query here TODO
    query = 'SELECT u.' + ', u.'.join(user_fields) + ', fe.follower, fr.followee \
             FROM User u LEFT JOIN Followee f ON u.email = f.follower \
                         LEFT JOIN Followee fe ON u.email = fe.name \
                         LEFT JOIN Follower fr ON u.email = fr.name \
             WHERE f.name = "%(user)s"' % data \
             if action == 'listFollowers' else \
            'SELECT u.' + ', u.'.join(user_fields) + ', fr.followee, fe.follower \
             FROM User u LEFT JOIN Follower f ON u.email = f.followee \
                         LEFT JOIN Follower fr ON u.email = fr.name \
                         LEFT JOIN Followee fe ON u.email = fe.name \
             WHERE f.name = "%(user)s"' % data
    if 'since_id' in data.keys():
        if data['since_id'].isalnum():
            query += ' AND u.id >= %(since_id)s' % data
        else:
            return jsonify({ 'code': 2, 'response': 'json error in since_id' })
    if 'order' in data.keys():
        if data['order'] == 'asc':
            query += ' ORDER BY f.follower ASC' if action == 'listFollowers' else ' ORDER BY f.followee ASC'
        elif data['order'] == 'desc':
            query += ' ORDER BY f.follower DESC' if action == 'listFollowers' else ' ORDER BY f.followee DESC'
        else:
            return jsonify({ 'code': 2, 'response': 'json error in order' })
    if 'limit' in data.keys():
        if data['limit'].isalnum() and int(data['limit']) >= 0:
            query += ' LIMIT ' + data['limit']
        else:
            return jsonify({ 'code': 2, 'response': 'json error in limit' })
    query += ';'
    try:
        response = select(query)
    except Exception as e:
        return jsonify({ 'code': 4, 'response': str(e) })
    else:
        if not response:
            return jsonify({ 'code': 1, 'response': 'user not found' })
        response = minimize_response(response, action)
        return jsonify({ 'code': 0, 'response': response })
