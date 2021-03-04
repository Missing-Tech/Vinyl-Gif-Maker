from __future__ import print_function
from transloadit import client
import os
import requests
import cv2
import numpy as np

TRANSLOADIT_KEY = os.environ.get('TRANSLOADIT_KEY')
TRANSLOADIT_SECRET = os.environ.get('TRANSLOADIT_SECRET')

tl = client.Transloadit(TRANSLOADIT_KEY, TRANSLOADIT_SECRET)

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
    # Creates a new assembly on our Transloadit client using our template ID
    assembly = tl.new_assembly({'template_id': templateID})
    # This is for the watermark step, not very pretty however
    if override_url != '':
        assembly.add_step('watermark', '/image/resize', {'watermark_url': override_url})

    # Adds the file to the assembly
    assembly.add_file(open(file_path, 'rb'))
    # Attempts to create an assembly, if it fails after 5 tries it'll throw an error
    assembly_response = assembly.create(retries=5, wait=True)
    if get_url:
        # Parses the JSON returned from the assembly to find the URL of our result
        # Since, in our templates we're not exporting the file it gets stored on Transloadit servers
        # For a maximum of 24 hours
        assembly_url = assembly_response.data.get('results').get(result_name)[0].get('ssl_url')
        return assembly_url


def maskImage(img_path):
    # Reads the input image
    img = cv2.imread(img_path)
    # Creates a mask with the same size as the image
    mask = np.zeros(img.shape, dtype=np.uint8)
    # Creates a white circle in the centre
    mask = cv2.circle(mask, (175, 175), 175, (255, 255, 255), -1)
    # Makes a small whole in the centre of the mask
    mask = cv2.circle(mask, (175, 175), 20, (0, 0, 0), -1)

    cv2.imwrite('.github/images/mask2.png', mask)

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
resize_url = useTemplate('cea84f9d24c74003ab7febd0187c5b7d', img_path, 'resize')
# Download the image locally
resized_image_location = 'Assets/resized_image.png'
downloadImage(resize_url, resized_image_location)

# Masks the image
trimmed_url = maskImage(resized_image_location)

# Now we add the watermark to the vinyl
finished_watermarked_location = 'Assets/vinyl_finished.png'
vinyl_url = useTemplate('0f8a6a9156ed4a7c84b76a934a985b8f', vinyl_path, 'watermark', True, trimmed_url)

# Now we make a list of images that represent each frame
no_of_frames = 60
# Length of our animation in seconds
length = 2

assembly = tl.new_assembly({'template_id': 'e8129b18ee35441cb1e7c2f43e777332'})
# Overrides our template with the necessary settings
assembly.add_step('import', '/http/import', {'url': vinyl_url})
assembly.add_step('animated', '/video/merge', {'duration': length, 'framerate': no_of_frames / length})
assembly_response = assembly.create(retries=5, wait=True)
assembly_url = assembly_response.data.get('results').get('animated')[0].get('ssl_url')

print(assembly_url)
final_gif_location = 'Assets/finished_gif.gif'
downloadImage(assembly_url, final_gif_location)
