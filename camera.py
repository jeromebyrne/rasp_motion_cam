# -*- coding: utf-8 -*-
from picamera import PiCamera
import datetime
import io
import os
import time
from PIL import Image
from time import sleep
from twython import Twython
from subprocess import call

from auth import (
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret
)

twitter = Twython(
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret
)

# Twitter used for pic upload
# Effectively used for push notification alerts 
def uploadImageToTwitter(imageFilename, message):
    try:
        with open(imageFilename, 'rb') as photo:
            response = twitter.upload_media(media=photo)
            twitter.update_status(status=message, media_ids=[response['media_id']])
    except:
        print 'Unable to upload photo to twitter'

# dropbox used for video upload
def uploadFileToDropbox(videoFileFullpath, videoFilename):
    try:
        print 'uploading to dropbox'
        photofile = "Dropbox-Uploader/dropbox_uploader.sh upload {0} {1}".format(videoFileFullpath, videoFilename)
        print photofile
        call ([photofile], shell=True)
    except:
        print 'Unable to upload file to dropbox'

def compare():
   camera.resolution = (streamWidth, streamHeight)
   stream = io.BytesIO()
   camera.capture(stream, format = 'bmp')
   stream.seek(0)
   im = Image.open(stream)
   buffer = im.load()
   stream.close()
   return im, buffer

def saveImage(captureWidth, captureHeight):
   time = datetime.datetime.now()
   filename = 'image_captures/motion-%04d%02d%02d-%02d%02d%02d.jpg' % (time.year, time.month, time.day, time.hour, time.minute, time.second)
   camera.resolution = (captureWidth, captureHeight)
   camera.annotate_text = time.strftime("%Y-%m-%d %H:%M:%S")
   img = camera.capture(filename)
   print 'Captured %s' % filename
   return filename

def saveImageWithFilename(filename, captureWidth, captureHeight):
   time = datetime.datetime.now()
   camera.resolution = (captureWidth, captureHeight)
   camera.annotate_text = time.strftime("%Y-%m-%d %H:%M:%S")
   img = camera.capture(filename)

difference = 20
pixelThreshold = 100

streamWidth = 160
streamHeight = 90

captureWidth = 1920
captureHeight = 1080

videoCaptureWidth = 1280
videoCaptureHeight = 720

sleepBetweenFrames = 0.2

startupDelay=900

camera = PiCamera()
camera.rotation = 180
camera.resolution = (1920,1080)
camera.start_preview(alpha=128)
sleep(2)

saveImageWithFilename('image_captures/BootUpCapture.jpg', captureWidth, captureHeight)
uploadImageToTwitter('image_captures/BootUpCapture.jpg', "Camera Startup")
print 'Captured and uploaded welcome capture to twitter'

sleep(startupDelay)

timestamp = time.time()
lastRecordTime = 0

# Take a picture at least every half day so we know things are working
lastCaptureTime = timestamp
takePicAtLeastEvery = 43200

recordCooldown = 15
recordTime = 10
capturedImage = False

image1, buffer1 = compare()

while (True):

    sleep(sleepBetweenFrames)
    image2, buffer2 = compare()
    timestamp = time.time()

    changedpixels = 0
    for x in xrange(0, streamWidth):
        for y in xrange(0, streamHeight):
            pixdiff = abs(buffer1[x,y][1] - buffer2[x,y][1])
            if pixdiff > difference:
                changedpixels += 1

    if changedpixels > pixelThreshold:
        if capturedImage == False:
            imgFilename = saveImage(captureWidth, captureHeight)
            uploadImageToTwitter(imgFilename, "Motion Detected!")
            lastCaptureTime = timestamp
            print timestamp
            print lastRecordTime
            if (timestamp - lastRecordTime) > recordCooldown:
                print 'starting recording'
                camera.resolution = (videoCaptureWidth, videoCaptureHeight)
                cdt = datetime.datetime.now()
                camera.framerate = 15
                filename = 'video_captures/motion-%04d%02d%02d-%02d%02d%02d.h264' % (cdt.year, cdt.month, cdt.day, cdt.hour, cdt.minute, cdt.second)
                camera.start_recording(filename)
                sleep(recordTime)
                camera.stop_recording()
                lastRecordTime = timestamp
                uploadFileToDropbox('./{0}'.format(filename), filename)
            capturedImage = True
        else:
            capturedImage = False

    if (timestamp - lastCaptureTime) > takePicAtLeastEvery:
        saveImageWithFilename('image_captures/inactive_interval.jpg', captureWidth, captureHeight)
        uploadImageToTwitter('image_captures/inactive_interval.jpg', "Interval capture")
        lastCaptureTime = timestamp
        print 'Interval Capture'
        
    image1 = image2
    buffer1 = buffer2 
