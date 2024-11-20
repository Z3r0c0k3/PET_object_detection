import cv2
import torch
from PIL import Image
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator

# YOLO 모델 불러오기
model = YOLO("./last.pt")

colors = [(255, 0, 0), (0, 255, 0)]

def process_frame(frame):
    results = model.track(source=frame, show=False, stream=False, save=False, save_txt=False)
    label_status = {"PET_transparent": False, "PET_color": False}
    max_score = 0
    best_label = None
    annotator = Annotator(frame)

    for result in results:
        detections = result.boxes.data

        for detection in detections:
            x1, y1, x2, y2, _, score, class_id = detection
            class_name = model.names[int(class_id)]

            # 감지된 클래스가 'PET_transparent' 또는 'PET_color'일 때 처리
            if class_name in label_status and score > 0.7:
                if score > max_score:
                    max_score = score
                    best_label = class_name

                annotator.box_label(
                    (x1, y1, x2, y2),
                    f"{class_name}: {score:.2f}",
                    color=colors[int(class_id) % len(colors)],
                )

    # 스코어가 가장 높은 클래스의 값을 True로 설정
    if best_label:
        label_status[best_label] = True
        print(f"{best_label} detected with highest score: {max_score:.2f}")
    else:
        print("No relevant objects detected")

    frame = annotator.result()
    return frame, label_status

# 웹캠 설정 (기본 카메라: 인덱스 0)
cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    frame, label_status = process_frame(frame)
    cv2.imshow('YOLO Detection', frame)

    # 'q' 키를 누르면 종료
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
