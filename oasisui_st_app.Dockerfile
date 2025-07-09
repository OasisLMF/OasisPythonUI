FROM python:3.12-slim AS compile-image

RUN apt-get update
RUN apt-get install -y --no-install-recommends build-essential gcc

# Install requirement
COPY ./requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.12-slim AS build-image
COPY --from=compile-image /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Set WORKDIR
WORKDIR /usr/src/app

# Copy app files
COPY ./images ./images
COPY ./modules ./modules
COPY ./app.py ./app.py
COPY ./defaults ./defaults
COPY ./pages ./pages
COPY ./assets/ ./assets
COPY ./.streamlit ./.streamlit
COPY ./ui-config.json ./ui-config.json

# Run streamlit
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501"]
