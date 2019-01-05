FROM python:3.6-slim

# Working directory for the application
WORKDIR /usr/src/app
RUN apt-get update && apt-get install -y git
# prepare to run bot.
RUN apt-get update && apt-get install -y supervisor
RUN mkdir -p /var/log/supervisor
RUN touch /var/run/supervisor.sock && chmod 777 /var/run/supervisor.sock


# clone project
RUN git clone https://github.com/Breee/pokemon-raid-bot.git /usr/src/app/
RUN pip install --no-cache-dir -r requirements.txt
COPY ./supervisord.conf /
COPY ./entrypoint.sh /
RUN chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]