from utils.window_utils import *
from utils.camera_utils import *

class PokaYokeAssembly:
    def __init__(self):
        self.Window = AssemblyWindow()
        self.Cameras = AssemblyCameras(self.DrawImages)

        self.PrimaryImage = None
        self.ModelImage = None
        self.SecondaryImage = None

    def DrawImages(self, primary_image: np.ndarray, model_image: np.ndarray, secondary_image: np.ndarray):
        if primary_image.any() and model_image.any() and secondary_image.any():

            DrawRectangle(primary_image, (159, 160), (229, 230), COLOR_CV_BLUE)
            DrawText(primary_image, 'assembly', (159-25, 160-10), COLOR_CV_BLUE)

            DrawRectangle(model_image, (5, 5), (395, 395), COLOR_CV_BLUE)
            DrawText(model_image, 'label', (5+5, 5+25), COLOR_CV_BLUE)

            SetLabelImageFromArray(self.Window.PrimaryLabel, primary_image)
            SetLabelImageFromArray(self.Window.ModelLabel, model_image)
            SetLabelImageFromArray(self.Window.SecondaryLabel, secondary_image)

def Main():
    assembly_poka_yoke = PokaYokeAssembly()
    assembly_poka_yoke.Cameras.StartMainLoop()
    assembly_poka_yoke.Window.StartMainLoop()

if __name__ == '__main__':
    Main()