from typing import Any
from utils.window_utils import *
from utils.camera_utils import *

VALIDATION_COUNT = 10
IMAGES_FOLDER = './images/'
IMAGE_EXTENSION = '.jpg'

class StepValidation:
    def __init__(self, label: str, widget, part: str, ok: str, ko: str):
        self.Label = label
        self.Widget = widget
        self.Part = part
        self.OK = ok
        self.KO = ko

        self.Reset()
    
    def IsValid(self):
        return self.Count >= VALIDATION_COUNT
    
    def Reset(self):
        self.Count = 0

class PokaYokeAssembly:
    def __init__(self):
        self.Window = AssemblyWindow()
        self.Cameras = AssemblyCameras(self.DrawImages)

        self.label_image_length = 400

        step_labels = [
            '1_carrier',
            '2_bot',
            'gear',
            '4_top_ok',
            '5_gear_ok',
            '6_axis']

        step_widgets = [
            self.Window.PartALabel,
            self.Window.PartBLabels[0],
            [
                self.Window.PartBLabels[1],
                self.Window.PartBLabels[2],
                self.Window.PartBLabels[3]
            ],
            self.Window.PartBLabels[4],
            self.Window.PartCLabel,
            self.Window.PartDLabel]
        
        step_parts = [
            'a_6285647',
            'b_4565452',
            'b_4565452',
            'b_4565452',
            'c_6285646',
            'd_6130007']
        
        step_oks = [
            'ok_6285647',
            'ok_4565452',
            'ok_4565452',
            'ok_4565452',
            'ok_6285646',
            'ok_6130007']
        
        step_kos = [
            None,
            None,
            None,
            'ko_4565452',
            'ko_6285646',
            None]
        
        self.current_validation = 0
        
        self.step_validations = []

        for index, label in enumerate(step_labels):
            self.step_validations.append(StepValidation(label, 
                step_widgets[index], step_parts[index],
                step_oks[index], step_kos[index]))
        
        self.evidence_image_size = (120, 120)

    def DrawImages(self, primary_image: np.ndarray, model_image: np.ndarray, secondary_image: np.ndarray, classifications: list, detections: list):
        if primary_image.any() and model_image.any() and secondary_image.any():
            if self.current_validation < len(self.step_validations):
                DrawRectangle(primary_image, (159, 160), (229, 230), COLOR_CV_BLUE)
                DrawText(primary_image, 'differential assembly', (159-95, 160-12), COLOR_CV_BLUE)
                DrawText(primary_image, 'in progress', (159-35, 230+25), COLOR_CV_BLUE)

                if self.current_validation != 2 and len(classifications) > 0:
                    color = COLOR_CV_GREEN
                    label = classifications[0].Label

                    if '0_' in label:
                        color = COLOR_CV_BLUE
                    if '7_' in label:
                        color = COLOR_CV_WHITE
                    if '_ko' in label:
                        color = COLOR_CV_RED
                        if label.split('_')[1] == self.step_validations[self.current_validation].Label.split('_')[1]:
                            SetLabelImageFromPath(
                                self.step_validations[self.current_validation].Widget, 
                                IMAGES_FOLDER + self.step_validations[self.current_validation].KO + IMAGE_EXTENSION)
                    else:
                        if self.step_validations[self.current_validation].KO is not None:
                            SetLabelImageFromPath(
                                self.step_validations[self.current_validation].Widget, 
                                IMAGES_FOLDER + self.step_validations[self.current_validation].Part + IMAGE_EXTENSION)
                    
                    text = label[2:] + ' {:.2f}'.format(classifications[0].Score)
                    
                    DrawRectangle(model_image, (5, 5), (395, 395), color)
                    DrawText(model_image, text, (5+5, 5+25), color)

                    if label == self.step_validations[self.current_validation].Label:
                        self.step_validations[self.current_validation].Count = self.step_validations[self.current_validation].Count + 1
                    
                    if self.step_validations[self.current_validation].IsValid():
                        SetLabelImageFromPath(
                            self.step_validations[self.current_validation].Widget, 
                            IMAGES_FOLDER + self.step_validations[self.current_validation].OK + IMAGE_EXTENSION)
                        model_resized = cv2.resize(model_image, self.evidence_image_size, interpolation=cv2.INTER_AREA)
                        SetLabelImageFromArray(self.Window.EvidenceLabels[self.current_validation], model_resized)
                        self.current_validation = self.current_validation + 1

                if self.current_validation == 2 and len(detections) > 0:
                    ok_labels = 0

                    detect_evidence = model_image.copy()

                    for detection in detections:
                        color = COLOR_CV_WHITE
                        label = detection.Label
                        
                        if label == self.step_validations[self.current_validation].Label:
                            color = COLOR_CV_GREEN
                            ok_labels = ok_labels + 1
                        
                        x_min = int(self.label_image_length * detection.Box.Left)
                        y_min = int(self.label_image_length * detection.Box.Top)
                        x_max = int(self.label_image_length * detection.Box.Right)
                        y_max = int(self.label_image_length * detection.Box.Bottom)

                        DrawRectangle(model_image, (x_min, y_min), (x_max, y_max), color)
                        DrawText(model_image, label, (x_min+5, y_min+25), color)
                        DrawText(model_image, '{:.2f}'.format(detection.Score), (x_min+5, y_min+50), color)
                    
                    if ok_labels > 0:
                        SetLabelImageFromPath(
                            self.step_validations[self.current_validation].Widget[ok_labels - 1], 
                            IMAGES_FOLDER + self.step_validations[self.current_validation].OK + IMAGE_EXTENSION)               
                    
                    if ok_labels == 3:
                        self.step_validations[self.current_validation].Count = self.step_validations[self.current_validation].Count + 1
                    
                    if self.step_validations[self.current_validation].IsValid():
                        text_evidence = '3x mid'
                        for detection in detections:
                            text_evidence = text_evidence + ' {:.2f}'.format(detection.Score)
                            
                            x_min = int(self.label_image_length * detection.Box.Left)
                            y_min = int(self.label_image_length * detection.Box.Top)
                            x_max = int(self.label_image_length * detection.Box.Right)
                            y_max = int(self.label_image_length * detection.Box.Bottom)

                            DrawRectangle(detect_evidence, (x_min, y_min), (x_max, y_max), COLOR_CV_GREEN)

                        DrawRectangle(detect_evidence, (5, 5), (395, 395), COLOR_CV_GREEN)
                        DrawText(detect_evidence, text_evidence, (5+5, 5+25), COLOR_CV_GREEN)
                        model_resized = cv2.resize(detect_evidence, self.evidence_image_size, interpolation=cv2.INTER_AREA)
                        SetLabelImageFromArray(self.Window.EvidenceLabels[self.current_validation], model_resized)
                        self.current_validation = self.current_validation + 1
            
            if self.current_validation == len(self.step_validations):
                DrawText(primary_image, 'differential assembly', (159-95, 160-12), COLOR_CV_GREEN)
                DrawText(primary_image, 'in progress', (159-35, 230+25), COLOR_CV_GREEN)

            SetLabelImageFromArray(self.Window.PrimaryLabel, primary_image)
            SetLabelImageFromArray(self.Window.ModelLabel, model_image)
            SetLabelImageFromArray(self.Window.SecondaryLabel, secondary_image)

def Main():
    assembly_poka_yoke = PokaYokeAssembly()
    assembly_poka_yoke.Cameras.StartMainLoop()
    assembly_poka_yoke.Window.StartMainLoop()

if __name__ == '__main__':
    Main()