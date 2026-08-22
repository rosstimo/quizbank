FROM python:3.12-slim-bookworm

ARG PANDOC_VERSION=3.10.1
ARG TYPST_VERSION=0.15.1
ARG TARGETARCH

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        fonts-libertinus \
        fonts-noto-core \
        texlive-fonts-recommended \
        texlive-latex-recommended \
        texlive-xetex \
        xz-utils \
    && case "${TARGETARCH:-amd64}" in \
         amd64) pandoc_arch=amd64; typst_arch=x86_64 ;; \
         arm64) pandoc_arch=arm64; typst_arch=aarch64 ;; \
         *) echo "Unsupported architecture: ${TARGETARCH}" >&2; exit 1 ;; \
       esac \
    && curl -fsSL \
       "https://github.com/jgm/pandoc/releases/download/${PANDOC_VERSION}/pandoc-${PANDOC_VERSION}-linux-${pandoc_arch}.tar.gz" \
       -o /tmp/pandoc.tar.gz \
    && mkdir /tmp/pandoc \
    && tar -xzf /tmp/pandoc.tar.gz -C /tmp/pandoc --strip-components=1 --no-same-owner \
    && install -m 0755 /tmp/pandoc/bin/pandoc /usr/local/bin/pandoc \
    && curl -fsSL \
       "https://github.com/typst/typst/releases/download/v${TYPST_VERSION}/typst-${typst_arch}-unknown-linux-musl.tar.xz" \
       -o /tmp/typst.tar.xz \
    && mkdir /tmp/typst \
    && tar -xJf /tmp/typst.tar.xz -C /tmp/typst --strip-components=1 --no-same-owner \
    && install -m 0755 /tmp/typst/typst /usr/local/bin/typst \
    && pandoc --version \
    && typst --version \
    && rm -rf /var/lib/apt/lists/* /tmp/pandoc /tmp/pandoc.tar.gz /tmp/typst /tmp/typst.tar.xz

WORKDIR /workspace
COPY . /opt/quizbank
RUN python -m pip install --no-cache-dir '/opt/quizbank[dev]'

ENV HOME=/tmp/quizbank-home
ENTRYPOINT ["quizbank"]
