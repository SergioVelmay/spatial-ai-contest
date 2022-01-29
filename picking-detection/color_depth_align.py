import cv2
import numpy as np
import depthai as dai

rgbWeight = 0.4
depthWeight = 0.6

def updateBlendWeights(percent_rgb):
    global depthWeight
    global rgbWeight
    rgbWeight = float(percent_rgb)/100.0
    depthWeight = 1.0 - rgbWeight

pipeline = dai.Pipeline()
queueNames = []

camRgb = pipeline.create(dai.node.ColorCamera)
left = pipeline.create(dai.node.MonoCamera)
right = pipeline.create(dai.node.MonoCamera)
stereo = pipeline.create(dai.node.StereoDepth)

rgbOut = pipeline.create(dai.node.XLinkOut)
disparityOut = pipeline.create(dai.node.XLinkOut)

rgbOut.setStreamName("rgb")
queueNames.append("rgb")
disparityOut.setStreamName("disp")
queueNames.append("disp")

fps = 30

camRgb.setBoardSocket(dai.CameraBoardSocket.RGB)
camRgb.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
camRgb.setFps(fps)
camRgb.setIspScale(1, 3)
camRgb.initialControl.setManualFocus(48)

left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
left.setBoardSocket(dai.CameraBoardSocket.LEFT)
left.setFps(fps)

right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
right.setBoardSocket(dai.CameraBoardSocket.RIGHT)
right.setFps(fps)

stereo.initialConfig.setMedianFilter(dai.MedianFilter.MEDIAN_OFF)
stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_ACCURACY)
stereo.setLeftRightCheck(True)
stereo.setExtendedDisparity(False)
stereo.setSubpixel(False)
stereo.setDepthAlign(dai.CameraBoardSocket.RGB)

camRgb.isp.link(rgbOut.input)
left.out.link(stereo.left)
right.out.link(stereo.right)
stereo.disparity.link(disparityOut.input)

with dai.Device(pipeline) as device:

    frameRgb = None
    frameDisp = None

    rgbWindowName = "rgb"
    depthWindowName = "depth"
    blendedWindowName = "rgb-depth"
    cv2.namedWindow(rgbWindowName)
    cv2.namedWindow(depthWindowName)
    cv2.namedWindow(blendedWindowName)
    cv2.createTrackbar('RGB Weight %', blendedWindowName, int(rgbWeight*100), 100, updateBlendWeights)

    while True:
        latestPacket = {}
        latestPacket["rgb"] = None
        latestPacket["disp"] = None

        queueEvents = device.getQueueEvents(("rgb", "disp"))
        for queueName in queueEvents:
            packets = device.getOutputQueue(queueName).tryGetAll()
            if len(packets) > 0:
                latestPacket[queueName] = packets[-1]

        if latestPacket["rgb"] is not None:
            frameRgb = latestPacket["rgb"].getCvFrame()
            cv2.imshow(rgbWindowName, frameRgb)

        if latestPacket["disp"] is not None:
            frameDisp = latestPacket["disp"].getFrame()
            maxDisparity = stereo.initialConfig.getMaxDisparity()
            frameDisp = (frameDisp * 255. / maxDisparity).astype(np.uint8)
            frameDisp[frameDisp<128] = 0
            frameDisp = cv2.applyColorMap(frameDisp, cv2.COLORMAP_JET)
            frameDisp = np.ascontiguousarray(frameDisp)
            cv2.imshow(depthWindowName, frameDisp)

        if frameRgb is not None and frameDisp is not None:
            if len(frameDisp.shape) < 3:
                frameDisp = cv2.cvtColor(frameDisp, cv2.COLOR_GRAY2BGR)
            blended = cv2.addWeighted(frameRgb, rgbWeight, frameDisp, depthWeight, 0)
            cv2.imshow(blendedWindowName, blended)
            frameRgb = None
            frameDisp = None

        if cv2.waitKey(1) == ord('q'):
            break