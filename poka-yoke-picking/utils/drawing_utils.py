from utils.picking_utils import *
from utils.mediapipe_utils import *

CONFIG_FILE_NAME = 'config.json'
MAX_PICKING_ITEMS = 8
COLOR_WHITE = (255, 255, 255)
COLOR_GREEN = (14, 168, 75)
COLOR_RED = (236, 31, 36)
COLOR_YELLOW = '#FFE61A' # (100, 90, 10)
COLOR_DEFAULT = '#F0F0F0' # 'SystemWindow'
DEFAULT_NAME = 'NewItem#'

def DisableWidget(widget: Widget):
    widget['state'] = DISABLED

def EnableWidget(widget: Widget):
    widget['state'] = NORMAL

def GetRectFromRegion(frame: np.ndarray, region: HandRegion):
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

def GetRoiByPercent(percent: float, xMin: int, yMin: int, xMax: int, yMax: int):
    delta_x = int((xMax - xMin) * percent / 2)
    delta_y = int((yMax - yMin) * percent / 2)
    xMin += delta_x
    yMin += delta_y
    xMax -= delta_x
    yMax -= delta_y
    return xMin, yMin, xMax, yMax

def GetRoiByRadius(radius: int, point: Point):
    x1 = point.X - radius
    y1 = point.Y - radius
    x2 = point.X + radius
    y2 = point.Y + radius
    return x1, y1, x2, y2

def CalculateRectFromRegion(color_image: np.ndarray, region: HandRegion):
    x1, y1, x2, y2 = GetRectFromRegion(color_image, region)
    xMin, yMin, xMax, yMax = GetRoiByPercent(0.5, x1, y1, x2, y2)
    return xMin, yMin, xMax, yMax

def CalculateDepthFromCoords(depth_image: np.ndarray, xMin: int, yMin: int, xMax: int, yMax: int):
    depth_roi = depth_image[yMin:yMax, xMin:xMax]
    float_mean = np.mean(depth_roi[True])
    if np.isnan(float_mean):
        average_depth = None
    else:
        average_depth = int(float_mean)
    return average_depth

def CalculateTextPoints(xMin: int, yMin: int, xMax: int, yMax: int):
    centroid_x = int((xMax - xMin) / 2) + xMin
    centroid_y = int((yMax - yMin) / 2) + yMin
    point_x = (centroid_x - 13, centroid_y + 4)
    point_y = (centroid_x - 4, centroid_y + 4)
    point_z = (centroid_x + 5, centroid_y + 4)
    return point_x, point_y, point_z

def CalculateDepthRange(depth_image: np.ndarray, current_depth: Depth):
    min_x1, min_y1, min_x2, min_y2 = GetRoiByRadius(10, current_depth.LowerLevel)
    max_x1, max_y1, max_x2, max_y2 = GetRoiByRadius(10, current_depth.UpperLevel)
    min_depth = CalculateDepthFromCoords(depth_image, min_x1, min_y1, min_x2, min_y2)
    max_depth = CalculateDepthFromCoords(depth_image, max_x1, max_y1, max_x2, max_y2)
    return min_depth, max_depth

def IsRectInRangeX(rect: Rect, x1: int, x2: int):
    left_value = rect.TopLeft.X < x1
    right_value = rect.BottomRight.X > x2
    return left_value and right_value

def IsRectInRangeY(rect: Rect, y1: int, y2: int):
    top_value = rect.TopLeft.Y < y1
    bot_value = rect.BottomRight.Y > y2
    return top_value and bot_value

def IsRectInsideItemRect(rect: Rect, x1: int, y1: int, x2: int, y2: int):
    top_left_value = rect.TopLeft.X < x1 and rect.TopLeft.Y < y1
    bot_right_value = rect.BottomRight.X > x2 and rect.BottomRight.Y > y2
    return top_left_value and bot_right_value

def IsDepthInRangeZ(depth: int, lower_z: int, upper_z: int):
    lower_value = lower_z > depth
    upper_value = upper_z < depth
    return lower_value and upper_value