import cv2
import numpy as np
import threading
import depthai as dai

class AssemblyCameras:
    def __init__(self, drawImages: classmethod):
        self.DrawImages = drawImages

        self.primary_device_id = '1844301041F08B1200'
        self.secondary_device_id = '1844301051CC711200'

        self.primary_device = None
        self.secondary_device = None

        self.primary_stream = 'primary'
        self.secondary_stream = 'secondary'

        self.primary_image = None
        self.model_image = None
        self.secondary_image = None

    def CreatePrimaryPipeline(self):
        pipeline = dai.Pipeline()

        camera = pipeline.create(dai.node.ColorCamera)
        camera.setBoardSocket(dai.CameraBoardSocket.RGB)
        camera.setResolution(dai.ColorCameraProperties.SensorResolution.THE_13_MP)
        camera.initialControl.setManualFocus(50)
        color_out = pipeline.create(dai.node.XLinkOut)
        color_out.setStreamName(self.primary_stream)
        camera.isp.link(color_out.input)

        return pipeline

    def CreateSecondaryPipeline(self):
        pipeline = dai.Pipeline()

        camera = pipeline.create(dai.node.ColorCamera)
        camera.setBoardSocket(dai.CameraBoardSocket.RGB)
        camera.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        camera.initialControl.setManualFocus(65)
        color_out = pipeline.create(dai.node.XLinkOut)
        color_out.setStreamName(self.secondary_stream)
        camera.isp.link(color_out.input)

        return pipeline
    
    def StartMainLoop(self):
        threading.Thread(target=self.Run, daemon=True).start()

    def Run(self):
        devices = dai.Device.getAllAvailableDevices()

        if len(devices) == 0:
            raise RuntimeError("No devices found!")

        for device_info in devices:
            if device_info.getMxId() == self.primary_device_id:
                self.primary_device = dai.Device(dai.OpenVINO.Version.VERSION_2021_4, device_info, False)
                self.primary_device.startPipeline(self.CreatePrimaryPipeline())
            elif device_info.getMxId() == self.secondary_device_id:
                self.secondary_device = dai.Device(dai.OpenVINO.Version.VERSION_2021_4, device_info, False)
                self.secondary_device.startPipeline(self.CreateSecondaryPipeline())
            else:
                raise RuntimeError("Device unknown!")
        
        if self.primary_device is None:
            raise RuntimeError("No primary device found!")

        if self.primary_device is None:
            raise RuntimeError("No secondary device found!")

        while True:
            latestPacket = {}
            latestPacket[self.primary_stream] = None
            latestPacket[self.secondary_stream] = None

            primary_packets = self.primary_device.getOutputQueue(self.primary_stream).tryGetAll()
            secondary_packets = self.secondary_device.getOutputQueue(self.secondary_stream).tryGetAll()

            if len(primary_packets) > 0:
                latestPacket[self.primary_stream] = primary_packets[-1]
            
            if len(secondary_packets) > 0:
                latestPacket[self.secondary_stream] = secondary_packets[-1]

            primary_frame = None
            secondary_frame = None

            if latestPacket[self.primary_stream] is not None:
                primary_frame = latestPacket[self.primary_stream].getCvFrame()
            
            if latestPacket[self.secondary_stream] is not None:
                secondary_frame = latestPacket[self.secondary_stream].getCvFrame()
            
            if primary_frame is not None:
                # Primary Image 1600x1600 --> 400x400
                primary_crop = primary_frame[775:2375, 1348:2948]
                self.primary_image = cv2.resize(primary_crop, (400, 400), interpolation=cv2.INTER_AREA)

                # Model Image 224x224 --> 400x400 & 416x416
                model_crop = primary_frame[1443:1667, 2011:2235]
                if False:
                    model_detect = cv2.resize(model_crop, (416, 416), interpolation=cv2.INTER_AREA)
                self.model_image = cv2.resize(model_crop, (400, 400), interpolation=cv2.INTER_AREA)
            
            if secondary_frame is not None:
                # Secondary Image 460x460 --> 400x400
                secondary_crop = secondary_frame[220:680, 780:1240]
                self.secondary_image = cv2.resize(secondary_crop, (400, 400), interpolation=cv2.INTER_AREA)
            
            if self.primary_image is not None and self.model_image is not None and self.secondary_image is not None:
                self.DrawImages(self.primary_image, self.model_image, self.secondary_image)