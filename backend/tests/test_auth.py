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


def test_login_rejects_invalid_credentials(client):
    client.post('/auth/register', json={'email': 'writer@example.com', 'password': 'strongpass123'})

    response = client.post('/auth/login', json={'email': 'writer@example.com', 'password': 'wrongpass123'})

    assert response.status_code == 401
    assert response.json()['detail'] == 'INVALID_CREDENTIALS'


def test_me_requires_token(client):
    response = client.get('/auth/me')

    assert response.status_code == 401
    assert response.json()['detail'] == 'UNAUTHORIZED'


def test_me_rejects_token_with_non_integer_subject(client):
    token = create_access_token('not-an-int')

    response = client.get('/auth/me', headers={'Authorization': f'Bearer {token}'})

    assert response.status_code == 401
    assert response.json()['detail'] == 'UNAUTHORIZED'
