# 使用 Python 3.12 官方镜像
FROM python:3.12-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖和 Poetry
RUN sed -i 's|http://deb.debian.org/debian|https://mirrors.aliyun.com/debian|g' /etc/apt/sources.list.d/debian.sources \
    && apt-get -o Acquire::Retries=5 update \
    && apt-get -o Acquire::Retries=5 install -y --no-install-recommends \
    gcc \
    libmariadb-dev-compat \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && pip install poetry

# 复制 poetry 相关文件
COPY pyproject.toml poetry.lock ./

# 安装依赖。安装源（清华镜像）在 pyproject.toml 的 [[tool.poetry.source]] 中声明：
# Poetry 2.x 下 `poetry config repositories.*` 仅用于发布，对安装源无效。
RUN poetry install --only main --no-interaction --no-ansi --no-root

# 复制应用代码
COPY app/ ./app/

# 设置 PYTHONPATH
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["poetry", "run", "python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
