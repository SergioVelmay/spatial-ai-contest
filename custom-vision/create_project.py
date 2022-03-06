import os
import json
from msrest.authentication import ApiKeyCredentials
from azure.cognitiveservices.vision.customvision.training import CustomVisionTrainingClient

SECRETS_FILE_NAME = 'secrets.json'

if os.path.isfile(SECRETS_FILE_NAME):
    with open(SECRETS_FILE_NAME, 'r') as secret_file:
        secrets_data = json.load(secret_file)
        secret_file.close()
else:
    raise FileNotFoundError

training_url = secrets_data['training_url']
training_key = secrets_data['training_key']

credentials = ApiKeyCredentials(in_headers={'Training-key': training_key})
cv_trainer = CustomVisionTrainingClient(training_url, credentials)

# Domain Types
CLASSIFICATION = 'Classification'
OBJECT_DETECTION = 'ObjectDetection'

# Classification Types
MULTICLASS = 'Multiclass'
MULTILABEL = 'Multilabel'

# Domain IDs
CLASSIFICATION_GENERAL_COMPACT_ID = '0732100f-1a38-4e49-a514-c9b44c697ab5'
CLASSIFICATION_GENERAL_COMPACT_S1_ID = 'a1db07ca-a19a-4830-bae8-e004a42dc863'
OBJECT_DETECTION_GENERAL_COMPACT_ID = 'a27d5ca5-bb19-49d8-a70a-fec086c47f5b'
OBJECT_DETECTION_GENERAL_COMPACT_S1_ID = '7ec2ac80-887b-48a6-8df9-8b1357765430'

# Export Platforms
CORE_ML = 'CoreML'
TENSOR_FLOW = 'TensorFlow'
DOCKER_FILE = 'DockerFile'
ONNX = 'ONNX'
OPEN_VINO = 'OpenVino'
VAIDK = 'VAIDK'

project_name = 'scvpy_part_counting'
project_description = 'Spatial Computer Vision Poka-yoke Counting Object Detection model.'

project = cv_trainer.create_project(project_name, project_description, OBJECT_DETECTION_GENERAL_COMPACT_ID)