import cv2
import threading
import depthai as dai
from pathlib import Path

from utils.model_utils import *

class AssemblyCameras:
    def __init__(self, drawImages: classmethod):
        self.DrawImages = drawImages

        self.primary_stream = 'primary'
        self.secondary_stream = 'secondary'

        self.primary_device_id = '1844301041F08B1200'
        self.secondary_device_id = '1844301051CC711200'

        self.primary_device = None
        self.secondary_device = None

        self.classify_in_stream = 'classify_in'
        self.classify_out_stream = 'classify_out'
        self.detect_in_stream = 'detect_in'
        self.detect_out_stream = 'detect_out'

        self.classify_input_length = 224
        self.detect_input_length = 416

        self.window_image_size = (400, 400)

        self.primary_image = None
        self.model_image = None
        self.secondary_image = None

        self.classify_predictions = []
        self.detect_predictions = []

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

        classify_nn = pipeline.createNeuralNetwork()
        classify_nn.setBlobPath(str(Path('./models/classify-model.blob').resolve().absolute()))
        classify_in = pipeline.createXLinkIn()
        classify_in.setStreamName(self.classify_in_stream)
        classify_in.out.link(classify_nn.input)
        classify_out = pipeline.createXLinkOut()
        classify_out.setStreamName(self.classify_out_stream)
        classify_nn.out.link(classify_out.input)

        detect_nn = pipeline.createNeuralNetwork()
        detect_nn.setBlobPath(str(Path('./models/detect-model.blob').resolve().absolute()))
        detect_in = pipeline.createXLinkIn()
        detect_in.setStreamName(self.detect_in_stream)
        detect_in.out.link(detect_nn.input)
        detect_out = pipeline.createXLinkOut()
        detect_out.setStreamName(self.detect_out_stream)
        detect_nn.out.link(detect_out.input)

        return pipeline
    
    def StartMainLoop(self):
        threading.Thread(target=self.Run, daemon=True).start()

    def Run(self):
        devices = dai.Device.getAllAvailableDevices()

        if len(devices) == 0:
            raise RuntimeError('No devices found!')

        for device_info in devices:
            if device_info.getMxId() == self.primary_device_id:
                self.primary_device = dai.Device(dai.OpenVINO.Version.VERSION_2021_4, device_info, False)
                self.primary_device.startPipeline(self.CreatePrimaryPipeline())
            elif device_info.getMxId() == self.secondary_device_id:
                self.secondary_device = dai.Device(dai.OpenVINO.Version.VERSION_2021_4, device_info, False)
                self.secondary_device.startPipeline(self.CreateSecondaryPipeline())
            else:
                raise RuntimeError('Device unknown!')
        
        if self.primary_device is None:
            raise RuntimeError('No primary device found!')

        if self.secondary_device is None:
            raise RuntimeError('No secondary device found!')
        
        queue_classify_in = self.secondary_device.getInputQueue(name=self.classify_in_stream)
        queue_classify_out = self.secondary_device.getOutputQueue(name=self.classify_out_stream, maxSize=4, blocking=True)

        queue_detect_in = self.secondary_device.getInputQueue(name=self.detect_in_stream)
        queue_detect_out = self.secondary_device.getOutputQueue(name=self.detect_out_stream, maxSize=4, blocking=True)

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
                self.primary_image = cv2.resize(primary_crop, self.window_image_size, interpolation=cv2.INTER_AREA)

                # Model Image 224x224 --> 400x400 & 416x416
                model_crop = primary_frame[1443:1667, 2011:2235]

                image_classify_data = ImagePreprocess(model_crop, (self.classify_input_length, self.classify_input_length))
                frame_classify_nn = dai.ImgFrame()
                frame_classify_nn.setWidth(self.classify_input_length)
                frame_classify_nn.setHeight(self.classify_input_length)
                frame_classify_nn.setData(image_classify_data)
                queue_classify_in.send(frame_classify_nn)

                classify_inference = queue_classify_out.get()

                if classify_inference is not None:
                    classify_layer_names = classify_inference.getAllLayerNames()
                    classify_layer_float = classify_inference.getLayerFp16(classify_layer_names[0])
                    self.classify_predictions = ClassifyPostprocess(classify_layer_float)

                image_detect_data = ImagePreprocess(model_crop, (self.detect_input_length, self.detect_input_length))
                frame_detect_nn = dai.ImgFrame()
                frame_detect_nn.setWidth(self.detect_input_length)
                frame_detect_nn.setHeight(self.detect_input_length)
                frame_detect_nn.setData(image_detect_data)
                queue_detect_in.send(frame_detect_nn)

                detect_inference = queue_detect_out.get()

                if detect_inference is not None:
                    detect_layer_names = detect_inference.getAllLayerNames()
                    detect_layer_float = detect_inference.getLayerFp16(detect_layer_names[0])
                    self.detect_predictions = DetectPostprocess(detect_layer_float)

                self.model_image = cv2.resize(model_crop, self.window_image_size, interpolation=cv2.INTER_AREA)
            
            if secondary_frame is not None:
                # Secondary Image 460x460 --> 400x400
                secondary_crop = secondary_frame[220:680, 780:1240]
                self.secondary_image = cv2.resize(secondary_crop, self.window_image_size, interpolation=cv2.INTER_AREA)
            
            if self.primary_image is not None and self.model_image is not None and self.secondary_image is not None:
                self.DrawImages(self.primary_image, self.model_image, self.secondary_image, self.classify_predictions, self.detect_predictions)