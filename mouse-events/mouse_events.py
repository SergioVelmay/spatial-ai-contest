import cv2
import depthai as dai

class MouseEvents:
    def __init__(self):
        self.reference_points = []

        self.preview_width = 1280
        self.preview_height = 720
    
    def create_pipeline(self):
        pipeline = dai.Pipeline()
        pipeline.setOpenVINOVersion(version=dai.OpenVINO.Version.VERSION_2021_4)
        self.pd_input_length = 128

        cam = pipeline.createColorCamera()
        cam.setPreviewSize(self.preview_width, self.preview_height)
        cam.setInterleaved(False)
        cam.setBoardSocket(dai.CameraBoardSocket.RGB)
        cam_out = pipeline.createXLinkOut()
        cam_out.setStreamName("cam_out")
        cam.preview.link(cam_out.input)

        return pipeline

    def click_and_draw(self, event, x, y, flags, param):
        self.mouse_x = x
        self.mouse_y = y
        if event == cv2.EVENT_LBUTTONUP and len(self.reference_points) != 1:
            self.reference_points = [(x, y)]
        elif event == cv2.EVENT_LBUTTONUP and len(self.reference_points) == 1:
            self.reference_points.append((x, y))
        elif event == cv2.EVENT_RBUTTONUP:
            self.reference_points = []

    def run(self):
        device = dai.Device()
        device.startPipeline(self.create_pipeline())

        q_video_out = device.getOutputQueue(name="cam_out", maxSize=1, blocking=False)

        cv2.namedWindow("image")

        cv2.setMouseCallback("image", self.click_and_draw)

        while True:
            in_video = q_video_out.get()
            self.image = in_video.getCvFrame()

            key = cv2.waitKey(1) & 0xFF

            if len(self.reference_points) == 2:
                cv2.rectangle(self.image, self.reference_points[0], self.reference_points[1], (255, 255, 255), 2)
            elif len(self.reference_points) == 1:
                cv2.rectangle(self.image, self.reference_points[0], (self.mouse_x, self.mouse_y), (128, 128, 128), 1)
            
            cv2.imshow("image", self.image)

            if key == ord("q"):
                break

        cv2.destroyAllWindows()

if __name__ == "__main__":
    mouse_events = MouseEvents()
    mouse_events.run()