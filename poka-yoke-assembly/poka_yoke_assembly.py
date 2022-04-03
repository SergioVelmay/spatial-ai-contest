from utils.window_utils import *
from utils.camera_utils import *

class PokaYokeAssembly:
    def __init__(self):
        self.Window = AssemblyWindow()
        self.Cameras = AssemblyCameras(self.DrawImages)

        self.label_image_length = 400

        self.PrimaryImage = None
        self.ModelImage = None
        self.SecondaryImage = None

    def DrawImages(self, primary_image: np.ndarray, model_image: np.ndarray, secondary_image: np.ndarray, classifications: list, detections: list):
        if primary_image.any() and model_image.any() and secondary_image.any():

            DrawRectangle(primary_image, (159, 160), (229, 230), COLOR_CV_BLUE)
            DrawText(primary_image, 'assembly', (159-25, 160-10), COLOR_CV_BLUE)
            if len(classifications) == 1:
                color = COLOR_CV_GREEN
                label = classifications[0].Label

                if '0_' in label:
                    color = COLOR_CV_BLUE
                if '7_' in label:
                    color = COLOR_CV_WHITE
                if '_ko' in label:
                    color = COLOR_CV_RED
                
                text = label[2:] + ' {:.2f}'.format(classifications[0].Score)
                
                DrawRectangle(model_image, (5, 5), (395, 395), color)
                DrawText(model_image, text, (5+5, 5+25), color)

            if len(detections) == 3:
                for detection in detections:
                    color = COLOR_CV_WHITE
                    label = detection.Label
                    
                    if 'gear' in label:
                        color = COLOR_CV_GREEN
                    
                    x_min = int(self.label_image_length * detection.Box.Left)
                    y_min = int(self.label_image_length * detection.Box.Top)
                    x_max = int(self.label_image_length * detection.Box.Right)
                    y_max = int(self.label_image_length * detection.Box.Bottom)

                    DrawRectangle(model_image, (x_min, y_min), (x_max, y_max), color)
                    DrawText(model_image, label, (x_min+5, y_min+25), color)
                    DrawText(model_image, '{:.2f}'.format(detection.Score), (x_min+5, y_min+50), color)

            SetLabelImageFromArray(self.Window.PrimaryLabel, primary_image)
            SetLabelImageFromArray(self.Window.ModelLabel, model_image)
            SetLabelImageFromArray(self.Window.SecondaryLabel, secondary_image)

def Main():
    assembly_poka_yoke = PokaYokeAssembly()
    assembly_poka_yoke.Cameras.StartMainLoop()
    assembly_poka_yoke.Window.StartMainLoop()

if __name__ == '__main__':
    Main()