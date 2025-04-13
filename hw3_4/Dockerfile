FROM python:3.12.8
LABEL authors="ilushka-obnimashka"

WORKDIR /hw5

COPY src/ /hw5/src/
COPY main.py /hw5
COPY requirements.txt /hw5

RUN pip install -r requirements.txt

RUN apt-get update && apt-get install -y wget unzip && \
    wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb && \
    apt install -y ./google-chrome-stable_current_amd64.deb && \
    rm google-chrome-stable_current_amd64.deb && apt-get clean

ENTRYPOINT ["python", "main.py"]