FROM ubuntu:24.04

ENV PIP_BREAK_SYSTEM_PACKAGES=1
RUN apt-get update && apt-get install -y git curl python3 python3-pip python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Set WORKDIR
WORKDIR /usr/src/app

# Install requirement
COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# Copy app files
COPY ./images ./images
COPY ./modules ./modules
COPY ./app.py ./app.py
COPY ./pages ./pages
COPY ./assets/ ./assets
COPY ./.streamlit ./.streamlit
COPY ./ui-config.json ./ui-config.json

# Run streamlit
EXPOSE 8501
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health
ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501"]
