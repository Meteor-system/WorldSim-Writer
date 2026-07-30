from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]


def test_backend_image_is_pinned_non_root_and_uses_the_production_runner():
    dockerfile = (REPO_ROOT / 'backend' / 'Dockerfile').read_text(encoding='utf-8')

    assert 'FROM python:3.12.13-slim-bookworm@sha256:' in dockerfile
    assert 'USER 10001:10001' in dockerfile
    assert 'STOPSIGNAL SIGTERM' in dockerfile
    assert 'CMD ["python", "scripts/run_api.py"]' in dockerfile
    assert 'SECRET_KEY=' not in dockerfile
    assert 'LLM_API_KEY=' not in dockerfile


def test_backend_build_context_excludes_local_state_tests_and_protected_files():
    dockerignore = (REPO_ROOT / 'backend' / '.dockerignore').read_text(encoding='utf-8').splitlines()

    for ignored_path in ['.env', 'tests/', 'backups/', '*.db', '*.dump', '_chk.py', 'uv.lock']:
        assert ignored_path in dockerignore


def test_compose_serializes_migrations_before_a_non_root_ready_api():
    compose = (REPO_ROOT / 'compose.yaml').read_text(encoding='utf-8')
    db_service = compose.split('  db:\n', 1)[1].split('  migrate:\n', 1)[0]
    api_service = compose.split('  api:\n', 1)[1].split('\nvolumes:\n', 1)[0]

    assert 'postgres:18.4-alpine@sha256:' in db_service
    assert 'postgres-data:/var/lib/postgresql' in db_service
    assert 'ports:' not in db_service
    assert 'command: ["python", "scripts/run_migrations.py"]' in compose
    assert 'condition: service_completed_successfully' in api_service
    assert 'API_HOST: "0.0.0.0"' in compose
    assert '${COMPOSE_API_BIND_ADDRESS:-127.0.0.1}:${COMPOSE_API_PORT:-8000}:8000' in api_service
    assert "http://127.0.0.1:8000/ready" in api_service
    assert 'read_only: true' in api_service
    assert 'no-new-privileges:true' in api_service
    assert 'stop_signal: SIGTERM' in api_service
    assert 'LLM_API_MODE: "${LLM_API_MODE:-responses}"' in compose
    assert 'LLM_TIMEOUT_SECONDS: "${LLM_TIMEOUT_SECONDS:-60}"' in compose
    assert 'LLM_READ_TIMEOUT_SECONDS: "${LLM_READ_TIMEOUT_SECONDS:-300}"' in compose


def test_compose_example_defaults_to_loopback_and_mock_llm_without_real_secrets():
    env_example = (REPO_ROOT / '.env.example').read_text(encoding='utf-8')

    assert 'COMPOSE_API_BIND_ADDRESS=127.0.0.1' in env_example
    assert 'LLM_MOCK=true' in env_example
    assert 'LLM_API_MODE=responses' in env_example
    assert 'LLM_TIMEOUT_SECONDS=60' in env_example
    assert 'LLM_READ_TIMEOUT_SECONDS=300' in env_example
    assert 'SECRET_KEY=change-this-local-secret' in env_example
    assert 'POSTGRES_PASSWORD=change-this-database-password' in env_example
    assert 'replace the database password and SECRET_KEY' in env_example
    assert 'replace the LLM provider placeholders only when LLM_MOCK=false' in env_example
    assert 'replace every placeholder' not in env_example
