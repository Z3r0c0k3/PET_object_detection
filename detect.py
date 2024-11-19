import torch
import cv2
import numpy as np
from models.experimental import attempt_load
from utils.general import non_max_suppression, scale_coords
from utils.plots import plot_one_box
from utils.torch_utils import select_device
from utils.datasets import letterbox

class PETBottleDetector:
    def __init__(self, weights_path):
        # 디바이스 설정
        self.device = select_device('cpu')
        # 모델 로드
        self.model = attempt_load(weights_path, device=self.device)
        # 타겟 라벨 초기화
        self.target_labels = {
            'PET_transparent': False,
            'PET_color': False
        }

    def detect_pet_bottles(self, frame):
        # 이미지 전처리
        img = letterbox(frame, 640, stride=32)[0]
        img = img[:, :, ::-1].transpose(2, 0, 1)  # BGR to RGB
        img = np.ascontiguousarray(img)
        img = torch.from_numpy(img).to(self.device)
        img = img.float()
        img /= 255.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        # 추론
        pred = self.model(img, augment=False)[0]
        pred = non_max_suppression(pred, 0.25, 0.45)

        # 결과 처리
        confidence_scores = {
            'PET_transparent': 0.0,
            'PET_color': 0.0
        }
        
        # 모든 라벨을 False로 초기화
        self.target_labels = {
            'PET_transparent': False,
            'PET_color': False
        }

        # 감지된 객체 처리
        if pred[0] is not None and len(pred[0]):
            det = pred[0]
            det[:, :4] = scale_coords(img.shape[2:], det[:, :4], frame.shape).round()
            
            for *xyxy, conf, cls in det:
                label = self.model.names[int(cls)]
                if label in self.target_labels:
                    # 현재 객체의 신뢰도 저장
                    current_conf = conf.item()
                    if current_conf > confidence_scores[label]:
                        confidence_scores[label] = current_conf
                        # 바운딩 박스 그리기
                        plot_one_box(
                            xyxy, 
                            frame, 
                            label=f'{label} {current_conf:.2f}', 
                            color=(0, 255, 0)
                        )

        # 가장 높은 신뢰도를 가진 라벨만 True로 설정
        if any(confidence_scores.values()):
            max_label = max(confidence_scores.items(), key=lambda x: x[1])[0]
            if confidence_scores[max_label] > 0:
                self.target_labels[max_label] = True

        return frame, self.target_labels, confidence_scores

def main():
    # 모델 초기화
    weights_path = './last.pt'  # 학습된 가중치 파일 경로
    detector = PETBottleDetector(weights_path)
    
    # 카메라 설정
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # 객체 감지 실행
        frame, target_labels, confidence_scores = detector.detect_pet_bottles(frame)

        # 결과 텍스트 생성
        result_text = "Detection Results: "
        for label, detected in target_labels.items():
            result_text += f"{label}: {detected} ({confidence_scores[label]:.2f}) | "
        
        # 결과 화면에 표시
        cv2.putText(
            frame, 
            result_text, 
            (10, 30), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.6, 
            (0, 255, 0), 
            2
        )
        cv2.imshow('PET Bottle Detection', frame)

        # 'q' 키를 누르면 종료
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == '__main__':
    main()