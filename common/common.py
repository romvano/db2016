from flask import Blueprint, jsonify, g
import MySQLdb as db
import json

common = Blueprint('common', __name__)

tables = [
    'User',
    'Thread',
    'Forum',
    'Post',
    'Follower',
    'Followee',
    'Subscription',
    'PostHierarchy',
]

user_fields = ['id', 'username', 'about', 'name', 'email', 'isAnonymous']
post_fields_to_insert = ['date', 'forum', 'isApproved', 'isDeleted', 'isEdited', 'isHighlighted', 'isSpam', 'message', 'parent', 'thread', 'user']
post_fields = ['id'] + post_fields_to_insert + ['likes', 'dislikes', 'points']
thread_fields_to_insert = ['forum', 'title', 'isClosed', 'user', 'date', 'message', 'slug', 'isDeleted']
thread_fields = ['id'] + thread_fields_to_insert + ['dislikes', 'likes', 'points', 'posts']
forum_fields_to_insert = ['name', 'short_name', 'user']
forum_fields = ['id'] + forum_fields_to_insert

def get_post_data(request):
    return dict((k, v) for (k, v) in request.json.items())

def get_get_data(request):
    return dict(request.args.items())

def select(query, params=()):
    g.cursor.execute(query, params)
    print g.cursor._last_executed
    result = g.cursor.fetchall()
    return result

def select_from_where(table, what='', key=None, value=None):
    query = 'SELECT ' + ', '.join(what) + ' FROM ' + table + ' WHERE ' + key + '= %s;'
    params = (value,)
    selected = select(query, params)
    if not selected:
        return None
    result = dict(zip(what, selected[0]))
    if 'date' in result:
        result['date'] = result['date'].strftime('%Y-%m-%d %H:%M:%S')
    return result

def create_update_exceptions(table, e, success):
    print g.cursor._last_executed
    g.connection.rollback()
    if e == db.IntegrityError:
        if table == 'User':
            return { 'code': 5, 'response': str(e)}
        return { 'code': 0, 'response': success }
    if e == db.DataError:
        return { 'code': 2, 'response': str(e) }
    if e == db.Error:
        return { 'code': 4, 'response': str(e) }
    raise Exception()
   
def create(table, data, *select_args):
    try:
        query = 'INSERT INTO ' + table + '(' + ', '.join(data.keys()) + ') \
                 VALUES (' + '%s, '*(len(data) - 1) + '%s);'
        g.cursor.execute(query, tuple(data.values()))
    except Exception as e:
        success = data if not select_args else select_from_where(table, *select_args)
        return create_update_exceptions(table, type(e), success)
    else:
        data['id'] = g.cursor.lastrowid
        g.connection.commit()
        return { 'code': 0, 'response': data }

def update(table, data, clause, success):
    query = 'UPDATE ' + table + ' SET '
    for i, field in enumerate(data):
        query += table + '.' + field + ' = ' + '%s'
        query += ', ' if i < len(data)-1 else ''
    query += ' WHERE '
    query = query % tuple(data.values())
    for i, field in enumerate(clause):
        query += table + '.' + field + ' = ' + '%s'
        query += ' AND ' if i < len(clause)-1 else ';'
    query = query % tuple(clause.values())
    try:
        g.cursor.execute(query)#, tuple(clause.values()))
    except Exception as e:
        return create_update_exceptions(table, e, success())
    else:
        if g.cursor.rowcount == 0:
            return { 'code': 1, 'response': 'No object was changed' }
    finally:
        print g.cursor._last_executed
        g.connection.commit()
        return { 'code': 0, 'response': success() }

def delete(table, clause, success):
    query = 'DELETE FROM ' + table + ' WHERE ' 
    for i, field in enumerate(clause):
        query += table + '.' + field + ' = ' + '%s'
        query += ' AND ' if i < len(clause)-1 else ';'
    try:
        g.cursor.execute(query, tuple(clause.values()))
    except Exception as e:
        return create_update_exceptions(table, e, success)
    else:
        if g.cursor.rowcount == 0:
            return { 'code': 1, 'response': 'No object was changed' }
    finally:
        print g.cursor._last_executed
        g.connection.commit()
        return { 'code': 0, 'response': success }

def minimize_response(response, default_fields, main_field, additional_fields=[]):
    response = list(dict(zip(default_fields + additional_fields, l)) for l in response)
    new_response = response.pop(0)
    for f in additional_fields:
        new_response[f] = [] if new_response[f] is None else [new_response[f]]
    new_response = [new_response]
    for d in response:
        if new_response[-1][main_field] == d[main_field]: # email remains the same
            for f in additional_fields:
                if new_response[-1][f] != d[f] and d[f] is not None:
                    new_response[-1][f].append(d[f])
        else:
            new_response.append(d)
            for f in additional_fields:
                new_response[-1][f] = [] if new_response[-1][f] is None else [new_response[-1][f]]
    return new_response

def list_users_where_email(table, email, data, clause):
    query = 'SELECT DISTINCT u.' + ', u.'.join(user_fields) + ', GROUP_CONCAT(fe.follower), GROUP_CONCAT(fr.followee), GROUP_CONCAT(s.thread) \
             FROM User u LEFT JOIN ' + table + ' t ON u.email = t.' + email + ' \
                         LEFT JOIN Followee fe ON u.email = fe.name \
                         LEFT JOIN Follower fr ON u.email = fr.name \
                         LEFT JOIN Subscription s ON u.email = s.name \
             WHERE '
    for i, field in enumerate(clause):
        query += 't.' + field + ' = ' + '%s'
        query += ' AND ' if i < len(clause)-1 else ''
    if 'since_id' in data.keys():
        if data['since_id'].lstrip('-').isdigit():
            query += ' AND u.id >= %(since_id)s' % data
        else:
            return jsonify({ 'code': 2, 'response': 'json error in since_id' })
    query += ' GROUP BY u.email '
    if 'order' in data.keys():
        if data['order'] == 'asc':
            query += ' ORDER BY u.name ASC'
        elif data['order'] == 'desc':
            query += ' ORDER BY u.name DESC'
        else:
            return jsonify({ 'code': 2, 'response': 'json error in order' })
    if 'limit' in data.keys():
        if not (data['limit'].lstrip('-').isdigit() and int(data['limit']) >= 0):
            return jsonify({ 'code': 2, 'response': 'json error in limit' })
        query += ' LIMIT %s ' % data['limit']
    query += ';'
    try:
        response = select(query, clause.values())
    except db.Error as e:
        return jsonify({ 'code': 4, 'response': str(e) })
    else:
        if not response:
            response = []
        else:
            response = [dict(zip(user_fields, l) +
                             [('followers', [] if l[-3] is None else l[-3].split(','))] +
                             [('following', [] if l[-2] is None else l[-2].split(','))] +
                             [('subscriptions', [] if l[-1] is None else [int(k) for k in l[-1].split(',')])]
                        ) for l in response]
        return jsonify({ 'code': 0, 'response': response })

@common.route('clear/', methods=['POST'])
def clear():
    try:
        for table in tables:
            g.cursor.execute('TRUNCATE %s;' % table)
        return jsonify({ 'code': 0, 'response': 'OK' })
    except db.Error as e:
        g.connection.rollback()
        return jsonify({ 'code': 4, 'response': str(e) })

@common.route('status/', methods=['GET'])
def status():
    try:
        response = {}
        for table in tables:
            g.cursor.execute('SELECT COUNT(*) FROM %s' % table)
            response[table] = g.cursor.fetchone()[0]
        return jsonify({ 'code': 0, 'response': response })
    except:
        g.connection.rollback()
        return jsonify({ 'code': 1, 'response': str(e) })

def list_threads_where(data, clause):
    query = 'SELECT DISTINCT t.' + ', t.'.join(thread_fields)
    forum = 'forum' in data['related']
    user = 'user' in data['related']
    join = 'user' if user else 'forum'
    if forum:
        query += ', f.' + ', f.'.join(forum_fields)
    if user:
        query += ', u.' + ', u.'.join(user_fields) + ', GROUP_CONCAT(fe.follower), GROUP_CONCAT(fr.followee), GROUP_CONCAT(s.thread)'
    query += ' FROM Thread t LEFT JOIN ' + join.capitalize() + ' ' + join[0] + ' ON t.' + join + ' = ' + join[0] + '.'
    query += 'email ' if join == 'user' else 'short_name '
    if forum and join != 'forum':
        query += ' LEFT JOIN Forum f ON t.forum = f.short_name '
    if user:
        if join != 'user':
            query += ' LEFT JOIN User u ON t.user = u.email '
        query += ' LEFT JOIN Followee fe ON t.user = fe.name \
                   LEFT JOIN Follower fr ON t.user = fr.name \
                   LEFT JOIN Subscription s ON t.user = s.name '
    query += ' WHERE '
    for i, field in enumerate(clause):
        query += 't.' + field + ' = ' + '%s'
        query += ' AND ' if i < len(clause)-1 else ''
    if 'since' in data.keys():
        query += ' AND t.date >= "%(since)s"' % data
    if user:
        query += ' GROUP BY t.id '
    if 'order' in data.keys():
        if data['order'] == 'asc':
            query += ' ORDER BY t.date ASC'
        elif data['order'] == 'desc':
            query += ' ORDER BY t.date DESC'
        else:
            return jsonify({ 'code': 2, 'response': 'json error in order' })
    if 'limit' in data.keys():
        if not (data['limit'].lstrip('-').isdigit() and int(data['limit']) >= 0):
            return jsonify({ 'code': 2, 'response': 'json error in limit' })
        query += ' LIMIT %s ' % data['limit']
    query += ';'
    try:
        response = select(query, clause.values())
    except db.Error as e:
        print str(e)
        return jsonify({ 'code': 4, 'response': str(e) })
    else:
        if not response:
            response = []
        else:
            new_response = []
            for l in response:
                zipped = zip(thread_fields, l)
                i = len(thread_fields)
                if forum:
                    zipped.append(('forum', dict(zip(forum_fields, l[i:i + len(forum_fields)]))))
                    i += len(forum_fields)
                if user:
                    u = dict(zip(user_fields, l[i:-3]))
                    u.update({'followers': [] if l[-3] is None else l[-3].split(',')})
                    u.update({'following': [] if l[-2] is None else l[-2].split(',')})
                    u.update({'subscriptions': [] if l[-1] is None else [int(k) for k in l[-1].split(',')]})
                    zipped.append(('user', u))
                new_el = dict(zipped)
                new_el['date'] = new_el['date'].strftime('%Y-%m-%d %H:%M:%S')
                new_response.append(new_el)
            response = new_response
        return jsonify({ 'code': 0, 'response': response })

def list_posts_where(data, clause, sort='flat'):
    query = 'SELECT DISTINCT p.' + ', p.'.join(post_fields)
    join = 'thread' if 'thread' in data else 'forum'
    forum = 'forum' in data['related']
    thread = 'thread' in data['related']
    user = 'user' in data['related']
    if forum:
        query += ', f.' + ', f.'.join(forum_fields)
    if thread:
        query += ', t.' + ', t.'.join(thread_fields)
    if user:
        query += ', u.' + ', u.'.join(user_fields) + ', fe.follower, fr.followee, s.thread'
    query += ' FROM Post p LEFT JOIN ' + join.capitalize() + ' ' + join[0] + ' ON p.' + join + ' = ' + join[0] + '.'
    query += 'id ' if join == 'thread' else 'short_name '
    if sort != 'flat':
        query += ' LEFT JOIN PostHierarchy ph ON p.id = ph.post '
    if forum and join != 'forum':
        query += ' LEFT JOIN Forum f ON p.forum = f.short_name'
    if thread and join != 'thread':
        query += ' LEFT JOIN Thread t ON p.thread = t.id '
    if user:
        query += ' LEFT JOIN User u ON p.user = u.email \
                   LEFT JOIN Followee fe ON p.user = fe.name \
                   LEFT JOIN Follower fr ON p.user = fr.name \
                   LEFT JOIN Subscription s ON p.user = s.name '
    query += ' WHERE '
    if sort == 'parent_tree':
        if 'limit' in data:
            query += ' ph.parent IN (SELECT parent FROM (SELECT DISTINCT ph.parent FROM Post p LEFT JOIN PostHierarchy ph ON p.id = ph.post WHERE '
        else:
            sort = 'tree'

    for i, field in enumerate(clause):
        query += 'p.' + field + ' = ' + '%s'
        query += ' AND ' if i < len(clause)-1 else ''
    if 'since' in data.keys():
        query += ' AND p.date >= "%(since)s"' % data

    if 'order' in data:
        if data['order'] in ['asc', 'desc']:
            order = ' ' + data['order'].upper() + ' '
        else:
            return jsonify({'code': 2, 'response': 'json error'})
    else:
        order = ''

    if sort == 'parent_tree':
        query += ' ORDER BY ph.parent ' + order
#        query += ', address ASC '
        query += 'LIMIT %s ) a) ORDER BY ph.parent %s, ph.address' % (data['limit'], order)

    elif sort == 'tree':
        query += ' ORDER BY ph.parent ' + order
        query += ', ph.address ASC '
    else: # flat
        query += ' ORDER BY p.date ' + order
    if 'limit' in data.keys():
        if not (data['limit'].lstrip('-').isdigit() and int(data['limit']) >= 0):
            return jsonify({ 'code': 2, 'response': 'json error in limit' })
        if sort != 'parent_tree':
            query += ' LIMIT %s ' % data['limit']
    query += ';'
    try:
        response = select(query, clause.values())
    except db.Error as e:
        print str(e)
        return jsonify({ 'code': 4, 'response': str(e) })
    else:
        if not response:
            response = []
        else:
            new_response = []
            for l in response:
                zipped = zip(post_fields, l)
                i = len(post_fields)
                if forum:
                    zipped.append(('forum', dict(zip(forum_fields, l[i:i + len(forum_fields)]))))
                    i += len(forum_fields)
                if thread:
                    t = dict(zip(thread_fields, l[i:i + len(thread_fields)]))
                    t['date'] = t['date'].strftime('%Y-%m-%d %H:%M:%S')
                    zipped.append(('thread', t))
                    i += len(thread_fields)
                if user:
                    u = dict(zip(user_fields, l[i:-3]))
                    u.update({'followers': [] if l[-3] is None else l[-3].split(',')})
                    u.update({'following': [] if l[-2] is None else l[-2].split(',')})
                    u.update({'subscriptions': [] if l[-1] is None else [int(k) for k in l[-1].split(',')]})
                    zipped.append(('user', u))
                new_el = dict(zipped)
                new_el['date'] = new_el['date'].strftime('%Y-%m-%d %H:%M:%S')
                new_response.append(new_el)
            response = new_response
        return jsonify({ 'code': 0, 'response': response })
