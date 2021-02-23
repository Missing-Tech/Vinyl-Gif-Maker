from __future__ import print_function
from transloadit import client
import os
import requests
import cv2
import numpy as np

tl = client.Transloadit('6528ded4ea0d49e2a8f1197b0dc77d85', '1ed089c8e5def7d124df1685165736446815e30d')

img_name = 'okcomputer'
img_path = 'Assets/{name}.jpg'.format(name=img_name)
vinyl_path = 'Assets/vinyl.png'
remove_bg_location = 'Assets/trimmed_image.png'


def downloadImage(url, location):
    # Sends a request to the url
    r = requests.get(url)
    # Downloads the content locally
    image = open(location, 'wb')
    image.write(r.content)
    image.close()


def useTemplate(templateID, file_path, result_name, get_url=True, override_url=''):
    assembly = tl.new_assembly({'template_id': templateID})
    # This is for the watermark step, not very pretty however
    if override_url != '':
        assembly.add_step('watermark', '/image/resize', {'watermark_url': override_url})
    assembly.add_file(open(file_path, 'rb'))
    assembly_response = assembly.create(retries=5, wait=True)
    if get_url:
        assembly_url = assembly_response.data.get('results').get(result_name)[0].get('ssl_url')
        return assembly_url


def maskImage(img_path):
    # Mask the image
    # Reads the input image
    img = cv2.imread(img_path)
    # Creates a mask with the same size as the image
    mask = np.zeros(img.shape, dtype=np.uint8)
    # Creates a white circle in the centre
    mask = cv2.circle(mask, (175, 175), 175, (255, 255, 255), -1)
    # Makes a small whole in the centre of the mask
    mask = cv2.circle(mask, (175, 175), 20, (0, 0, 0), -1)
    result = cv2.bitwise_and(img, mask)


    result_location = 'Assets/mask.png'
    cv2.imwrite(result_location, result)

    # However this leaves a black BG which we don't want
    # You can use the transloadit transparent parameter on the /image/resize robot for this
    # By setting transparent to 0,0,0 it sets all black pixels to transparent
    remove_bg_url = useTemplate('c7713a444d214d85a6aa0694de77b348', result_location, 'trimmed')
    downloadImage(remove_bg_url, remove_bg_location)
    return remove_bg_url


# Resize the image using a template
# Automatically converts it to a png
resize_url = useTemplate('cea84f9d24c74003ab7febd0187c5b7d', img_path, 'resize_image')

# Download the image locally
resized_image_location = 'Assets/resized_image.png'

downloadImage(resize_url, resized_image_location)

# Masks the image
trimmed_url = maskImage(resized_image_location)

# Now we add the watermark to the vinyl
finished_watermarked_location = 'Assets/vinyl_finished.png'
vinyl_url = useTemplate('0f8a6a9156ed4a7c84b76a934a985b8f', vinyl_path, 'watermark', True, trimmed_url)
downloadImage(vinyl_url, finished_watermarked_location)

finished_vinyl = cv2.imread(finished_watermarked_location)
# cv2.imshow('Final Result', finished_vinyl)

# Now we make a list of images that represent each frame
no_of_frames = 60
assembly = tl.new_assembly({'template_id': 'e8129b18ee35441cb1e7c2f43e777332'})
directory = 'Assets/Frames/{image}'.format(image=img_name)

for i in range(no_of_frames):
    if not os.path.exists(directory):
        os.mkdir(directory)
    location = '{directory}/{index}.png'.format(directory=directory, index=round(i*360/no_of_frames))
    cv2.imwrite(location, finished_vinyl)
    assembly.add_file(open(location, 'rb'))

# Length of our animation in seconds
length = 2

# assembly.add_file(open('Assets/Frames/oos/160.png', 'rb'))

# Overrides our template with the necessary settings
assembly.add_step('animated', '/video/merge', {'duration': length, 'framerate': no_of_frames / length})
assembly_response = assembly.create(retries=5, wait=True)
assembly_url = assembly_response.data.get('results').get('animated')[0].get('ssl_url')
print(assembly_url)
final_gif_location = 'Assets/finished_gif.gif'
downloadImage(assembly_url, final_gif_location)