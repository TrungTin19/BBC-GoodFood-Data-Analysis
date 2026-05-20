# Offline Model Evaluation

- Database: `C:\Users\dhp01\OneDrive\Máy tính\bai-tap\BBC-GoodFood-Data-Analysis\data\recipes.db`
- Status: **ok**
- Database exists: `True`

## Search Index

```json
{
  "status": "ok",
  "reason": "",
  "sample_query": "chopped oil sugar",
  "results": [
    {
      "title": "French Onion Soup",
      "similarity": 0.3903
    },
    {
      "title": "Puttanesca baked gnocchi",
      "similarity": 0.2295
    },
    {
      "title": "Tteokbokki lasagne",
      "similarity": 0.172
    },
    {
      "title": "Bhel puri",
      "similarity": 0.0784
    },
    {
      "title": "Puff puff",
      "similarity": 0.0746
    }
  ],
  "recipe_count": 1146,
  "feature_count": 5000
}
```

## Classification Metrics

### Vegetarian

```json
{
  "status": "ok",
  "total_samples": 1146,
  "positive_count": 569,
  "negative_count": 577,
  "train_size": 916,
  "test_size": 230,
  "models": {
    "nb": {
      "accuracy": 0.787,
      "precision": 0.8571,
      "recall": 0.6842,
      "f1": 0.761,
      "confusion_matrix": [
        [
          103,
          13
        ],
        [
          36,
          78
        ]
      ],
      "cv_accuracy_mean": 0.7282,
      "cv_folds": 5
    },
    "logistic": {
      "accuracy": 0.8043,
      "precision": 0.8,
      "recall": 0.807,
      "f1": 0.8035,
      "confusion_matrix": [
        [
          93,
          23
        ],
        [
          22,
          92
        ]
      ],
      "cv_accuracy_mean": 0.8013,
      "cv_folds": 5
    }
  }
}
```

### Vegan

```json
{
  "status": "ok",
  "total_samples": 1146,
  "positive_count": 123,
  "negative_count": 1023,
  "train_size": 916,
  "test_size": 230,
  "models": {
    "nb": {
      "accuracy": 0.8957,
      "precision": 0.5714,
      "recall": 0.16,
      "f1": 0.25,
      "confusion_matrix": [
        [
          202,
          3
        ],
        [
          21,
          4
        ]
      ],
      "cv_accuracy_mean": 0.8897,
      "cv_folds": 5
    },
    "logistic": {
      "accuracy": 0.913,
      "precision": 0.7778,
      "recall": 0.28,
      "f1": 0.4118,
      "confusion_matrix": [
        [
          203,
          2
        ],
        [
          18,
          7
        ]
      ],
      "cv_accuracy_mean": 0.8886,
      "cv_folds": 5
    }
  }
}
```

### Gluten-free

```json
{
  "status": "ok",
  "total_samples": 1146,
  "positive_count": 263,
  "negative_count": 883,
  "train_size": 916,
  "test_size": 230,
  "models": {
    "nb": {
      "accuracy": 0.8087,
      "precision": 0.5957,
      "recall": 0.5283,
      "f1": 0.56,
      "confusion_matrix": [
        [
          158,
          19
        ],
        [
          25,
          28
        ]
      ],
      "cv_accuracy_mean": 0.8166,
      "cv_folds": 5
    },
    "logistic": {
      "accuracy": 0.8609,
      "precision": 0.7234,
      "recall": 0.6415,
      "f1": 0.68,
      "confusion_matrix": [
        [
          164,
          13
        ],
        [
          19,
          34
        ]
      ],
      "cv_accuracy_mean": 0.8362,
      "cv_folds": 5
    }
  }
}
```

## Limitations

- Dietary labels are noisy because they come from source tags/keywords.
- Class imbalance can make accuracy look better than recall/F1.
- The dataset may be small or stale if data/ is ignored in a fresh clone.
- No direct data leakage from dietary_labels into features is used here, but recipe titles/descriptions are intentionally not used to reduce leakage risk.
