FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1
ENV PYTHONIOENCODING=UTF-8

WORKDIR /app

# COPY ./requirements.txt /app

# Install individually due to large container size
# RUN pip install --no-cache-dir -r requirements.txt
RUN pip install uvicorn fastapi nltk numpy
RUN pip install torch --extra-index-url https://download.pytorch.org/whl/cpu
RUN pip install sentence-transformers

COPY ./api.py /app
COPY ./embedding_search.py /app

EXPOSE 8000

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
