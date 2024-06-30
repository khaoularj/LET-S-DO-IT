FROM python:3
ENV FLASK_APP=app.py
RUN mkdir /app
WORKDIR /app
COPY requirements.txt /app/
RUN pip install -r requirements.txt 
COPY . /app/
EXPOSE 5000
CMD python app.py