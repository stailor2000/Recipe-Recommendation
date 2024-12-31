import sqlite3
from scraping_utils import scrape_recipes, generate_urls, parse_recipes


if __name__ == "__main__":

    categories = [
        "soups-guk-and-stews-jjigae/",
        "appetizer-2/",
        "salads/",
        "main-dishes/",
        "side-dishes/",
        "desserts/",
    ]
    pages_per_category = [3, 2, 2, 5, 5, 3]

    # Generate a list of urls which are the pages on which recipe cards are displayed
    all_urls = generate_urls(
        base_url="https://kimchimari.com/category/{}/page/{}/",
        categories=categories,
        pages_per_category=pages_per_category,
    )

    # Generates a list of all recipe urls found on the food blog
    recipes = scrape_recipes(
        all_urls=all_urls,
        recipe_card_selector="article.status-publish",
        title_selector="h2.entry-title",
        image_selector="img",
        image_attr="data-lazy-src",  # Default to "data-lazy-src" but handle "src" fallback
    )

    # Create a dataframe to store the metadata for each recipe
    df_korean_recipes = parse_recipes(
        recipes=recipes,
        title_selector="h2.wprm-recipe-name",
        description_selector="div.wprm-recipe-summary.wprm-block-text-normal",
        time_selector="div.wprm-recipe-total-time-container",
        type_food_selector="div.wprm-recipe-tags-container",
        ingredients_selector="li.wprm-recipe-ingredient",
        nutrition_selector="span.wprm-nutrition-label-text-nutrition-container",
        instructions_selector="ul.wprm-recipe-instructions",
        check_recipe_exists=("a.wprm-recipe-jump", None),  # Check for valid recipes
    )
    # Convert lists to strings so df can be stored in sql db
    if "ingredients" in df_korean_recipes.columns:
        df_korean_recipes["ingredients"] = df_korean_recipes["ingredients"].apply(
            lambda x: "; ".join(x) if isinstance(x, list) else x
        )

    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect("./data/korean_recipes.db")

    # Save DataFrame to SQL database
    df_korean_recipes.to_sql("recipes", conn, if_exists="replace", index=False)

    # Close the connection
    conn.close()

    print("Data saved to database!")
