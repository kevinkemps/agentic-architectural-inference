## file_paths
- paragliding_recognition/download_dataset.py
- paragliding_recognition/README.md
- paragliding_recognition/tflite_models/yolov8s_saved_model/metadata.yaml
- paragliding_recognition/jetson/direct_inf.py
- paragliding_recognition/jetson/timed_run.py
- paragliding_recognition/jetson/on_container.py
- paragliding_recognition/jetson/stream_inf.py

## purpose
Computer vision project for paraglider detection using YOLOv8/YOLOv11 models, supporting dataset download, model training/conversion, and multi-platform inference (macOS development, Jetson edge deployment, RTSP streaming).

## exports
- `download_dataset.py`: dataset download script
- `jetson/direct_inf.py`: single-image inference
- `jetson/timed_run.py`: performance benchmarking
- `jetson/on_container.py`: workflow execution via local inference server
- `jetson/stream_inf.py`: real-time RTSP stream processing

## dependencies
- roboflow: dataset download and model access
- inference / inference-sdk: model loading and inference pipelines
- supervision: detection visualization
- opencv-python (cv2): image/video processing
- dotenv: environment variable management
- ultralytics: YOLO training and export
- tensorflow: model conversion to TFLite
- tflite_runtime: TFLite inference

## architecture_signals
- **external integrations**: Roboflow API for dataset download and model hosting
- **config**: environment variables via `.env` (ROBOFLOW_API_KEY, QAI_HUB_API_TOKEN, RTSP_URL)
- **API handlers**: local inference server on http://localhost:9001 (on_container.py)
- **streaming**: RTSP video stream processing via InferencePipeline
- **edge deployment**: Jetson-specific requirements and inference scripts
- **model artifacts**: pre-trained .pt models, ONNX exports, TFLite conversions, saved_model format

## entrypoints
- CLI: `python download_dataset.py` (dataset download)
- CLI: `python jetson/direct_inf.py` (single-image inference)
- CLI: `python jetson/timed_run.py` (benchmarking)
- CLI: `python jetson/on_container.py` (workflow execution)
- CLI: `python jetson/stream_inf.py` (RTSP stream processing)
- CLI: `yolo task=detect mode=train ...` (model training)
- CLI: `python convert_to_tflite_simple.py <model>` (model conversion)

## side_effects
- writes files: downloads dataset to `paraglider_recognition-8/` directory
- writes files: saves converted models to `tflite_models/` directory
- writes files: training artifacts to `training/` directory
- calls external API: Roboflow API for dataset and model access
- calls external API: connects to RTSP camera streams
- calls external API: local inference server at localhost:9001

## risk_or_ambiguity
- API key security: `.env` file must be properly gitignored to prevent credential leaks
- Platform-specific dependencies: Jetson requirements (TensorRT, Jetson.GPIO) require system drivers and SDK Manager setup
- Model conversion issues: programmatic TFLite export may fail on macOS, fallback to CLI wrapper recommended
- RTSP stream availability: stream_inf.py assumes valid and accessible RTSP URL
- Dataset version hardcoded: scripts reference version 8 of paraglider_recognition dataset
- Missing error handling: scripts raise ValueError for missing env vars but don't gracefully handle network/API failures

## confidence
0.92
