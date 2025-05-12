FROM apify/actor-python-playwright

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt

CMD ["python", "main.py"]
