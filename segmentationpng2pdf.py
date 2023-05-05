from PIL import Image
import os
cases = os.listdir('/home/jtoledo/Documents/CTsegmentation_workstation/Overlays/')

print(cases)

for i in cases:
    image_dir = os.listdir('/home/jtoledo/Documents/CTsegmentation_workstation/Overlays/'+i)
    image_dir.sort()
    image_list = []

    for j in image_dir:
        image =Image.open('/home/jtoledo/Documents/CTsegmentation_workstation/Overlays/'+i+'/'+j)


        image_list.append(image)
    image.save('/home/jtoledo/Documents/CTsegmentation_workstation/Overlays/'+i+'_segmentations.pdf', save_all=True, append_images=image_list)
