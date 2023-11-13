FROM ubuntu:22.04

ENV POETRY_VERSION=1.6.1
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        software-properties-common \
        gpg \
        gpg-agent && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get install -y --no-install-recommends \
        curl \
        python3.11 && \
    rm -rf /var/lib/apt/lists/* && \
    apt clean

ARG USER=alerts
ARG USER_PID=1000
ARG GROUP=${USER}
ARG GROUP_PID=${USER_PID}
ENV PYTHONPATH=/opt:$PYTHONPATH

RUN curl -sSL https://install.python-poetry.org | POETRY_VERSION=${POETRY_VERSION} python3.11 -

ADD server /opt/blueiris_alerts/server
ADD utils /opt/blueiris_alerts/utils
ADD schemas /opt/blueiris_alerts/schemas
COPY pyproject.toml /opt/blueiris_alerts/server
COPY poetry.lock /opt/blueiris_alerts/server

WORKDIR /opt/blueiris_alerts/server

RUN groupadd --gid ${GROUP_PID} ${GROUP} && \
    useradd --uid ${USER_PID} --gid ${GROUP_PID} -m ${USER} && \
    chown -R ${USER}:${GROUP} /opt/blueiris_alerts

WORKDIR /opt/blueiris_alerts/server

RUN ${HOME}/.local/bin/poetry config virtualenvs.create false && \
    ${HOME}/.local/bin/poetry install --no-dev

USER ${USER}

EXPOSE 8560
CMD [ "python3.11", "-m", "gunicorn", "-k", "uvicorn.workers.UvicornWorker", "app:app", "--workers", "4", "--bind", "0.0.0.0:8560", "--access-logfile", "-", "--error-logfile", "-" ]