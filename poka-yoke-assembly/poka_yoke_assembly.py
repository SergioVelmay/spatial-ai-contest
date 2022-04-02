import cv2
import depthai as dai
from datetime import datetime

class PokaYokeAssembly:
    def __init__(self):
        self.CurrentImage = None

    def CreatePrimaryPipeline(self):
        pipeline = dai.Pipeline()

        camera = pipeline.create(dai.node.ColorCamera)
        camera.setBoardSocket(dai.CameraBoardSocket.RGB)
        camera.setResolution(dai.ColorCameraProperties.SensorResolution.THE_13_MP)
        camera.setFps(30)
        camera.setIspScale(1, 1)
        camera.initialControl.setManualFocus(50)
        color_out = pipeline.create(dai.node.XLinkOut)
        color_out.setStreamName('RGB')
        camera.isp.link(color_out.input)

        return pipeline

    def CreateSecondaryPipeline(self):
        pipeline = dai.Pipeline()

        camera = pipeline.create(dai.node.ColorCamera)
        camera.setBoardSocket(dai.CameraBoardSocket.RGB)
        camera.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        camera.setFps(30)
        camera.setIspScale(1, 1)
        camera.initialControl.setManualFocus(65)
        color_out = pipeline.create(dai.node.XLinkOut)
        color_out.setStreamName('RGB')
        camera.isp.link(color_out.input)

        return pipeline

    def StartStreaming(self):
        device = dai.Device()
        device.startPipeline(self.CreateSecondaryPipeline())

        color_frame = None

        while True:
            latestPacket = {}
            latestPacket['RGB'] = None

            packets = device.getOutputQueue('RGB').tryGetAll()

            if len(packets) > 0:
                latestPacket['RGB'] = packets[-1]

            color_frame = None

            if latestPacket['RGB'] is not None:
                color_frame = latestPacket['RGB'].getCvFrame()
            
            if color_frame is not None:
                crop_image = color_frame[220:680, 780:1240]
                cv2.imshow("RGB Image", crop_image)
            
            key = cv2.waitKey(1)

            if key == ord('q'):
                break

def Main():
    device = PokaYokeAssembly()
    device.StartStreaming()

if __name__ == '__main__':
    Main()