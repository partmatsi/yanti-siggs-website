FROM python:3.9-slim 
 
WORKDIR /app 
 
COPY requirements.txt . 
RUN pip install --upgrade pip && pip install -r requirements.txt 
 
COPY . . 
 
RUN mkdir -p music_uploads gallery_uploads header_photos 
 
EXPOSE 8501 
CMD ["streamlit", "run", "network_control_center_streamlit.py", "--server.port=8501", "--server.address=0.0.0.0"] 
