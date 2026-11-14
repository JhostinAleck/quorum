# One image for every service: the monitor, the three agents and the report.
FROM python:3.12-slim

# WITH_LLM=1 also installs the OpenAI-compatible client that agents need in llm mode.
ARG WITH_LLM=0

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_ROOT_USER_ACTION=ignore

# Unprivileged user with a fixed id. /data is where the monitor keeps its SQLite
# store: a named volume mounted there starts with this ownership.
RUN groupadd --system --gid 10001 quorum \
 && useradd --system --uid 10001 --gid quorum --no-create-home --home-dir /nonexistent \
        --shell /usr/sbin/nologin quorum \
 && mkdir /data \
 && chown quorum:quorum /data

WORKDIR /src
COPY pyproject.toml ./
COPY quorum ./quorum
RUN pip install --no-cache-dir . \
 && if [ "$WITH_LLM" = "1" ]; then pip install --no-cache-dir openai; fi

# Leave the source tree so imports resolve to the installed package, then fail
# the build if the wheel did not carry the policy file of some scenario.
WORKDIR /app
RUN python -c "import pathlib, quorum.scenarios as s; \
root = pathlib.Path(s.__file__).parent; \
assert 'site-packages' in root.parts, root; \
names = sorted(d.name for d in root.iterdir() if (d / '__init__.py').is_file()); \
missing = [n for n in names if not (root / n / 'policy.toml').is_file()]; \
assert names and not missing, f'policy.toml missing in {missing or root}'; \
print('policy files:', names)"

USER 10001:10001

# Compose passes the subcommand: monitor, agent or report.
ENTRYPOINT ["python", "-m", "quorum.launch"]
CMD ["--help"]
