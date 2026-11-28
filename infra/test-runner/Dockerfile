# Linux test runner for team unit tests, coverage and mutation testing.
# Why: Indico needs Python 3.12 + PostgreSQL + redis-server, and Cosmic Ray mutates source in place.
# Same toolchain as .github/workflows/ci.yml so local results match CI.
FROM python:3.12-bookworm

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    UV_SYSTEM_PYTHON=1 \
    UV_LINK_MODE=copy \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends redis-server postgresql-client libpq-dev git \
 && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:0.9.5 /uv /uvx /bin/

# Install pinned Indico runtime + dev deps (cached layer). Source is bind-mounted at /repo at run time.
COPY requirements.txt requirements.dev.txt /tmp/req/
COPY tests/team/requirements.txt /tmp/req/team.txt
RUN uv pip install -r /tmp/req/requirements.txt -r /tmp/req/requirements.dev.txt -r /tmp/req/team.txt

COPY infra/test-runner/entrypoint.sh /usr/local/bin/sqe-entrypoint
RUN sed -i 's/\r$//' /usr/local/bin/sqe-entrypoint && chmod +x /usr/local/bin/sqe-entrypoint

WORKDIR /repo
ENTRYPOINT ["sqe-entrypoint"]
CMD ["bash"]
