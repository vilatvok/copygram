FROM python:3.12

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONBUFFERED=1
ENV PATH="/root/.local/bin:${PATH}"

RUN curl -sSL https://install.python-poetry.org | python3 -
COPY pyproject.toml .
RUN poetry install --no-root

COPY . .

ENTRYPOINT ["poetry", "run"]
