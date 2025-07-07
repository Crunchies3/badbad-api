import json

# File paths
ata_file = "ata.txt"
eng_file = "eng.txt"
output_file = "aligned_data.json"

# Read and clean lines
with open(ata_file, "r", encoding="utf-8") as f:
    ata_lines = [line.strip() for line in f if line.strip()]

with open(eng_file, "r", encoding="utf-8") as f:
    eng_lines = [line.strip() for line in f if line.strip()]

# Check length match
if len(ata_lines) != len(eng_lines):
    raise ValueError(f"Mismatch: {len(ata_lines)} Ata lines vs {len(eng_lines)} English lines")

# Create dictionary
aligned_dict = {
    ata: eng for ata, eng in zip(ata_lines, eng_lines)
}

# Save to JSON file
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(aligned_dict, f, ensure_ascii=False, indent=2)

print(f"Saved {len(aligned_dict)} sentence pairs to '{output_file}'")
