# Dockerfile 
FROM python:3.14.7-bookworm

# allow statements and log messages to show immediately in the logs
ENV PYTHONUNBUFFERED True
# copy local code to container image
ENV APP_HOME /back-end
WORKDIR $APP_HOME
COPY . ./

RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Run web service on container startup.
# Using gunicorn webserver, with one worker process and 8 threads.
# For environments with multiple CPU cores, increase number of workers
# to be equal to number of cores available.
# Timeout is set to zero to disable the timeouts of the workers to allow Cloud Run to handle instance scaling.
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 app:app