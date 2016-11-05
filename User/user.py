from flask import Blueprint, request, g, jsonify
import MySQLdb as db

User = Blueprint('user', __name__)

user_fields = ['id', 'username', 'about', 'name', 'email', 'isAnonymous']

def get_post_data(request):
    return dict((k.encode('utf-8'), str(v).encode('utf-8')) for (k, v) in request.json.items())

def get_get_data(request):
    return dict((k, request.args[k]) for k in request.args)

def select(query):
    g.cursor.execute(query)
# () == ()
    return g.cursor.fetchall()[0]

def select_from_user_where(what, key, value):
    if what == '*':
        what = user_fields
    query = 'SELECT ' + ', '.join(what) + ' FROM User WHERE ' + key + '="' + value + '";'
    selected = select(query)
    return dict(zip(what, selected))

def select_followers(user):
    query = 'SELECT follower FROM Followee WHERE name = "' + user + '";'
    #selected = select(query)
    g.cursor.execute(query)
    selected = g.cursor.fetchall()
    print '\n' + str(selected) + '\n'
    if selected is None:
        return []
    return selected[0]

def select_followees(user):
    query = 'SELECT followee FROM Follower WHERE name = "' + user + '";'
    #selected = select(query)
    g.cursor.execute(query)
    selected = g.cursor.fetchall()
    if selected is None:
        return []
    return selected[0]


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
        if response is None:
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

@User.route('listFollowers/', methods=['GET'])
def list_followers():
    data = get_get_data(request)
    if not 'user' in data.keys():
        return jsonify({ 'code': 2, 'response': 'json error' })
    query = 'SELECT u.' + ', u.'.join(user_fields) + ' FROM User u INNER JOIN Followee f ON u.email = f.name WHERE u.email = "%(user)s"' % data
    if 'since_id' in data.keys():
        if data['since_id'].isalnum():
            query += ' AND u.id >= %(since_id)s' % data
        else:
            return jsonify({ 'code': 2, 'response': 'json error in since_id' })
    if 'order' in data.keys():
        if data['order'] == 'asc':
            query += ' ORDER BY f.name ASC'
        elif data['order'] == 'desc':
            query += ' ORDER BY f.name DESC'
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
        if response is None:
            return jsonify({ 'code': 1, 'response': 'user not found' })
        response = dict(zip(user_fields, response))
        response['followers'] = select_followers(data['user'])
        response['followees'] = select_followees(data['user'])
        return jsonify({ 'code': 0, 'response': response })
