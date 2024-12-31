# Definimos el lenguaje y la versión de Linux (alpine) que es una distribución ligera
FROM python:3.9-alpine3.13
LABEL maintainer="davidfernandez999"

# Se agrega esta línea para imprimir directamente los mensajes de Python en la consola
ENV PYTHONUNBUFFERED 1

# Se pasan las dependencias definidas en los requerimientos
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt

# Se pasa la carpeta de scripts para el deployment
COPY ./scripts /scripts

# Se pasa la carpeta de la aplicación y el puerto
COPY ./app /app
WORKDIR /app
EXPOSE 8000

# Se define un argumento que va a establecer el modo DEV en falso, esto se cambia
# según el archivo de configuración .yml que se use
ARG DEV=false

# Es importante que sea todo en un solo comando para que la imagen sea ligera, acá se
# crea el venv, se actualiza el pip, se instalan las dependencias de la base de datos.
# Primero el postgresql-client y luego otras dependencias que solo son necesarias para
# la instalacion del cliente de postgresql.
# Se instalan los requerimientos, primero los generales y luego los de desarrollo si
# fuera el caso. Se borran las dependencias una vez que la imagen es creada, solo las
# dependencias que son necesarias para la instalacion.
# Finalmente se crea un usuario distinto del usuario root
# de la distribución de Linux, esto se hace para correr la aplicación desde este usuario y no
# desde el root, porque este último tiene todos los privilegios de administrador y en caso
# de hackeo de la aplicación todo el contenedor se ve comprometido. No obstante es necesario
# crear un directorio donde el django user tenga determinados privilegios
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    apk add --update --no-cache postgresql-client jpeg-dev && \
    apk add --update --no-cache --virtual .tmp-build-deps \
    build-base postgresql-dev musl-dev zlib zlib-dev linux-headers && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ "$DEV" = "true" ]; then /py/bin/pip install -r /tmp/requirements.dev.txt; fi && \
    rm -rf /tmp && \
    apk del .tmp-build-deps && \
    adduser -D -H -s /bin/false django-user && \
    mkdir -p /vol/web/media && \
    mkdir -p /vol/web/static && \
    chown -R django-user:django-user /vol && \
    chmod -R 755 /vol && \
    chmod -R +x /scripts

ENV PATH="/scripts:/py/bin:$PATH"

USER django-user

# este es el script para el deployment
CMD ["run.sh"]