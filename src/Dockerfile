FROM python:3.11

ENV APP_DIR /app

WORKDIR $APP_DIR

COPY requirements.txt $APP_DIR/requirements.txt

RUN  apt-get update \
     && apt-get -y install libpq-dev gcc \
     && apt-get install acl \
     && apt install -y netcat \
     && groupadd -r web \
     && useradd -d $APP_DIR -r -g web web \
     && chown web:web -R $APP_DIR \
     && pip install --upgrade pip

RUN pip install -r $APP_DIR/requirements.txt

COPY . $APP_DIR

RUN chmod u+x $APP_DIR/start-flask.sh

ENTRYPOINT ["./start-flask.sh"]