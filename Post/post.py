from flask import Blueprint, request, g, jsonify
import MySQLdb as db
from itertools import chain
import bisect
from common.common import *
from User.user import User as u, get_user_where
from Forum.forum import Forum as f, select_from_forum_where
from Thread.thread import Thread as t, select_from_thread_where

Post = Blueprint('post', __name__)

def select_from_post_where(key, value):
    return select_from_where('Post', post_fields, key, value)

def add_to_hierarchy(id, parent=0):
    if parent != 0:
        query = 'INSERT INTO PostHierarchy (post, address, parent) \
                 SELECT %d, CONCAT(address, "%d", "/"), SUBSTRING_INDEX(address, "/", 1) FROM PostHierarchy WHERE post = %d;'
        query = query % (id, id, parent)
    else:
        query = 'INSERT INTO PostHierarchy (post, parent, address) VALUES (%d, %d, "%s/");' % (id, id, id)
    try:
        g.cursor.execute(query)
    except db.Error as e:
        print e
        g.connection.rollback()
        return {'code': 4, 'response': 'hierarchy error'}
    else:
        g.connection.commit()
        return {'code': 0, 'response': 'OK'}

@Post.route('create/', methods=['POST'])
def create_post():
    data = get_post_data(request)
    if not {'date', 'thread', 'message', 'user', 'forum'} <= set(data.keys()):
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    data['parent'] = data.get('parent', None)
    data['isApproved'] = data.get('isApproved', False)
    data['isHighlighted'] = data.get('isHighlighted', False)
    data['isEdited'] = data.get('isEdited', False)
    data['isSpam'] = data.get('isSpam', False)
    data['isDeleted'] = data.get('isDeleted', False)
    data['likes'] = data['points'] = 0
    response = create('Post', data, post_fields, 'message', data['message'])
    if response['code'] == 0 and not data['isDeleted']:
        id = g.cursor.lastrowid
        thread_response = update('Thread', { 'posts': 'Thread.posts + 1' }, { 'id': data['thread'] }, lambda: ({ 'code': 0 }) )
        if thread_response['code'] != 0:
            return jsonify(thread_response)
        if data['parent']:
            hierarchy_response = add_to_hierarchy(id, data['parent'])
        else:
            hierarchy_response = add_to_hierarchy(id)
        if hierarchy_response['code'] != 0:
            return jsonify(hierarchy_response)
    return jsonify(response)


@Post.route('details/', methods=['GET'])
def post_details():
    data = get_get_data(request)
    if 'post' not in data.keys():
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    if not data['post'].lstrip('-').isdigit():
        return jsonify({ 'code': 2, 'response': 'json error' })
    try:
        response = select_from_post_where('id', data['post'])
    except db.Error as e:
        return jsonify({ 'code': 4, 'response': str(e) })
    else:
        if response is None:
            return jsonify({ 'code': 1, 'response': 'Object not found' })
        for el in request.args.getlist('related'):
            if el == 'user':
                response['user'] = get_user_where('email', response['user'])
            if el == 'forum':
                response['forum'] = select_from_forum_where('short_name', response['forum'])
            if el == 'thread':
                response['thread'] = select_from_thread_where('id', response['thread'])
        return jsonify({ 'code': 0, 'response': response })

def set_isDeleted(request, is_deleted):
    data = get_post_data(request)
    if 'post' not in data.keys():
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    if type(data['post']) != int:
        return jsonify({ 'code': 2, 'response': 'json error' })
    post_response = update('Post', { 'isDeleted': is_deleted }, { 'id': data['post'] }, lambda: ({ 'code': 0 }))
    if post_response['code'] == 0:
        return jsonify(update(
            'Thread',
            { 'posts': 'Thread.posts - 1' if is_deleted else 'Thread.posts + 1' },
            { 'id': '(SELECT thread FROM Post WHERE Post.id = %d)' % data['post'] },
            lambda: ({ 'post': data['post'] })
        ))
    else:
        return jsonify(post_response)

@Post.route('remove/', methods=['POST'])
def remove_post():
    return set_isDeleted(request, 1)

@Post.route('restore/', methods=['POST'])
def restore_post():
    return set_isDeleted(request, 0)

@Post.route('update/', methods=['POST'])
def update_post():
    data = get_post_data(request)
    if not {'message', 'post'} <= set(data):
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    if type(data['post']) != int:
        return jsonify({ 'code': 2, 'response': 'json error' })
    return jsonify(update(
        'Post',
        { 'message': data['message'].join('""') },
        { 'id': data['post'] },
        lambda: (select_from_post_where('id', data['post']))
    ))

@Post.route('vote/', methods=['POST'])
def post_vote():
    data = get_post_data(request)
    if not {'vote', 'post'} <= set(data):
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    if type(data['post']) != int or type(data['vote']) != int or data['vote'] not in [-1, 1]:
        return jsonify({ 'code': 2, 'response': 'json error' })
    likes = 'likes' if data['vote'] == 1 else 'dislikes'
    return jsonify(update(
        'Post',
        { likes: "Post."+likes+" + 1", "points": "Post.points + "+str(data['vote']) },
        { 'id': data['post'] },
        lambda: (select_from_post_where('id', data['post']))
    ))

@Post.route('list/', methods=['GET'])
def list_posts():
    data = get_get_data(request)
    data['related'] = request.args.getlist('related')
    if 'forum' in data:
        return list_posts_where(data, { 'forum': data['forum'] })
    elif 'thread' in data:
        return list_posts_where(data, { 'thread': data['thread'] })
    else:
        return jsonify({ 'code': 3, 'response': 'Bad request' })
