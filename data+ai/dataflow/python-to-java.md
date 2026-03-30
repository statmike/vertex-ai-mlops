![tracker](https://us-central1-vertex-ai-mlops-369716.cloudfunctions.net/pixel-tracking?path=statmike%2Fvertex-ai-mlops%2Fdata%2Bai%2Fdataflow&file=python-to-java.md)
<!--- header table --->
<table>
<tr>     
  <td style="text-align: center">
    <a href="https://github.com/statmike/vertex-ai-mlops/blob/main/data%2Bai/dataflow/python-to-java.md">
      <img width="32px" src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub logo">
      <br>View on<br>GitHub
    </a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Share On: </b> 
    <a href="https://www.linkedin.com/sharing/share-offsite/?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/dataflow/python-to-java.md"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a> 
    <a href="https://reddit.com/submit?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/dataflow/python-to-java.md"><img src="https://redditinc.com/hubfs/Reddit%20Inc/Brand/Reddit_Logo.png" alt="Reddit Logo" width="20px"></a> 
    <a href="https://bsky.app/intent/compose?text=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/dataflow/python-to-java.md"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://twitter.com/intent/tweet?url=https://github.com/statmike/vertex-ai-mlops/blob/main/data%252Bai/dataflow/python-to-java.md"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a> 
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <b>Connect With Author On: </b> 
    <a href="https://www.linkedin.com/in/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/8/81/LinkedIn_icon.svg" alt="Linkedin Logo" width="20px"></a>
    <a href="https://www.github.com/statmike"><img src="https://www.svgrepo.com/download/217753/github.svg" alt="GitHub Logo" width="20px"></a> 
    <a href="https://www.youtube.com/@statmike-channel"><img src="https://upload.wikimedia.org/wikipedia/commons/f/fd/YouTube_full-color_icon_%282024%29.svg" alt="YouTube Logo" width="20px"></a>
    <a href="https://bsky.app/profile/statmike.bsky.social"><img src="https://upload.wikimedia.org/wikipedia/commons/7/7a/Bluesky_Logo.svg" alt="BlueSky Logo" width="20px"></a> 
    <a href="https://x.com/statmike"><img src="https://upload.wikimedia.org/wikipedia/commons/5/5a/X_icon_2.svg" alt="X (Twitter) Logo" width="20px"></a>
  </td>
</tr>
<tr>
  <td style="text-align: right">
    <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/dataflow/python-to-java.md"><img src="https://www.svgrepo.com/download/5445/download-button.svg" alt="Download icon" width="20px"></a> <a href="https://raw.githubusercontent.com/statmike/vertex-ai-mlops/main/data%2Bai/dataflow/python-to-java.md">Download File</a> <i>(right-click and "Save As")</i>
  </td>
</tr>
</table><br/><br/>

---
# Python to Java Feature Support

To translate the Python to Java, utilize the Beam Fn API and package the Python logic as an external transform. When the Java pipeline runs on Dataflow, it starts a side Python process. The Java SDK manages the data flow while the Python process handles the complex ML inference and model hot-swapping. The Java SDK acts as a wrapper that will pass the parameters in the Python execution environment. 

**Multi-language pipelines rely on the Beam Fn API which is only available in Runner v2. If they try to run this on the older Dataflow runner, the Java-Python bridge will fail immediately. [Beam Fn API](https://github.com/apache/beam/blob/master/model/fn-execution/src/main/proto/org/apache/beam/model/fn_execution/v1/beam_fn_api.proto)

### Feature Parity

| Python Feature | Translation Method (Java) |
|----------|----------|
| **RunInference** | Wrap the Python RunInference in a PythonExternalTransform called from Java |
| **ModelHandler (PyTorch/TF)** | (PyTorch/TF): Keep the ModelHandler in a Python script; invoke it via Java's withKwarg |
| **KeyedModelHandler** | Use the Python KeyedModelHandler within the cross-language composite transform |
| **Event-Mode Hot-Swap** | Use Java PCollectionView as a side input passed to the PythonExternalTransform |
| **PredictionResult** | Python returns this object and Java receives it as a Beam Row or JSON string |

## Overview

If using RunInference, you have 5 key features to translate

1. **[RunInference](#1-RunInference)** - ML Engine
2. **[ModelHandler (PyTorch/TF)](#2-modelhandler-pytorch)** - Local ML Configuration
3. **[KeyedModelHandler](#3-keyedmodelhandler)** - Context Preservation
4. **[Event-Mode Hot-Swap](#4-event-mode-hot-swap)** - Zero-Downtime Updates
5. **[PredictionResult](#5-predictionresult)** - Output Contract

### Implementation Checklist

1. Set Up Python Environment
    - Encase the ML logic in a class inheriting from beam.PTransform
    - Ensure RunInference is configured with model_metadata_pcollection assigned to your side input parameter
    - Run a Python Expansion Service
2. Set Up Java Pipeline
   - Use PubsubIO to read the data and model update signals
   - Apply PythonExternalTransform.from(TRANSFORM_NAME, EXPANSION_SERVICE_URL)
   - Use .withSideInputs() to pass the Java model update PCollection to the Python process
3. Data Integrity
   - Define a schema in Java that mirrors exactly the keys returned by your Python format_output function
   - Use RowCoder to ensure Java can correctly deserialize the results for BigQuery


## 1. RunInference

**Translation to Java**: Wrap the Python RunInference in a PythonExternalTransform called from Java.

#### Resources
[Beam RunInference from Java Multi-Language Pipeline](https://beam.apache.org/documentation/ml/multi-language-inference/)

[Multi-Language Quickstart](https://beam.apache.org/documentation/sdks/java-multi-language-pipelines/)

[Global Window Side Inputs](https://beam.apache.org/documentation/patterns/side-inputs/)

## 2. ModelHandler (PyTorch/TF)

**Translation to Java**: Wrap the Python ModelHandler within a KeyedModelHandler inside the Python script. Java passes a PCollection of pairs or strings and the Python transform ensures the keys are preserved through the inference process.

**Why?**: ModelHandler in Python requires specific configurations (device type, batch size, model path). Java .withKwargs() pass a structured Map that matches the Python __init__ signature allowing Java to control behavior without touching the Python code.

### Example 

Package your ModelHandler and a PTransform into a Python file:

```python
-- Python
# Native Python ML Handlers
class MyInferenceTransform(beam.PTransform):
    def __init__(self, model_path):
        self.model_path = model_path

    def expand(self, pcoll):
        # Initialized in Python, configured via Java params
        handler = PytorchModelHandlerTensor(model_script_path=self.model_path)
        return pcoll | RunInference(handler)
```

The Java pipeline calls the Python transform using PythonExternalTransform.

```java
-- Java
// withKwargs invocation
Map<String, Object> kwargs = new HashMap<>();
kwargs.put("model_path", "gs://efx-bucket/v1/model.pt");

PCollection<Row> results = input.apply("RunInference",
    PythonExternalTransform.<String, Row>from("inference_logic.MyInferenceTransform")
        .withKwargs(kwargs)
        .withExtraPackages(Arrays.asList("torch", "apache-beam[gcp]"))
);
```

[ModelHandler](https://beam.apache.org/releases/pydoc/current/apache_beam.ml.inference.html)

## 3. KeyedModelHandler (PyTorch/TF)

**Translation to Java**: Wrap the Python ModelHandler within a KeyedModelHandler inside the Python script. Java passes a PCollection of pairs or strings and the Python transform ensures the keys are preserved through the inference process.

**Why?**: By using the KeyedModelHandler on the Python side, the Java pipeline can send a complex record, have the Python code set the ID aside, run the inference and then re-attach the ID to the result before handing it back to Java.

### Example 

Package your ModelHandler and a PTransform into a Python file:

```python
-- Python
# Wrap the base handler to support (key, features) tuples
def expand(self, pcoll):
    base_handler = PytorchModelHandlerTensor(model_script_path=self.model_path)
    # KeyedModelHandler connects metadata to the tensor
   keyed_handler = KeyedModelHandler(base_handler) 
   
   return (
        pcoll 
        | "RunInference" >> RunInference(
            keyed_handler, 
            model_metadata_pcollection=model_update_pcoll
        )
        | "FormatOutput" >> beam.Map(self.format_output)
    )
```
The Java pipeline calls the Python transform using PythonExternalTransform.

```java
-- Java
// Java provides the data as a Row and Python processes it
// withKwargs is used to pass structured parameters to the Python class
Map<String, Object> kwargs = new HashMap<>();
kwargs.put("model_path", "gs://my-bucket/models/v1/model.pt");

PCollection<Row> results = input.apply("RunInferenceXlang",
    PythonExternalTransform.<Row,Row>from(
"my_inference_logic.MyInferenceTransform",
options.getExpansionServiceUri()
    )
    .withKwargs(kwargs)
    .withOutputCoder(RowCoder.of(inferenceSchema))  // Enforces the schema
);
```

## 4. Event-Mode Hot-Swap

**Translation to Java**: Define the Python RunInference transform to accept a model_metadata_pcollection. In Java, create a side-input stream from a separate Pub/Sub topic and pass it to the Python transform using the withSideInputs method.

**Why?**: Allows the Java SDK to manage the update message while the Python side handles reloading the heavy PyTorch model into worker memory.

### Example 

Package your ModelHandler and a PTransform into a Python file:

```python
-- Python
class MyInferenceTransform(beam.PTransform):
    def expand(self, pcoll, model_update_pcoll=None):
 # model_update_pcoll is the Side Input from the Java environment
        return pcoll | RunInference(
            self.handler, 
            model_metadata_pcollection=model_update_pcoll
        )
```
Modifying to use ‘ImmutableMap.of("key", view)’ to ensure that the Java SDK directly maps the side input to the model_update_pcoll parameter in the Python expand method. GlobalWindow added so the pipeline doesn’t stall looking for an update within a specific time window not matching your main data. 

```java
-- Java
// Java SDK manages the infra side of the update 
PCollection<ModelMetadata> updates = p.apply("ReadModelUpdates", 
    PubsubIO.readMessages().fromTopic(options.getModelUpdateTopic()))
    .apply("WindowUpdates", Window.<ModelMetadata>into(new GlobalWindows())
        .triggering(Repeatedly.forever(AfterPane.elementCountAtLeast(1)))
        .accumulatingFiredPanes());

PCollectionView<ModelMetadata> sideInputView = updates.apply(View.asSingleton());

PCollection<Row> results = inputData.apply("HotSwapInference",
    PythonExternalTransform.<Row, Row>from(
        "inference_logic.MyInferenceTransform", 
        options.getExpansionServiceUri()
    )
    .withKwargs(ImmutableMap.of("model_path", options.getInitialModelPath()))
    .withExtraPackages(Arrays.asList("torch", "apache-beam[gcp]"))
    .withSideInputs(ImmutableMap.of("model_update_pcoll", sideInputView)) 
    .withOutputCoder(RowCoder.of(inferenceSchema))
);
```

## 5. PredictionResult

**Translation to Java**: Python's RunInference produces a PredictionResult object. The Python transform needs to convert the object into a beam.Row so that the Java SDK can map it to a schema in BigQuery or Bigtable.

**Why?**: A Python PredictionResult object is undetectable to Java. Formatting the output as a Row in Python allows the Java pipeline to see a structured object with defined types which makes it easy to write to BigQuery without errors.

### Example 

Package your ModelHandler and a PTransform into a Python file:

```python
-- Python
def format_output(result):
    return {
        'id': result.example[0], 
        'score': result.inference.item(),
        'model_version': result.model_id
    }

def expand(self, pcoll):
    return (pcoll | RunInference(self.handler) | beam.Map(format_output)
    )
```
Modifying to use ‘ImmutableMap.of("key", view)’ to ensure that the Java SDK directly maps the side input to the model_update_pcoll parameter in the Python expand method. GlobalWindow added so the pipeline doesn’t stall looking for an update within a specific time window not matching your main data. 

```java
-- Java
// Java receives the results as a Row, allowing for typed access to the score
results.apply("AnalyzeResults", MapElements.into(TypeDescriptors.voids())
    .via((Row res) -> {
        System.out.println("Inference Score: " + res.getFloat64("score"));
        System.out.println("Model Used: " + res.getString("model_version"));
        return null;
    })
    );
```

---
