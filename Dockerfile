FROM python

RUN mkdir -p /opt/app

WORKDIR /opt/app

COPY requirements.txt .

RUN pip3 install -r requirements.txt

COPY . .

CMD python3 app.py
