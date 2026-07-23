import json

with open("Interview_Questions.json", "r") as f:
    data = json.load(f)

kompetensi_set = set()
for item in data:
    kompetensi_set.add(item["kompetensi"])

print(f"Total Pertanyaan di JSON: {len(data)}")
print(f"Total Kompetensi Unik: {len(kompetensi_set)}")
print(f"Rata-rata tahap (S/T/A/R) per kompetensi: {len(data) / len(kompetensi_set)}")
