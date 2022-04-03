import cv2
import numpy as np

# OpenCV BGR
COLOR_CV_WHITE = (255, 255, 255)
COLOR_CV_GREEN = (75, 168, 14)
COLOR_CV_RED = (36, 31, 236)
COLOR_CV_BLUE = (210, 99, 18)
COLOR_CV_GRAY = (134, 134, 134)

# TkInter RGB
COLOR_TK_YELLOW = '#FFE61A' # (100, 90, 10)
COLOR_TK_DEFAULT = '#F0F0F0' # 'SystemWindow'
COLOR_TK_WHITE = '#FFFFFF' # 'white'

FONT_TK_BOLD = ('arial', 12, 'bold')
FONT_TK_NORMAL = ('arial', 12, 'normal')

def DrawRectangle(image: np.ndarray, point1: tuple, point2: tuple, color: tuple):
    cv2.rectangle(image, point1, point2, color, 3)
    
def DrawText(image: np.ndarray, text: str, point: tuple, color: tuple):
    cv2.putText(image, text, point, cv2.FONT_HERSHEY_DUPLEX, 0.78, color, 2)