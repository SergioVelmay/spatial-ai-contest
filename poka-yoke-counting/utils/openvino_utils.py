import cv2
import numpy as np
from openvino.inference_engine import IECore

class Classification:

    def __init__(self, label, score):
        self.Label = label
        self.Score = score

class Boundary:

    def __init__(self, x, y, w, h):
        self.Left = x
        self.Top = y
        self.Width = w
        self.Height = h

class Detection(Classification):

    def __init__(self, label, score, x, y, w, h):
        Classification.__init__(self, label, score)
        self.Box = Boundary(x, y, w, h)

class ObjectDetection():

    ANCHOR_BOXES = np.array([[0.573, 0.677], [1.87, 2.06], [3.34, 5.47], [7.88, 3.53], [9.77, 9.17]])
    IOU_THRESHOLD = 0.5

    def __init__(self):
        model_path = 'models/'
        model_xml = model_path + 'part_counting.xml'
        model_bin = model_path + 'part_counting.bin'
        model_labels = model_path + 'part_labels.txt'

        self.prob_threshold = 0.85
        self.max_detections = 5

        with open(model_labels, 'r') as io:
            self.labels = [label[2:] for label in io]

        inference_engine = IECore()

        network = inference_engine.read_network(model=model_xml, weights=model_bin)

        network.batch_size = 1

        self.input_blob = next(iter(network.input_info))
        self.output_blob = next(iter(network.outputs))

        n, c, h, w = network.inputs[self.input_blob].shape

        self.exec_network = inference_engine.load_network(network=network, device_name='MYRIAD')

        self.images = np.ndarray(shape=(n, c, h, w))

    def Infer(self, image):
        self.images[0] = self._preprocess(image)

        result = self.exec_network.infer(inputs={self.input_blob: self.images})

        outputs = result[self.output_blob]

        return self._postprocess(outputs)

    def _preprocess(self, image):
        resized_image = cv2.resize(image, (416, 416), interpolation=cv2.INTER_AREA)

        input_image = resized_image.transpose((2, 0, 1))

        return input_image

    def _postprocess(self, outputs):
        outputs = np.squeeze(outputs).transpose((1,2,0)).astype(np.float32)

        boxes, class_probs = self._extract_bounding_boxes(outputs)

        max_probs = np.amax(class_probs, axis=1)
        index, = np.where(max_probs > self.prob_threshold)
        index = index[(-max_probs[index]).argsort()]

        selected_boxes, selected_classes, selected_probs = self._non_maximum_suppression(
            boxes[index], class_probs[index])

        predictions = list()

        for i in range(len(selected_boxes)):
            label = self.labels[selected_classes[i]]
            probability = selected_probs[i] * 100
            left = round(float(selected_boxes[i][0]), 8)
            top = round(float(selected_boxes[i][1]), 8)
            width = round(float(selected_boxes[i][2]), 8)
            height = round(float(selected_boxes[i][3]), 3)
            prediction = Detection(label, probability, left, top, width, height)
            predictions.append(prediction)

        return predictions

    def _extract_bounding_boxes(self, output):
        num_anchor = self.ANCHOR_BOXES.shape[0]
        height, width, channels = output.shape
        num_class = int(channels / num_anchor) - 5

        outputs = output.reshape((height, width, num_anchor, -1))

        x = (self._logistic(outputs[..., 0]) + np.arange(width)[np.newaxis, :, np.newaxis]) / width
        y = (self._logistic(outputs[..., 1]) + np.arange(height)[:, np.newaxis, np.newaxis]) / height
        w = np.exp(outputs[..., 2]) * self.ANCHOR_BOXES[:, 0][np.newaxis, np.newaxis, :] / width
        h = np.exp(outputs[..., 3]) * self.ANCHOR_BOXES[:, 1][np.newaxis, np.newaxis, :] / height

        x = x - w / 2
        y = y - h / 2
        boxes = np.stack((x, y, w, h), axis=-1).reshape(-1, 4)

        objectness = self._logistic(outputs[..., 4])

        class_probs = outputs[..., 5:]
        class_probs = np.exp(class_probs - np.amax(class_probs, axis=3)[..., np.newaxis])
        class_probs = class_probs / np.sum(class_probs, axis=3)[..., np.newaxis] * objectness[..., np.newaxis]
        class_probs = class_probs.reshape(-1, num_class)

        return (boxes, class_probs)

    def _logistic(self, x):
        return np.where(x > 0, 1 / (1 + np.exp(-x)), np.exp(x) / (1 + np.exp(x)))

    def _non_maximum_suppression(self, boxes, class_probs):
        max_detections = min(self.max_detections, len(boxes))
        max_probs = np.amax(class_probs, axis=1)
        max_classes = np.argmax(class_probs, axis=1)

        areas = boxes[:, 2] * boxes[:, 3]

        selected_boxes = []
        selected_classes = []
        selected_probs = []

        while len(selected_boxes) < max_detections:
            i = np.argmax(max_probs)
            if max_probs[i] < self.prob_threshold:
                break

            selected_boxes.append(boxes[i])
            selected_classes.append(max_classes[i])
            selected_probs.append(max_probs[i])

            box = boxes[i]
            other_indices = np.concatenate((np.arange(i), np.arange(i + 1, len(boxes))))
            other_boxes = boxes[other_indices]

            x1 = np.maximum(box[0], other_boxes[:, 0])
            y1 = np.maximum(box[1], other_boxes[:, 1])
            x2 = np.minimum(box[0] + box[2], other_boxes[:, 0] + other_boxes[:, 2])
            y2 = np.minimum(box[1] + box[3], other_boxes[:, 1] + other_boxes[:, 3])
            w = np.maximum(0, x2 - x1)
            h = np.maximum(0, y2 - y1)

            overlap_area = w * h
            iou = overlap_area / (areas[i] + areas[other_indices] - overlap_area)

            overlapping_indices = other_indices[np.where(iou > self.IOU_THRESHOLD)[0]]
            overlapping_indices = np.append(overlapping_indices, i)

            class_probs[overlapping_indices, max_classes[i]] = 0
            max_probs[overlapping_indices] = np.amax(class_probs[overlapping_indices], axis=1)
            max_classes[overlapping_indices] = np.argmax(class_probs[overlapping_indices], axis=1)

        return selected_boxes, selected_classes, selected_probs