import cv2
import numpy as np
from paddleocr import PPStructure
import fitz

table_engine = PPStructure(show_log=True, layout=True)

print("Models downloaded successfully!")
