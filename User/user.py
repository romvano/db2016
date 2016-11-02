from flask import Blueprint, request, g, jsonify
import MySQLdb as db

User = Blueprint('user', __name__)

def get_post_data(request):
    return dict((k.encode('utf-8'), str(v).encode('utf-8')) for (k, v) in request.json.items())

def select_from_user_where(what, key, value):
    if what == '*':
        what = ['id', 'username', 'about', 'name', 'email', 'isAnonymous']
    query = 'SELECT ' + ', '.join(what) + ' FROM User WHERE ' + key + '="' + value + '";'
    g.cursor.execute(query)
    selected = g.cursor.fetchall()[0]
    result = dict(zip(what, selected))
    return result

@User.route('create/', methods = ['POST']) 
def user_create():
    try:
        data = get_post_data(request)
        if 'isAnonymous' not in data.keys():
            data['isAnonymous'] = 'false'
        g.cursor.execute(
            'INSERT INTO User(username, about, name, email, isAnonymous) \
             VALUES ("%(username)s", "%(about)s", "%(name)s", "%(email)s", %(isAnonymous)s);' % data)
        data['id'] = g.cursor.lastrowid
        g.connection.commit()
        return jsonify({ 'code': 0, 'response': data })
    except db.IntegrityError as ie:
        g.connection.rollback()
        return jsonify({ 'code': 5, 'response': str(ie)})
    except Exception as e:
        g.connection.rollback()
        return jsonify({ 'code': 2, 'response': str(e) })

@User.route('details/', methods=['GET'])
def user_details():
    try:
        email = request.args.get('user')
        if not email:
            return jsonify({ 'code': 3, 'response': 'Bad request' })
        response = select_from_user_where('*', 'email', email)
        if response is None:
            return jsonify({ 'code': 1, 'response': 'User not found' })
        print response
        for k in response.keys():
            if response[ k ] == 'None':
                response[ k ] = None
#        response['followers'] = TODO
#        response['followees'] = TODO
#        response['subscriptions'] = TODO
        return jsonify({ 'code': 0, 'response': response })
    except Exception as e:
        return jsonify({ 'code': 4, 'response': str(e) })

@User.route('follow/', methods=['POST'])
@User.route('unfollow/', methods=['POST'])
def set_following():
    url = request.url_rule.rule
    action = url.rsplit('/', 2)[1] # follow or unfollow
    print action
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

