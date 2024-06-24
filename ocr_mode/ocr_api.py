import time
from PIL import Image
# import pytesseract
from PIL import ImageGrab
from aip import AipOcr
from paddleocr import PaddleOCR, draw_ocr
import cv2
from dotenv import load_dotenv
import os

load_dotenv()

# Baidu OCR API
APP_ID = os.getenv('APP_ID')
API_KEY = os.getenv('API_KEY')
SECRET_KEY = os.getenv('SECRET_KEY')

client = AipOcr(APP_ID, API_KEY, SECRET_KEY)

ocr_ch = PaddleOCR(use_angle_cls = False, lang="ch")
ocr_en = PaddleOCR(use_angle_cls = False, lang="en")

print("OCR API initialized")

def ocr_text_paddle(image_path = "./img/screenshot.png", lang="ch"):
    if lang == "ch" or lang == "zh":
        result = ocr_ch.ocr(image_path, cls = False)
    elif lang == "en":
        result = ocr_en.ocr(image_path, cls = False)
    text = ''
    for idx in range(len(result)):
        res = result[idx]
        if res is not None:
            for line in res:
                if (line is not None):
                    text += '\n' + line[1][0]
    
    return text

def ocr_text_api(image_path):
    with open(image_path, 'rb') as image_file:
        image = image_file.read()
    
    result = client.basicGeneral(image)
    
    words_result = result.get('words_result', [])
    text = '\n'.join([word['words'] for word in words_result])
    
    return text

if __name__ == '__main__':
    image_path = './img/screenshot.png' 
    text = ocr_text_paddle(image_path, lang = "ch")
    print(text)
    
    
# [[[[[244.0, 3.0], [344.0, 3.0], [344.0, 27.0], [244.0, 27.0]], ('钟表小子', 0.9973875880241394)], [[[284.0, 33.0], [307.0, 33.0], [307.0, 41.0], [284.0, 41.0]], ('""', 0.5046016573905945)], [[[146.0, 47.0], [435.0, 47.0], [435.0, 69.0], [146.0, 69.0]], ('哦，那等你休息好了，我们再出发？', 0.9944297075271606)]]]

