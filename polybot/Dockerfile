FROM python
WORKDIR /app
RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install awscli
RUN pip install --upgrade pip
COPY . .
RUN pip install -r requirements.txt
ENV telegram_chat_url='a7c4e3f0497484be8b8bfbd29c23e08c-886387923.us-east-1.elb.amazonaws.com'
EXPOSE 8443
CMD ["python3", "app.py"]
