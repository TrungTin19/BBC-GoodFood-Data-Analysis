# -*- coding: utf-8 -*-
"""
seed_data.py - Tạo dữ liệu mẫu cho database
================================================
Chèn 8 công thức mẫu vào database để test ngay mà không cần crawl.
Chạy: python seed_data.py
"""

import sys
import os

# Đảm bảo import đúng khi chạy từ thư mục dự án
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import create_tables, get_connection, get_recipe_count
from config import DB_PATH


# ============================================================
# DỮ LIỆU MẪU: 8 CÔNG THỨC ĐA DẠNG
# ============================================================
SAMPLE_RECIPES = [
    {
        "title": "Classic Chicken Curry",
        "url": "https://www.bbcgoodfood.com/recipes/classic-chicken-curry",
        "prep_time_min": 20,
        "cook_time_min": 45,
        "difficulty": "Easy",
        "rating": 4.6,
        "review_count": 350,
        "dietary_labels": "Gluten-free",
        "raw_ingredients": "500g chicken breast; 2 onions; 3 cloves garlic; 2 tbsp curry powder; 400ml coconut milk; 1 tbsp vegetable oil; 1 tsp ginger; salt and pepper",
        "instructions": "Step 1: Heat oil in a large pan\nStep 2: Add onions and cook until soft\nStep 3: Add garlic, ginger and curry powder\nStep 4: Add chicken and cook for 5 minutes\nStep 5: Pour in coconut milk and simmer for 30 minutes\nStep 6: Season and serve with rice",
        "description": "A rich and warming chicken curry that's easy to make at home.",
        "image_url": "https://images.immediate.co.uk/production/volatile/sites/30/2020/08/chicken-curry-161144e.jpg",
        "clean_ingredients": ["chicken breast", "onion", "garlic", "curry powder", "coconut milk", "vegetable oil", "ginger", "salt", "pepper"],
    },
    {
        "title": "Beef Stew with Root Vegetables",
        "url": "https://www.bbcgoodfood.com/recipes/beef-stew-root-vegetables",
        "prep_time_min": 30,
        "cook_time_min": 120,
        "difficulty": "More effort",
        "rating": 4.5,
        "review_count": 280,
        "dietary_labels": "",
        "raw_ingredients": "800g beef chuck; 3 potatoes; 2 carrots; 2 parsnips; 2 onions; 2 cloves garlic; 500ml beef stock; 2 tbsp flour; 2 tbsp olive oil; thyme; bay leaves",
        "instructions": "Step 1: Cut beef into chunks and coat with flour\nStep 2: Brown beef in batches\nStep 3: Saut onions and garlic\nStep 4: Add vegetables and stock\nStep 5: Simmer for 2 hours until tender",
        "description": "A hearty beef stew perfect for cold winter days.",
        "image_url": "https://images.immediate.co.uk/production/volatile/sites/30/2020/08/beef-stew.jpg",
        "clean_ingredients": ["beef chuck", "potato", "carrot", "parsnip", "onion", "garlic", "beef stock", "flour", "olive oil", "thyme", "bay leaf"],
    },
    {
        "title": "Vegetable Stir Fry with Tofu",
        "url": "https://www.bbcgoodfood.com/recipes/veg-stir-fry-tofu",
        "prep_time_min": 15,
        "cook_time_min": 10,
        "difficulty": "Easy",
        "rating": 4.3,
        "review_count": 180,
        "dietary_labels": "Vegetarian, Vegan",
        "raw_ingredients": "300g firm tofu; 1 broccoli; 1 red bell pepper; 200g mushrooms; 3 tbsp soy sauce; 1 tbsp sesame oil; 2 cloves garlic; 1 tsp ginger; rice noodles",
        "instructions": "Step 1: Press and cube tofu\nStep 2: Stir fry tofu until golden\nStep 3: Add vegetables and cook for 3-4 minutes\nStep 4: Add sauce and toss\nStep 5: Serve over rice noodles",
        "description": "A quick and healthy vegetarian stir fry.",
        "image_url": "https://images.immediate.co.uk/production/volatile/sites/30/2020/08/stir-fry.jpg",
        "clean_ingredients": ["firm tofu", "broccoli", "bell pepper", "mushroom", "soy sauce", "sesame oil", "garlic", "ginger", "rice noodle"],
    },
    {
        "title": "French Onion Soup",
        "url": "https://www.bbcgoodfood.com/recipes/french-onion-soup",
        "prep_time_min": 15,
        "cook_time_min": 60,
        "difficulty": "Easy",
        "rating": 4.7,
        "review_count": 420,
        "dietary_labels": "Vegetarian",
        "raw_ingredients": "6 large onions; 50g butter; 1 tbsp olive oil; 1 tsp sugar; 1.5 litres vegetable stock; 150g gruyere cheese; 4 slices crusty bread; thyme",
        "instructions": "Step 1: Slice onions thinly\nStep 2: Cook onions in butter and oil for 40 minutes\nStep 3: Add sugar and stock\nStep 4: Simmer for 20 minutes\nStep 5: Top with bread and cheese, grill until golden",
        "description": "Classic French onion soup with melted cheese croutons.",
        "image_url": "https://images.immediate.co.uk/production/volatile/sites/30/2020/08/onion-soup.jpg",
        "clean_ingredients": ["onion", "butter", "olive oil", "sugar", "vegetable stock", "gruyere cheese", "crusty bread", "thyme"],
    },
    {
        "title": "Salmon with Lemon Dill Sauce",
        "url": "https://www.bbcgoodfood.com/recipes/salmon-lemon-dill",
        "prep_time_min": 10,
        "cook_time_min": 20,
        "difficulty": "Easy",
        "rating": 4.8,
        "review_count": 520,
        "dietary_labels": "Gluten-free",
        "raw_ingredients": "4 salmon fillets; 2 lemons; 200ml cream; bunch of dill; 2 cloves garlic; 1 tbsp butter; salt; pepper; asparagus",
        "instructions": "Step 1: Season salmon fillets\nStep 2: Pan sear skin-side down for 4 minutes\nStep 3: Flip and cook 3 more minutes\nStep 4: Make sauce with cream, lemon and dill\nStep 5: Serve with asparagus",
        "description": "Pan-seared salmon with a creamy lemon dill sauce.",
        "image_url": "https://images.immediate.co.uk/production/volatile/sites/30/2020/08/salmon.jpg",
        "clean_ingredients": ["salmon fillet", "lemon", "cream", "dill", "garlic", "butter", "salt", "pepper", "asparagus"],
    },
    {
        "title": "Pasta Carbonara",
        "url": "https://www.bbcgoodfood.com/recipes/pasta-carbonara",
        "prep_time_min": 10,
        "cook_time_min": 20,
        "difficulty": "Easy",
        "rating": 4.5,
        "review_count": 890,
        "dietary_labels": "",
        "raw_ingredients": "400g spaghetti; 200g pancetta; 4 egg yolks; 100g parmesan; 2 cloves garlic; black pepper; olive oil",
        "instructions": "Step 1: Cook pasta al dente\nStep 2: Fry pancetta until crispy\nStep 3: Mix egg yolks with parmesan\nStep 4: Combine hot pasta with pancetta\nStep 5: Add egg mixture off heat, toss quickly",
        "description": "Authentic Italian carbonara with crispy pancetta.",
        "image_url": "https://images.immediate.co.uk/production/volatile/sites/30/2020/08/carbonara.jpg",
        "clean_ingredients": ["spaghetti", "pancetta", "egg yolk", "parmesan", "garlic", "black pepper", "olive oil"],
    },
    {
        "title": "Thai Green Curry",
        "url": "https://www.bbcgoodfood.com/recipes/thai-green-curry",
        "prep_time_min": 20,
        "cook_time_min": 25,
        "difficulty": "More effort",
        "rating": 4.6,
        "review_count": 310,
        "dietary_labels": "Gluten-free",
        "raw_ingredients": "400g chicken thighs; 400ml coconut milk; 3 tbsp green curry paste; 200g Thai aubergine; 150g green beans; bunch of Thai basil; 2 tbsp fish sauce; 1 tbsp palm sugar; lime",
        "instructions": "Step 1: Fry curry paste in coconut cream\nStep 2: Add chicken and cook through\nStep 3: Add coconut milk and vegetables\nStep 4: Simmer until vegetables are tender\nStep 5: Season with fish sauce and lime\nStep 6: Garnish with Thai basil",
        "description": "Authentic Thai green curry with tender chicken.",
        "image_url": "https://images.immediate.co.uk/production/volatile/sites/30/2020/08/green-curry.jpg",
        "clean_ingredients": ["chicken thigh", "coconut milk", "green curry paste", "aubergine", "green bean", "thai basil", "fish sauce", "palm sugar", "lime"],
    },
    {
        "title": "Chocolate Lava Cake",
        "url": "https://www.bbcgoodfood.com/recipes/chocolate-lava-cake",
        "prep_time_min": 15,
        "cook_time_min": 12,
        "difficulty": "More effort",
        "rating": 4.9,
        "review_count": 650,
        "dietary_labels": "Vegetarian",
        "raw_ingredients": "200g dark chocolate; 100g butter; 3 eggs; 50g sugar; 30g flour; cocoa powder; vanilla extract",
        "instructions": "Step 1: Melt chocolate and butter\nStep 2: Whisk eggs and sugar\nStep 3: Fold in chocolate mixture and flour\nStep 4: Pour into greased ramekins\nStep 5: Bake at 200C for 12 minutes\nStep 6: Turn out and serve immediately",
        "description": "Indulgent chocolate lava cake with a molten center.",
        "image_url": "https://images.immediate.co.uk/production/volatile/sites/30/2020/08/lava-cake.jpg",
        "clean_ingredients": ["dark chocolate", "butter", "egg", "sugar", "flour", "cocoa powder", "vanilla extract"],
    },
]


def seed_database():
    """
    Chèn dữ liệu mẫu vào database.
    Bỏ qua nếu database đã có dữ liệu.
    """
    # Khởi tạo bảng nếu chưa có
    create_tables()

    # Kiểm tra đã có dữ liệu chưa
    count = get_recipe_count()
    if count > 0:
        print(f"Database đã có {count} công thức. Bỏ qua seed.")
        return

    print("Đang chèn dữ liệu mẫu...")

    conn = get_connection()
    cursor = conn.cursor()

    for recipe_data in SAMPLE_RECIPES:
        cursor.execute("""
            INSERT OR IGNORE INTO recipes
                (title, url, prep_time_min, cook_time_min, difficulty,
                 rating, review_count, dietary_labels, raw_ingredients,
                 instructions, description, image_url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            recipe_data["title"],
            recipe_data["url"],
            recipe_data.get("prep_time_min"),
            recipe_data.get("cook_time_min"),
            recipe_data.get("difficulty"),
            recipe_data.get("rating"),
            recipe_data.get("review_count", 0),
            recipe_data.get("dietary_labels", ""),
            recipe_data.get("raw_ingredients", ""),
            recipe_data.get("instructions", ""),
            recipe_data.get("description", ""),
            recipe_data.get("image_url", ""),
        ))

        # Chỉ insert ingredients khi recipe mới được chèn (rowcount > 0)
        if cursor.rowcount > 0:
            recipe_id = cursor.lastrowid

            for ing_name in recipe_data.get("clean_ingredients", []):
                if ing_name.strip():
                    cursor.execute(
                        "INSERT INTO ingredients (recipe_id, ingredient) VALUES (?, ?)",
                        (recipe_id, ing_name.strip()),
                    )

    conn.commit()
    conn.close()
    print(f"Đã chèn {len(SAMPLE_RECIPES)} công thức mẫu vào database.")
    print(f"Database: {DB_PATH}")


if __name__ == "__main__":
    seed_database()