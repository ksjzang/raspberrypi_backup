from picamera2 import Picamera2
import cv2
import numpy as np
import time

def decision(x):
    if 80 < x <= 240:
        return 'f'
    elif x <= 80:
        return 'l'
    elif 240<x:
        return 'r'
    else:
        return 'b'

def make_black(image, threshold=140):
    gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # 반전 처리: 밝은 영역(노란색 선)은 검은색, 나머지는 흰색
    inverted_gray = cv2.bitwise_not(gray_image)
    black_image = cv2.inRange(inverted_gray, threshold, 255)
    return black_image, gray_image

def find_contour_center_and_draw(gray, original_image):
    crop_gray = gray[:, :]
    blur = cv2.GaussianBlur(crop_gray, (5, 5), 0)
    _, thresh = cv2.threshold(blur, 123, 255, cv2.THRESH_BINARY_INV)

    # 노이즈 제거
    mask = cv2.erode(thresh, None, iterations=2)
    mask = cv2.dilate(mask, None, iterations=2)

    # 윤곽선 검출
    contours, _ = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if contours:
        c = max(contours, key=cv2.contourArea)  # 가장 큰 윤곽선 선택
        M = cv2.moments(c)
        if M['m00'] != 0:
            cx = int(M['m10'] / M['m00'])
            cy = int(M['m01'] / M['m00'])

            # 윤곽선 그리기 (테두리)
            cv2.polylines(original_image, [c], isClosed=True, color=(0, 255, 0), thickness=2)

            # 중심점 시각화
            cv2.circle(original_image, (cx, cy), 5, (255, 0, 0), -1)

            print(f"Contour center: {cx}")
            return cx
    return None


# Picamera2 초기화
picam2 = Picamera2()
config = picam2.create_preview_configuration(main={"size": (320, 240)})
picam2.configure(config)
picam2.start()

time.sleep(0.05)  # 카메라 초기화 대기

try:
    while True:
        # 프레임 캡처
        frame = picam2.capture_array()

        # 컬러 공간 변환 (RGB에서 BGR로 변환)
        frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # 화면 Flip (상하좌우 반전)
        frame_bgr_flipped = cv2.flip(frame_bgr, -1)

        # 그레이스케일 및 임계값 적용
        black_image, gray = make_black(frame_bgr_flipped)

        # 중심 결정 및 방향 결정 (컬러 이미지에 윤곽선 표시)
        cx = find_contour_center_and_draw(black_image, frame_bgr_flipped)
        if cx is not None:
            key = decision(cx)
            print(f"Decision: {key}")

        # 디버깅용 컬러 화면 출력
        cv2.imshow('Processed Frame', frame_bgr_flipped)

        # 종료 조건
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
finally:
    picam2.stop()
    cv2.destroyAllWindows()
