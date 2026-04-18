## file_path
`paragliding_recognition/download_dataset.py`

## purpose
Downloads the paraglider_recognition dataset (version 8) from Roboflow in YOLOv8 format for local use on Jetson devices.

## exports
- Script execution (no exported classes/functions)

## dependencies
- os
- dotenv (load_dotenv)
- roboflow (Roboflow)

## architecture_signals
- external integration: Roboflow API client for dataset download
- config: reads ROBOFLOW_API_KEY from .env file
- data pipeline: downloads training/validation datasets for ML model training

## side_effects
- reads file: .env for API key
- calls external api: Roboflow workspace and project endpoints
- writes file: downloads dataset to local filesystem

## confidence
0.95

---

## file_path
`paragliding_recognition/README.md`

## purpose
Project documentation describing a multi-platform paraglider detection system using YOLOv8/YOLOv11 models for macOS development, Jetson edge deployment, and RTSP streaming.

## exports
none

## dependencies
none

## architecture_signals
- documentation: comprehensive project overview, setup instructions, and usage examples
- multi-platform: macOS (development), Jetson (edge), Rubik Pi (offline inference)
- ML pipeline: training, conversion (TFLite), and deployment workflows

## confidence
0.9

---

## file_path
`paragliding_recognition/rubikpi/__init__.py`

## purpose
Package marker for the Rubik Pi runtime module for offline TFLite inference.

## exports
none

## dependencies
none

## architecture_signals
- module boundary: defines rubikpi as a Python package for offline inference runtime

## confidence
0.85

---

## file_path
`paragliding_recognition/rubikpi/README.md`

## purpose
Documentation for the Rubik Pi 3 offline deployment runtime that performs local RTSP + TFLite inference without external API dependencies.

## exports
none

## dependencies
none

## architecture_signals
- documentation: deployment guide for offline edge inference
- deployment target: Rubik Pi 3 device with local TFLite models
- offline runtime: explicitly no Roboflow API or inference server dependencies

## confidence
0.9

---

## file_path
`paragliding_recognition/rubikpi/run_rtsp_tflite.py`

## purpose
Offline RTSP video stream processor that runs TFLite object detection inference, annotates frames with bounding boxes, and optionally saves video/snapshots without external API calls.

## exports
- Detection (dataclass)
- parse_args
- load_labels
- load_interpreter
- letterbox
- preprocess
- sigmoid
- xywh_to_xyxy
- rescale_boxes
- non_max_suppression
- parse_yolo_outputs
- parse_already_postprocessed_outputs
- run_inference
- load_video_writer
- annotate_frame
- emit_event
- main

## dependencies
- argparse
- json
- sys
- time
- dataclasses (dataclass)
- pathlib (Path)
- typing (Sequence)
- cv2 (opencv)
- numpy
- tflite_runtime.interpreter (Interpreter) or tensorflow.lite (fallback)

## architecture_signals
- entrypoint: CLI script with argparse for RTSP stream processing
- ML inference: TFLite interpreter for YOLOv8 object detection
- video processing: RTSP capture, letterboxing, NMS, annotation pipeline
- offline runtime: no external API dependencies, fully local inference

## entrypoints
- CLI command: `python run_rtsp_tflite.py --source <RTSP_URL> --model <path>`

## side_effects
- reads file: TFLite model file, optional labels file
- writes file: annotated video (mp4), periodic frame snapshots (jpg)
- calls external api: none (offline runtime)
- publishes message: JSON events to stdout when --verbose flag is set

## confidence
0.95

---

## file_path
`paragliding_recognition/rubikpi/tflite_models/yolov8s_saved_model/metadata.yaml`

## purpose
Model metadata file describing a YOLOv8s COCO-80 detection model exported to TFLite format with 640x640 input size.

## exports
none

## dependencies
none

## architecture_signals
- config: model metadata including class names, input dimensions, task type, and license
- ML artifact: describes a pre-trained YOLOv8s model for 80-class COCO object detection

## confidence
0.9

---

## file_path
`paragliding_recognition/jetson/direct_inf.py`

## purpose
Demonstrates basic single-image inference using the Roboflow inference SDK for paraglider detection on Jetson devices.

## exports
- Script execution (no exported classes/functions)

## dependencies
- os
- dotenv (load_dotenv)
- inference

## architecture_signals
- ML inference: Roboflow model loading and single-image inference
- config: reads ROBOFLOW_API_KEY from .env file
- example/demo: basic inference demonstration script

## side_effects
- reads file: .env for API key, test image file
- calls external api: Roboflow model loading endpoint

## confidence
0.9

---

## file_path
`paragliding_recognition/jetson/timed_run.py`

## purpose
Benchmarks paraglider detection model performance by running 10 inference iterations on a single image and measuring average latency.

## exports
- Script execution (no exported classes/functions)

## dependencies
- os
- dotenv (load_dotenv)
- inference (get_model)
- supervision
- cv2 (opencv)
- time

## architecture_signals
- performance testing: benchmarking script for edge device inference latency
- ML inference: Roboflow model inference with timing measurements
- config: reads ROBOFLOW_API_KEY from .env file

## side_effects
- reads file: .env for API key, test image file
- calls external api: Roboflow model loading and inference endpoints

## confidence
0.9

---

## file_path
`paragliding_recognition/jetson/on_container.py`

## purpose
Demonstrates running Roboflow workflows via the Inference SDK by connecting to a local inference server and comparing two YOLO models on the same image.

## exports
- Script execution (no exported classes/functions)

## dependencies
- inference_sdk (InferenceHTTPClient)

## architecture_signals
- API client: HTTP client for local inference server
- workflow orchestration: executes multi-model comparison workflow
- local inference server: connects to localhost:9001 for edge inference

## entrypoints
- HTTP client: connects to http://localhost:9001

## side_effects
- calls external api: local inference server at localhost:9001, Roboflow workflow endpoint

## confidence
0.85

---

## file_path
`paragliding_recognition/jetson/stream_inf.py`

## purpose
Creates a real-time inference pipeline that processes live RTSP camera streams and detects paragliders with bounding box rendering.

## exports
- Script execution (no exported classes/functions)

## dependencies
- os
- dotenv (load_dotenv)
- inference (InferencePipeline)
- inference.core.interfaces.stream.sinks (render_boxes)

## architecture_signals
- streaming pipeline: real-time RTSP video processing with inference
- ML inference: YOLOv8 model inference on video frames
- config: reads ROBOFLOW_API_KEY and RTSP_URL from .env file

## entrypoints
- RTSP stream: connects to RTSP_URL from environment variable

## side_effects
- reads file: .env for API key and RTSP URL
- calls external api: Roboflow model loading endpoint, RTSP camera stream

## confidence
0.95