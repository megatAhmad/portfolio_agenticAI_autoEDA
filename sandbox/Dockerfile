FROM python:3.11-slim

# Security: run as non-root user
RUN useradd -m -u 1000 sandbox && \
    mkdir -p /workspace /tmp && \
    chown -R sandbox:sandbox /workspace /tmp

# Install only whitelisted packages
RUN pip install --no-cache-dir \
    pandas==2.1.4 \
    numpy==1.26.3 \
    scipy==1.11.4 \
    scikit-learn==1.3.2 \
    plotly==5.18.0 \
    matplotlib==3.8.2 \
    openpyxl==3.1.2

# Security: remove pip and other tools
RUN pip uninstall -y pip setuptools wheel && \
    rm -rf /usr/local/bin/pip* /usr/local/bin/easy_install*

# Switch to non-root user
USER sandbox
WORKDIR /workspace

# Set restrictive environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HOME=/workspace

# Default command
CMD ["python3", "/workspace/run.py"]
