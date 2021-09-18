FROM tigrlab/datman:0.1

# NOTE: When building this container, do it from
# inside the dashboard folder and build with
#       docker build -f containers/devel/Dockerfile .
# or the build context will be incorrect and files may not
# be copied

COPY containers/devel/entrypoint.sh /entrypoint.sh

COPY . /dashboard

RUN cd /dashboard && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

ENV PATH="/dashboard:${PATH}"
ENV PYTHONPATH="/dashboard:${PYTHONPATH}"

CMD ["uwsgi", \
        "--socket=0.0.0.0:5000", \
        "--protocol=http", \
        "--wsgi-file=/dashboard/wsgi.py", \
        "--callable=app", \
        "--enable-threads"]
