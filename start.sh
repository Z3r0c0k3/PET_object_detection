#!/bin/bash
# setup.sh - 초기 설치 스크립트

# 로그 파일 설정
LOG_FILE="/home/pi/pet_detection_setup.log"
exec 1> >(tee -a "$LOG_FILE") 2>&1

echo "=== PET 병 감지 시스템 설치 스크립트 시작 ===" 
echo "시작 시간: $(date)"

# 에러 처리 함수
handle_error() {
    echo "에러 발생: $1"
    echo "설치 중단됨"
    exit 1
}

# root 권한 확인
if [ "$EUID" -ne 0 ]; then 
    echo "이 스크립트는 root 권한으로 실행해야 합니다."
    echo "다음 명령어로 실행하세요: sudo bash setup.sh"
    exit 1
fi

# GitHub 저장소 설정
GITHUB_REPO="Z3r0c0k3/PET_object_detection"
REPO_DIR="/home/pi/pet_detection"

# 1. 시스템 업데이트 및 기본 패키지 설치
echo "1. 시스템 업데이트 및 기본 패키지 설치 중..."
apt-get update && apt-get upgrade -y || handle_error "시스템 업데이트 실패"
apt-get install -y python3-pip python3-opencv v4l-utils git || handle_error "기본 패키지 설치 실패"

# OpenCV 최적화 라이브러리 설치
echo "2. OpenCV 최적화 라이브러리 설치 중..."
apt-get install -y \
    libjpeg62-turbo-dev \
    libtiff5-dev \
    libpng-dev \
    libavcodec-dev \
    libavformat-dev \
    libswscale-dev \
    libv4l-dev \
    libxvidcore-dev \
    libx264-dev || handle_error "OpenCV 라이브러리 설치 실패"

# 2. Python 패키지 설치
echo "3. Python 패키지 설치 중..."
sudo -u pi pip3 install torch torchvision || handle_error "PyTorch 설치 실패"
sudo -u pi pip3 install opencv-python numpy Pillow || handle_error "Python 패키지 설치 실패"

# 3. YOLOv5 설치
echo "4. YOLOv5 설치 중..."
cd /home/pi || handle_error "홈 디렉토리 접근 실패"
sudo -u pi git clone https://github.com/ultralytics/yolov5 || handle_error "YOLOv5 클론 실패"
cd yolov5 || handle_error "YOLOv5 디렉토리 접근 실패"
sudo -u pi pip3 install -r requirements.txt || handle_error "YOLOv5 요구사항 설치 실패"

# 4. GitHub 프로젝트 클론
echo "5. 프로젝트 저장소 클론 중..."
cd /home/pi || handle_error "홈 디렉토리 접근 실패"
if [ -d "$REPO_DIR" ]; then
    echo "기존 저장소 삭제 중..."
    rm -rf "$REPO_DIR"
fi
sudo -u pi git clone "https://github.com/$GITHUB_REPO" "$REPO_DIR" || handle_error "GitHub 저장소 클론 실패"

# 5. 스왑 파일 설정
echo "6. 스왑 파일 설정 중..."
dphys-swapfile swapoff
sed -i 's/CONF_SWAPSIZE=.*/CONF_SWAPSIZE=2048/g' /etc/dphys-swapfile || handle_error "스왑 파일 설정 실패"
dphys-swapfile setup
dphys-swapfile swapon

# 6. 비디오 그룹에 사용자 추가
echo "7. 사용자 권한 설정 중..."
usermod -a -G video pi || handle_error "비디오 그룹 권한 설정 실패"

# 7. 실행 스크립트 생성
echo "8. 실행 스크립트 생성 중..."
cat > /home/pi/run_detection.sh << 'EOL'
#!/bin/bash

# 로그 파일 설정
LOG_FILE="/home/pi/pet_detection_run.log"
exec 1> >(tee -a "$LOG_FILE") 2>&1

echo "=== PET 병 감지 시스템 실행 ===" 
echo "시작 시간: $(date)"

# GitHub 저장소 설정
REPO_DIR="/home/pi/pet_detection"
cd "$REPO_DIR" || exit 1

# GitHub에서 최신 코드 가져오기
echo "최신 코드 가져오기 중..."
git fetch origin
git reset --hard origin/main

# Python 가상환경 활성화 (필요한 경우)
# source venv/bin/activate

# 메인 스크립트 실행
echo "감지 프로그램 실행 중..."
python3 main.py

EOL

# 실행 스크립트 권한 설정
chmod +x /home/pi/run_detection.sh
chown pi:pi /home/pi/run_detection.sh

# 8. 서비스 파일 생성
echo "9. 시스템 서비스 설정 중..."
cat > /etc/systemd/system/pet-detection.service << EOL
[Unit]
Description=PET Bottle Detection Service
After=multi-user.target

[Service]
User=pi
WorkingDirectory=/home/pi/pet_detection
ExecStart=/home/pi/run_detection.sh
Restart=always

[Install]
WantedBy=multi-user.target
EOL

# 서비스 활성화
systemctl enable pet-detection || handle_error "서비스 활성화 실패"

# 설치 완료 확인
echo "10. 설치 상태 확인 중..."
echo "Python 버전:"
python3 --version
echo "Pip 버전:"
pip3 --version
echo "OpenCV 버전:"
python3 -c "import cv2; print('OpenCV 버전:', cv2.__version__)"
echo "웹캠 장치 확인:"
ls -l /dev/video*
echo "스왑 상태:"
free -h

echo "=== 설치 완료 ==="
echo "완료 시간: $(date)"
echo "로그 파일 위치: $LOG_FILE"

echo "
설치 후 사용방법:
1. 수동으로 실행: /home/pi/run_detection.sh
2. 서비스 시작: sudo systemctl start pet-detection
3. 서비스 상태 확인: sudo systemctl status pet-detection
4. 실행 로그 확인: tail -f /home/pi/pet_detection_run.log
5. 서비스 로그 확인: sudo journalctl -u pet-detection
"