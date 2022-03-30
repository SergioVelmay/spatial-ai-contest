import cv2
import numpy as np
import threading
import depthai as dai
import utils.mediapipe_utils as mpu
from pathlib import Path

class Detection:
    def __init__(self, drawImage: classmethod):
        self.DrawImage = drawImage
        self.QueueNames = []

        self.PalmInputLength = 128
        self.PalmScoreThreshold = 0.6
        self.PalmNmsThreshold = 0.3

        self.CountInputLength = 416
        self.CountScoreThreshold = 0.85
        self.CountNmsThreshold = 0.45

    def CreatePipeline(self):
        pipeline = dai.Pipeline()
        
        cam_color = pipeline.create(dai.node.ColorCamera)
        cam_left = pipeline.create(dai.node.MonoCamera)
        cam_right = pipeline.create(dai.node.MonoCamera)
        stereo_depth = pipeline.create(dai.node.StereoDepth)

        color_out = pipeline.create(dai.node.XLinkOut)
        depth_out = pipeline.create(dai.node.XLinkOut)

        color_out.setStreamName("color")
        self.QueueNames.append("color")
        depth_out.setStreamName("depth")
        self.QueueNames.append("depth")

        fps = 30

        cam_color.setBoardSocket(dai.CameraBoardSocket.RGB)
        cam_color.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        cam_color.setFps(fps)
        cam_color.setIspScale(1, 3)
        cam_color.initialControl.setManualFocus(48)

        cam_left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        cam_left.setBoardSocket(dai.CameraBoardSocket.LEFT)
        cam_left.setFps(fps)

        cam_right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        cam_right.setBoardSocket(dai.CameraBoardSocket.RIGHT)
        cam_right.setFps(fps)

        stereo_depth.initialConfig.setMedianFilter(dai.MedianFilter.MEDIAN_OFF)
        stereo_depth.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_ACCURACY)
        stereo_depth.setLeftRightCheck(True)
        stereo_depth.setExtendedDisparity(False)
        stereo_depth.setSubpixel(False)
        stereo_depth.setDepthAlign(dai.CameraBoardSocket.RGB)
        
        self.MaxDisparity = stereo_depth.initialConfig.getMaxDisparity()

        cam_color.isp.link(color_out.input)
        cam_left.out.link(stereo_depth.left)
        cam_right.out.link(stereo_depth.right)
        stereo_depth.disparity.link(depth_out.input)

        palm_nn = pipeline.createNeuralNetwork()
        palm_nn.setBlobPath(str(Path("models/palm_detection.blob").resolve().absolute()))
        palm_in = pipeline.createXLinkIn()
        palm_in.setStreamName("palm_in")
        palm_in.out.link(palm_nn.input)
        palm_out = pipeline.createXLinkOut()
        palm_out.setStreamName("palm_out")
        palm_nn.out.link(palm_out.input)

        count_nn = pipeline.createNeuralNetwork()
        count_nn.setBlobPath(str(Path("models/count_detection.blob").resolve().absolute()))
        count_in = pipeline.createXLinkIn()
        count_in.setStreamName("count_in")
        count_in.out.link(count_nn.input)
        count_out = pipeline.createXLinkOut()
        count_out.setStreamName("count_out")
        count_nn.out.link(count_out.input)

        return pipeline
    
    def ToPlanar(self, array, shape):
        resized = cv2.resize(array, shape, interpolation=cv2.INTER_NEAREST).transpose(2,0,1)
        return resized

    def PalmPostprocess(self, inference):
        anchor_options = mpu.SSDAnchorOptions(
            num_layers=4, 
            min_scale=0.1484375,
            max_scale=0.75,
            input_size_height=128,
            input_size_width=128,
            anchor_offset_x=0.5,
            anchor_offset_y=0.5,
            strides=[8, 16, 16, 16],
            aspect_ratios= [1.0],
            reduce_boxes_in_lowest_layer=False,
            interpolated_scale_aspect_ratio=1.0,
            fixed_anchor_size=True)

        anchors = mpu.generate_anchors(anchor_options)
        
        nb_anchors = anchors.shape[0]

        scores = np.array(inference.getLayerFp16("classificators"), dtype=np.float16) 
        boxes = np.array(inference.getLayerFp16("regressors"), dtype=np.float16).reshape((nb_anchors, 18))
        
        self.regions_palm = mpu.decode_bboxes(self.PalmScoreThreshold, scores, boxes, anchors)
        self.regions_palm = mpu.non_max_suppression(self.regions_palm, self.PalmNmsThreshold)

        mpu.detections_to_rect(self.regions_palm)
        mpu.rect_transformation(self.regions_palm, self.frame_size, self.frame_size)

    def GetRectFromRegion(self, frame: np.ndarray, region: mpu.HandRegion):
        x1_float = region.pd_box[0]
        y1_float = region.pd_box[1]
        x2_float = x1_float + region.pd_box[2]
        y2_float = y1_float + region.pd_box[3]
        h, w = frame.shape[:2]
        frame_size = max(h, w)
        pad_h = int((frame_size - h)/2)
        pad_w = int((frame_size - w)/2)
        x1 = int(x1_float*frame_size) - pad_w
        y1 = int(y1_float*frame_size) - pad_h
        x2 = int(x2_float*frame_size) - pad_w
        y2 = int(y2_float*frame_size) - pad_h
        return x1, y1, x2, y2

    def CalculateRectFromRegion(self, color_image: np.ndarray, region: mpu.HandRegion):
        x1, y1, x2, y2 = self.GetRectFromRegion(color_image, region)
        return x1, y1, x2, y2

    def StartMainLoop(self):
        threading.Thread(target=self.Run, daemon=True).start()

    def Run(self):
        device = dai.Device(self.CreatePipeline())
        device.startPipeline()

        frame_color = None
        frame_depth = None

        q_palm_in = device.getInputQueue(name="palm_in")
        q_palm_out = device.getOutputQueue(name="palm_out", maxSize=4, blocking=True)

        q_count_in = device.getInputQueue(name="count_in")
        q_count_out = device.getOutputQueue(name="count_out", maxSize=4, blocking=True)

        while True:
            latestPacket = {}
            latestPacket["color"] = None
            latestPacket["depth"] = None

            queueEvents = device.getQueueEvents(("color", "depth"))
            for queueName in queueEvents:
                packets = device.getOutputQueue(queueName).tryGetAll()
                if len(packets) > 0:
                    latestPacket[queueName] = packets[-1]

            color_image_copy = None

            if latestPacket["color"] is not None:
                frame_color = latestPacket["color"].getCvFrame()

                h, w = frame_color.shape[:2]
                self.frame_size = max(h, w)
                self.pad_h = int((self.frame_size - h)/2)
                self.pad_w = int((self.frame_size - w)/2)

                color_image_copy = cv2.copyMakeBorder(frame_color, self.pad_h, self.pad_h, self.pad_w, self.pad_w, cv2.BORDER_CONSTANT)
                
                frame_nn_palm = dai.ImgFrame()
                frame_nn_palm.setWidth(self.PalmInputLength)
                frame_nn_palm.setHeight(self.PalmInputLength)
                frame_nn_palm.setData(self.ToPlanar(color_image_copy, (self.PalmInputLength, self.PalmInputLength)))
                q_palm_in.send(frame_nn_palm)
                
                inference = q_palm_out.get()
                self.PalmPostprocess(inference)

                palm_image = None

                for region in self.regions_palm:
                    xMin, yMin, xMax, yMax = self.CalculateRectFromRegion(frame_color, region)
                    y_percentage = int((yMax-yMin)*0.125)
                    x_percentage = int((xMax-xMin)*0.125)
                    palm_image = frame_color[yMin-(2*y_percentage):yMax, xMin-x_percentage:xMax[2]+x_percentage]

                self.regions_count = None

                if palm_image is not None:

                    frame_nn_count = dai.ImgFrame()
                    frame_nn_count.setWidth(self.CountInputLength)
                    frame_nn_count.setHeight(self.CountInputLength)
                    frame_nn_count.setData(self.ToPlanar(color_image_copy, (self.CountInputLength, self.CountInputLength)))
                    q_count_in.send(frame_nn_count)
                    
                    inference = q_count_out.get()
                    self.CountPostprocess(inference)
            
            if latestPacket["depth"] is not None:
                frame_depth = latestPacket["depth"].getFrame()
                frame_depth = (frame_depth * 255. / self.MaxDisparity).astype(np.uint8)
                frame_depth[frame_depth<128] = 0
                frame_depth = cv2.applyColorMap(frame_depth, cv2.COLORMAP_JET)
                frame_depth = np.ascontiguousarray(frame_depth)

            if frame_color is not None and frame_depth is not None:
                self.DrawImage(frame_color, frame_depth, self.regions_palm)
                frame_color = None
                frame_depth = None