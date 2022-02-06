import cv2
import numpy as np
import depthai as dai
import mediapipe_utils as mpu
from pathlib import Path

class DepthCalculation:
    def __init__(self):
        self.colorWeight = 0.5
        self.depthWeight = 0.5
        self.queueNames = []

        self.palm_input_length = 128
        self.palm_score_threshold = 0.6
        self.palm_nms_threshold = 0.3

    def create_pipeline(self):
        pipeline = dai.Pipeline()
        
        camColor = pipeline.create(dai.node.ColorCamera)
        left = pipeline.create(dai.node.MonoCamera)
        right = pipeline.create(dai.node.MonoCamera)
        stereo = pipeline.create(dai.node.StereoDepth)

        colorOut = pipeline.create(dai.node.XLinkOut)
        disparityOut = pipeline.create(dai.node.XLinkOut)

        colorOut.setStreamName("color")
        self.queueNames.append("color")
        disparityOut.setStreamName("depth")
        self.queueNames.append("depth")

        fps = 30

        camColor.setBoardSocket(dai.CameraBoardSocket.RGB)
        camColor.setResolution(dai.ColorCameraProperties.SensorResolution.THE_1080_P)
        camColor.setFps(fps)
        camColor.setIspScale(1, 3)
        camColor.initialControl.setManualFocus(48)

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
        
        self.maxDisparity = stereo.initialConfig.getMaxDisparity()

        camColor.isp.link(colorOut.input)
        left.out.link(stereo.left)
        right.out.link(stereo.right)
        stereo.disparity.link(disparityOut.input)

        palm_nn = pipeline.createNeuralNetwork()
        palm_nn.setBlobPath(str(Path("models/palm_detection.blob").resolve().absolute()))
        palm_in = pipeline.createXLinkIn()
        palm_in.setStreamName("palm_in")
        palm_in.out.link(palm_nn.input)
        palm_out = pipeline.createXLinkOut()
        palm_out.setStreamName("palm_out")
        palm_nn.out.link(palm_out.input)

        return pipeline
    
    def to_planar(self, arr, shape):
        resized = cv2.resize(arr, shape, interpolation=cv2.INTER_NEAREST).transpose(2,0,1)
        return resized

    def updateBlendWeights(self, percent_color):
        global depthWeight
        global colorWeight
        colorWeight = float(percent_color)/100.0
        depthWeight = 1.0 - colorWeight

    def palm_postprocess(self, inference):
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
        bboxes = np.array(inference.getLayerFp16("regressors"), dtype=np.float16).reshape((nb_anchors, 18))
        
        self.regions = mpu.decode_bboxes(self.palm_score_threshold, scores, bboxes, anchors)
        self.regions = mpu.non_max_suppression(self.regions, self.palm_nms_threshold)

        mpu.detections_to_rect(self.regions)
        mpu.rect_transformation(self.regions, self.frame_size, self.frame_size)

    def run(self):
        device = dai.Device(self.create_pipeline())
        device.startPipeline()

        frameColor = None
        frameDisp = None

        colorWindowName = "color"
        depthWindowName = "depth"
        blendedWindowName = "color-depth"
        cv2.namedWindow(colorWindowName)
        cv2.namedWindow(depthWindowName)
        cv2.namedWindow(blendedWindowName)
        cv2.createTrackbar('RGB Weight %', blendedWindowName, int(self.colorWeight*100), 100, self.updateBlendWeights)

        q_palm_in = device.getInputQueue(name="palm_in")
        q_palm_out = device.getOutputQueue(name="palm_out", maxSize=4, blocking=True)

        while True:
            latestPacket = {}
            latestPacket["color"] = None
            latestPacket["depth"] = None

            queueEvents = device.getQueueEvents(("color", "depth"))
            for queueName in queueEvents:
                packets = device.getOutputQueue(queueName).tryGetAll()
                if len(packets) > 0:
                    latestPacket[queueName] = packets[-1]

            copiaColor = None

            if latestPacket["color"] is not None:
                frameColor = latestPacket["color"].getCvFrame()

                h, w = frameColor.shape[:2]
                self.frame_size = max(h, w)
                self.pad_h = int((self.frame_size - h)/2)
                self.pad_w = int((self.frame_size - w)/2)

                copiaColor = cv2.copyMakeBorder(frameColor, self.pad_h, self.pad_h, self.pad_w, self.pad_w, cv2.BORDER_CONSTANT)
                
                frame_nn = dai.ImgFrame()
                frame_nn.setWidth(self.palm_input_length)
                frame_nn.setHeight(self.palm_input_length)
                frame_nn.setData(self.to_planar(copiaColor, (self.palm_input_length, self.palm_input_length)))
                q_palm_in.send(frame_nn)
                
                inference = q_palm_out.get()
                self.palm_postprocess(inference)

                for i, region in enumerate(self.regions):
                    self.draw_palm_rectangle(frameColor, copiaColor, region)

                cv2.imshow(colorWindowName, frameColor)
            
            if latestPacket["depth"] is not None:
                frameDisp = latestPacket["depth"].getFrame()
                frameDisp = (frameDisp * 255. / self.maxDisparity).astype(np.uint8)
                frameDisp[frameDisp<128] = 0
                frameDisp = cv2.applyColorMap(frameDisp, cv2.COLORMAP_JET)
                frameDisp = np.ascontiguousarray(frameDisp)

                for i, region in enumerate(self.regions):
                    self.averageDepth, self.centroidX, self.centroidY = self.calc_spatials(self.x1, self.y1, self.x2, self.y2, frameDisp)

                    xmin, ymin, xmax, ymax = self.get_roi_by_percent(0.5, self.x1, self.y1, self.x2, self.y2)

                    cv2.rectangle(frameDisp, (xmin, ymin), (xmax, ymax), (255, 255, 255), 2)

                    self.draw_palm_text(frameDisp, self.averageDepth, self.centroidX-10, self.centroidY)

                cv2.imshow(depthWindowName, frameDisp)

            if frameColor is not None and frameDisp is not None:
                if len(frameDisp.shape) < 3:
                    frameDisp = cv2.cvtColor(frameDisp, cv2.COLOR_GRAY2BGR)
                blended = cv2.addWeighted(frameColor, self.colorWeight, frameDisp, self.depthWeight, 0)
                cv2.imshow(blendedWindowName, blended)
                frameColor = None
                frameDisp = None

            if cv2.waitKey(1) == ord('q'):
                break

    def draw_palm_rectangle(self, frame, copy, region):
        x1_float = region.pd_box[0]
        y1_float = region.pd_box[1]
        x2_float = x1_float + region.pd_box[2]
        y2_float = y1_float + region.pd_box[3]
        new_h, new_w = copy.shape[:2]
        self.x1 = int(x1_float*new_w) - self.pad_w
        self.y1 = int(y1_float*new_h) - self.pad_h
        self.x2 = int(x2_float*new_w) - self.pad_w
        self.y2 = int(y2_float*new_h) - self.pad_h
        cv2.rectangle(frame, (self.x1, self.y1), (self.x2, self.y2), (255, 255, 255), 2)
    
    def draw_palm_text(self, frame, depth, pt1, pt2):
        cv2.putText(frame, str(depth), (pt1, pt2), cv2.FONT_HERSHEY_DUPLEX, 0.4, (255, 255, 255))
    
    def calc_spatials(self, xmin, ymin, xmax, ymax, depth):
        xmin, ymin, xmax, ymax = self.get_roi_by_percent(0.5, xmin, ymin, xmax, ymax)

        depthROI = depth[ymin:ymax, xmin:xmax]

        averageDepth = int(np.mean(depthROI[True]))

        centroidX = int((xmax - xmin) / 2) + xmin
        centroidY = int((ymax - ymin) / 2) + ymin

        return (averageDepth, centroidX, centroidY)

    def get_roi_by_percent(self, percent, xmin, ymin, xmax, ymax):
        deltaX = int((xmax - xmin) * percent / 2)
        deltaY = int((ymax - ymin) * percent / 2)
        xmin += deltaX
        ymin += deltaY
        xmax -= deltaX
        ymax -= deltaY
        return xmin, ymin, xmax, ymax

if __name__ == "__main__":
    depth_calculation = DepthCalculation()
    depth_calculation.run()