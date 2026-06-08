FROM ghcr.io/prefix-dev/pixi:latest

WORKDIR /app

COPY pixi.toml pixi.lock pyproject.toml ./
COPY src src

RUN pixi install --locked

EXPOSE 8086

CMD ["pixi", "run", "start"]
