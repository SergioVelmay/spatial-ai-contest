import numpy as np
import collections
import mediapipe_utils as mpu
import depthai as dai
import cv2
from pathlib import Path
import time
import argparse

def to_planar(arr: np.ndarray, shape: tuple) -> np.ndarray:
    resized = cv2.resize(arr, shape, interpolation=cv2.INTER_NEAREST).transpose(2,0,1)
    return resized

class HandLandmarks:
    def __init__(self,
                pd_path="models/palm_detection.blob", 
                pd_score_threshold=0.5,
                pd_nms_threshold=0.3,
                hl_path="models/hand_landmarks.blob",
                hl_score_threshold=0.4,
                show_landmarks=True,
                show_hand_box=False):

        self.pd_path = pd_path
        self.pd_score_threshold = pd_score_threshold
        self.pd_nms_threshold = pd_nms_threshold
        self.hl_path = hl_path
        self.hl_score_threshold = hl_score_threshold
        self.show_landmarks=show_landmarks
        self.show_hand_box = show_hand_box

        anchor_options = mpu.SSDAnchorOptions(num_layers=4, 
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

        self.anchors = mpu.generate_anchors(anchor_options)
        self.nb_anchors = self.anchors.shape[0]

        self.preview_width = 1280
        self.preview_height = 720

        self.frame_size = None

        self.right_char_queue = collections.deque(maxlen=5)
        self.left_char_queue = collections.deque(maxlen=5)

        self.previous_right_char = ""
        self.right_sentence = ""
        self.previous_right_update_time = time.time()
        self.previous_left_char = ""
        self.left_sentence = ""
        self.previous_left_update_time = time.time()

    def create_pipeline(self):
        pipeline = dai.Pipeline()
        pipeline.setOpenVINOVersion(version=dai.OpenVINO.Version.VERSION_2021_2)
        self.pd_input_length = 128

        cam = pipeline.createColorCamera()
        cam.setPreviewSize(self.preview_width, self.preview_height)
        cam.setInterleaved(False)
        cam.setBoardSocket(dai.CameraBoardSocket.RGB)
        cam_out = pipeline.createXLinkOut()
        cam_out.setStreamName("cam_out")
        cam.preview.link(cam_out.input)

        pd_nn = pipeline.createNeuralNetwork()
        pd_nn.setBlobPath(str(Path(self.pd_path).resolve().absolute()))
        pd_in = pipeline.createXLinkIn()
        pd_in.setStreamName("pd_in")
        pd_in.out.link(pd_nn.input)
        pd_out = pipeline.createXLinkOut()
        pd_out.setStreamName("pd_out")
        pd_nn.out.link(pd_out.input)

        hl_nn = pipeline.createNeuralNetwork()
        hl_nn.setBlobPath(str(Path(self.hl_path).resolve().absolute()))
        self.hl_input_length = 224
        hl_in = pipeline.createXLinkIn()
        hl_in.setStreamName("hl_in")
        hl_in.out.link(hl_nn.input)
        hl_out = pipeline.createXLinkOut()
        hl_out.setStreamName("hl_out")
        hl_nn.out.link(hl_out.input)

        return pipeline

    def pd_postprocess(self, inference):
        scores = np.array(inference.getLayerFp16("classificators"), dtype=np.float16) 
        bboxes = np.array(inference.getLayerFp16("regressors"), dtype=np.float16).reshape((self.nb_anchors,18)) 
        
        self.regions = mpu.decode_bboxes(self.pd_score_threshold, scores, bboxes, self.anchors)
        
        self.regions = mpu.non_max_suppression(self.regions, self.pd_nms_threshold)
        mpu.detections_to_rect(self.regions)
        mpu.rect_transformation(self.regions, self.frame_size, self.frame_size)

    def hl_postprocess(self, region, inference):
        region.hl_score = inference.getLayerFp16("Identity_1")[0]    
        region.handedness = inference.getLayerFp16("Identity_2")[0]
        hl_raw = np.array(inference.getLayerFp16("Squeeze"))
        
        hl = []
        for i in range(int(len(hl_raw)/3)):
            
            hl.append(hl_raw[3*i:3*(i+1)]/self.hl_input_length)
        region.landmarks = hl

    def hl_render(self, frame, original_frame, region):
        cropped_frame = None
        hand_bbox = []
        palmar_text = ""
        if region.hl_score > self.hl_score_threshold:
            palmar = True
            src = np.array([(0, 0), (1, 0), (1, 1)], dtype=np.float32)
            dst = np.array([ (x, y) for x,y in region.rect_points[1:]], dtype=np.float32) 
            mat = cv2.getAffineTransform(src, dst)
            hl_xy = np.expand_dims(np.array([(l[0], l[1]) for l in region.landmarks]), axis=0)
            hl_xy = np.squeeze(cv2.transform(hl_xy, mat)).astype(np.int)
            
            if self.show_landmarks:
                list_connections = [[0, 1, 2, 3, 4], 
                                    [5, 6, 7, 8], 
                                    [9, 10, 11, 12],
                                    [13, 14 , 15, 16],
                                    [17, 18, 19, 20]]
                palm_line = [np.array([hl_xy[point] for point in [0, 5, 9, 13, 17, 0]])]
                
                cv2.polylines(frame, palm_line, False, (255, 255, 255), 1, cv2.LINE_AA)
                
                for i in range(len(list_connections)):
                    finger = list_connections[i]
                    line = [np.array([hl_xy[point] for point in finger])]

                    cv2.polylines(frame, line, False, (255, 255, 255), 1, cv2.LINE_AA)

                    for point in finger:
                            pt = hl_xy[point]
                            cv2.drawMarker(frame, (pt[0], pt[1]), (0, 0, 0), cv2.MARKER_CROSS, 5, 1, cv2.LINE_AA)

            if region.handedness > 0.5:
                palmar_text = "Right: "
            else:
                palmar_text = "Left: "
            if palmar:
                palmar_text = palmar_text + "Palmar"
            else:
                palmar_text = palmar_text + "Dorsal"

            max_x = 0
            max_y = 0
            min_x = frame.shape[1]
            min_y = frame.shape[0]
            for x,y in hl_xy:
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y

            box_width = max_x - min_x
            box_height = max_y - min_y
            x_center = min_x + box_width / 2
            y_center = min_y + box_height / 2

            draw_width = box_width/2 * 1.2
            draw_height = box_height/2 * 1.2
            draw_size = max(draw_width, draw_height)

            draw_min_x = int(x_center - draw_size)
            draw_min_y = int(y_center - draw_size)
            draw_max_x = int(x_center + draw_size)
            draw_max_y = int(y_center + draw_size)

            hand_bbox = [draw_min_x, draw_min_y, draw_max_x, draw_max_y]

            if self.show_hand_box:
                cv2.rectangle(frame, (draw_min_x, draw_min_y), (draw_max_x, draw_max_y), (36, 152, 0), 2)

        return cropped_frame, region.handedness, hand_bbox, palmar_text

    def run(self):
        device = dai.Device(self.create_pipeline())
        device.startPipeline()

        q_video_out = device.getOutputQueue(name="cam_out", maxSize=1, blocking=False)
        q_pd_in = device.getInputQueue(name="pd_in")
        q_pd_out = device.getOutputQueue(name="pd_out", maxSize=4, blocking=True)
        q_hl_in = device.getInputQueue(name="hl_in")
        q_hl_out = device.getOutputQueue(name="hl_out", maxSize=4, blocking=True)

        while True:
            in_video = q_video_out.get()
            video_frame = in_video.getCvFrame()

            h, w = video_frame.shape[:2]
            self.frame_size = max(h, w)
            self.pad_h = int((self.frame_size - h)/2)
            self.pad_w = int((self.frame_size - w)/2)

            video_frame = cv2.copyMakeBorder(video_frame, self.pad_h, self.pad_h, self.pad_w, self.pad_w, cv2.BORDER_CONSTANT)
            
            frame_nn = dai.ImgFrame()
            frame_nn.setWidth(self.pd_input_length)
            frame_nn.setHeight(self.pd_input_length)
            frame_nn.setData(to_planar(video_frame, (self.pd_input_length, self.pd_input_length)))
            q_pd_in.send(frame_nn)

            annotated_frame = video_frame.copy()
            
            inference = q_pd_out.get()
            self.pd_postprocess(inference)

            for i,r in enumerate(self.regions):
                img_hand = mpu.warp_rect_img(r.rect_points, video_frame, self.hl_input_length, self.hl_input_length)
                nn_data = dai.NNData()   
                nn_data.setLayer("input_1", to_planar(img_hand, (self.hl_input_length, self.hl_input_length)))
                q_hl_in.send(nn_data)

            for i,r in enumerate(self.regions):
                inference = q_hl_out.get()
                self.hl_postprocess(r, inference)
                hand_frame, handedness, hand_bbox, palmar_text = self.hl_render(video_frame, annotated_frame, r)

            video_frame = video_frame[self.pad_h:self.pad_h+h, self.pad_w:self.pad_w+w]
            cv2.imshow("Hand Landmarks", video_frame)
            key = cv2.waitKey(1) 
            if key == ord('q') or key == 27:
                break

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pd_m", default="models/palm_detection.blob", type=str,
                        help="Path to a blob file for palm detection model (default=%(default)s)")
    parser.add_argument("--hl_m", default="models/hand_landmarks.blob", type=str,
                        help="Path to a blob file for hand landmarks model (default=%(default)s)")
    args = parser.parse_args()

    hand_landmarks = HandLandmarks(pd_path=args.pd_m, hl_path=args.hl_m)
    hand_landmarks.run()