FROM ubuntu:24.04

# RUN apt-get update && apt-get install -y libspatialindex-dev git curl g++ build-essential python3-dev python3 python3-pip pkg-config
ENV PIP_BREAK_SYSTEM_PACKAGES=1
RUN apt-get update && apt-get install -y git curl python3 python3-pip python3-dev

# Set WORKDIR
WORKDIR /usr/src/app

# Install requirement
COPY ./requirements.txt ./requirements.txt
RUN pip install -r requirements.txt

# Copy app files
COPY ./images ./images
COPY ./modules ./modules
COPY ./app.py ./app.py
COPY ./defaults ./defaults
COPY ./pages ./pages
COPY ./.streamlit ./.streamlit
COPY ./ui-config.json ./ui-config.json
COPY ./defaults ./defaults

# Run streamlit
CMD ["streamlit", "run", "app.py"]
EXPOSE 8501
