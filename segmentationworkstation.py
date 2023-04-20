import PySimpleGUI as psg
import os
import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk, ImageFilter
import pydicom as dicom
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

import matplotlib
matplotlib.use('TkAgg')
from roipoly import RoiPoly

psg.set_options(font=('Arial Bold', 16))

def drawContour(image, segs, includeChannels, RGBs):
    for (ichannel,RGB) in zip(includeChannels, RGBs):

        seg = Image.fromarray(segs[:,:,ichannel]).convert('L')
        thisContour = seg.point(lambda p:p!=0)

        thisEdges = thisContour.filter(ImageFilter.FIND_EDGES)
        thisEdgesN = np.array(thisEdges)
        image[np.nonzero(thisEdgesN)] = RGB
    return image

def updateInclude(includedChannels, down, c):
    if not down:
        includedChannels.append(c)
    else:
        includedChannels.remove(c)

    RGBoptions = [(255,0,0), (0,255,0), (0,0,255), (128,0,0), (255,165,0), (255,255,0), (127,255,0), (0,100,0), (0,255,255), (25,25,112), (139,0,139), (255,0,255), (245,245,220), (112,128,144), (0,0,0), (192,192,192)]

    RGB = [RGBoptions[i] for i in includedChannels]

    return includedChannels, RGB

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

anatomy = ['calvarial fracture','midline']
region = [*range(1,21)]
anat_lst = psg.Combo(anatomy, font=('Arial Bold', 14),  expand_x=True, enable_events=True,  readonly=False, key='-COMBO-')
reg_lst = psg.Combo(region, font=('Arial Bold', 14),  expand_x=True, enable_events=True,  readonly=False, key='-region-')
file_list_column = [[psg.Text("Case Folder"),
                    psg.In(size=(25,1), enable_events=True, key="-CASE-"),
                    psg.FolderBrowse()],[psg.Text("Anatomy"),anat_lst],[psg.Text("Region"),reg_lst],[psg.Text('Enter W: '), psg.Input(key='-window-')],
                    [psg.Text('Enter L: '), psg.Input(key='-level-')],[psg.Button('Apply W/L', key = '-scale-'),psg.Button('Segment')]]
image_viewer_column = [[psg.Text("CHOOSE A CASE FROM THE BROWSER", key="-DIRECTIONS-")],
                       [psg.Image(key="-IMAGE-")],
                       [psg.Text("", key="-SLICETRACK-")]]

layout =  [file_list_column, image_viewer_column]
window = psg.Window(title="PBI Segmentation Interface", layout=layout, return_keyboard_events=True, finalize=True)
includeChannels = []
RGB = []
chosen_image = 0
segmenting = True
window_scale = 80
level_scale = 40
while segmenting:
    event, values = window.read()
    includedChannels = []

    if event == "-QUIT-" or event == psg.WIN_CLOSED:
        #MAKE THINGS TO ASK IF WANT TO SAVE
        break

    if event == "-CASE-":
        casePath = values["-CASE-"]
        imList = os.listdir(os.path.join(casePath))
        imList.sort()
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

        currentSlice = 0
        currentIm = Image.fromarray(imStack[0,:,:]).convert('L')

        window["-IMAGE-"].update(data=ImageTk.PhotoImage(image=currentIm), size=(512,512))
        window["-DIRECTIONS-"].update("Evaluate segmentations")
        window["-SLICETRACK-"].update([str(currentSlice+1)+'/'+str(len(imList))])

    elif event == "MouseWheel:Up":
        currentSlice += 1
        currentSlice = max(min(len(imList)-1, currentSlice), 0)
        currentIm = Image.fromarray(imStack[currentSlice,:,:]).convert('L')
        currentImN = np.array(currentIm)
        currentIm = drawContour(currentImN, c[currentSlice,:,:,:], includeChannels, RGB)
        window["-IMAGE-"].update(data=ImageTk.PhotoImage(image=Image.fromarray(currentIm)), size=(512,512))
        window["-SLICETRACK-"].update([str(currentSlice+1)+'/'+str(len(imList))])

    elif event == "MouseWheel:Down":
        currentSlice += -1
        currentSlice = max(min(len(imList)-1, currentSlice), 0)
        currentIm = Image.fromarray(imStack[currentSlice,:,:]).convert('L')
        currentImN = np.array(currentIm)
        currentIm = drawContour(currentImN, c[currentSlice,:,:,:], includeChannels, RGB)
        window["-IMAGE-"].update(data=ImageTk.PhotoImage(image=Image.fromarray(currentIm)), size=(512,512))
        window["-SLICETRACK-"].update([str(currentSlice+1)+'/'+str(len(imList))])
    elif event == "-scale-":
        window_scale = int(values['-window-'])
        level_scale = int(values['-level-'])
        currentIm = Image.fromarray(imStack[currentSlice,:,:]).convert('L')
        currentImN = np.array(currentIm)
        currentIm = drawContour(currentImN, c[currentSlice,:,:,:], includeChannels, RGB)
        window["-IMAGE-"].update(data=ImageTk.PhotoImage(image=Image.fromarray(currentIm)), size=(512,512))
        window["-SLICETRACK-"].update([str(currentSlice+1)+'/'+str(len(imList))])
        print(window_scale)
    elif event == "Segment":
        if chosen_image == 0:
            psg.popup_auto_close('Choose Image Directory First')
        else:

            print('segmenting:',values['-COMBO-'])
            currentIm = Image.fromarray(imStack[currentSlice,:,:]).convert('L')
            currentImN = np.array(currentIm)
            try:
                plt.rcParams['figure.figsize'] = [10, 10]
                plt.imshow(currentImN,cmap=plt.cm.gray)
                my_roi = RoiPoly(color='r')
                mask = my_roi.get_mask(currentImN)
                plt.figure()
                plt.imshow(mask)
                plt.show()

                if not os.path.exists('masks'):
                    os.mkdir('masks')
                segmentation_path = 'masks'+'/'+values['-COMBO-']
                if not os.path.exists(segmentation_path):
                    os.mkdir(segmentation_path)

                case_id = find_between(casePath,'PBI_Images/','/')
                recon = casePath.split('/')[-1].strip()
                region_num = values['-region-']
                slice_id = imList[currentSlice]
                slice_id = slice_id.split('.dcm')

                fullpath = os.path.join(segmentation_path,case_id+'_'+'rec-'+recon+'_'+'reg-'+str(region_num)+'_'+slice_id[0]+'.binary.png')
                print(fullpath)

                if os.path.exists(fullpath):
                    ch = psg.popup_yes_no("Segmentation for that slice and region exists, do you wish to overwrite?",  title="YesNo")
                    if ch =='Yes':
                        cv2.imwrite(fullpath, mask * 255)

                else:
                    cv2.imwrite(fullpath, mask * 255)

            except:
                psg.popup_auto_close('Closed Slice')

window.close()

#typed comment from desktop
