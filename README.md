# Let's Build: Spinning Vinyl GIF Generator
Personally, as a huge fan of music, I jumped at the opportunity to work on a project like this. Especially, as a newly hired Support Engineer at Transloadit, I thought it'd be great to learn more about their [Python SDK](https://transloadit.com/docs/#python-sdk).

Moreover, we'll be using the open source tool [OpenCV](https://pypi.org/project/opencv-python/) which allows us to perform bitwise calculations on images, alongside many other image and video processing options that we won't be needing today - although if you're interested you might want to take a look at the [OpenCV Docs](https://opencv-python-tutroals.readthedocs.io/en/latest/index.html).

We'll also be using the [NumPy package](https://numpy.org/). Again, there's a lot more functionality beyond the scope of our project, but we'll be using it in tandem with OpenCV to help with local image processing. In short, NumPy offers powerful tools for scientific and mathematic computations within Python.

## Our Aim
Originally, this blog post was intended as a response to a stack overflow question, but we found the project to be a worthwhile example on how versatile the Transloadit robots are. In addition, it's a useful demo on utilising the [Python SDK](https://transloadit.com/docs/#python-sdk); so lets get started!

## Assets
To download the assets that we'll be using today you can find them here:
- [Vinyl Record Background](https://raw.githubusercontent.com/Missing-Tech/Vinyl-Gif-Maker/main/.github/images/vinyl.png)
- [Album Art *(Necessary)*](https://raw.githubusercontent.com/Missing-Tech/Vinyl-Gif-Maker/main/.github/images/okcomputer.jpg)

## Templates
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
Here, we first of all use the `:original` snippet explained earlier, followed by the [`/image/resize/`](https://transloadit.com/docs/transcoding/#image-resize) robot. This step specifies that we want to use the result from `:original` and what robot we want functionality from (full list of robots can be found [here](https://transloadit.com/docs/transcoding/)). Then, `format` lets the robot know what format the image should be, although this can further be fine-tuned with FFmpeg (I'd recommend the [previous Let's Build](https://transloadit.com/blog/2021/01/waveform-video/) if you want to learn more about that). It's then just as easy as specifying how big we want to make the image, as well as what [resize strategy](https://transloadit.com/docs/transcoding/#resize-strategies) we'd like to use. For our purposes, `"fillcrop"` makes the most sense. Finally, we just need to let the robot know the version of the [ImageMagick](https://imagemagick.org/index.php) stack that we are using. 

