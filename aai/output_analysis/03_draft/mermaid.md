# Reconciliation Summary

Based on the provided file summaries, I have constructed an initial architecture diagram for the paragliding recognition system. The evidence supports a clear separation between:

1. **Development/Training Environment** (macOS-based)
2. **Edge Deployment Environment** (Jetson-based)
3. **External Services** (Roboflow API, RTSP streams)
4. **Model Artifacts Pipeline** (training → conversion → deployment)

All components and edges are directly traceable to the file summaries. Confidence scores reflect the explicitness of the evidence:
- **High confidence (0.9-0.95)**: Explicit imports, documented workflows, clear file purposes
- **Medium confidence (0.75-0.85)**: Inferred from architecture signals and dependencies
- **Lower confidence (0.7)**: Logical connections not explicitly documented but strongly implied

No speculative components have been added. The diagram represents only what is evidenced in the summaries.

---

# Updated Mermaid Diagram

```mermaid
graph TB
    subgraph External["External Services"]
        RoboflowAPI["Roboflow API<br/>(Dataset & Models)"]
        RTSPStream["RTSP Camera Stream"]
    end

    subgraph Development["Development Environment (macOS)"]
        DownloadScript["download_dataset.py<br/>(Dataset Download)"]
        TrainingWorkflow["YOLO Training<br/>(ultralytics CLI)"]
        ConversionScript["convert_to_tflite_simple.py<br/>(Model Conversion)"]
        EnvConfig[".env Configuration<br/>(API Keys)"]
    end

    subgraph EdgeDeployment["Edge Deployment (Jetson)"]
        DirectInf["direct_inf.py<br/>(Single Image)"]
        TimedRun["timed_run.py<br/>(Benchmarking)"]
        StreamInf["stream_inf.py<br/>(RTSP Processing)"]
        ContainerWorkflow["on_container.py<br/>(Server Workflow)"]
        LocalInferenceServer["Local Inference Server<br/>(localhost:9001)"]
    end

    subgraph ModelArtifacts["Model Artifacts"]
        PTModels["Pre-trained Models<br/>(.pt format)"]
        ONNXModels["ONNX Exports<br/>(.onnx format)"]
        TFLiteModels["TFLite Models<br/>(.tflite format)"]
        SavedModel["TensorFlow SavedModel<br/>(metadata.yaml)"]
    end

    subgraph SharedLibraries["Shared Dependencies"]
        InferenceSDK["inference / inference-sdk<br/>(Model Loading)"]
        Supervision["supervision<br/>(Visualization)"]
        OpenCV["opencv-python<br/>(Image/Video Processing)"]
        TFLiteRuntime["tflite_runtime<br/>(TFLite Inference)"]
    end

    %% Development Workflow
    EnvConfig -->|"provides credentials<br/>[0.95]"| DownloadScript
    DownloadScript -->|"downloads dataset<br/>[0.92]"| RoboflowAPI
    DownloadScript -->|"writes to paraglider_recognition-8/<br/>[0.92]"| TrainingWorkflow
    TrainingWorkflow -->|"produces .pt models<br/>[0.90]"| PTModels
    PTModels -->|"input for conversion<br/>[0.88]"| ConversionScript
    ConversionScript -->|"exports to TFLite<br/>[0.85]"| TFLiteModels
    ConversionScript -->|"exports to ONNX<br/>[0.85]"| ONNXModels
    PTModels -->|"exports to SavedModel<br/>[0.80]"| SavedModel

    %% Edge Deployment Workflows
    EnvConfig -->|"provides RTSP_URL<br/>[0.90]"| StreamInf
    TFLiteModels -->|"loaded for inference<br/>[0.90]"| DirectInf
    TFLiteModels -->|"loaded for benchmarking<br/>[0.90]"| TimedRun
    
    StreamInf -->|"connects to stream<br/>[0.88]"| RTSPStream
    StreamInf -->|"uses InferencePipeline<br/>[0.92]"| InferenceSDK
    
    ContainerWorkflow -->|"sends requests<br/>[0.95]"| LocalInferenceServer
    LocalInferenceServer -->|"loads models from<br/>[0.85]"| RoboflowAPI
    
    DirectInf -->|"uses for inference<br/>[0.90]"| TFLiteRuntime
    TimedRun -->|"uses for inference<br/>[0.90]"| TFLiteRuntime
    
    %% Shared Library Usage
    DirectInf -->|"uses for visualization<br/>[0.88]"| Supervision
    StreamInf -->|"uses for visualization<br/>[0.88]"| Supervision
    DirectInf -->|"uses for image I/O<br/>[0.92]"| OpenCV
    StreamInf -->|"uses for video processing<br/>[0.92]"| OpenCV
    TimedRun -->|"uses for image I/O<br/>[0.92]"| OpenCV

    %% Styling
    classDef external fill:#e1f5ff,stroke:#0288d1,stroke-width:2px
    classDef development fill:#fff3e0,stroke:#f57c00,stroke-width:2px
    classDef edge fill:#f3e5f5,stroke:#7b1fa2,stroke-width:2px
    classDef artifacts fill:#e8f5e9,stroke:#388e3c,stroke-width:2px
    classDef libraries fill:#fce4ec,stroke:#c2185b,stroke-width:2px

    class RoboflowAPI,RTSPStream external
    class DownloadScript,TrainingWorkflow,ConversionScript,EnvConfig development
    class DirectInf,TimedRun,StreamInf,ContainerWorkflow,LocalInferenceServer edge
    class PTModels,ONNXModels,TFLiteModels,SavedModel artifacts
    class InferenceSDK,Supervision,OpenCV,TFLiteRuntime libraries
```

---

# Confidence Delta

Since this is the initial architecture generation, all confidence scores are newly assigned. Key confidence assignments:

| Component/Edge | Confidence | Rationale |
|----------------|-----------|-----------|
| **DownloadScript → RoboflowAPI** | 0.92 | Explicit dependency on `roboflow` package and API key requirement |
| **StreamInf → RTSPStream** | 0.88 | RTSP_URL environment variable and InferencePipeline usage documented |
| **ContainerWorkflow → LocalInferenceServer** | 0.95 | Explicit localhost:9001 endpoint documented in architecture_signals |
| **TrainingWorkflow → PTModels** | 0.90 | YOLO training CLI produces .pt models per ultralytics standard |
| **ConversionScript → TFLiteModels** | 0.85 | Conversion script purpose explicitly stated, TFLite output inferred |
| **DirectInf → TFLiteRuntime** | 0.90 | Explicit dependency on tflite_runtime for Jetson inference |
| **LocalInferenceServer → RoboflowAPI** | 0.85 | Inference server loads models; Roboflow integration documented but connection method not explicit |
| **PTModels → SavedModel** | 0.80 | metadata.yaml presence suggests SavedModel export, but conversion path not explicitly documented |

**Needs Verification:**
- Exact model format used by `LocalInferenceServer` (assumes Roboflow-hosted models based on API integration)
- Whether `on_container.py` uses local TFLite models or remote Roboflow models (evidence suggests remote)
