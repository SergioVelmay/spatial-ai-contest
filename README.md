# spatial-ai-contest
OpenCV Spatial AI Contest

- Installation
    ```
    python -m venv venv
    ```
    ```
    venv\Scripts\activate
    ```
    ```
    python -m pip install --upgrade pip
    ```
    ```
    pip install -r requirements.txt
    ```

- Hand landmarks demo
    ```
    cd hand-landmarks
    ```
    ```
    python hand_landmarks.py
    ```

- Depth recording demo
    ```
    cd depth-recording
    ```
    ```
    python depth_recording.py
    ```

- Mouse events demo
    ```
    cd mouse-events
    ```
    ```
    python mouse_events.py
    ```

- OAK-D Lite cameras demo
    ```
    cd oakdlite-cameras
    ```
    ```
    python oakdlite_cameras.py
    ```

- Color depth align demo
    ```
    cd color-depth-align
    ```
    ```
    python color_depth_align.py
    ```

- Depth calculation demo
    ```
    cd depth-calculation
    ```
    ```
    python depth_calculation.py
    ```

- JSON config file demo
    ```
    cd json-config-file
    ```
    ```
    python json_config_file.py
    ```

- User interface demo
    ```
    cd user-interface
    ```
    ```
    python user_interface.py
    ```

- Picking detection demo
    ```
    cd picking-detection
    ```
    ```
    python picking_detection.py
    ```

- Poka-Yoke picking demo
    ```
    cd poka-yoke-picking
    ```
    ```
    python poka_yoke_picking.py
    ```

- Custom Vision demo
    ```
    cd custom-vision
    ```
    ```
    python create_project.py
    ```

- Model Optimization
    ```
    python -m venv venv-openvino
    ```
    ```
    venv-openvino\Scripts\activate
    ```
    ```
    python -m pip install --upgrade pip
    ```
    ```
    pip install openvino-dev[tensorflow2]
    ```
    ```
    python -c "from openvino.runtime import Core"
    ```
    ```
    mo -h
    ```
    ```
    mo --input_model C:\...\models\custom-vision\TensorFlow\model.pb --output_dir C:\...\models\custom-vision\TensorFlow --batch 1 --log_level DEBUG
    ```

- Blob Compilation
    - PiPy.org
        ```
        pip install blobconverter
        ```
        ```
        blobconverter -h
        ```
        ```
        blobconverter --openvino-xml C:\...\models\custom-vision\fTensorFlow\model.xml --openvino-bin C:\...\models\custom-vision\TensorFlow\model.bin --shaves 8
        ```
    - OpenVINO
        ```
        cd "C:\Program Files (x86)\Intel\openvino_2022"
        ```
        ```
        setupvars.bat
        ```
        ```
        cd "C:\Program Files (x86)\Intel\openvino_2022\tools\compile_tool"
        ```
        ```
        compile_tool -h
        ```
        ```
        compile_tool -m C:\...\models\custom-vision\fTensorFlow\model.xml -o C:\...\models\custom-vision\TensorFlow -d MYRIAD
        ```
