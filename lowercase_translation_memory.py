import json

file_path = "translation_memory.json"

with open(file_path, "r", encoding="utf-8") as f:
    data = json.load(f)

lowercased = {k.lower(): v.lower() for k, v in data.items()}

with open(file_path, "w", encoding="utf-8") as f:
    json.dump(lowercased, f, ensure_ascii=False, indent=2)

print("All keys and values have been converted to lowercase.")
