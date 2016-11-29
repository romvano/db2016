from flask import Blueprint, request, g, jsonify
import MySQLdb as db
from common.common import *
from User.user import get_user_where, user_fields
from Forum.forum import select_from_forum_where, forum_fields

Thread = Blueprint('thread', __name__)

def select_from_thread_where(key, value):
    return select_from_where('Thread', thread_fields, key, value)

@Thread.route('create/', methods=['POST'])
def create_thread():
    data = get_post_data(request)
    if not {'forum', 'title', 'isClosed', 'user', 'date', 'message', 'slug'} <= set(data.keys()):
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    data['isDeleted'] = data.get('isDeleted', 0)
    return jsonify(create('Thread', data, thread_fields, 'title', data['title']))

@Thread.route('details/', methods=['GET'])
def thread_details():
    data = get_get_data(request)
    if 'thread' not in data.keys():
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    if not data['thread'].lstrip('-').isdigit():
        return jsonify({ 'code': 2, 'response': 'json error' })
    try:
        response = select_from_thread_where('id', data['thread'])
    except db.Error as e:
        return jsonify({ 'code': 4, 'response': str(e) })
    else:
        if response is None:
            return jsonify({ 'code': 1, 'response': 'Object not found' })
        for el in request.args.getlist('related'):
            if el not in ['user', 'forum']:
                return jsonify({ 'code': 3, 'response': 'Baaaaad request' })
            if el == 'user':
                response['user'] = get_user_where('email', response['user'])
            if el == 'forum':
                response['forum'] = select_from_forum_where('short_name', response['forum'])
        return jsonify({ 'code': 0, 'response': response })

def set_isClosed(request, is_closed):
    data = get_post_data(request)
    if 'thread' not in data.keys():
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    if type(data['thread']) != int:
        return jsonify({ 'code': 2, 'response': 'json error' })
    return jsonify(update('Thread', { 'isClosed': is_closed }, { 'id': data['thread'] }, lambda: ({ 'thread': data['thread'] })))
    
@Thread.route('open/', methods=['POST'])
def open_thread():
    return set_isClosed(request, False)

@Thread.route('close/', methods=['POST'])
def close_thread():
    return set_isClosed(request, True)

def set_isDeleted(request, is_deleted):
    data = get_post_data(request)
    if 'thread' not in data.keys():
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    if type(data['thread']) != int:
        return jsonify({ 'code': 2, 'response': 'json error' })
    post_response = update('Post', { 'isDeleted': is_deleted }, { 'thread': data['thread'] }, lambda: ('success'))
    if post_response['code'] != 0:
        return post_response
    return jsonify(update(
        'Thread',
        { 'isDeleted': is_deleted, 'posts': 0 if is_deleted else '(SELECT COUNT(*) FROM Post WHERE Post.thread = %d AND Post.isDeleted = 0)' % data['thread'] },
        { 'id': data['thread'] },
        lambda: ({ 'thread': data['thread'] })
    ))

@Thread.route('remove/', methods=['POST'])
def remove_thread():
    return set_isDeleted(request, True)

@Thread.route('restore/', methods=['POST'])
def restore_thread():
    return set_isDeleted(request, False)

@Thread.route('update/', methods=['POST'])
def update_thread():
    data = get_post_data(request)
    if not {'message', 'slug', 'thread'} <= set(data):
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    if type(data['thread']) != int:
        return jsonify({ 'code': 2, 'response': 'json error' })
    return jsonify(update(
        'Thread',
        { 'message': data['message'].join('""'), 'slug': data['slug'].join('""')},
        { 'id': data['thread'] },
        lambda: (select_from_thread_where('id', data['thread']))
    ))

@Thread.route('vote/', methods=['POST'])
def thread_vote():
    data = get_post_data(request)
    if not {'vote', 'thread'} <= set(data):
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    if type(data['thread']) != int or type(data['vote']) != int or data['vote'] not in [-1, 1]:
        return jsonify({ 'code': 2, 'response': 'json error' })
    likes = 'likes' if data['vote'] == 1 else 'dislikes'
    return jsonify(update(
        'Thread',
        { likes: 'Thread.'+likes+' + 1', 'points': 'Thread.points + '+str(data['vote']) },
        { 'id': data['thread'] },
        lambda: (select_from_thread_where('id', data['thread']))
    ))

@Thread.route('subscribe/', methods=['POST'])
@Thread.route('unsubscribe/', methods=['POST'])
def set_subscription():
    data = get_post_data(request)
    if not {'user', 'thread'} <= set(data):
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    if type(data['thread']) != int:
        return jsonify({ 'code': 2, 'response': 'json error' })
    url = request.url_rule.rule
    action = url.rsplit('/', 2)[1] # subscribe or unsubscripe - that is the question
    if action == 'subscribe':
        return jsonify(create('Subscription', { 'name': data['user'], 'thread': data['thread'] }))
    elif action == 'unsubscribe':
        return jsonify(delete('Subscription', { 'name': data['user'], 'thread': data['thread'] }, { 'name': data['user'], 'thread': data['thread'] }))

@Thread.route('list/', methods=['GET'])
def list_threads():
    data = get_get_data(request)
    data['related'] = request.args.getlist('related')
    if 'forum' in data:
        return list_threads_where(data, { 'forum': data['forum'] })
    elif 'user' in data:
        return list_threads_where(data, { 'user': data['user'] })
    else:
        return jsonify({ 'code': 3, 'response': 'Bad request' })

@Thread.route('listPosts/', methods=['GET'])
def list_posts():
    data = get_get_data(request)
    data['related'] = request.args.getlist('related')
    if 'thread' not in data:
        return jsonify({ 'code': 3, 'response': 'Bad request' })
    sort = data.get('sort', 'flat')
    return list_posts_where(data, { 'thread': data['thread'] }, sort)
