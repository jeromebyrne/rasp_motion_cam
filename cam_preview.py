# -*- coding: utf-8 -*-
from picamera import PiCamera
import datetime
import time
from time import sleep

camera = PiCamera()
camera.rotation = 180
camera.resolution = (1280, 720)
sleep(1)

camera.start_preview(alpha=190)
sleep(120)
camera.stop_preview()

