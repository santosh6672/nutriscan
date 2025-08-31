import cv2
from pyzbar import pyzbar

def scan_barcode(image_path):
    """Scan barcode from image file"""
    image = cv2.imread(image_path)
    barcodes = pyzbar.decode(image)
    
    if barcodes:
        return barcodes[0].data.decode('utf-8')
    return None