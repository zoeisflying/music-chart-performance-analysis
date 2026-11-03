
import pandas as pd
import json
import os

# 1. Đọc modeling dataset
input_file = "data/processed/modeling_dataset.csv"

df = pd.read_csv(input_file)

# 2. Danh sách 9 lyrics features
features = [
    "word_count",
    "unique_word_count",
    "lexical_diversity",
    "repetition_ratio",
    "avg_word_length",
    "line_count",
    "chorus_repetition_count",
    "punctuation_ratio",
    "pronoun_ratio"
]

# 3. Chỉ lấy những bài thu thập lyrics thành công
df = df[df["lyrics_status"] == "success"].copy()

# 4. Tính median riêng cho từng feature theo market
market_medians = {}

for market in ["KR", "US", "VN"]:
    market_data = df[df["market"] == market]

    market_medians[market] = {}

    for feature in features:
        median_value = market_data[feature].median()

        if pd.notna(median_value):
            market_medians[market][feature] = float(median_value)
        else:
            market_medians[market][feature] = None

# 5. Tạo thư mục nếu chưa tồn tại
output_file = "data/processed/lyrics_market_medians.json"

os.makedirs(os.path.dirname(output_file), exist_ok=True)

# 6. Xuất JSON
with open(output_file, "w", encoding="utf-8") as f:
    json.dump(
        market_medians,
        f,
        ensure_ascii=False,
        indent=4
    )

print("Export completed!")
print("Output:", output_file)

# 7. Hiển thị kết quả kiểm tra
for market, values in market_medians.items():
    print(f"\nMarket: {market}")

    for feature, value in values.items():
        print(f"{feature}: {value}")
