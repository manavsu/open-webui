FROM python:3.11

WORKDIR /usr/src/app

RUN git clone https://github.com/open-webui/pipelines.git

WORKDIR /usr/src/app/pipelines

RUN pip install -r requirements.txt

RUN pip install langchain langgraph langchain-ollama langchain-community

CMD ["./start.sh"]
