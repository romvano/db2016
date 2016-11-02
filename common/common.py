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
