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

difference = 20
pixelThreshold = 100

streamWidth = 160
streamHeight = 90

captureWidth = 1920
captureHeight = 1080

videoCaptureWidth = 1280
videoCaptureHeight = 720

sleepBetweenFrames = 0.2

startupDelay=10

camera = PiCamera()
camera.rotation = 180
sleep(startupDelay)

camera.start_preview(alpha=128)

twitter = Twython(
    consumer_key,
    consumer_secret,
    access_token,
    access_token_secret
)

# Twitter used for pic upload
# Effectively used for push notification alerts 
def uploadImageToTwitter(imageFilename):
    message = "Motion detected!"
    try:
        with open(imageFilename, 'rb') as photo:
            response = twitter.upload_media(media=photo)
            twitter.update_status(status=message, media_ids=[response['media_id']])
    except:
        print 'Unable to upload image to twitter'

# dropbox used for video upload
def uploadFileToDropbox(videoFileFullpath, videoFilename):
    try:
        print 'uploading to dropbox'
        photofile = "/home/pi/Dropbox-Uploader/dropbox_uploader.sh upload {0} {1}".format(videoFileFullpath, videoFilename)   
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

timestamp = time.time()
lastRecordTime = 0
recordCooldown = 20
recordTime = 10
capturedImage = False

image1, buffer1 = compare()

while (True):

    sleep(sleepBetweenFrames)
    image2, buffer2 = compare()

    changedpixels = 0
    for x in xrange(0, streamWidth):
        for y in xrange(0, streamHeight):
            pixdiff = abs(buffer1[x,y][1] - buffer2[x,y][1])
            if pixdiff > difference:
                changedpixels += 1

    if changedpixels > pixelThreshold:
        if capturedImage == False:
            timestamp = time.time()
            imgFilename = saveImage(captureWidth, captureHeight)
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
            uploadImageToTwitter(imgFilename)
            capturedImage = True
        else:
            capturedImage = False

    image1 = image2
    buffer1 = buffer2 
