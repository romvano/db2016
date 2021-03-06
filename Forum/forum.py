from flask import Blueprint, request, g, jsonify
import MySQLdb as db
from itertools import chain
import bisect
from common.common import *
from User.user import User as u, get_user_where

Forum = Blueprint('forum', __name__)

def select_from_forum_where(key, value):
    return select_from_where('Forum', forum_fields, key, value)

@Forum.route('create/', methods=['POST'])
def create_forum():
    data = get_post_data(request)
    if not {'name', 'short_name', 'user'} <= set(data.keys()):
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    return jsonify(create('Forum', data, forum_fields, 'short_name', data['short_name']))

@Forum.route('details/', methods=['GET'])
def forum_details():
    data = get_get_data(request)
    if 'forum' not in data.keys():
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    try:
        response = select_from_forum_where('short_name', data['forum'])
    except db.Error as e:
        return jsonify({ 'code': 4, 'response': str(e) })
    else:
        if response is None:
            return jsonify({ 'code': 1, 'response': 'Object not found' })
        for el in request.args.getlist('related'):
            if el != 'user':
                return jsonify({ 'code': 3, 'response': 'Baaaaad request' })
            response['user'] = get_user_where('email', response['user'])
        return jsonify({ 'code': 0, 'response': response })
                
@Forum.route('listUsers/', methods=['GET'])
def list_users():
    data = get_get_data(request)
    if 'forum' not in data:
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    table, email = 'Post', 'user'
    response = list_users_where_email(table, email, data, { 'forum': data['forum'] })
    return response

@Forum.route('listThreads/', methods=['GET'])
def list_threads():
    data = get_get_data(request)
    if 'forum' not in data:
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    data['related'] = request.args.getlist('related')
    return list_threads_where(data, { 'forum': data['forum'] })

@Forum.route('listPosts/', methods=['GET'])
def list_posts():
    data = get_get_data(request)
    if 'forum' not in data:
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    data['related'] = request.args.getlist('related')
    return list_posts_where(data, { 'forum': data['forum'] })
