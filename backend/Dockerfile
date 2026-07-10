FROM python:3.12.13-slim-bookworm@sha256:8a7e7cc04fd3e2bd787f7f24e22d5d119aa590d429b50c95dfe12b3abe52f48b

ENV HOME=/home/worldsim \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --gid 10001 worldsim \
    && useradd --uid 10001 --gid worldsim --create-home --home-dir /home/worldsim --shell /usr/sbin/nologin worldsim

COPY pyproject.toml /tmp/worldsim-pyproject.toml
RUN python -c "import pathlib, subprocess, sys, tomllib; project = tomllib.loads(pathlib.Path('/tmp/worldsim-pyproject.toml').read_text(encoding='utf-8')); subprocess.run([sys.executable, '-m', 'pip', 'install', *project['project']['dependencies']], check=True)" \
    && rm /tmp/worldsim-pyproject.toml

COPY --chown=10001:10001 alembic.ini ./alembic.ini
COPY --chown=10001:10001 alembic ./alembic
COPY --chown=10001:10001 app ./app
COPY --chown=10001:10001 scripts ./scripts

USER 10001:10001

EXPOSE 8000
STOPSIGNAL SIGTERM
CMD ["python", "scripts/run_api.py"]
