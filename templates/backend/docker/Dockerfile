# ---------- Stage 1: builder ----------
# 锁小版本号（pin minor + patch），生产审计时知道用了哪个具体 build
FROM python:3.11.9-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 一起 copy pyproject + readme：hatchling 构建 wheel 时会读取 readme，缺文件直接报错
# 这两个文件基本不变，layer cache 仍然有效（app 代码在第二阶段 COPY）
COPY pyproject.toml 后端说明.md ./
RUN pip install --upgrade pip && \
    pip install --prefix=/install .

# ---------- Stage 2: runtime ----------
# 用 debian-slim 而非 alpine：避免 asyncpg / bcrypt / cryptography musl 兼容坑
FROM python:3.11.9-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# 非 root 用户运行（生产硬要求）
RUN groupadd --system app && useradd --system --create-home --gid app app

WORKDIR /app

# 从 builder 阶段拷 wheel / site-packages
COPY --from=builder /install /usr/local
COPY --chown=app:app . .

# 生产用 gunicorn + uvicorn worker（已通过 pyproject 依赖装好）

USER app

EXPOSE 8000

# readiness 探针（K8s readiness 用 /readyz 含 DB ping）
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
    # slim 镜像无 wget，用 python urllib 替代
    CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/readyz', timeout=3).status == 200 else 1)"

# 显式 gunicorn 配置（不依赖 shell 拼接）
CMD ["gunicorn", "app.main:app", \
     "-w", "4", \
     "-k", "uvicorn.workers.UvicornWorker", \
     "-b", "0.0.0.0:8000", \
     "--timeout", "60", \
     "--graceful-timeout", "30", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
