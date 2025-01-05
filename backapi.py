from flask import Flask, request, jsonify, render_template, redirect, url_for
import datetime
import sqlite3
import json
import os
from flask_bcrypt import Bcrypt

app = Flask(__name__, static_folder='.', template_folder='.')
bcrypt = Bcrypt(app)

def query_db(query, args=(), one=False):
    conn = sqlite3.connect('db\\db.db')
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')

    if not username or not password or not role:
        return jsonify({'error': 'Missing required fields'}), 400

    hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
    try:
        query_db('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', [username, hashed_password, role])
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username already exists'}), 400

    return jsonify({'message': 'User registered successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': 'Missing required fields'}), 400

    user = query_db('SELECT user_id, password,role FROM users WHERE username = ?', [username], one=True)
    if user is None or not bcrypt.check_password_hash(user[1], password):
        return jsonify({'error': 'Invalid username or password'}), 400

    return jsonify({'message': 'Login successful', 'user_id': user[0],"user_role":user[2]}), 200

@app.route('/career_test', methods=['POST'])
def create_career_test():
    data = request.get_json()
    user_id = data.get('user_id')
    result = data.get('result')

    if not user_id or not result:
        return jsonify({'error': 'Missing user_id or result'}), 400

    # Save result to JSON file
    result_filename = f'results/user_{user_id}_{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}.json'
    os.makedirs(os.path.dirname(result_filename), exist_ok=True)
    with open(result_filename, 'w') as f:
        json.dump(result, f)

    # Save JSON file path to database
    query_db('INSERT INTO career_tests (user_id, result) VALUES (?, ?)', [user_id, result_filename])
    result = query_db('SELECT test_id FROM career_tests WHERE user_id = ? and result = ?',[user_id,result_filename], one=True)
    return jsonify({'message': 'Career test created successfully','test_id':result[0]}), 201

# @app.route('/career_test/<int:user_id>', methods=['GET'])
# def get_career_test(user_id):
#     tests = query_db('SELECT test_id, result, created_at FROM career_tests WHERE user_id = ?', [user_id])
#     if not tests:
#         return jsonify({'error': 'No tests found for this user'}), 404

#     return jsonify([{'test_id': test[0], 'result': test[1], 'created_at': test[2]} for test in tests]), 200

@app.route('/articles', methods=['POST'])
def create_article():
    data = request.form
    author_id = data.get('author_id')
    title = data.get('title')
    career_type = data.get('career_type')
    content = data.get('content')

    if not author_id or not title or not career_type or not content:
        return jsonify({'error': 'Missing required fields'}), 400

    media_files = request.files.getlist('media')
    media_filenames = []

    for media_file in media_files:
        if media_file.filename == '':
            continue
        media_filename = f'media/{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}_{media_file.filename}'
        os.makedirs(os.path.dirname(media_filename), exist_ok=True)
        media_file.save(media_filename)
        media_filenames.append(media_filename)

    media_filenames_json = json.dumps(media_filenames)

    query_db('INSERT INTO articles (author_id, title, career_type, media, content) VALUES (?, ?, ?, ?, ?)', 
             [author_id, title, career_type, media_filenames_json, content])
    return jsonify({'message': 'Article created successfully'}), 201

@app.route('/comments/<int:article_id>', methods=['GET'])
def get_comments(article_id):
    comments = query_db('SELECT comment_id, created_at,user_id, content, created_at FROM comments WHERE article_id = ?', [article_id])
    if not comments:
        return jsonify({'message': '此文章還沒有任何留言'}), 200

    return jsonify([{'comment_id': comment[0], 'user_id': comment[1], 'content': comment[2], 'created_at': comment[3]} for comment in comments]), 200

@app.route('/comments', methods=['POST'])
def create_comment():
    data = request.get_json()
    article_id = data.get('article_id')
    user_id = data.get('user_id')
    content = data.get('content')

    if not article_id or not user_id or not content:
        return jsonify({'error': 'Missing required fields'}), 400

    query_db('INSERT INTO comments (article_id, user_id, content) VALUES (?, ?, ?)', [article_id, user_id, content])
    return jsonify({'message': 'Comment added successfully'}), 201

@app.route('/search_articles', methods=['GET'])
def search_articles():
    career_type = request.args.get('career_type')
    keyword = request.args.get('keyword')

    if not career_type and not keyword:
        return jsonify({'error': '至少需要一個檢索條件'}), 400

    query = 'SELECT article_id, author_id, title, career_type, media, content, created_at FROM articles WHERE 1=1'
    args = []

    if career_type:
        query += ' AND career_type LIKE ?'
        args.append(f'%{career_type}%')

    if keyword:
        query += ' AND (title LIKE ? OR content LIKE ?)'
        args.append(f'%{keyword}%')
        args.append(f'%{keyword}%')

    articles = query_db(query, args)
    if not articles:
        return jsonify({'message': '查無符合條件的文章'}), 200

    return jsonify([{'article_id': article[0], 'author_id': article[1], 'title': article[2], 'career_type': article[3], 'media': article[4], 'content': article[5], 'created_at': article[6]} for article in articles]), 200

@app.route('/careers', methods=['GET'])
def get_careers():
    careers = query_db('SELECT career_id, type, description FROM careers')
    return jsonify([{'career_id': career[0], 'type': career[1], 'description': career[2]} for career in careers]), 200

@app.route('/careers/<int:career_id>', methods=['GET'])
def get_career(career_id):
    career = query_db('SELECT career_id, type, description FROM careers WHERE career_id = ?', [career_id], one=True)
    if not career:
        return jsonify({'message': '該職業目前沒有任何詳細介紹'}), 404

    return jsonify({'career_id': career[0], 'type': career[1], 'description': career[2]}), 200

@app.route('/history_tests/<int:user_id>', methods=['GET'])
def get_history_tests(user_id):
    tests = query_db('SELECT test_id, created_at FROM career_tests WHERE user_id = ?', [user_id])
    if not tests:
        return jsonify({'message': '您尚未做過職涯測驗'}), 200

    return jsonify([{'test_id': test[0], 'created_at': test[1]} for test in tests]), 200

@app.route('/history_tests/detail/<int:test_id>', methods=['GET'])
def get_test_detail(test_id):
    test = query_db('SELECT result FROM career_tests WHERE test_id = ?', [test_id], one=True)
    if not test:
        return jsonify({'message': '該測驗結果不存在'}), 404

    with open(test[0], 'r') as f:
        result = json.load(f)

    return jsonify(result), 200

@app.route('/user_articles/<int:user_id>', methods=['GET'])
def get_user_articles(user_id):
    articles = query_db('SELECT article_id, title, created_at FROM articles WHERE author_id = ?', [user_id])
    if not articles:
        return jsonify({'message': '您尚未發表任何文章'}), 200

    return jsonify([{'article_id': article[0], 'title': article[1], 'created_at': article[2]} for article in articles]), 200

@app.route('/user_articles/detail/<int:article_id>', methods=['GET'])
def get_article_detail(article_id):
    article = query_db('SELECT title, career_type, media, content, created_at, is_deleted FROM articles WHERE article_id = ?', [article_id], one=True)  # 修改這一行
    if not article or article[5] == 1:  # 修改這一行
        return jsonify({'message': '該文章不存在或已被刪除'}), 404  # 修改這一行

    return jsonify({'title': article[0], 'career_type': article[1], 'media': article[2], 'content': article[3], 'created_at': article[4]}), 200

@app.route('/user_articles/edit/<int:article_id>', methods=['POST'])
def edit_article(article_id):
    data = request.get_json()
    title = data.get('title')
    career_type = data.get('career_type')
    media = data.get('media')
    content = data.get('content')

    if not title or not career_type or not content:
        return jsonify({'error': 'Missing required fields'}), 400

    query_db('UPDATE articles SET title = ?, career_type = ?, media = ?, content = ? WHERE article_id = ?', 
             [title, career_type, media, content, article_id])
    return jsonify({'message': '文章編輯成功'}), 200

@app.route('/user_articles/delete/<int:article_id>', methods=['DELETE'])
def delete_article(article_id):
    query_db('UPDATE articles SET is_deleted = 1 WHERE article_id = ?', [article_id])  # 修改這一行
    return jsonify({'message': '該文章已被刪除'}), 200

@app.route('/favorites/<int:user_id>', methods=['GET'])
def get_favorites(user_id):
    favorites = query_db('SELECT articles.article_id, articles.title, articles.created_at FROM favorites JOIN articles ON favorites.article_id = articles.article_id WHERE favorites.user_id = ?', [user_id])
    if not favorites:
        return jsonify({'message': '您尚未收藏任何文章'}), 200

    return jsonify([{'article_id': favorite[0], 'title': favorite[1], 'created_at': favorite[2]} for favorite in favorites]), 200

@app.route('/favorites/detail/<int:article_id>', methods=['GET'])
def get_favorite_detail(article_id):
    article = query_db('SELECT title, career_type, media, content, created_at, is_deleted FROM articles WHERE article_id = ?', [article_id], one=True)  # 修改這一行
    if not article or article[5] == 1:  # 修改這一行
        return jsonify({'message': '該文章已被刪除'}), 404  # 修改這一行

    return jsonify({'title': article[0], 'career_type': article[1], 'media': article[2], 'content': article[3], 'created_at': article[4]}), 200

if __name__ == '__main__':
    app.run(debug=True)