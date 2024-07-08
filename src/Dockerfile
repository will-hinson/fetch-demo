FROM python:3.12-alpine

# install all prerequisites
COPY requirements.txt .
RUN pip install -r requirements.txt

# copy our target module to the container
COPY . .

# start the target module
CMD ["python", "-m", "fetch_demo"]
