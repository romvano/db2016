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
    return dict((k, v) for (k, v) in request.json.items())

def get_get_data(request):
    return dict((k, request.args[k]) for k in request.args)

def select(query, params=()):
    g.cursor.execute(query, params)
    result = g.cursor.fetchall()
    return result

def select_from_where(table, what='', key=None, value=None):
    query = 'SELECT ' + ', '.join(what) + ' FROM ' + table + ' WHERE ' + key + '= %s;'
    params = (value,)
    selected = select(query, params)[0]
    if not selected:
        return {}
    return {k: v if k != 'date' else v.strftime('%Y-%m-%d %H:%M:%S') for (k, v) in zip(what, selected)}
    return dict(zip(what, selected))

def create_update_exceptions(table, e, success):
    g.connection.rollback()
    if e == db.IntegrityError:
        if table == 'User':
            return jsonify({ 'code': 5, 'response': str(e)})
        return jsonify({ 'code': 0, 'response': success })
    if e == db.DataError:
        return jsonify({ 'code': 2, 'response': str(e) })
    if e == db.Error:
        return jsonify({ 'code': 4, 'response': str(e) })
    raise Exception()
   
def create(table, data, *select_args):
    try:
        query = 'INSERT INTO ' + table + '(' + ', '.join(data.keys()) + ') \
                 VALUES (' + '%s, '*(len(data) - 1) + '%s)'
        g.cursor.execute(query, tuple(data.values()))
    except Exception as e:
        success = data if not select_args else select_from_where(table, ['id']+data.keys(), *select_args)
        return create_update_exceptions(table, type(e), success)
    else:
        data['id'] = g.cursor.lastrowid
        g.connection.commit()
        return jsonify({ 'code': 0, 'response': data })


def update(table, data, clause, success):
    query = 'UPDATE ' + table + 'SET '
    for i, field in enumerate(data):
        query += table + '.' + field + ' = ' + '%s'
        query += ', ' if i < len(data) else ''
    query += ' WHERE '
    for i, field in enumerate(clause):
        query += table + '.' + field + ' = ' + '%s'
        query += ' AND ' if i < len(clause) else ';'
    try:
        g.cursor.execute(query, tuple(data.values()) + tuple(clause.values()))
    except Exception as e:
        return create_update_exceptions(table, e, success)
    else:
        if g.cursor.rowcount == 0:
            return jsonify({ 'code': 1, 'response': 'No object was changed' })
    finally:
        g.connection.commit()
        return jsonify({ 'code': 0, 'response': success })

def delete(table, clause, success):
    query = 'DELETE FROM ' + table + ' WHERE ' 
    for i, field in enumerate(clause):
        query += table + '.' + field + ' = ' + '%s'
        query += ' AND ' if i < len(clause) else ';'
    try:
        g.cursor.execute(query, tuple(clause.values()))
    except Exception as e:
        return create_update_exceptions(table, e, success)
    else:
        if g.cursor.rowcount == 0:
            return jsonify({ 'code': 1, 'response': 'No object was changed' })
    finally:
        g.connection.commit()
        return jsonify({ 'code': 0, 'response': success })

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
