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
    'Subscription'
]

def get_post_data(request):
    return dict((k.encode('utf-8'), unicode(v)) for (k, v) in request.json.items())

def get_get_data(request):
    return dict((k, request.args[k]) for k in request.args)

def select(query):
    g.cursor.execute(query)
    result = g.cursor.fetchall()
    return result

def select_from_where(table, what, key, value):
    query = 'SELECT ' + ', '.join(what) + ' FROM ' + table + ' WHERE ' + key + '="' + value + '";'
    selected = select(query)[0]
    if not selected:
        return {}
    return dict(zip(what, selected))

def create(table, fields, data, *select_args):
    try:
        query = ('INSERT INTO ' + table + '(' + ', '.join(fields) + ') \
                 VALUES ("%(' + ')s", "%('.join(fields) + ')s");') % data
        g.cursor.execute(query)
    except db.IntegrityError as ie:
        g.connection.rollback()
        return jsonify({ 'code': 0, 'response': select_from_where(table, ['id'] + fields, *select_args) })
    except db.Error as e:
        g.connection.rollback()
        return jsonify({ 'code': 4, 'response': str(e) })
    else:
        data['id'] = g.cursor.lastrowid
        g.connection.commit()
        return jsonify({ 'code': 0, 'response': data })

def details(table, fields, *select_params):
    try:
        response = select_function(*select_params)
    except db.Error as e:
        return jsonify({ 'code': 4, 'response': str(e) })
    else:
        if response is None:
            return jsonify({ 'code': 1, 'response': 'Object not found' })
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
