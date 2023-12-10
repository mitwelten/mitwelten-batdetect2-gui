FROM python:3.10.13
WORKDIR /batdetect2_gui
COPY ./batdetect2_gui /batdetect2_gui
COPY ./requirements.txt /batdetect2_gui/requirements.txt
COPY ./credentials.py /batdetect2_gui/credentials.py
RUN pip install -U pip
RUN pip install --no-cache-dir -r /batdetect2_gui/requirements.txt
CMD ["gunicorn", "application:application", "--bind", "0.0.0.0"]
