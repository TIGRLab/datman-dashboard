FROM tigrlab/datman:0.1

COPY . /dashboard

RUN pip install --upgrade pip && \
    pip install -r /dashboard/requirements.txt

ENV PATH="/dashboard:${PATH}"
ENV PYTHONPATH="/dashboard:${PYTHONPATH}"

COPY containers/prod/entrypoint.sh /

CMD ["uwsgi", \
        "--socket=0.0.0.0:5000", \
        "--protocol=http", \
        "--wsgi-file=/dashboard/wsgi.py", \
        "--callable=app", \
        "--enable-threads"]
