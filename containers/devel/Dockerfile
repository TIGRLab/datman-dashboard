FROM tigrlab/datman:0.1

# NOTE: When building this container, do it from
# inside the dashboard folder and build with
#       docker build -f containers/devel/Dockerfile .
# or the build context will be incorrect and files may not
# be copied

COPY containers/devel/entrypoint.sh /entrypoint.sh

# Copy the requirements and set up the python env first so
# that rebuilds are faster.
COPY ./requirements.txt /
RUN pip install --upgrade pip && \
    pip install -r /requirements.txt && \
    pip install flask-debugtoolbar

ENV PATH="/dashboard:${PATH}"
ENV PYTHONPATH="/dashboard:${PYTHONPATH}"

COPY . /dashboard

CMD ["uwsgi", \
        "--socket=0.0.0.0:5000", \
        "--protocol=http", \
        "--wsgi-file=/dashboard/wsgi.py", \
        "--callable=app", \
        "--enable-threads"]
