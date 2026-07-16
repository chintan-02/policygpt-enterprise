FROM python:3.13-slim

ARG APP_UID=10001
ARG APP_GID=10001
ARG EMBEDDING_MODEL_NAME=sentence-transformers/all-MiniLM-L6-v2
ARG EMBEDDING_MODEL_REVISION=1110a243fdf4706b3f48f1d95db1a4f5529b4d41
ARG TORCH_VERSION=2.12.1

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    HF_HOME=/opt/huggingface \
    HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    EMBEDDING_MODEL_NAME=${EMBEDDING_MODEL_NAME}

WORKDIR /app

RUN groupadd --gid "${APP_GID}" policygpt \
    && useradd --uid "${APP_UID}" --gid policygpt --create-home --shell /usr/sbin/nologin policygpt

COPY requirements.txt ./requirements.txt

RUN python -m pip install --upgrade pip \
    && python -m pip install --no-deps --index-url https://download.pytorch.org/whl/cpu "torch==${TORCH_VERSION}" \
    && python -m pip install -r requirements.txt

# Cache the pinned public model in Hugging Face's standard snapshot layout.
# Remote ADD is build-time only; normal application startup is fully offline.
ADD https://huggingface.co/${EMBEDDING_MODEL_NAME}/resolve/${EMBEDDING_MODEL_REVISION}/1_Pooling/config.json /opt/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/${EMBEDDING_MODEL_REVISION}/1_Pooling/config.json
ADD https://huggingface.co/${EMBEDDING_MODEL_NAME}/resolve/${EMBEDDING_MODEL_REVISION}/config.json /opt/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/${EMBEDDING_MODEL_REVISION}/config.json
ADD https://huggingface.co/${EMBEDDING_MODEL_NAME}/resolve/${EMBEDDING_MODEL_REVISION}/config_sentence_transformers.json /opt/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/${EMBEDDING_MODEL_REVISION}/config_sentence_transformers.json
ADD https://huggingface.co/${EMBEDDING_MODEL_NAME}/resolve/${EMBEDDING_MODEL_REVISION}/data_config.json /opt/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/${EMBEDDING_MODEL_REVISION}/data_config.json
ADD https://huggingface.co/${EMBEDDING_MODEL_NAME}/resolve/${EMBEDDING_MODEL_REVISION}/model.safetensors /opt/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/${EMBEDDING_MODEL_REVISION}/model.safetensors
ADD https://huggingface.co/${EMBEDDING_MODEL_NAME}/resolve/${EMBEDDING_MODEL_REVISION}/modules.json /opt/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/${EMBEDDING_MODEL_REVISION}/modules.json
ADD https://huggingface.co/${EMBEDDING_MODEL_NAME}/resolve/${EMBEDDING_MODEL_REVISION}/sentence_bert_config.json /opt/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/${EMBEDDING_MODEL_REVISION}/sentence_bert_config.json
ADD https://huggingface.co/${EMBEDDING_MODEL_NAME}/resolve/${EMBEDDING_MODEL_REVISION}/special_tokens_map.json /opt/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/${EMBEDDING_MODEL_REVISION}/special_tokens_map.json
ADD https://huggingface.co/${EMBEDDING_MODEL_NAME}/resolve/${EMBEDDING_MODEL_REVISION}/tokenizer.json /opt/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/${EMBEDDING_MODEL_REVISION}/tokenizer.json
ADD https://huggingface.co/${EMBEDDING_MODEL_NAME}/resolve/${EMBEDDING_MODEL_REVISION}/tokenizer_config.json /opt/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/${EMBEDDING_MODEL_REVISION}/tokenizer_config.json
ADD https://huggingface.co/${EMBEDDING_MODEL_NAME}/resolve/${EMBEDDING_MODEL_REVISION}/vocab.txt /opt/huggingface/hub/models--sentence-transformers--all-MiniLM-L6-v2/snapshots/${EMBEDDING_MODEL_REVISION}/vocab.txt

RUN mkdir -p "${HF_HOME}/hub/models--sentence-transformers--all-MiniLM-L6-v2/refs" \
    && printf '%s' "${EMBEDDING_MODEL_REVISION}" > "${HF_HOME}/hub/models--sentence-transformers--all-MiniLM-L6-v2/refs/main"

RUN python -c 'import os; from sentence_transformers import SentenceTransformer; model = SentenceTransformer(os.environ["EMBEDDING_MODEL_NAME"]); print(model.get_sentence_embedding_dimension())' \
    && chown -R policygpt:policygpt "${HF_HOME}"

COPY --chown=policygpt:policygpt app ./app
COPY --chown=policygpt:policygpt alembic ./alembic
COPY --chown=policygpt:policygpt alembic.ini ./alembic.ini

RUN mkdir -p /app/data/chroma /app/data/uploads /app/logs /app/eval/results \
    && chown -R policygpt:policygpt /app/data /app/logs /app/eval

USER policygpt

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
