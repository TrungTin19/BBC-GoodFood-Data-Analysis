# Offline EDA Summary

- Database: `C:\Users\dhp01\OneDrive\Máy tính\bai-tap\BBC-GoodFood-Data-Analysis\data\recipes.db`
- Status: **ok**
- Database exists: `True`

## Row Counts

```json
{
  "recipes": 1146,
  "ingredients": 12389
}
```

## Time Quality Used For EDA

```json
{
  "prep_time_min": {
    "raw_count": 1146,
    "valid_count": 1137,
    "invalid_count": 0,
    "outlier_count": 9,
    "threshold_minutes": 1440
  },
  "cook_time_min": {
    "raw_count": 1145,
    "valid_count": 1053,
    "invalid_count": 0,
    "outlier_count": 92,
    "threshold_minutes": 1440
  }
}
```

## Charts and Interpretation

### rating_distribution

- Output: `C:\Users\dhp01\OneDrive\Máy tính\bai-tap\BBC-GoodFood-Data-Analysis\outputs\charts\rating_distribution.png`
- Interpretation: The chart shows 889 rated recipes. Median=4.50, mean=4.38. Ratings are concentrated near the high end. Missing ratings are excluded.

### top_ingredients

- Output: `C:\Users\dhp01\OneDrive\Máy tính\bai-tap\BBC-GoodFood-Data-Analysis\outputs\charts\top_ingredients.png`
- Interpretation: The chart ranks the 20 most frequent cleaned ingredients. `olive oil` is most common with 228 appearances. Limitation: ingredient cleaning may merge or split synonyms imperfectly.

### difficulty_distribution

- Output: `C:\Users\dhp01\OneDrive\Máy tính\bai-tap\BBC-GoodFood-Data-Analysis\outputs\charts\difficulty_distribution.png`
- Interpretation: The chart shows recipe difficulty categories. `Easy` is the dominant group. Limitation: missing or changed BBC labels are grouped as Unknown.

### dietary_distribution

- Output: `C:\Users\dhp01\OneDrive\Máy tính\bai-tap\BBC-GoodFood-Data-Analysis\outputs\charts\dietary_distribution.png`
- Interpretation: The chart shows that dietary labels are multi-label and imbalanced. Limitation: labels come from site tags/keywords and may be noisy or incomplete.

### cooking_time_distribution

- Output: `C:\Users\dhp01\OneDrive\Máy tính\bai-tap\BBC-GoodFood-Data-Analysis\outputs\charts\cooking_time_distribution.png`
- Interpretation: The chart excludes invalid values and values above 1440 minutes so unrealistic outliers do not distort the distribution. Excluded outliers: 101; other invalid values: 0. The threshold is one full day, which is generous for recipe prep/cook durations.

