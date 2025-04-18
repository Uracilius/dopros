from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

model_path = "inceptionai/Llama-3.1-Sherkala-8B-Chat"
save_directory = "./llama_model"

# Load tokenizer and model
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(
    model_path, torch_dtype=torch.bfloat16, device_map="auto"
)

# Save the model and tokenizer locally
model.save_pretrained(save_directory)
tokenizer.save_pretrained(save_directory)

print(f"Model saved to {save_directory}")
