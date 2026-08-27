FROM ubuntu:22.04

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update -qq && apt-get install -y --no-install-recommends \
    dbus-x11 \
    gir1.2-appindicator3-0.1 \
    gir1.2-gdkpixbuf-2.0 \
    gir1.2-glib-2.0 \
    gir1.2-gstreamer-1.0 \
    gir1.2-gtk-3.0 \
    gir1.2-gtk-3.0 \
    gir1.2-notify-0.7 \
    gir1.2-playerctl-2.0 \
    gir1.2-unity-5.0 \
    curl \
    git \
    gstreamer1.0-plugins-base \
    notification-daemon \
    python3-dbus \
    python3-dbusmock \
    python3-gi \
    python3-pip \
    python3-pytest \
    python3-pytest-cov \
    python3-pytest-flake8 \
    python3-pytest-mock \
    python3-venusian \
    python3-wrapt \
    python3-xdg \
    python3-yapsy \
    xvfb \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml uv.lock /tmp/

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

ENV PATH="/root/.local/bin:${PATH}"

RUN cd /tmp && \
    uv venv --system-site-packages --python python3 .venv && \
    uv sync --frozen --group dev --no-install-project

ENV PATH="/tmp/.venv/bin:${PATH}"

WORKDIR /code

RUN sh -c "$(curl --location https://taskfile.dev/install.sh)" -- -d -b /usr/local/bin v3.48.0

ENTRYPOINT ["task"]

CMD ["test"]
