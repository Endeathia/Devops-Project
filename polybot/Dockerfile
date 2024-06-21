FROM python
WORKDIR /app
RUN pip install --upgrade pip
COPY . .
RUN pip install -r requirements.txt
ENV telegram_chat_url='Tamer-Load-Balancer-1677582904.us-west-1.elb.amazonaws.com'
EXPOSE 8443
CMD ["python3", "app.py"]
