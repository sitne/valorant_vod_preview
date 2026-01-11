import torch
from transformers import AutoModelForCausalLM, AutoProcessor
from PIL import Image
import inspect

model_path = "PaddlePaddle/PaddleOCR-VL"

print("Loading model...")
model = AutoModelForCausalLM.from_pretrained(
    model_path, 
    trust_remote_code=True, 
    torch_dtype=torch.float16,
    device_map="auto"
)
print(f"Model class: {model.__class__.__name__}")

print("Loading processor...")
processor = AutoProcessor.from_pretrained(model_path, trust_remote_code=True)

print("Inspecting forward signature...")
if hasattr(model, "forward"):
    print(inspect.signature(model.forward))
else:
    print("Model has no forward method?")

# Dummy image
image = Image.new('RGB', (100, 100), color='red')
messages = [
    {"role": "user", "content": [
        {"type": "image", "image": image},
        {"type": "text", "text": "OCR:"}
    ]}
]

print("Preparing inputs...")
inputs = processor.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=True,
    return_dict=True,
    return_tensors="pt"
).to(model.device)

print(f"Input keys: {inputs.keys()}")

print("Generating...")
try:
    outputs = model.generate(**inputs, max_new_tokens=10)
    print("Generation/Inference successful.")
    print(processor.batch_decode(outputs, skip_special_tokens=True)[0])
except Exception as e:
    print(f"Generation failed: {e}")
    # Try to print which hook failed if possible
    import traceback
    traceback.print_exc()
