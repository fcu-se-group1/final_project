import pytest
import json
from backapi import app, query_db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        with app.app_context():
            query_db('DROP TABLE IF EXISTS users')
            query_db('DROP TABLE IF EXISTS career_tests')
            query_db('DROP TABLE IF EXISTS articles')
            query_db('DROP TABLE IF EXISTS comments')
            query_db('DROP TABLE IF EXISTS favorites')
            query_db('DROP TABLE IF EXISTS careers')
            query_db('''
                CREATE TABLE users (
                    user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    password TEXT NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('job_seeker', 'professional'))
                )
            ''')
            query_db('''
                CREATE TABLE career_tests (
                    test_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    result TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            query_db('''
                CREATE TABLE articles (
                    article_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    author_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    career_type TEXT NOT NULL,
                    media TEXT NOT NULL,
                    content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (author_id) REFERENCES users(user_id)
                )
            ''')
            query_db('''
                CREATE TABLE comments (
                    comment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles(article_id),
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            ''')
            query_db('''
                CREATE TABLE favorites (
                    favorite_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    article_id INTEGER NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(user_id),
                    FOREIGN KEY (article_id) REFERENCES articles(article_id)
                )
            ''')
            query_db('''
                CREATE TABLE careers (
                    career_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    type TEXT UNIQUE NOT NULL,
                    description TEXT NOT NULL
                )
            ''')
        yield client

def test_register(client):
    response = client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword',
        'role': 'job_seeker'
    })
    assert response.status_code == 201
    assert response.get_json()['message'] == 'User registered successfully'

def test_login(client):
    client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword',
        'role': 'job_seeker'
    })
    response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    assert response.status_code == 200
    assert response.get_json()['message'] == 'Login successful'

def test_create_career_test(client):
    client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword',
        'role': 'job_seeker'
    })
    login_response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    user_id = login_response.get_json()['user_id']
    response = client.post('/career_test', json={
        'user_id': user_id,
        'result': {'test': 'result'}
    })
    assert response.status_code == 201
    assert response.get_json()['message'] == 'Career test created successfully'

def test_get_career_test(client):
    client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword',
        'role': 'job_seeker'
    })
    login_response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    user_id = login_response.get_json()['user_id']
    client.post('/career_test', json={
        'user_id': user_id,
        'result': {'test': 'result'}
    })
    response = client.get(f'/career_test/{user_id}')
    assert response.status_code == 200
    assert len(response.get_json()) > 0

def test_create_article(client):
    client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword',
        'role': 'professional'
    })
    login_response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    user_id = login_response.get_json()['user_id']
    response = client.post('/articles', json={
        'author_id': user_id,
        'title': 'Test Article',
        'career_type': 'Engineering',
        'media': 'image.png',
        'content': 'This is a test article.'
    })
    assert response.status_code == 201
    assert response.get_json()['message'] == 'Article created successfully'

def test_get_comments(client):
    client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword',
        'role': 'professional'
    })
    login_response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    user_id = login_response.get_json()['user_id']
    client.post('/articles', json={
        'author_id': user_id,
        'title': 'Test Article',
        'career_type': 'Engineering',
        'media': 'image.png',
        'content': 'This is a test article.'
    })
    article_id = query_db('SELECT article_id FROM articles WHERE author_id = ?', [user_id], one=True)[0]
    response = client.get(f'/comments/{article_id}')
    assert response.status_code == 200
    assert response.get_json() == []

def test_create_comment(client):
    client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword',
        'role': 'professional'
    })
    login_response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    user_id = login_response.get_json()['user_id']
    client.post('/articles', json={
        'author_id': user_id,
        'title': 'Test Article',
        'career_type': 'Engineering',
        'media': 'image.png',
        'content': 'This is a test article.'
    })
    article_id = query_db('SELECT article_id FROM articles WHERE author_id = ?', [user_id], one=True)[0]
    response = client.post('/comments', json={
        'article_id': article_id,
        'user_id': user_id,
        'content': 'This is a test comment.'
    })
    assert response.status_code == 201
    assert response.get_json()['message'] == 'Comment added successfully'

def test_search_articles(client):
    client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword',
        'role': 'professional'
    })
    login_response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    user_id = login_response.get_json()['user_id']
    client.post('/articles', json={
        'author_id': user_id,
        'title': 'Test Article',
        'career_type': 'Engineering',
        'media': 'image.png',
        'content': 'This is a test article.'
    })
    response = client.get('/search_articles?career_type=Engineering&keyword=Test')
    assert response.status_code == 200
    assert len(response.get_json()) > 0

def test_get_careers(client):
    query_db('INSERT INTO careers (type, description) VALUES (?, ?)', ['Engineering', 'Engineering description'])
    response = client.get('/careers')
    assert response.status_code == 200
    assert len(response.get_json()) > 0

def test_get_career(client):
    query_db('INSERT INTO careers (type, description) VALUES (?, ?)', ['Engineering', 'Engineering description'])
    career_id = query_db('SELECT career_id FROM careers WHERE type = ?', ['Engineering'], one=True)[0]
    response = client.get(f'/careers/{career_id}')
    assert response.status_code == 200
    assert response.get_json()['type'] == 'Engineering'

def test_get_history_tests(client):
    client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword',
        'role': 'job_seeker'
    })
    login_response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    user_id = login_response.get_json()['user_id']
    client.post('/career_test', json={
        'user_id': user_id,
        'result': {'test': 'result'}
    })
    response = client.get(f'/history_tests/{user_id}')
    assert response.status_code == 200
    assert len(response.get_json()) > 0

def test_get_test_detail(client):
    client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword',
        'role': 'job_seeker'
    })
    login_response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    user_id = login_response.get_json()['user_id']
    client.post('/career_test', json={
        'user_id': user_id,
        'result': {'test': 'result'}
    })
    test_id = query_db('SELECT test_id FROM career_tests WHERE user_id = ?', [user_id], one=True)[0]
    response = client.get(f'/history_tests/detail/{test_id}')
    assert response.status_code == 200
    assert response.get_json()['test'] == 'result'

def test_get_user_articles(client):
    client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword',
        'role': 'professional'
    })
    login_response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    user_id = login_response.get_json()['user_id']
    client.post('/articles', json={
        'author_id': user_id,
        'title': 'Test Article',
        'career_type': 'Engineering',
        'media': 'image.png',
        'content': 'This is a test article.'
    })
    response = client.get(f'/user_articles/{user_id}')
    assert response.status_code == 200
    assert len(response.get_json()) > 0

def test_get_article_detail(client):
    client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword',
        'role': 'professional'
    })
    login_response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    user_id = login_response.get_json()['user_id']
    client.post('/articles', json={
        'author_id': user_id,
        'title': 'Test Article',
        'career_type': 'Engineering',
        'media': 'image.png',
        'content': 'This is a test article.'
    })
    article_id = query_db('SELECT article_id FROM articles WHERE author_id = ?', [user_id], one=True)[0]
    response = client.get(f'/user_articles/detail/{article_id}')
    assert response.status_code == 200
    assert response.get_json()['title'] == 'Test Article'

def test_edit_article(client):
    client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword',
        'role': 'professional'
    })
    login_response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    user_id = login_response.get_json()['user_id']
    client.post('/articles', json={
        'author_id': user_id,
        'title': 'Test Article',
        'career_type': 'Engineering',
        'media': 'image.png',
        'content': 'This is a test article.'
    })
    article_id = query_db('SELECT article_id FROM articles WHERE author_id = ?', [user_id], one=True)[0]
    response = client.post(f'/user_articles/edit/{article_id}', json={
        'title': 'Updated Article',
        'career_type': 'Engineering',
        'media': 'updated_image.png',
        'content': 'This is an updated test article.'
    })
    assert response.status_code == 200
    assert response.get_json()['message'] == '文章編輯成功'

def test_delete_article(client):
    client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword',
        'role': 'professional'
    })
    login_response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    user_id = login_response.get_json()['user_id']
    client.post('/articles', json={
        'author_id': user_id,
        'title': 'Test Article',
        'career_type': 'Engineering',
        'media': 'image.png',
        'content': 'This is a test article.'
    })
    article_id = query_db('SELECT article_id FROM articles WHERE author_id = ?', [user_id], one=True)[0]
    response = client.delete(f'/user_articles/delete/{article_id}')
    assert response.status_code == 200
    assert response.get_json()['message'] == '該文章已被刪除'

def test_get_favorites(client):
    client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword',
        'role': 'job_seeker'
    })
    login_response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    user_id = login_response.get_json()['user_id']
    client.post('/articles', json={
        'author_id': user_id,
        'title': 'Test Article',
        'career_type': 'Engineering',
        'media': 'image.png',
        'content': 'This is a test article.'
    })
    article_id = query_db('SELECT article_id FROM articles WHERE author_id = ?', [user_id], one=True)[0]
    query_db('INSERT INTO favorites (user_id, article_id) VALUES (?, ?)', [user_id, article_id])
    response = client.get(f'/favorites/{user_id}')
    assert response.status_code == 200
    assert len(response.get_json()) > 0

def test_get_favorite_detail(client):
    client.post('/register', json={
        'username': 'testuser',
        'password': 'testpassword',
        'role': 'job_seeker'
    })
    login_response = client.post('/login', json={
        'username': 'testuser',
        'password': 'testpassword'
    })
    user_id = login_response.get_json()['user_id']
    client.post('/articles', json={
        'author_id': user_id,
        'title': 'Test Article',
        'career_type': 'Engineering',
        'media': 'image.png',
        'content': 'This is a test article.'
    })
    article_id = query_db('SELECT article_id FROM articles WHERE author_id = ?', [user_id], one=True)[0]
    query_db('INSERT INTO favorites (user_id, article_id) VALUES (?, ?)', [user_id, article_id])
    response = client.get(f'/favorites/detail/{article_id}')
    assert response.status_code == 200
    assert response.get_json()['title'] == 'Test Article'