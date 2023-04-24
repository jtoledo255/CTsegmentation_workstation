import numpy as np
import cv2 as cv
import os
import pydicom as dicom
from PIL import Image, ImageTk, ImageFilter
import matplotlib.pyplot as plt
from skimage.draw import polygon2mask

drawing = False # true if mouse is pressed
pt1_x , pt1_y = None , None
point_matrix = []
# mouse callback function
def line_drawing(event,x,y,flags,param):
    global pt1_x,pt1_y,drawing

    if event==cv.EVENT_LBUTTONDOWN:
        drawing=True
        pt1_x,pt1_y=x,y
        points = [pt1_x,pt1_y]
        point_matrix.append(points)
    elif event==cv.EVENT_MOUSEMOVE:
        if drawing==True:
            cv.line(img,(pt1_x,pt1_y),(x,y),color=(255,255,255),thickness=1)
            pt1_x,pt1_y=x,y
            points = [pt1_x,pt1_y]
            point_matrix.append(points)
    elif event==cv.EVENT_LBUTTONUP:
        drawing=False
        cv.line(img,(pt1_x,pt1_y),(x,y),color=(255,255,255),thickness=1)


def transform_to_hu(medical_image, image):
    intercept = medical_image.RescaleIntercept
    slope = medical_image.RescaleSlope
    hu_image = image*slope+intercept
    return hu_image
#windowing function
def window_image(image, window_center, window_width):
    img_min = window_center - window_width//2
    img_max = window_center + window_width//2
    window_image = image.copy()
    window_image[window_image < img_min] = img_min
    window_image[window_image > img_max] = img_max
    return window_image

window_scale = 80
level_scale = 40
casePath = '/nfs/kitbag/data1/jdfuhrman/PBI_Project/PBI_Images/Corr-001/study_20151104_815956941181f5c7_CT-ANG-HEAD-AND-NECK-WWO/CT301_AXL_RECON_f5249939/'
imList = os.listdir(os.path.join(casePath))
imList.sort()
ds = dicom.dcmread(casePath+'/'+imList[0])
imStack = np.zeros((len(imList), 512, 512))
c = np.zeros((len(imList), 512, 512, 16))
chosen_image = 1

for i in range(len(imList)):
    ds = dicom.dcmread(casePath+'/'+imList[i])
    pixel_array = ds.pixel_array
    hu_image = transform_to_hu(ds,pixel_array)
    windowed_image = window_image(hu_image,level_scale,window_scale)
    windowed_image = 255*windowed_image/windowed_image.max()
    imStack[i,:,:] = windowed_image
currentSlice = 15
currentIm = Image.fromarray(imStack[currentSlice,:,:]).convert('L')
img = np.array(currentIm)
cv.namedWindow('test draw')
cv.setMouseCallback('test draw',line_drawing)

while(1):
    cv.imshow('test draw',img)
    if cv.waitKey(1) & 0xFF == 27:
        break
cv.destroyAllWindows()

point_matrix.append(point_matrix[0])
mask = polygon2mask(img.shape, point_matrix)
plt.imshow(mask)
plt.show()
print(point_matrix)
