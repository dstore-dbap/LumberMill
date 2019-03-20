FROM pypy:2-5

WORKDIR /opt/LumberMill

COPY requirements/requirements.txt ./
COPY requirements/requirements-pypy.txt ./
COPY requirements/requirements-test.txt ./
RUN pip install --no-cache-dir --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt \
 && pip install --no-cache-dir -r requirements-pypy.txt \
 && pip install --no-cache-dir -r requirements-test.txt \
 && rm -f /opt/LumberMill/requirements.txt \
 && rm -f /opt/LumberMill/requirements-pypy.txt \
 && rm -f /opt/LumberMill/requirements-test.txt
