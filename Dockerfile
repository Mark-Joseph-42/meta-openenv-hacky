FROM python:3.10-slim

# /repo layout:
#   /repo/omnisupport_sim/__init__.py  <- package root
#   /repo/omnisupport_sim/models.py
#   /repo/omnisupport_sim/server/app.py
#
# PYTHONPATH="/repo:/repo/omnisupport_sim" means:
#   from omnisupport_sim.models import ...  -> resolves via /repo
#   from server.mock_db import ...          -> resolves via /repo/omnisupport_sim

WORKDIR /repo

# Install dependencies (layer-cached separately)
COPY omnisupport_sim/server/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the full package
COPY omnisupport_sim/ ./omnisupport_sim/

# Make both the root and the package dir importable
ENV PYTHONPATH="/repo:/repo/omnisupport_sim"

EXPOSE 7860

HEALTHCHECK --interval=30s --timeout=10s \
  CMD python -c "import requests; requests.get('http://localhost:7860/health')" || exit 1

CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "7860"]
