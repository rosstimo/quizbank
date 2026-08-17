FROM python:3.12-slim-bookworm

ARG TYPST_VERSION=0.13.1
ARG TARGETARCH

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        fonts-noto-core \
        pandoc \
        texlive-fonts-recommended \
        texlive-latex-recommended \
        texlive-xetex \
        xz-utils \
    && case "${TARGETARCH:-amd64}" in \
         amd64) typst_arch=x86_64 ;; \
         arm64) typst_arch=aarch64 ;; \
         *) echo "Unsupported architecture: ${TARGETARCH}" >&2; exit 1 ;; \
       esac \
    && curl -fsSL \
       "https://github.com/typst/typst/releases/download/v${TYPST_VERSION}/typst-${typst_arch}-unknown-linux-musl.tar.xz" \
       -o /tmp/typst.tar.xz \
    && mkdir /tmp/typst \
    && tar -xJf /tmp/typst.tar.xz -C /tmp/typst --strip-components=1 --no-same-owner \
    && install -m 0755 /tmp/typst/typst /usr/local/bin/typst \
    && rm -rf /var/lib/apt/lists/* /tmp/typst /tmp/typst.tar.xz

WORKDIR /workspace
COPY . /opt/quizbank
RUN python -m pip install --no-cache-dir '/opt/quizbank[dev]'

ENV HOME=/tmp/quizbank-home
ENTRYPOINT ["quizbank"]
