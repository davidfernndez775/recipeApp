# definimos el lenguaje y la version de Linux(alpine) que es una distribucion ligera
FROM python:3.9-alpine3.13
LABEL mantainer="davidfernandez999"

# se agrega esta linea para imprimir directamente los mensajes de Python en la consola
ENV PYTHONUNBUFFERED 1


# se pasan las dependencias definidas en los requerimientos
COPY ./requirements.txt /tmp/requirements.txt
COPY ./requirements.dev.txt /tmp/requirements.dev.txt
# se pasa la carpeta de la aplicacion y el puerto
COPY ./app /app
WORKDIR /app
EXPOSE 8000

# se define un argumento que va a establecer el modo DEV en falso,  esto se cambia 
# segun el archivo de configuracion .yml que se use
ARG DEV=false
# es importante que sea todo en un solo comando para que la imagen sea ligera, aca se
# crea el venv, se actualiza el pip, se instalan las dependencias, se borran las dependencias
# una vez que la imagen es creada. Finalmente se crea un usuario distinto del usuario root
# de la distribucion de Linux, esto se hace para correr la aplicacion desde este usuario y no
# desde el root, porque este ultimo tiene todos los privilegios de administrador y en caso 
# de hackeo de la aplicacion todo el contenedor se ve comprometido
RUN python -m venv /py && \
    /py/bin/pip install --upgrade pip && \
    /py/bin/pip install -r /tmp/requirements.txt && \
    if [ $DEV = "true"]; \
        then /py/bin/pip install -r /tmp/requirements.dev.txt; \
    fi && \
    rm -rf /tmp && \
    adduser -D -H -s /bin/false django-user

ENV PATH="/py/bin:$PATH"

USER django-user