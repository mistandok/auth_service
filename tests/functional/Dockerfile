FROM python:3.11-slim

ENV APP_DIR=/tests/functional

WORKDIR $APP_DIR

COPY requirements.txt requirements.txt

RUN  apt-get update \
     && apt-get -y install libpq-dev gcc \
     && apt-get install acl \
     && apt-get install -y iputils-ping \
     && apt install -y netcat \
     && groupadd -r tests \
     && useradd -d $APP_DIR -r -g tests tests \
     && chown tests:tests -R $APP_DIR \
     && pip install --upgrade pip

RUN pip install -r $APP_DIR/requirements.txt

COPY . $APP_DIR

RUN chmod u+x $APP_DIR/start-tests.sh

ENV PYTHONPATH "${PYTHONPATH}:/"

USER tests

ENTRYPOINT ["/tests/functional/start-tests.sh"]