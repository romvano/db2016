from flask import Blueprint, request, g, jsonify
import MySQLdb as db
from itertools import chain
import bisect

User = Blueprint('user', __name__)

user_fields = ['id', 'username', 'about', 'name', 'email', 'isAnonymous']

def get_post_data(request):
    return dict((k.encode('utf-8'), str(v).encode('utf-8')) for (k, v) in request.json.items())

def get_get_data(request):
    return dict((k, request.args[k]) for k in request.args)

def select(query):
    g.cursor.execute(query)
    result = g.cursor.fetchall()
    return result

def select_from_user_where(what, key, value):
    if what == '*':
        what = user_fields
    query = 'SELECT ' + ', '.join(what) + ' FROM User WHERE ' + key + '="' + value + '";'
    selected = select(query)[0]
    if not selected:
        return {}
    return dict(zip(what, selected))

def select_followers(user):
    query = 'SELECT follower FROM Followee WHERE name = "' + user + '";'
    return list(chain.from_iterable(select(query)))

def select_followees(user):
    query = 'SELECT followee FROM Follower WHERE name = "' + user + '";'
    return list(chain.from_iterable(select(query)))

@User.route('create/', methods = ['POST']) 
def user_create():
    data = get_post_data(request)
    if 'isAnonymous' not in data.keys():
        data['isAnonymous'] = 'false'
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

@User.route('details/', methods=['GET'])
def user_details():
    data = get_get_data(request)
    if 'user' not in data.keys():
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    try:
        response = select_from_user_where('*', 'email', data['user'])
    except Exception as e:
        return jsonify({ 'code': 4, 'response': str(e) })
    else:
        if not response:
            return jsonify({ 'code': 1, 'response': 'User not found' })
        for k in response.keys():
            if response[k] == 'None':
                response[k] = None
        response['followers'] = select_followers(data['user'])
        response['followees'] = select_followees(data['user'])
#        response['subscriptions'] = TODO
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
        return jsonify({ 'code': 0, 'response': select_from_user_where('*', 'email', follower) })

@User.route('updateProfile/', methods=['POST'])
def update_user():
    data = get_post_data(request)
    if not {'about', 'user', 'name'} <= set(data.keys()):
        return jsonify({ 'code': 2, 'response': 'json error' })
    try:
        g.cursor.execute('UPDATE User SET User.about = "%(about)s", \
                                          User.name = "%(name)s" WHERE User.email = "%(user)s";' % data)
    except Exception as e:
        return jsonify({ 'code': 4, 'response': str(e) })
    else:
        g.connection.commit()
        if g.cursor.rowcount == 0:
            return jsonify({ 'code': 1, 'response': 'User not found' })
    finally:
        return jsonify({ 'code': 0, 'response': select_from_user_where('*', 'email', data['user']) })

def minimize_response(response):
    # TODO add subscriptions
    response = list(dict(zip(user_fields + ['followers', 'followees'], l)) for l in response)
    new_response = response.pop()
    new_response['followers'] = [] if new_response['followers'] is None else [new_response['followers']]
    new_response['followees'] = [] if new_response['followees'] is None else [new_response['followees']]
    new_response = [new_response]
    for d in response:
        # followers - first index
        # followees - second index
        if new_response[-1]['email'] == d['email']: # email remains the same
            new_response[-1]['followers'].append(d['followers']) # 1st index
            if bisect.bisect_left(new_response[-1]['followees'], d['followees']) == len(new_response[-1]['followees']):
                new_response[-1]['followees'].append(d['followees'])
        else:
            new_response.append(d)
            new_response[-1]['followers'] = [new_response[-1]['followers']]
            new_response[-1]['followees'] = [new_response[-1]['followees']]
    return new_response

@User.route('listFollowers/', methods=['GET'])
def list_followers():
    data = get_get_data(request)
    if not 'user' in data.keys():
        return jsonify({ 'code': 2, 'response': 'json error' })
    # add subscription query here TODO
    query = 'SELECT u.' + ', u.'.join(user_fields) + ', fe.follower, fr.followee \
             FROM User u LEFT JOIN Followee f ON u.email = f.follower \
                         LEFT JOIN Followee fe ON u.email = fe.name \
                         LEFT JOIN Follower fr ON u.email = fr.name \
             WHERE f.name = "%(user)s"' % data
    if 'since_id' in data.keys():
        if data['since_id'].isalnum():
            query += ' AND u.id >= %(since_id)s' % data
        else:
            return jsonify({ 'code': 2, 'response': 'json error in since_id' })
    if 'order' in data.keys():
        if data['order'] == 'asc':
            query += ' ORDER BY f.follower ASC'
        elif data['order'] == 'desc':
            query += ' ORDER BY f.follower DESC'
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
        response = minimize_response(response)
        return jsonify({ 'code': 0, 'response': response })
