from flask import Blueprint, request, g, jsonify
import MySQLdb as db
from itertools import chain
import bisect
from common.common import get_post_data, get_get_data, select, select_from_where, create
from User.user import User as u, get_user_where

Forum = Blueprint('forum', __name__)

forum_fields_to_insert = ['name', 'short_name', 'user']
forum_fields = ['id'] + forum_fields_to_insert

def select_from_forum_where(key, value):
    return select_from_where('Forum', forum_fields, key, value)

@Forum.route('create/', methods=['POST'])
def create_forum():
    data = get_post_data(request)
    if not {'name', 'short_name', 'user'} <= set(data.keys()):
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    return create('Forum', data, 'short_name', data['short_name'])

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
        if 'related' in data.keys():
            if 'user' in data['related']:
                response['user'] = get_user_where('email', response['user'])
            else:
                return jsonify({ 'code': 2, 'response': 'json error' })
        return jsonify({ 'code': 0, 'response': response })
                
