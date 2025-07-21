import io
from typing import Tuple, List, Dict, Any
from ultralytics import YOLO
from PIL import Image, ImageDraw, ImageFont
import numpy as np

model = YOLO('app/utils/best.pt')

def detect_and_annotate(image_file: io.BytesIO) -> Tuple[List[Dict[str, Any]], io.BytesIO]:
    pil_img = Image.open(image_file).convert("RGB")
    img_np = np.array(pil_img)
    results = model.predict(source=img_np, save=False, verbose=False)
    det = results[0]

    detections = []
    draw = ImageDraw.Draw(pil_img)
    font = ImageFont.load_default()
    if det.boxes is not None:
        for box in det.boxes:
            x1, y1, x2, y2 = box.xyxy[0].tolist()
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            cls_name = model.names[cls_id]
            label = f"{cls_name} {conf:.2f}"

            detections.append({
                "class": cls_name,
                "confidence": conf,
                "box": [x1, y1, x2, y2]
            })

            draw.rectangle([x1, y1, x2, y2], outline="red", width=2)
            bbox = draw.textbbox((x1, y1), label, font=font)
            text_w = bbox[2] - bbox[0]
            text_h = bbox[3] - bbox[1]
            draw.rectangle([x1, y1 - text_h, x1 + text_w, y1], fill="red")
            draw.text((x1, y1 - text_h), label, fill="white", font=font)

    buf = io.BytesIO()
    pil_img.save(buf, format="PNG")
    buf.seek(0)
    return detections, buf