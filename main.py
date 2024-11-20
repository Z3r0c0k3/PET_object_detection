import os
import sys
import torch
from pathlib import Path

# YOLOR 경로 설정
FILE = Path("../yolor").resolve()
ROOT = FILE.parents[0]  # YOLO 레포지토리 루트
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # 경로 추가

from models.experimental import attempt_load
from utils.datasets import LoadStreams
from utils.general import check_img_size, non_max_suppression, scale_coords
from utils.plots import Annotator, colors
from utils.torch_utils import select_device, time_sync

# 모델 파일 및 설정
WEIGHTS = "./last.pt"  # YOLOR 가중치 파일 경로
IMG_SIZE = 640
CONF_THRES = 0.25
IOU_THRES = 0.45
DEVICE = ""
CLASSES = ["PET_transparent", "PET_color"]

# YOLOR 모델 로드
device = select_device(DEVICE)
model = attempt_load(WEIGHTS, map_location=device)
stride = int(model.stride.max())  # 모델 stride
img_size = check_img_size(IMG_SIZE, s=stride)

# 데이터 스트림(웹캠)
dataset = LoadStreams(0, img_size=img_size, stride=stride, auto=True)  # 0: 웹캠

# 탐지 시작
for path, img, im0s, vid_cap, s in dataset:
    img = torch.from_numpy(img).to(device)
    img = img.float() / 255.0  # 0~255 정규화
    if img.ndimension() == 3:
        img = img.unsqueeze(0)

    # 추론
    pred = model(img, augment=False)[0]
    pred = non_max_suppression(pred, CONF_THRES, IOU_THRES, classes=None, agnostic=False)

    # 탐지 결과 처리
    for i, det in enumerate(pred):
        im0 = im0s[i].copy()
        annotator = Annotator(im0, line_width=2, example=str(CLASSES))

        if len(det):
            det[:, :4] = scale_coords(img.shape[2:], det[:, :4], im0.shape).round()
            max_score = 0
            best_label = None

            for *xyxy, conf, cls in reversed(det):
                label = f"{CLASSES[int(cls)]}: {conf:.2f}"
                if CLASSES[int(cls)] in CLASSES:  # 관심 있는 클래스만 확인
                    if conf > max_score:
                        max_score = conf
                        best_label = CLASSES[int(cls)]

                    annotator.box_label(xyxy, label, color=colors(int(cls)))

            if best_label:
                print(f"Detected {best_label} with confidence {max_score:.2f}")
            else:
                print("No relevant objects detected.")

        cv2.imshow("YOLOR Detection", im0)
        if cv2.waitKey(1) & 0xFF == ord("q"):  # 'q' 키로 종료
            break
