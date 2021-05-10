FROM tigrlab/datman:0.1

########################################## Update this after testing
RUN git clone https://github.com/DESm1th/dashboard.git && \
    cd /dashboard && \
    git checkout easybake_dashboard && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

ENV PATH="${PATH}:/dashboard"
ENV PYTHONPATH="${PYTHONPATH}:/dashboard"

# This entry point is only needed if the container itself needs to take
# charge of keeping the database schema up to date
COPY ./entrypoint3.sh /entrypoint3.sh

# Might need the --static-map command from srv_uwsgi.sh to correctly
# serve qc pages
# might need         "--daemonize=/output.log" to hold log output
CMD ["uwsgi", \
        "--socket=0.0.0.0:5000", \
        "--protocol=http", \
        "--wsgi-file=/dashboard/wsgi.py", \
        "--callable=app", \
        "--enable-threads"]
