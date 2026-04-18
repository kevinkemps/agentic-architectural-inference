# Identified Architectural Issues

## Issue 1: Missing Evidence for Local Inference Server Deployment
**Severity:** High  
**Type:** Missing Evidence  
**The Claim:** `LocalInfServer["Inference Server<br/>localhost:9001"]` exists as a deployed component in the Jetson runtime.  
**The "Why":** The candidate architecture shows `on_container.py` connecting to `localhost:9001`, but there is **zero evidence** in the subsystem summaries of how this server is deployed, configured, or started. The HTTP client code proves intent to connect, not that the server exists. This could be:
- A manually deployed Docker container (not shown in codebase)
- A third-party service assumed to be running
- A configuration error where the server doesn't actually exist

**Verification Request:** Provide evidence of:
1. Deployment scripts, Docker Compose files, or systemd services that launch the inference server
2. Configuration files that bind the server to port 9001
3. Any startup scripts in the Jetson subsystem that initialize this service

---

## Issue 2: Ambiguous Roboflow API Interaction Model
**Severity:** Medium  
**Type:** Overgeneralization  
**The Claim:** Multiple Jetson components (`DirectInf`, `TimedRun`, `StreamInf`) all connect directly to `RoboflowAPI` with labels like "Model Loading" and "Model Inference."  
**The "Why":** The summaries show these scripts use the `inference` SDK, but do not clarify whether:
- The SDK makes **direct HTTP calls** to Roboflow's cloud API
- The SDK connects to a **local inference server** (like the one in `on_container.py`)
- Models are **cached locally** after first download

The current diagram conflates "uses Roboflow SDK" with "calls Roboflow cloud API," which may be architecturally incorrect. If models are cached, the runtime dependency on the external API is overstated.

**Verification Request:**
1. Trace the `inference` SDK's network calls to determine if they hit `api.roboflow.com` or `localhost`
2. Check for model caching behavior in the SDK (e.g., does `get_model()` download once and reuse?)
3. Clarify if the Jetson scripts can run **offline** after initial model download

---

## Issue 3: Contradictory Offline Claims for Rubik Pi
**Severity:** Medium  
**Type:** Contradiction  
**The Claim:** `RTSPTFLite` is described as "fully local inference" with "no external API dependencies."  
**The "Why":** While the code evidence supports this (no Roboflow imports, uses `tflite_runtime`), the **model artifact** (`yolov8s_saved_model`) is described as a "COCO-80 pre-trained model." The summaries do **not** show:
- How this TFLite model was obtained (was it downloaded from Roboflow? Converted locally?)
- Whether the model file is bundled in the repository or fetched at runtime
- If there's a hidden dependency on a one-time download step

If the model must be downloaded from Roboflow initially, the "offline" claim is misleading—it should be "offline **after** initial setup."

**Verification Request:**
1. Confirm whether `yolov8s_saved_model/` is committed to the repository or downloaded separately
2. If downloaded, identify the script/process that fetches it (is it part of `download_dataset.py`?)
3. Clarify the deployment workflow: does Rubik Pi require internet access during setup?

---

## Issue 4: Missing Data Flow Between Development and Deployment
**Severity:** High  
**Type:** Missing Evidence  
**The Claim:** The diagram shows `download_dataset.py` acquiring data from Roboflow, but there is **no edge** showing how this data reaches the Jetson or Rubik Pi runtimes.  
**The "Why":** The architecture implies a training pipeline (macOS downloads dataset → trains model → deploys to edge), but the summaries provide **zero evidence** of:
- Model training scripts
- Model export/conversion scripts (PyTorch → TFLite)
- Artifact transfer mechanisms (SCP, Docker images, manual copy)

The current diagram shows data acquisition in isolation, with no path to the deployed models. This is a **critical gap** in the architecture.

**Verification Request:**
1. Identify scripts that train models using the downloaded dataset
2. Locate model conversion scripts (e.g., `export_tflite.py`, `convert_model.sh`)
3. Document the deployment process: how do trained models reach Jetson/Rubik Pi?

---

## Issue 5: Overstated Confidence for LocalInfServer → RoboflowAPI Edge
**Severity:** Medium  
**Type:** Ambiguous Boundary  
**The Claim:** `LocalInfServer → RoboflowAPI` with confidence 0.8, labeled "Workflow Execution."  
**The "Why":** The evidence states this is "inferred from workflow execution pattern," but the summary for `on_container.py` only shows:
- A client connecting to `localhost:9001`
- Execution of a "multi-model comparison workflow"

There is **no direct evidence** that the local server forwards requests to Roboflow's cloud API. It could be:
- A fully local inference server (no cloud calls)
- A caching proxy that only calls Roboflow on cache misses
- A workflow orchestrator that calls Roboflow for model metadata but runs inference locally

**Verification Request:**
1. Inspect the inference server's configuration to determine if it proxies to Roboflow
2. Check network logs or server code to confirm external API calls
3. If the server is containerized, examine the Docker image's dependencies

---

## Issue 6: Unclear Role of `metadata.yaml`
**Severity:** Low  
**Type:** Overgeneralization  
**The Claim:** `TFLiteModel → ModelMetadata` with label "Metadata Reference."  
**The "Why":** The summary describes `metadata.yaml` as "model metadata including class names, input dimensions, task type," but does not show:
- Whether `run_rtsp_tflite.py` **actually reads** this file
- If the metadata is embedded in the TFLite model itself (making the YAML redundant)
- If this is just documentation for humans, not a runtime dependency

The edge implies a runtime dependency, but the code summary for `run_rtsp_tflite.py` shows it loads labels from a **separate labels file** (not `metadata.yaml`).

**Verification Request:**
1. Confirm if `run_rtsp_tflite.py` parses `metadata.yaml` at runtime
2. Check if the TFLite model contains embedded metadata (making the YAML file unnecessary)
3. Clarify the relationship between the "optional labels file" and `metadata.yaml`

---

# Edge & Relationship Actions

| Source | Target | Action | Confidence Delta | Reasoning |
|--------|--------|--------|------------------|-----------|
| `LocalInfServer` | `RoboflowAPI` | **Needs More Evidence** | -0.4 (0.8 → 0.4) | No direct evidence of cloud API calls; could be fully local |
| `ContainerInf` | `LocalInfServer` | **Downgrade Confidence** | -0.15 (0.85 → 0.7) | Client code exists, but server deployment is unverified |
| `TFLiteModel` | `ModelMetadata` | **Needs More Evidence** | -0.3 (0.9 → 0.6) | No proof that runtime code reads this file |
| `DirectInf` | `RoboflowAPI` | **Needs More Evidence** | -0.2 (0.9 → 0.7) | Unclear if SDK calls cloud or uses local cache |
| `TimedRun` | `RoboflowAPI` | **Needs More Evidence** | -0.2 (0.9 → 0.7) | Same caching ambiguity as `DirectInf` |
| `StreamInf` | `RoboflowAPI` | **Needs More Evidence** | -0.2 (0.95 → 0.75) | Same caching ambiguity; high initial confidence unjustified |

---

# Missing or Hidden Components

## 1. Model Training Pipeline
**Label:** `ModelTrainingService`  
**Reason:** The system downloads datasets but shows no training scripts. There must be a component that consumes the downloaded data and produces trained models. This is likely a Python script using Ultralytics YOLO or similar.

## 2. Model Conversion Service
**Label:** `TFLiteExporter`  
**Reason:** The Rubik Pi uses TFLite models, but the development environment likely trains PyTorch models. There must be a conversion step (e.g., `model.export(format='tflite')`).

## 3. Artifact Storage/Registry
**Label:** `ModelRegistry`  
**Reason:** Trained models must be stored somewhere accessible to both Jetson and Rubik Pi deployments. This could be a local filesystem, S3 bucket, or Docker registry.

## 4. Inference Server Deployment Orchestrator
**Label:** `InferenceServerDeployment`  
**Reason:** The `localhost:9001` server must be deployed somehow. This could be a Docker Compose file, Kubernetes manifest, or systemd service.

## 5. Configuration Management System
**Label:** `ConfigStore`  
**Reason:** Multiple components read from `.env` files, but there's no evidence of how these files are generated, validated, or distributed across environments.

---

# Critic's Summary

The proposed architecture suffers from **critical evidentiary gaps** in three areas:

1. **The Training-to-Deployment Pipeline:** The diagram shows data acquisition and inference runtimes, but completely omits the model training, conversion, and distribution mechanisms. This is not a minor oversight—it's the **core value chain** of an ML system.

2. **Ambiguous API Dependency Model:** The Jetson components are labeled as calling the Roboflow cloud API, but the evidence does not distinguish between:
   - Direct cloud API calls
   - Local inference server proxying
   - Cached model execution (offline-capable after first run)

   This conflation makes it impossible to assess the system's **network dependency profile** or offline capabilities.

3. **Unverified Infrastructure Components:** The `LocalInfServer` is shown as a first-class component, but there is **zero deployment evidence**. This could be a phantom dependency—a service assumed to exist but never actually deployed.

**Recommendation:** Before accepting this architecture, the system must provide:
- Evidence of model training scripts
- Model export/conversion workflows
- Deployment manifests for the inference server
- Clarification of the Roboflow SDK's caching and network behavior

The current model is **60% complete**—it accurately maps the inference runtimes but fails to capture the upstream ML pipeline and infrastructure dependencies. The confidence scores are inflated due to conflating "uses SDK" with "proven runtime behavior."