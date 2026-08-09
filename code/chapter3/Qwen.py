# Увеличьте HF_ENDPOINT, чтобы избежать прерывания соединения. 
import os
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

# Укажите идентификатор модели
model_id = "Qwen/Qwen1.5-0.5B-Chat"

# Настройте устройство для определения приоритета графического процессора
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using device: {device}")

# Загрузить токенизатор
tokenizer = AutoTokenizer.from_pretrained(model_id)

# Загрузите модель и переместите ее на указанное устройство.
model = AutoModelForCausalLM.from_pretrained(model_id).to(device)

print("Модель и токенизатор загружены!")

# Подготовьте ввод разговора
messages = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "Здравствуйте, представьтесь, пожалуйста."}
]

# Ввод в формате шаблона с использованием токенизатора
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)

# Кодировать вводимый текст
model_inputs = tokenizer([text], return_tensors="pt").to(device)

print("Закодированный входной текст:")
print(model_inputs)

# Используйте модель для генерации ответов
# max_new_tokens контролирует максимальное количество новых токенов, которые может сгенерировать модель.
generated_ids = model.generate(
    model_inputs.input_ids,
    max_new_tokens=512
)

# Отрежьте входную часть сгенерированного идентификатора токена.
# Таким образом, мы декодируем только вновь созданную часть модели.
generated_ids = [
    output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
]

# Раскодируйте сгенерированный идентификатор токена.
response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

print("\nОтвет модели:")
print(response)
