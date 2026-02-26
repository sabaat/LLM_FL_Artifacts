# Artifact evaluation image: Python + dependencies for fault-localization pipeline.
# Ollama is NOT installed in the image; run Ollama on the host and connect from the container
# (e.g. --network host on Linux, or OLLAMA_HOST=http://host.docker.internal:11434 on Mac/Windows).

FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    bash \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /artifact

# Install Python dependencies used by test_llm, plot_artifact_results, etc.
RUN pip install --no-cache-dir \
    ollama \
    pydantic \
    autopep8 \
    matplotlib

# Copy the whole artifact directory (scripts, datasets, optional pre-generated spm_*).
# When you run the container, mount over this with -v so results land on the host.
COPY . /artifact/

RUN chmod +x /artifact/run_artifact.sh

# Default: run quick eval (eval-only) with llama3.2:3b. Override when running:
#   docker run ... artifact-eval ./run_artifact.sh --eval-only llama3.2:3b
#   docker run ... artifact-eval ./run_artifact.sh llama3.2:3b 5
CMD ["./run_artifact.sh", "--eval-only", "llama3.2:3b"]
