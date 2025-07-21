# PCB Detector

A Streamlit app for detecting defects in PCB images using YOLO and computer vision.

## Install dependencies

```bash
pip install -r requirements.txt
```

## Run locally

```bash
streamlit run main.py
```

## Run with Docker

Build the image:
```bash
docker build -t pcb-detector .
```

Run the container:
```bash
docker run -p 8501:8501 -v $(pwd)/best.pt:/app/best.pt:ro pcb-detector
```

## Run with Docker Compose

```bash
docker-compose up --build
```

Then open [http://localhost:8501](http://localhost:8501) in your browser.