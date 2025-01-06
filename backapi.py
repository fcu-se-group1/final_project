from flask import Flask, request, jsonify, render_template, redirect, url_for
import datetime
import sqlite3
import json
import os
from flask_bcrypt import Bcrypt
import json
import random

app = Flask(__name__, static_folder='static', template_folder='templates')
bcrypt = Bcrypt(app)

def query_db(query, args=(), one=False):
    conn = sqlite3.connect('db\\database.db')
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

@app.route('/')
def homepage():
    return render_template('homepage.html')

@app.route('/add_comment')
def add_comment():
    return render_template('add_comment.html')

@app.route('/article_content')
def article_content():
    return render_template('article_content.html')

@app.route('/article_record')
def article_record():
    return render_template('article_record.html')

@app.route('/career_test_result')
def career_test_result():
    return render_template('career_test_result.html')

@app.route('/career_test_start')
def career_test_start():
    return render_template('career_test_start.html')

@app.route('/career_test')
def career_test():
    return render_template('career_test.html')

@app.route('/chooseFunction')
def chooseFunction():
    return render_template('chooseFunction.html')

@app.route('/edit_article')
def edit_article():
    return render_template('edit_article.html')

@app.route('/favorite_article')
def favorite_article():
    return render_template('favorite_article.html')

@app.route('/history_test_record_check')
def history_test_record_check():
    return render_template('history_test_record_check.html')

@app.route('/history_test_record')
def history_test_record():
    return render_template('history_test_record.html')

@app.route('/job_intro')
def job_intro():
    return render_template('job_intro.html')

@app.route('/log_in')
def log_in():
    return render_template('log_in.html')

@app.route('/post_article')
def post_article():
    return render_template('post_article.html')

@app.route('/reply_author')
def reply_author():
    return render_template('reply_author.html')

@app.route('/search_article')
def search_article():
    return render_template('search_article.html')

@app.route('/search_result')
def search_result():
    return render_template('search_result.html')

@app.route('/seeker_personal_homepage')
def seeker_personal_homepage():
    return render_template('seeker_personal_homepage.html')

@app.route('/sign_up')
def sign_up():
    return render_template('sign_up.html')

@app.route('/social_personal_homepage')
def social_personal_homepage():
    return render_template('social_personal_homepage.html')

@app.route('/type_intro_choose')
def type_intro_choose():
    return render_template('type_intro_choose.html')

@app.route('/type_intro')
def type_intro():
    return render_template('type_intro.html')

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

@app.route('/login_check', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'error': '帳號或密碼不可空白'}), 400

    user = query_db('SELECT user_id, password,role,username FROM users WHERE username = ?', [username], one=True)
    if user is None or not bcrypt.check_password_hash(user[1], password):
        return jsonify({'error': '帳號或密碼錯誤'}), 400

    return jsonify({'message': 'Login successful', 'user_id': user[0],"user_role":user[2],'user_name':user[3]}), 200

@app.route('/show_career_test/<string:filename>', methods=['GET'])
def show_career_test(filename):
    filepath = os.path.join('career_quation', f'{filename}.json')
    if not os.path.exists(filepath):
        return jsonify({'error': 'File not found'}), 404

    with open(filepath, 'r', encoding="utf-8") as f:
        data = json.load(f)

    questions = data.get('選擇題', [])
    if len(questions) < 10:
        return jsonify({'error': 'Not enough questions in the file'}), 400

    selected_questions = random.sample(questions, 10)
    return jsonify({'選擇題': selected_questions}), 200

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

# @app.route('/comments/<int:article_id>', methods=['GET'])
# def get_comments(article_id):
#     comments = query_db('SELECT comment_id, created_at,user_id, content, created_at FROM comments WHERE article_id = ?', [article_id])
#     if not comments:
#         return jsonify({'message': '此文章還沒有任何留言'}), 200

#     return jsonify([{'comment_id': comment[0], 'user_id': comment[1], 'content': comment[2], 'created_at': comment[3]} for comment in comments]), 200

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

# @app.route('/re_comments/<int:comment_id>', methods=['GET'])
# def get_re_comments(comment_id):
#     re_comments = query_db('SELECT re_comment_id, user_id, content, created_at FROM re_comments WHERE comment_id = ?', [comment_id])
#     if not re_comments:
#         return jsonify({'message': '此留言還沒有任何回覆'}), 200

#     return jsonify([{'re_comment_id': re_comment[0], 'user_id': re_comment[1], 'content': re_comment[2], 'created_at': re_comment[3]} for re_comment in re_comments]), 200

@app.route('/re_comments', methods=['POST'])
def create_re_comment():
    data = request.get_json()
    comment_id = data.get('comment_id')
    user_id = data.get('user_id')
    content = data.get('content')

    if not comment_id or not user_id or not content:
        return jsonify({'error': 'Missing required fields'}), 400

    query_db('INSERT INTO re_comments (comment_id, user_id, content) VALUES (?, ?, ?)', [comment_id, user_id, content])
    return jsonify({'message': '回覆留言已成功添加'}), 201

@app.route('/search_articles', methods=['GET'])
def search_articles():
    career_type = request.args.get('career_type')
    keyword = request.args.get('keyword')
    username = request.args.get('username')  # 新增這一行

    if not career_type and not keyword and not username:  # 修改這一行
        return jsonify({'error': '至少需要一個檢索條件'}), 400

    query = '''
        SELECT articles.article_id, articles.author_id, articles.title, articles.career_type, articles.media, articles.content, articles.created_at, users.username
        FROM articles
        JOIN users ON articles.author_id = users.user_id
        WHERE 1=1 AND  is_deliete=0
    '''
    args = []

    if career_type:
        query += ' AND articles.career_type = ?'
        args.append(career_type)

    if keyword:
        query += ' AND (articles.title LIKE ? OR articles.content LIKE ?)'
        args.append(f'%{keyword}%')
        args.append(f'%{keyword}%')

    if username:  # 新增這一段
        query += ' AND users.username LIKE ?'
        args.append(f'%{username}%')

    print(f"Query: {query}")
    print(f"Args: {args}")

    articles = query_db(query, args)
    print(f"Articles: {articles}")
    
    if not articles:
        return jsonify({'message': '查無符合條件的文章'}), 200

    return jsonify([{
        'article_id': article[0],
        'title': article[2],
        'career_type': article[3],
        'username': article[7]  # 新增這一行
    } for article in articles]), 200

@app.route('/article_details/<int:article_id>', methods=['GET'])
def get_article_details(article_id):
    # 獲取文章資訊
    article = query_db('''
        SELECT articles.article_id, articles.author_id, articles.title, articles.career_type, articles.media, articles.content, articles.created_at, users.username
        FROM articles
        JOIN users ON articles.author_id = users.user_id
        WHERE articles.article_id = ? AND is_deleted = 0
    ''', [article_id], one=True)

    if not article:
        return jsonify({'error': '文章不存在'}), 404

    # 獲取留言資訊
    comments = query_db('''
        SELECT comments.comment_id, comments.user_id, comments.content, comments.created_at, users.username
        FROM comments
        JOIN users ON comments.user_id = users.user_id
        WHERE comments.article_id = ?
    ''', [article_id])

    # 獲取回覆留言資訊
    def get_re_comments(comment_id):
        re_comment_list = query_db('''
            SELECT re_comments.re_comment_id, re_comments.user_id, re_comments.content, re_comments.created_at, users.username
            FROM re_comments
            JOIN users ON re_comments.user_id = users.user_id
            WHERE re_comments.comment_id = ?
        ''', [comment_id])
        re_comments = []
        for re_comment in re_comment_list:
            re_comments.append({
                're_comment_id': re_comment[0],
                'user_id': re_comment[1],
                'content': re_comment[2],
                'created_at': re_comment[3],
                'username': re_comment[4],
            })
        return re_comments

    # 構建返回結果
    result = {
        'article_id': article[0],
        'author_id': article[1],
        'title': article[2],
        'career_type': article[3],
        'media': article[4],
        'content': article[5],
        'created_at': article[6],
        'username': article[7],
        'comments': [{
            'comment_id': comment[0],
            'user_id': comment[1],
            'content': comment[2],
            'created_at': comment[3],
            'username': comment[4],
            're_comments': get_re_comments(comment[0])  # 獲取回覆留言
        } for comment in comments]
    }

    return jsonify(result), 200

@app.route('/careers', methods=['GET'])
def get_careers():
    careers = query_db('SELECT career_id, type, description FROM careers')
    return jsonify([{'career_id': career[0], 'type': career[1], 'description': career[2]} for career in careers]), 200

@app.route('/work/<int:career_id>', methods=['GET'])
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
        print(result)

    return jsonify(result), 200

@app.route('/user_articles/<int:user_id>', methods=['GET'])
def get_user_articles(user_id):
    articles = query_db('SELECT article_id, title, created_at FROM articles WHERE author_id = ? AND is_deleted = 0', [user_id])
    if not articles:
        return jsonify({'message': '您尚未發表任何文章'}), 200

    return jsonify([{'article_id': article[0], 'title': article[1], 'created_at': article[2]} for article in articles]), 200

# @app.route('/user_articles/detail/<int:article_id>', methods=['GET'])
# def get_article_detail(article_id):
#     article = query_db('SELECT title, career_type, media, content, created_at, is_deleted FROM articles WHERE article_id = ?', [article_id], one=True)  # 修改這一行
#     if not article or article[5] == 1:  # 修改這一行
#         return jsonify({'message': '該文章不存在或已被刪除'}), 404  # 修改這一行

#     return jsonify({'title': article[0], 'career_type': article[1], 'media': article[2], 'content': article[3], 'created_at': article[4]}), 200

# @app.route('/user_articles/edit/<int:article_id>', methods=['POST'])
# def edit_article(article_id):
#     data = request.form
#     title = data.get('title')
#     career_type = data.get('career_type')
#     content = data.get('content')

#     if not title or not career_type or not content:
#         return jsonify({'error': 'Missing required fields'}), 400

#     media_files = request.files.getlist('media')
#     media_filenames = []

#     for media_file in media_files:
#         if media_file.filename == '':
#             continue
#         media_file.save(f'media/{datetime.datetime.now().strftime("%Y%m%d%H%M%S")}_{media_file.filename}')
#         media_filenames.append(media_file.filename)

#     media_filenames_json = json.dumps(media_filenames)

#     query_db('UPDATE articles SET title = ?, career_type = ?, media = ?, content = ? WHERE article_id = ?', 
#              [title, career_type,media_filenames_json, content, article_id])
#     return jsonify({'message': '文章編輯成功'}), 200

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

# @app.route('/favorites/detail/<int:article_id>', methods=['GET'])
# def get_favorite_detail(article_id):
#     article = query_db('SELECT title, career_type, media, content, created_at, is_deleted FROM articles WHERE article_id = ?', [article_id], one=True)  # 修改這一行
#     if not article or article[5] == 1:  # 修改這一行
#         return jsonify({'message': '該文章已被刪除'}), 404  # 修改這一行

#     return jsonify({'title': article[0], 'career_type': article[1], 'media': article[2], 'content': article[3], 'created_at': article[4]}), 200

@app.route('/careers/<type>', methods=['GET'])
def get_career_type(type):
    try:
        with open(f'type/{type}.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        return jsonify(data), 200
    except FileNotFoundError:
        return jsonify({'error': '類型不存在'}), 404

@app.route('/careers/<type>/jobs', methods=['GET'])
def get_career_type_jobs(type):
    try:
        with open(f'work/{type}.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        job_titles = list(data.keys())
        return jsonify(job_titles), 200
    except FileNotFoundError:
        return jsonify({'error': '類型不存在'}), 404

@app.route('/careers/<type>/jobs/<job_title>', methods=['GET'])
def get_career_type_job_detail(type, job_title):
    try:
        with open(f'work/{type}.json', 'r', encoding='utf-8') as file:
            data = json.load(file)
        job_detail = data.get(job_title)
        if not job_detail:
            return jsonify({'error': '職業不存在'}), 404
        return jsonify(job_detail), 200
    except FileNotFoundError:
        return jsonify({'error': '類型不存在'}), 404

if __name__ == '__main__':
    app.run(debug=True)