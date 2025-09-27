FROM python:3.12-slim-bookworm

WORKDIR /api

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

RUN chmod +x /api/bin/boot.sh

EXPOSE 8000

ENTRYPOINT ["/api/bin/boot.sh"]
