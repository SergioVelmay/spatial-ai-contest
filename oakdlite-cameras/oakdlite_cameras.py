import cv2
import depthai as dai
import numpy as np

pipeline = dai.Pipeline()

mono_left = pipeline.create(dai.node.MonoCamera)
mono_right = pipeline.create(dai.node.MonoCamera)
depth = pipeline.create(dai.node.StereoDepth)
depth_xout = pipeline.create(dai.node.XLinkOut)

depth_xout.setStreamName("depth")

mono_left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
mono_left.setBoardSocket(dai.CameraBoardSocket.LEFT)
mono_right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
mono_right.setBoardSocket(dai.CameraBoardSocket.RIGHT)

depth.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
depth.initialConfig.setMedianFilter(dai.MedianFilter.MEDIAN_OFF)
depth.setLeftRightCheck(True)
depth.setExtendedDisparity(False)
depth.setSubpixel(False)

mono_left.out.link(depth.left)
mono_right.out.link(depth.right)
depth.disparity.link(depth_xout.input)

color = pipeline.createColorCamera()
color.setPreviewSize(640, 400)
color.setInterleaved(False)
color.setBoardSocket(dai.CameraBoardSocket.RGB)
cam_out = pipeline.createXLinkOut()
cam_out.setStreamName("color")
color.preview.link(cam_out.input)

with dai.Device(pipeline) as device:

    queue_depth = device.getOutputQueue(name="depth", maxSize=4, blocking=False)
    queue_color = device.getOutputQueue(name="color", maxSize=1, blocking=False)

    while True:
        depth_input = queue_depth.get()
        depth_frame = depth_input.getFrame()

        depth_crop = depth_frame[0:390, 25:545]

        color_input = queue_color.get()
        color_frame = color_input.getCvFrame()

        color_crop = color_frame[0:390, 65:585]

        depth_color = cv2.normalize(depth_crop, None, 255, 0, cv2.NORM_INF, cv2.CV_8UC1)
        
        depth_color[depth_color<128] = 0

        depth_color = cv2.equalizeHist(depth_color)
        depth_color = cv2.applyColorMap(depth_color, cv2.COLORMAP_JET)

        cv2.imshow("depth", depth_color)

        cv2.imshow("color", color_crop)

        if cv2.waitKey(1) == ord('q'):
            break