# Data Quality Report

- Database: `C:\Users\dhp01\OneDrive\Máy tính\bai-tap\BBC-GoodFood-Data-Analysis\data\recipes.db`
- Status: **ok**
- Database exists: `True`

## Totals

| Metric | Value |
|---|---:|
| recipes | 1146 |
| ingredients | 12389 |

## Missing Values

| Field | Missing count |
|---|---:|
| title | 0 |
| url | 0 |
| rating | 257 |
| prep_time_min | 0 |
| cook_time_min | 1 |
| total_time | not_available |
| total_time_min | not_available |

## Duplicate Checks

| Field | Extra duplicate rows |
|---|---:|
| url_extra_rows | 0 |
| title_extra_rows | 2 |

## Ingredients and Labels

- Recipes without ingredients: `0`

### Top 20 Ingredients

| Ingredient | Count |
|---|---:|
| olive oil | 228 |
| plain flour | 177 |
| caster sugar | 171 |
| eggs | 139 |
| butter | 121 |
| vanilla extract | 121 |
| vegetable oil | 112 |
| double cream | 109 |
| milk | 107 |
| baking powder | 101 |
| golden caster sugar | 95 |
| light brown soft sugar | 84 |
| cornflour | 80 |
| honey | 76 |
| tomato purée | 76 |
| self-raising flour | 74 |
| emon juiced | 73 |
| onion finely chopped | 67 |
| arlic cloves crushed | 66 |
| emon zested and juiced | 61 |

## Rating and Time Statistics

### Rating

```json
{
  "count": 889,
  "mean": 4.3781,
  "median": 4.5,
  "min": 1.0,
  "max": 5.0
}
```

### Time

Raw values include invalid/outlier records. Valid-only values keep 0..1440 minutes.

#### Raw Time Stats

```json
{
  "prep_time_min": {
    "count": 1146,
    "mean": 1389965.6981,
    "median": 15.0,
    "min": 1.0,
    "max": 176986657.0
  },
  "cook_time_min": {
    "count": 1145,
    "mean": 14220803.4987,
    "median": 30.0,
    "min": 1.0,
    "max": 176986657.0
  }
}
```

#### Valid-Only Time Stats

```json
{
  "prep_time_min": {
    "count": 1137,
    "mean": 18.2735,
    "median": 15.0,
    "min": 1.0,
    "max": 180.0
  },
  "cook_time_min": {
    "count": 1053,
    "mean": 45.1681,
    "median": 30.0,
    "min": 1.0,
    "max": 720.0
  }
}
```

### Time Quality

```json
{
  "prep_time_min": {
    "valid_time_count": 1137,
    "invalid_time_count": 0,
    "outlier_time_count": 9,
    "max_valid_time": 180,
    "threshold_minutes": 1440,
    "top_invalid_or_outlier_records": [
      {
        "recipe_id": 59,
        "title": "Tamales",
        "url": "https://www.bbcgoodfood.com/recipes/tamales",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 213,
        "title": "Homemade kimchi",
        "url": "https://www.bbcgoodfood.com/recipes/homemade-kimchi",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 821,
        "title": "Chilli con carne recipe",
        "url": "https://www.bbcgoodfood.com/recipes/chilli-con-carne-recipe",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 1041,
        "title": "Easy lemonade",
        "url": "https://www.bbcgoodfood.com/recipes/really-easy-lemonade",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 1080,
        "title": "Lemon drizzle cake",
        "url": "https://www.bbcgoodfood.com/recipes/lemon-drizzle-cake",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 1094,
        "title": "Roasted cauliflower",
        "url": "https://www.bbcgoodfood.com/recipes/roasted-cauliflower",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 1109,
        "title": "Perfect seared scallops",
        "url": "https://www.bbcgoodfood.com/recipes/seared-scallops-leeks-lemon-chilli-butter",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 1134,
        "title": "Red onion gravy",
        "url": "https://www.bbcgoodfood.com/recipes/red-onion-gravy",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 1146,
        "title": "Espagueti verde (green spaghetti)",
        "url": "https://www.bbcgoodfood.com/recipes/espagueti-verde-green-spaghetti",
        "value": 176986657,
        "reason": ">1440 minutes"
      }
    ]
  },
  "cook_time_min": {
    "valid_time_count": 1053,
    "invalid_time_count": 0,
    "outlier_time_count": 92,
    "max_valid_time": 720,
    "threshold_minutes": 1440,
    "top_invalid_or_outlier_records": [
      {
        "recipe_id": 22,
        "title": "Campari soda & blood orange pitcher",
        "url": "https://www.bbcgoodfood.com/recipes/campari-soda-blood-orange-pitcher",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 48,
        "title": "Mint sauce",
        "url": "https://www.bbcgoodfood.com/recipes/mint-sauce",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 58,
        "title": "Lemon drop martini",
        "url": "https://www.bbcgoodfood.com/recipes/absolut-hunni-lemon-drop-martini",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 59,
        "title": "Tamales",
        "url": "https://www.bbcgoodfood.com/recipes/tamales",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 81,
        "title": "Rainbow hummus plate",
        "url": "https://www.bbcgoodfood.com/recipes/rainbow-hummus-plate",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 87,
        "title": "Shaved kohlrabi salad with pickled jalapeño dressing",
        "url": "https://www.bbcgoodfood.com/recipes/shaved-kohlrabi-salad-with-pickled-jalapeno-dressing",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 95,
        "title": "Snack stadium",
        "url": "https://www.bbcgoodfood.com/recipes/snack-stadium",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 113,
        "title": "Pomegranate salad",
        "url": "https://www.bbcgoodfood.com/recipes/pomegranate-salad",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 136,
        "title": "Espresso eggnog martini",
        "url": "https://www.bbcgoodfood.com/recipes/espresso-eggnog-martini",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 142,
        "title": "Hwachae (Korean watermelon punch)",
        "url": "https://www.bbcgoodfood.com/recipes/hwachae-korean-watermelon-punch",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 148,
        "title": "Spicy tuna wrap",
        "url": "https://www.bbcgoodfood.com/recipes/spicy-tuna-wrap",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 155,
        "title": "Cherry sour",
        "url": "https://www.bbcgoodfood.com/recipes/cherry-sour",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 189,
        "title": "Grapefruit negroni",
        "url": "https://www.bbcgoodfood.com/recipes/grapefruit-negroni",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 195,
        "title": "Honey mustard dressing",
        "url": "https://www.bbcgoodfood.com/recipes/honey-mustard-dressing",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 213,
        "title": "Homemade kimchi",
        "url": "https://www.bbcgoodfood.com/recipes/homemade-kimchi",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 218,
        "title": "Caesar salad wrap",
        "url": "https://www.bbcgoodfood.com/recipes/caesar-salad-wrap",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 223,
        "title": "Shake-it-up chopped salad",
        "url": "https://www.bbcgoodfood.com/recipes/shake-it-up-chopped-salad",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 234,
        "title": "Ezme",
        "url": "https://www.bbcgoodfood.com/recipes/ezme",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 242,
        "title": "Tuna salad sandwich",
        "url": "https://www.bbcgoodfood.com/recipes/tuna-salad-sandwich",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 271,
        "title": "Dolcelatte & prosciutto stuffed dried figs",
        "url": "https://www.bbcgoodfood.com/recipes/dolcelatte-prosciutto-stuffed-dried-figs",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 297,
        "title": "Mini eton mess cheesecake tarts",
        "url": "https://www.bbcgoodfood.com/recipes/mini-eton-mess-cheesecake-tarts",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 307,
        "title": "Horseradish sauce",
        "url": "https://www.bbcgoodfood.com/recipes/horseradish-sauce",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 309,
        "title": "Easy panettone layer cake with spiced buttercream icing",
        "url": "https://www.bbcgoodfood.com/recipes/easy-panettone-layer-cake-with-spiced-buttercream-icing",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 320,
        "title": "Homemade yakisoba sauce",
        "url": "https://www.bbcgoodfood.com/recipes/homemade-yakisoba-sauce",
        "value": 176986657,
        "reason": ">1440 minutes"
      },
      {
        "recipe_id": 328,
        "title": "Chia pudding",
        "url": "https://www.bbcgoodfood.com/recipes/chia-pudding",
        "value": 176986657,
        "reason": ">1440 minutes"
      }
    ]
  }
}
```

## Distributions

### Difficulty

```json
{
  "Easy": 1010,
  "More effort": 112,
  "Unknown": 15,
  "A challenge": 6,
  "Medium": 3
}
```

### Dietary Labels

```json
{
  "Vegetarian": 569,
  "Egg-Free": 286,
  "Gluten-Free": 260,
  "Nut-Free": 247,
  "Dairy-Free": 181,
  "Vegan": 123,
  "Healthy": 100,
  "High-Protein": 89,
  "High-Fibre": 71,
  "Gluten-free": 3,
  "Low-Fat": 1
}
```
