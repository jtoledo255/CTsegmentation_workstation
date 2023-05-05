import os
import cv2 as cv
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk, ImageFilter
import pydicom as dicom
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from skimage.draw import polygon2mask
import matplotlib
import ast
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
def find_between( s, first, last ):
    try:
        start = s.index( first ) + len( first )
        end = s.index( last, start )
        return s[start:end]
    except ValueError:
        return ""
def image_stacking(imagelist,casePath,height,width,level_scale,window_scale):
    imStack = np.zeros((len(imagelist), height, width))
    c = np.zeros((len(imagelist), height, width, 16))
    for i in range(len(imagelist)):
            ds = dicom.dcmread(casePath+'/'+imagelist[i])
            pixel_array = ds.pixel_array
            hu_image = transform_to_hu(ds,pixel_array)
            windowed_image = window_image(hu_image,level_scale,window_scale)
            windowed_image = 255*windowed_image/windowed_image.max()
            imStack[i,:,:] = windowed_image

    return imStack,c

image_path = '/nfs/kitbag/data1/jdfuhrman/PBI_Project/PBI_Images/'
mask_directory = '/nfs/kitbag/data1/jdfuhrman/PBI_Project/CTsegmentation_Results/Masks/'

anatomy = ['calvarial fracture','midline','Thalamus','Brain Stem and cisterns','Lateral Ventricles','3rd Ventricles','4th Ventricles','Cerebellum and vermis']
window_scale = 80
level_scale = 40
segmentations = []
case_id = []
reconstruction = []
for root, dirs, files in os.walk(mask_directory, topdown=True):
    for name in files:
        if name.endswith('.txt'):
            segmentations.append(os.path.join(name))
            text = find_between(name,'_','_rec')
            recon_text = find_between(name,'rec-','_reg')

            if text not in case_id:
                case_id.append(find_between(name,'_','_rec'))
            if recon_text not in reconstruction:

                reconstruction.append(find_between(name,'rec-','_reg'))

cases_with_segmentations = []
for root, dirs, files in os.walk(image_path, topdown=True):
    for i in range(len(case_id)):
        if (case_id[i] and reconstruction[i]) in root:
            if root not in cases_with_segmentations:
                cases_with_segmentations.append(root)


for i in cases_with_segmentations:
    imList = os.listdir(os.path.join(i))
    imList.sort()
    ds = dicom.dcmread(i+'/'+imList[0])
    height = ds['Rows'].value
    width = ds['Columns'].value

    case_id = find_between(i,'PBI_Images/','/')
    print(case_id)
    for j in range(len(imList)):
        segmentation = []
        imStack,c = image_stacking(imList,i,height,width,level_scale,window_scale)
        currentIm = Image.fromarray(imStack[j,:,:]).convert('L').convert('RGB')
        currentImN = np.array(currentIm)
        slice_id = imList[j]
        slice_id = slice_id.split('.dcm')
        print(slice_id[0])
        for root, dirs, files in os.walk(mask_directory, topdown=True):
                for name in files:
                    if name.endswith('.txt') and case_id in name and slice_id[0] in name:
                        segmentation.append(os.path.join(root,name))
        print(segmentation)
        if len(segmentation) > 0:
                currentIm = Image.fromarray(imStack[j,:,:]).convert('L').convert('RGB')
                currentImN = np.array(currentIm)


                for k in segmentation:
                    with open(k, 'r') as f:
                        coordinates = ast.literal_eval(f.read())

                    if anatomy[0] in k:
                        color = (250,0,0)
                    elif anatomy[1] in k:
                        color = (0,255,0)
                    elif anatomy[2] in k:
                        color = (0,0,255)
                    elif anatomy[3] in k:
                        color = (255,255,0)
                    elif anatomy[4]in k:
                        color = (255,0,255)
                    elif anatomy[5] in k:
                        color = (255,165,0)
                    elif anatomy[6] in k:
                        color = (138,43,226)
                    elif anatomy[7] in k:
                        color = (0,0,128)


                    penta = np.array(coordinates,np.int32)
                    penta = np.flip(penta,1)
                    #penta = penta.reshape((1, -1, 2))
                    img = cv.polylines(currentImN, [penta], False, color,1)
                    #cv.imshow('shapes',img)
                    #cv.waitKey(0)
                    #cv.destroyAllWindows()



                overlay_path = 'Overlays/'+case_id
                if not os.path.isdir(overlay_path):
                    os.mkdir(overlay_path)
                slice_png_name = slice_id[0]+'.png'
                full_path = overlay_path+'/'+slice_png_name
                cv.imwrite(full_path,img)



                coordinates = []
        else:
            currentIm = Image.fromarray(imStack[j,:,:]).convert('L').convert('RGB')
            currentImN = np.array(currentIm)
            overlay_path = 'Overlays/'+case_id
            if not os.path.isdir(overlay_path):
                os.mkdir(overlay_path)
            slice_png_name = slice_id[0]+'.png'
            full_path = overlay_path+'/'+slice_png_name
            cv.imwrite(full_path,currentImN)

#imList = os.listdir(os.path.join(image_path))
#imList.sort()
#ds = dicom.dcmread(casePath+'/'+imList[0])



#case_id = find_between(casePath,'PBI_Images/','/')
#for root, dirs, files in os.walk(mask_directory, topdown=True):
    #for name in files:
        #if name.endswith('.txt') and case_id in name and slice_id[0] in name:
            #segmentations.append(os.path.join(root,name))

#height = ds['Rows'].value
#width = ds['Columns'].value

#height = ds['Rows'].value
#width = ds['Columns'].value
#imStack,c = image_stacking(imList,casePath,height,width,level_scale,window_scale)
#currentIm = Image.fromarray(imStack[currentSlice,:,:]).convert('L').convert('RGB')
#currentImN = np.array(currentIm)


#slice_id = imList[currentSlice]
#slice_id = slice_id.split('.dcm')
#for i in segmentations:
    #with open(i, 'r') as f:
        #coordinates = ast.literal_eval(f.read())

    #if anatomy[0] in i:
        #color = (250,0,0)
    #elif anatomy[1] in i:
        #color = (0,255,0)
    #elif anatomy[2] in i:
        #color = (0,0,255)
    #elif anatomy[3] in i:
        #color = (255,255,0)
    #elif anatomy[4]in i:
        #color = (255,0,255)
    #elif anatomy[5] in i:
        #color = (255,165,0)
    #elif anatomy[6] in i:
        #color = (138,43,226)
    #elif anatomy[7] in i:
        #color = (0,0,128)


    #penta = np.array(coordinates,np.int32)
    #penta = np.flip(penta,1)
    ##penta = penta.reshape((1, -1, 2))
    #img = cv.polylines(currentImN, [penta], False, color,1)
