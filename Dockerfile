FROM python:3.8-slim

WORKDIR /app

# 复制项目文件
COPY requirements.txt .
COPY app/ ./app/
COPY config/ ./config/
COPY server.py .

# 创建日志目录
RUN mkdir -p logs

# 安装依赖
RUN pip install --no-cache-dir -r requirements.txt

# 暴露服务端口
EXPOSE 8000
EXPOSE 9090

# 启动服务
CMD ["python", "server.py"]