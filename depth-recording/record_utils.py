from pathlib import Path
from multiprocessing import Queue
from threading import Thread
import depthai as dai
from enum import Enum

class EncodingQuality(Enum):
    BEST = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4


class Record():
    def __init__(self, path: Path, device) -> None:
        self.save = ['depth']
        self.fps = 30
        self.timelapse = -1
        self.device = device
        self.quality = EncodingQuality.HIGH
        self.rotate = -1
        self.preview = False

        self.stereo = 1 < len(device.getConnectedCameras())
        self.mxid = device.getMxId()
        self.path = self.create_folder(path, self.mxid)

        calibData = device.readCalibration()
        calibData.eepromToJsonFile(str(self.path / "calib.json"))

        self.convert_mp4 = False

    def run(self):
        files = {}
        def create_video_file(name):
            if name == 'depth':
                files[name] = self.depthAiBag
            else:
                ext = 'h265' if self.quality == EncodingQuality.LOW else 'mjpeg'
                files[name] = open(str(self.path / f"{name}.{ext}"), 'wb')

        while True:
            try:
                frames = self.frame_q.get()
                if frames is None:
                    break
                for name in frames:
                    if name not in files:
                        create_video_file(name)

                    files[name].write(frames[name])
            except KeyboardInterrupt:
                break
        for name in files:
            files[name].close()

    def start(self):
        if not self.stereo:
            if "left" in self.save:
                self.save.remove("left")
            if "right" in self.save:
                self.save.remove("right")
            if "disparity" in self.save:
                self.save.remove("disparity")
            if "depth" in self.save:
                self.save.remove("depth")

        if self.preview:
            self.save.append('preview')

        if 0 < self.timelapse:
            self.fps = 5

        self.pipeline, self.nodes = self.create_pipeline()

        if "depth" in self.save:
            from rosbag_utils import DepthAiBags
            res = ['depth']
            if self.rotate in [0,2]:
                res = (res[1], res[0])
            self.depthAiBag = DepthAiBags(self.path, self.device, self.get_sizes(), rgb='color' in self.save)

        self.frame_q = Queue(20)
        self.process = Thread(target=self.run)
        self.process.start()

        self.device.startPipeline(self.pipeline)

        self.queues = []
        maxSize = 1 if 0 < self.timelapse else 10
        for stream in self.save:
            self.queues.append({
                'q': self.device.getOutputQueue(name=stream, maxSize=maxSize, blocking=False),
                'msgs': [],
                'name': stream,
                'mxid': self.mxid
            })

    def set_fps(self, fps):
        self.fps = fps

    def set_timelapse(self, timelapse):
        self.timelapse = timelapse

    def set_quality(self, quality: EncodingQuality):
        self.quality = quality

    def set_preview(self, preview: bool):
        self.preview = preview

    def set_save_streams(self, save_streams):
        self.save = save_streams

    def get_sizes(self):
        dict = {}
        if "color" in self.save:
            dict['color'] = self.nodes['color'].getVideoSize()
        if "right" in self.save:
            dict['right'] = self.nodes['right'].getResolutionSize()
        if "left" in self.save:
            dict['left'] = self.nodes['left'].getResolutionSize()
        if "disparity" in self.save:
            dict['disparity'] = self.nodes['left'].getResolutionSize()
        if "depth" in self.save:
            dict['depth'] = self.nodes['left'].getResolutionSize()
        return dict

    def create_folder(self, path: Path, mxid: str):
        i = 0
        while True:
            i += 1
            recordings_path = path / f"{i}-{str(mxid)}"
            if not recordings_path.is_dir():
                recordings_path.mkdir(parents=True, exist_ok=False)
                return recordings_path

    def create_pipeline(self):
        pipeline = dai.Pipeline()
        nodes = {}

        def create_mono(name):
            nodes[name] = pipeline.createMonoCamera()
            nodes[name].setResolution(dai.MonoCameraProperties.SensorResolution.THE_480_P)
            socket = dai.CameraBoardSocket.LEFT if name == "left" else dai.CameraBoardSocket.RIGHT
            nodes[name].setBoardSocket(socket)
            nodes[name].setFps(self.fps)

        def stream_out(name, fps, out, noEnc=False):
            xout = pipeline.createXLinkOut()
            xout.setStreamName(name)
            if noEnc:
                out.link(xout.input)
                return

            encoder = pipeline.createVideoEncoder()
            profile = dai.VideoEncoderProperties.Profile.H265_MAIN if self.quality == EncodingQuality.LOW else dai.VideoEncoderProperties.Profile.MJPEG
            encoder.setDefaultProfilePreset(fps, profile)

            if self.quality == EncodingQuality.BEST:
                encoder.setLossless(True)
            elif self.quality == EncodingQuality.HIGH:
                encoder.setQuality(97)
            elif self.quality == EncodingQuality.MEDIUM:
                encoder.setQuality(93)
            elif self.quality == EncodingQuality.LOW:
                encoder.setBitrateKbps(10000)

            out.link(encoder.input)
            encoder.bitstream.link(xout.input)

        if "color" in self.save:
            nodes['color'] = pipeline.createColorCamera()
            nodes['color'].setBoardSocket(dai.CameraBoardSocket.RGB)
            nodes['color'].setColorOrder(dai.ColorCameraProperties.ColorOrder.RGB)
            nodes['color'].setResolution(dai.ColorCameraProperties.SensorResolution.THE_4_K)
            nodes['color'].setIspScale(1,2)
            nodes['color'].setFps(self.fps)

            if self.preview:
                nodes['color'].setPreviewSize(640, 360)
                stream_out("preview", None, nodes['color'].preview, noEnc=True)

            stream_out("color", nodes['color'].getFps(), nodes['color'].video)

        if True in (el in ["left", "disparity", "depth"] for el in self.save):
            create_mono("left")
            if "left" in self.save:
                stream_out("left", nodes['left'].getFps(), nodes['left'].out)

        if True in (el in ["right", "disparity", "depth"] for el in self.save):
            create_mono("right")
            if "right" in self.save:
                stream_out("right", nodes['right'].getFps(), nodes['right'].out)

        if True in (el in ["disparity", "depth"] for el in self.save):
            nodes['stereo'] = pipeline.createStereoDepth()
            nodes['stereo'].initialConfig.setConfidenceThreshold(255)
            nodes['stereo'].initialConfig.setMedianFilter(dai.StereoDepthProperties.MedianFilter.MEDIAN_OFF)
            nodes['stereo'].setLeftRightCheck(True)
            nodes['stereo'].setExtendedDisparity(False)

            if "disparity" not in self.save and "depth" in self.save:
                nodes['stereo'].setSubpixel(True)

            nodes['left'].out.link(nodes['stereo'].left)
            nodes['right'].out.link(nodes['stereo'].right)

            if "disparity" in self.save:
                stream_out("disparity", nodes['right'].getFps(), nodes['stereo'].disparity)
            if "depth" in self.save:
                stream_out('depth', None, nodes['stereo'].depth, noEnc=True)

        self.nodes = nodes
        self.pipeline = pipeline
        return pipeline, nodes