import cv2
import depthai as dai

picking_device_id = '1844301041F08B1200'
assembly_device_id = '1844301051CC711200'

picking_pipeline = dai.Pipeline()
assembly_pipeline = dai.Pipeline()

def create_picking_pipeline():
    mono_left = picking_pipeline.create(dai.node.MonoCamera)
    mono_right = picking_pipeline.create(dai.node.MonoCamera)
    depth = picking_pipeline.create(dai.node.StereoDepth)
    depth_xout = picking_pipeline.create(dai.node.XLinkOut)
    depth_xout.setStreamName("depth")

    mono_left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
    mono_left.setBoardSocket(dai.CameraBoardSocket.LEFT)
    mono_right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
    mono_right.setBoardSocket(dai.CameraBoardSocket.RIGHT)

    depth.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
    depth.initialConfig.setMedianFilter(dai.MedianFilter.MEDIAN_OFF)
    depth.setLeftRightCheck(True)
    depth.setExtendedDisparity(False)
    depth.setSubpixel(False)

    mono_left.out.link(depth.left)
    mono_right.out.link(depth.right)
    depth.disparity.link(depth_xout.input)

    color = picking_pipeline.createColorCamera()
    color.setPreviewSize(640, 400)
    color.setInterleaved(False)
    color.setBoardSocket(dai.CameraBoardSocket.RGB)
    cam_out = picking_pipeline.createXLinkOut()
    cam_out.setStreamName("color")
    color.preview.link(cam_out.input)

def create_assembly_pipeline():
    color = assembly_pipeline.createColorCamera()
    color.setPreviewSize(520, 390)
    color.setInterleaved(False)
    color.setBoardSocket(dai.CameraBoardSocket.RGB)
    cam_out = assembly_pipeline.createXLinkOut()
    cam_out.setStreamName("color")
    color.preview.link(cam_out.input)

    mono_left = assembly_pipeline.create(dai.node.MonoCamera)
    mono_right = assembly_pipeline.create(dai.node.MonoCamera)
    depth = assembly_pipeline.create(dai.node.StereoDepth)
    depth_xout = assembly_pipeline.create(dai.node.XLinkOut)
    depth_xout.setStreamName("depth")

    mono_left.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
    mono_left.setBoardSocket(dai.CameraBoardSocket.LEFT)
    mono_right.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
    mono_right.setBoardSocket(dai.CameraBoardSocket.RIGHT)

    depth.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
    depth.initialConfig.setMedianFilter(dai.MedianFilter.MEDIAN_OFF)
    depth.setLeftRightCheck(True)
    depth.setExtendedDisparity(False)
    depth.setSubpixel(False)

    mono_left.out.link(depth.left)
    mono_right.out.link(depth.right)
    depth.disparity.link(depth_xout.input)

create_picking_pipeline()
create_assembly_pipeline()

devices = dai.Device.getAllAvailableDevices()
if len(devices) == 0:
    raise RuntimeError("No devices found!")

for device_info in devices:
    openvino_version = dai.OpenVINO.Version.VERSION_2021_4
    usb2_mode = False

    if device_info.getMxId() == picking_device_id:
        picking_device = dai.Device(openvino_version, device_info, usb2_mode)
        picking_device.startPipeline(picking_pipeline)
    elif device_info.getMxId() == assembly_device_id:
        assembly_device = dai.Device(openvino_version, device_info, usb2_mode)
        assembly_device.startPipeline(assembly_pipeline)

picking_queue_depth = picking_device.getOutputQueue(name="depth", maxSize=4, blocking=False)
picking_queue_color = picking_device.getOutputQueue(name="color", maxSize=1, blocking=False)

assembly_queue_depth = assembly_device.getOutputQueue(name="depth", maxSize=4, blocking=False)
assembly_queue_color = assembly_device.getOutputQueue(name="color", maxSize=1, blocking=False)

while True:
    picking_depth_input = picking_queue_depth.get()
    picking_depth_frame = picking_depth_input.getFrame()
    
    picking_depth_crop = picking_depth_frame[0:390, 25:545]
    picking_depth_color = cv2.normalize(picking_depth_crop, None, 255, 0, cv2.NORM_INF, cv2.CV_8UC1)
    picking_depth_color[picking_depth_color<128] = 0
    picking_depth_color = cv2.equalizeHist(picking_depth_color)
    picking_depth_color = cv2.applyColorMap(picking_depth_color, cv2.COLORMAP_JET)

    picking_color_input = picking_queue_color.get()
    picking_color_frame = picking_color_input.getCvFrame()

    picking_color_crop = picking_color_frame[0:390, 65:585]

    cv2.imshow("Picking Depth", picking_depth_color)

    cv2.imshow("Picking Color", picking_color_crop)

    assembly_color_input = assembly_queue_color.get()
    assembly_color_frame = assembly_color_input.getCvFrame()

    assembly_color_resized = cv2.resize(assembly_color_frame, (520, 390), cv2.INTER_AREA)

    assembly_depth_input = assembly_queue_depth.get()
    assembly_depth_frame = assembly_depth_input.getFrame()

    assembly_depth_crop = assembly_depth_frame[0:390, 30:550]
    assembly_depth_color = cv2.normalize(assembly_depth_crop, None, 255, 0, cv2.NORM_INF, cv2.CV_8UC1)
    assembly_depth_color[assembly_depth_color<128] = 0
    assembly_depth_color = cv2.equalizeHist(assembly_depth_color)
    assembly_depth_color = cv2.applyColorMap(assembly_depth_color, cv2.COLORMAP_JET)

    cv2.imshow("Assembly Depth", assembly_depth_color)

    cv2.imshow("Assembly Color", assembly_color_resized)

    if cv2.waitKey(1) == ord('q'):
        cv2.destroyAllWindows()
        break