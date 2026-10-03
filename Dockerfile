FROM python:3.13-slim
WORKDIR /app
COPY schema_migration_workbench ./schema_migration_workbench
RUN useradd --uid 10001 --create-home runner
USER runner
WORKDIR /workspace
ENV PYTHONPATH=/app PYTHONUNBUFFERED=1
ENTRYPOINT ["python", "-m", "schema_migration_workbench"]
CMD ["--help"]
