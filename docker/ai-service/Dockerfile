# 使用 Python 3.12 官方镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖和 Poetry
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libmariadb-dev-compat \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install poetry

# 复制 poetry 相关文件
COPY pyproject.toml poetry.lock ./

# 使用清华镜像源安装依赖
RUN poetry config repo.pypi https://pypi.tuna.tsinghua.edu.cn/simple && \
    poetry install --only main --no-interaction --no-ansi --no-root

# 复制应用代码
COPY app/ ./app/

# 设置 PYTHONPATH
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["poetry", "run", "python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]