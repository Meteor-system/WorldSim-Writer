from sqlalchemy import select

from app.auth.models import User
from app.core.security import create_access_token


def test_register_login_and_me(client):
    register_response = client.post('/auth/register', json={'email': 'writer@example.com', 'password': 'strongpass123'})

    assert register_response.status_code == 200
    token = register_response.json()['access_token']
    assert register_response.json()['user']['email'] == 'writer@example.com'

    me_response = client.get('/auth/me', headers={'Authorization': f'Bearer {token}'})
    assert me_response.status_code == 200
    assert me_response.json()['email'] == 'writer@example.com'

    login_response = client.post('/auth/login', json={'email': 'writer@example.com', 'password': 'strongpass123'})
    assert login_response.status_code == 200
    assert login_response.json()['access_token']


def test_register_rejects_duplicate_email(client):
    client.post('/auth/register', json={'email': 'writer@example.com', 'password': 'strongpass123'})

    response = client.post('/auth/register', json={'email': 'writer@example.com', 'password': 'strongpass123'})

    assert response.status_code == 409
    assert response.json()['detail'] == 'EMAIL_ALREADY_REGISTERED'


def test_register_rejects_extra_fields_without_creating_user(client, db_session):
    email = 'auth-extra-register@example.com'
    assert db_session.scalar(select(User).where(User.email == email)) is None

    response = client.post(
        '/auth/register',
        json={'email': email, 'password': 'strongpass123', 'raw_text': '认证请求不应接收运行时原文。'},
    )

    assert response.status_code == 422
    assert any(error['type'] == 'extra_forbidden' and error['loc'][-1] == 'raw_text' for error in response.json()['detail'])
    assert db_session.scalar(select(User).where(User.email == email)) is None


def test_login_rejects_extra_fields(client):
    client.post('/auth/register', json={'email': 'login-extra@example.com', 'password': 'strongpass123'})

    response = client.post(
        '/auth/login',
        json={
            'email': 'login-extra@example.com',
            'password': 'strongpass123',
            'raw_text': '认证请求不应接收运行时原文。',
        },
    )

    assert response.status_code == 422
    assert any(error['type'] == 'extra_forbidden' and error['loc'][-1] == 'raw_text' for error in response.json()['detail'])


def test_login_rejects_invalid_credentials(client):
    client.post('/auth/register', json={'email': 'writer@example.com', 'password': 'strongpass123'})

    response = client.post('/auth/login', json={'email': 'writer@example.com', 'password': 'wrongpass123'})

    assert response.status_code == 401
    assert response.json()['detail'] == 'INVALID_CREDENTIALS'


def test_logout_accepts_empty_body_contract(client):
    no_body = client.post('/auth/logout')
    empty_object = client.post('/auth/logout', json={})

    assert no_body.status_code == 200
    assert no_body.json() == {'success': True}
    assert empty_object.status_code == 200
    assert empty_object.json() == {'success': True}


def test_logout_rejects_extra_fields_without_user_side_effects(client, db_session):
    client.post('/auth/register', json={'email': 'logout-extra@example.com', 'password': 'strongpass123'})
    before_user_ids = list(db_session.scalars(select(User.id).order_by(User.id)))

    response = client.post('/auth/logout', json={'raw_text': '登出请求不应接收运行时原文。'})

    assert response.status_code == 422
    assert any(error['type'] == 'extra_forbidden' and error['loc'][-1] == 'raw_text' for error in response.json()['detail'])
    assert list(db_session.scalars(select(User.id).order_by(User.id))) == before_user_ids


def test_me_requires_token(client):
    response = client.get('/auth/me')

    assert response.status_code == 401
    assert response.json()['detail'] == 'UNAUTHORIZED'


def test_me_rejects_token_with_non_integer_subject(client):
    token = create_access_token('not-an-int')

    response = client.get('/auth/me', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 401
    assert response.json()['detail'] == 'UNAUTHORIZED'
