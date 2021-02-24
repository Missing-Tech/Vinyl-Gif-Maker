# Let's Build: Spinning Vinyl GIF Generator
Personally, as a huge fan of music, I jumped at the opportunity to work on a project like this. Especially, as a newly hired Support Engineer at Transloadit, I thought it'd be great to learn more about their [Python SDK](https://transloadit.com/docs/#python-sdk).

Moreover, we'll be using the open source tool [OpenCV](https://pypi.org/project/opencv-python/) which allows us to perform bitwise calculations on images, alongside many other image and video processing options that we won't be needing today - although if you're interested you might want to take a look at the [OpenCV Docs](https://opencv-python-tutroals.readthedocs.io/en/latest/index.html).

We'll also be using the [NumPy package](https://numpy.org/). Again, there's a lot more functionality beyond the scope of our project, but we'll be using it in tandem with OpenCV to help with local image processing. In short, NumPy offers powerful tools for scientific and mathematic computations within Python.

## Our Aim
Originally, this blog post was intended as a response to a stack overflow question, but we found the project to be a worthwhile example on how versatile the Transloadit robots are. In addition, it's a useful demo on utilising the [Python SDK](https://transloadit.com/docs/#python-sdk), and on how to use Transloadit templates - so lets get started!

## Assets
To download the assets that we'll be using today you can find them here:
- [Vinyl Record Background](https://raw.githubusercontent.com/Missing-Tech/Vinyl-Gif-Maker/main/.github/images/vinyl.png)
- [Album Art *(Necessary)*](https://raw.githubusercontent.com/Missing-Tech/Vinyl-Gif-Maker/main/.github/images/okcomputer.jpg)

## Setting up our project
The first thing you're going to want to do is install all the necessary packages, so in your Python Console run each of these:
- `pip install pytransloadit`
- `pip install numpy`
- `pip install opencv-python`
- `pip install requests`
- `pip install future`

Next we're going to want to create a python project, I'll be using PyCharm but any other code editor should work nicely.
At the top of our project we're going to want to add all of our imports like so:
```
from __future__ import print_function
from transloadit import client
import os
import requests
import cv2
import numpy as np
```
Make sure to also create a transloadit client like so:
```
tl = client.Transloadit(TRANSLOADIT_KEY, TRANSLOADIT_SECRET)
```
Finally, before we can start coding, we're going to create an `/Assets/` folder within our project folder, and a `../Frames` inside of that. Your folder hierarchy should end up being `Project/Assets/Frames`. Inside of Assets, put the two images you downloaded earlier.
We're going to create some global variables to use later now as well.
```
img_name = 'okcomputer'
img_path = 'Assets/{name}.jpg'.format(name=img_name)
vinyl_path = 'Assets/vinyl.png'
remove_bg_location = 'Assets/trimmed_image.png'
```
Make sure that `img_name` matches the name of the album art, without the file extension, and also that `vinyl_path` matches the name of the background image. Apart from that, `remove_bg_location` can be named anything, and you don't need to worry about `img_path`.

**We should be all set up now so lets make our first template!**
## Templates
### Making a template
In order to make a template, you want to go to your transloadit console and [create a new app](https://transloadit.com/c/create-new-app). Name your app anything you like, such as "Vinyl GIF Generator", then go to the templates section on the left. From here you will be creating a blank template, although Transloadit has a very helpful wizard to automatically generate a template for you! From this page, you can find your `template ID` which will be useful in the upcoming steps.
### :original
To provide the majority of the functionality to our program, we're going to need to create a few different robots - due to how the data is being passed between our local machine, and the Transloadit servers. Let's start with the one common component to all of our Assemblies though!
```
":original": {
  "robot": "/upload/handle"
}
```
While small, this snippet will handle the file uploading for us. Importantly, it has to be named `:original`, which is a keyword reserved for this robot. However, if you want to upload a file from a third party file-hosting service, you can find all supported services at the [Transloadit documentation](https://transloadit.com/docs/transcoding/#service-file-importing). For example, you can use the [`/dropbox/import`](https://transloadit.com/docs/transcoding/#dropbox-import) robot like so:
```
"imported": {
  "robot": "/dropbox/import",
  "result": true,
  "credentials": "YOUR_DROPBOX_CREDENTIALS",
  "path": "my_source_folder/"
}
```
### Resizing the image
This compact robot will do one simple job: resize the image to `350x350` pixels as well as making it a `PNG`. This is necessary to make sure that the image is properly scaled on the vinyl record at the end. If you're using your own background image, you may want to fiddle around with the settings on this template until it's just about right for you.
```
{
  "steps": {
    ":original": {
      "robot": "/upload/handle"
    },
    "resize": {
      "use": ":original",
      "robot": "/image/resize",
      "format": "png",
      "resize_strategy": "fillcrop",
      "width": 350,
      "height": 350,
      "imagemagick_stack": "v2.0.7"
    }
  }
}
```
Here, we first of all use the `:original` snippet explained earlier, followed by the [`/image/resize/`](https://transloadit.com/docs/transcoding/#image-resize) robot. This step specifies that we want to use the file that we upload and what robot we want functionality from (full list of robots can be found [here](https://transloadit.com/docs/transcoding/)). Then, `format` lets the robot know what format the image should be, although this can further be fine-tuned with FFmpeg (I'd recommend the [previous Let's Build](https://transloadit.com/blog/2021/01/waveform-video/) if you want to learn more about that). It's then just as easy as specifying how big we want to make the image, as well as what [resize strategy](https://transloadit.com/docs/transcoding/#resize-strategies) we'd like to use. For our purposes, `"fillcrop"` makes the most sense. Finally, we just need to let the robot know the version of the [ImageMagick](https://imagemagick.org/index.php) stack that we are using. 

## Using our templates
Because we're using multiple templates, we're going to create a small python function that will take our template ID, as well as a few other parameters, and return a *temporary* URL to our image, where we're going to send a HTTP request later, in order to download our image locally. While, this method isn't ideal, it serves our purposes nicely - however I definitely recommend using a third party service to download your files to!

We'll call it `useTemplate` and pass it our template ID, the file path of the image we want to upload, the name of the last step in our template (so for example in our resize template, it would be "resize"); as well as some optional parameters, like whether we want to return the URL - which we'll default to `True`, and an override URL - which will be useful when we're overlaying the images.
```
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
```
In short, this function will create an assembly with our template, and give us a URL to where we can find the outputted image.

We also need to create one more utility function in order to download our image to our Assets folder. Luckily this one is much smaller than the last one!
```
def downloadImage(url, location):
    # Sends a request to the url
    r = requests.get(url)
    # Downloads the content locally
    image = open(location, 'wb')
    image.write(r.content)
    image.close()
```
All this will do is send a request to the URL that we give it, create a new image at a file location, and then write the contents of our HTTP request to that location. Now lets create the rest of our templates to be used later!
### Removing the Background
```
{
  "steps": {
    ":original": {
      "robot": "/upload/handle"
    },
    "trimmed": {
      "use": ":original",
      "robot": "/image/resize",
      "alpha": "Activate",
      "type": "TrueColor",
      "transparent": "0,0,0",
      "imagemagick_stack": "v2.0.7"
    }
  }
}
```
This template is very simple, it will enable the alpha channnel on our PNG image, and then set all black pixels (0,0,0) to be transparent. However, this also means that we have to be careful if we're using album art with a black background - such as the Dark Side of the Moon, by Pink Floyd.
### Overlaying the image
Remember from earlier how we had the `override_url`? This is where that step becomes quite important, we're going to take the URL of the image from our last step - and supply it to the `/image/resize` robot here in order to get a finished vinyl image which we can rotate later. Make sure that the name of the watermark step and the name in the function match.
```
{
  "steps": {
    ":original": {
      "robot": "/upload/handle"
    },
    "watermark": {
      "use": ":original",
      "robot": "/image/resize",
      "watermark_size": "33%",
      "watermark_position": "center",
      "imagemagick_stack": "v2.0.7"
    }
  }
}
```
This uses the handy feature that Transloadit offers of watermarking a picture, if you've used different assets you might have to tweak around with the settings to get it just right.
### Making it a GIF!
This is the last template that we'll have to make I promise! While it might look daunting it's actually quite simple.
```
{
  "steps": {
    ":original": {
      "robot": "/upload/handle"
    },
    "rotate_image": {
      "use": ":original",
      "robot": "/image/resize",
      "rotation": "${file.basename}",
      "resize_strategy": "crop",
      "imagemagick_stack": "v2.0.7"
    },
    "animated": {
      "robot": "/video/merge",
      "use": {
        "steps": [
          {
            "name": "rotate_image",
            "as": "image"
          }
        ],
        "bundle_steps": true
      },
      "result": true,
      "ffmpeg_stack": "v4.3.1",
      "ffmpeg": {
        "f": "gif",
        "pix_fmt": "rgb24"
      }
    }
  }
}
```
Lets go through it step-by-step, skipping `:original` as we've already gone through that earlier.
#### `rotate_image`
Here we rotate the image by the amount specified in the name of the image - using Transloadit's [assembly variables](https://transloadit.com/docs/#assembly-variables). We're going to create frames for our GIF, name them the amount of degrees we want to rotate it by (so 234.png will rotate 234 degrees), and then stitch them all together.
#### `animated`
This step takes all of the results from the first step, and then makes them into a GIF - specified within the FFmpeg parameters. The key to making this work is `"bundle_steps": true`, as this means that it creates one GIF from all of the resultant images from the first step.

## Tying it all together in Python
Now we should have all the puzzle pieces we need in order to make our spinning vinyl GIF :)
If you want to skip to copy-pasting the code that'll be at the end for you, alongside the GitHub repo.
Make sure to replace the template IDs with your own (they'll be in square brackets).
Lets start by resizing the image and downloading it locally
```
# Resize the image using a template
# Automatically converts it to a png
resize_url = useTemplate([RESIZE_IMAGE_TEMPLATE_ID], img_path, 'resize')
# Download the image locally
resized_image_location = 'Assets/resized_image.png'
downloadImage(resize_url, resized_image_location)
```
Next we need to make our mask, we're going to create a function for this simply for readability. We'll call it `maskImage` and give it an `img_path`.
```
def maskImage(img_path):
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
    remove_bg_url = useTemplate([REMOVING_BG_TEMPLATE_ID], result_location, 'trimmed')
    downloadImage(remove_bg_url, remove_bg_location)
    return remove_bg_url
```
This function has two halves, lets go through them individually.
```
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
```
Here we create a black image with the same size as the image specified, and then create two white circles to produce a donut like so:
![](https://raw.githubusercontent.com/Missing-Tech/Vinyl-Gif-Maker/main/.github/images/mask2.png)
We then perform a bitwise AND operation on both the mask and our original image, meaning that the image is shown where it has a pixel, *and* where the mask is white. This gives us this result:
![](https://raw.githubusercontent.com/Missing-Tech/Vinyl-Gif-Maker/main/.github/images/mask.png)
However, we don't want this black BG, so this is where the second half of the function is useful.
```
    # However this leaves a black BG which we don't want
    # You can use the transloadit transparent parameter on the /image/resize robot for this
    # By setting transparent to 0,0,0 it sets all black pixels to transparent
    remove_bg_url = useTemplate([REMOVING_BG_TEMPLATE_ID], result_location, 'trimmed')
    downloadImage(remove_bg_url, remove_bg_location)
    return remove_bg_url
```
Using our template from earlier, this will make all the black pixels transparent for us - giving us this:

![](https://raw.githubusercontent.com/Missing-Tech/Vinyl-Gif-Maker/main/.github/images/trimmed.png)

We'll call our function like so:
```
# Masks the image
trimmed_url = maskImage(resized_image_location)
```
Now we just need to put our donut on the vinyl record and make it spin! We're almost there :)
Let's watermark the image using our template from earlier:
```
# Now we add the watermark to the vinyl
finished_watermarked_location = 'Assets/vinyl_finished.png'
vinyl_url = useTemplate([WATERMARK_IMAGE_TEMPLATE_ID], vinyl_path, 'watermark', True, trimmed_url)
downloadImage(vinyl_url, finished_watermarked_location)
```
This gives us this result:

![](https://raw.githubusercontent.com/Missing-Tech/Vinyl-Gif-Maker/main/.github/images/overlayed.png)

We'll make a reference to this
```
finished_vinyl = cv2.imread(finished_watermarked_location)
```
Now lets start making it spin!
```
# Now we make a list of images that represent each frame
no_of_frames = 60
assembly = tl.new_assembly({'template_id': [SPINNING_VINYL_TEMPLATE_ID]})
directory = 'Assets/Frames/{image}'.format(image=img_name)
# Length of our animation in seconds
length = 2

for i in range(no_of_frames):
    if not os.path.exists(directory):
        os.mkdir(directory)
    # Creates an image based on the index in the animation
    # We pass this to the robot so it knows how many degrees to rotate the image by
    location = '{directory}/{index}.png'.format(directory=directory, index=round(i*360/no_of_frames))
    cv2.imwrite(location, finished_vinyl)
    assembly.add_file(open(location, 'rb'))
```
This will create a folder specifically for our image, then make 60 frames - naming each one how many degrees it should rotate in order to make a 2 second animation. Remember earlier how we used the file name to say how many degrees to rotate the image? This is where we name our files. 
Because we need a little finer control over our assembly, we can't use the function we made earlier - which leads to our code looking a little ugly but that's ok!
```
# Overrides our template with the necessary settings
assembly.add_step('animated', '/video/merge', {'duration': length, 'framerate': no_of_frames / length})
assembly_response = assembly.create(retries=5, wait=True)
assembly_url = assembly_response.data.get('results').get('animated')[0].get('ssl_url')
```
We're essentially copying the cope from earlier, but just adding the `assembly.add_step` as an override, so we can tell the robot how long we want the animation to be and what frame rate - which is determined by dividing `no_of_frames` by `length`.

We can print the URL to the console, and also download it locally now.
```
print(assembly_url)
final_gif_location = 'Assets/finished_gif.gif'
downloadImage(assembly_url, final_gif_location)
```
Meaning we finally have our *spinning vinyl*!🎉

![](https://raw.githubusercontent.com/Missing-Tech/Vinyl-Gif-Maker/main/.github/images/finished_gif.gif)

**Congratulations on making it this far!** I know its been long but I hope you think it's worth it :)
```
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
    remove_bg_url = useTemplate([REMOVING_BG_TEMPLATE_ID], result_location, 'trimmed')
    downloadImage(remove_bg_url, remove_bg_location)
    return remove_bg_url


# Resize the image using a template
# Automatically converts it to a png
resize_url = useTemplate([RESIZE_IMAGE_TEMPLATE_ID], img_path, 'resize')
# Download the image locally
resized_image_location = 'Assets/resized_image.png'
downloadImage(resize_url, resized_image_location)

# Masks the image
trimmed_url = maskImage(resized_image_location)

# Now we add the watermark to the vinyl
finished_watermarked_location = 'Assets/vinyl_finished.png'
vinyl_url = useTemplate([WATERMARK_IMAGE_TEMPLATE_ID], vinyl_path, 'watermark', True, trimmed_url)
downloadImage(vinyl_url, finished_watermarked_location)

finished_vinyl = cv2.imread(finished_watermarked_location)

# Now we make a list of images that represent each frame
no_of_frames = 60
assembly = tl.new_assembly({'template_id': [SPINNING_VINYL_TEMPLATE_ID]})
directory = 'Assets/Frames/{image}'.format(image=img_name)
# Length of our animation in seconds
length = 2

for i in range(no_of_frames):
    if not os.path.exists(directory):
        os.mkdir(directory)
    # Creates an image based on the index in the animation
    # We pass this to the robot so it knows how many degrees to rotate the image by
    location = '{directory}/{index}.png'.format(directory=directory, index=round(i*360/no_of_frames))
    cv2.imwrite(location, finished_vinyl)
    assembly.add_file(open(location, 'rb'))

# Overrides our template with the necessary settings
assembly.add_step('animated', '/video/merge', {'duration': length, 'framerate': no_of_frames / length})
assembly_response = assembly.create(retries=5, wait=True)
assembly_url = assembly_response.data.get('results').get('animated')[0].get('ssl_url')

print(assembly_url)
final_gif_location = 'Assets/finished_gif.gif'
downloadImage(assembly_url, final_gif_location)
```

I hope you enjoyed making this, and maybe you've learned some things about the Transloadit API that you can use on your next project! If you want to check out the GitHub repo you can find it [here](https://github.com/Missing-Tech/Vinyl-Gif-Maker). 

