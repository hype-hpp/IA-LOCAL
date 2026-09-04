# Fase 04 - 4.1: Imagem do sandbox de execução de código.
#
# Base e pacotes definidos na Decision 020 do projeto (02_ARCHITECTURE.md):
# imagem python:3.11-slim + numpy, pandas, requests, beautifulsoup4,
# matplotlib, scipy pré-instalados, para não precisar de `pip install`
# (proibido sem autorização prévia) a cada execução de código gerado.

FROM python:3.11-slim

RUN pip install --no-cache-dir \
    numpy \
    pandas \
    requests \
    beautifulsoup4 \
    matplotlib \
    scipy

WORKDIR /sandbox

# Sem ENTRYPOINT/CMD fixo: o comando real (python script.py) é passado pelo
# executor.py no momento do `docker run`, junto com as flags de isolamento
# (--network none, --memory, --cpus, --cap-drop, etc.).
