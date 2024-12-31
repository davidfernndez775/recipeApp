FROM nginxinc/nginx-unprivileged:1-alpine
LABEL maintainer="davidfernandez999"

# su usa una version nginx-unprivileged por razones de seguridad de tal manera que
# el servidor funcione con la menor cantidad de privilegios necesarios para que
# la aplicacion funcione

COPY ./default.conf.tpl /etc/nginx/default.conf.tpl
COPY ./uwsgi_params /etc/nginx/uwsgi_params
COPY ./run.sh /run.sh

ENV LISTEN_PORT=8000
ENV APP_HOST=app
ENV APP_PORT=9000

# usamos el root user para ejecutar los comandos
USER root

RUN mkdir -p /vol/static && \
    chmod 755 /vol/static && \
    touch /etc/nginx/conf.d/default.conf && \
    chown nginx:nginx /etc/nginx/conf.d/default.conf && \
    chmod +x /run.sh

VOLUME /vol/static

# cambia el usuario para disminuir los privilegios
USER nginx

CMD [ "/run.sh" ]