FROM tensorzero/gateway:latest
COPY tensorzero/tensorzero.toml /app/config/tensorzero.toml
COPY tensorzero/templates/ /app/config/templates/
CMD ["--config-file", "/app/config/tensorzero.toml"]
