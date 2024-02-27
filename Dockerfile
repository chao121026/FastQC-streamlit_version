FROM python:3.8

# Install system dependencies
RUN apt-get update && apt-get install -y fastqc

# Set up your Streamlit app
WORKDIR /app
COPY requirements.txt /app
RUN pip install -r requirements.txt
COPY . /app

# Run Streamlit app
CMD ["streamlit", "run", "FastQC_streamlit.py"]

