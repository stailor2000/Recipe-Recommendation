import sqlite3
from scraping_utils import scrape_recipes, generate_urls, parse_recipes
import os


if __name__ == "__main__":
    # Generate a list of urls which are the pages on which recipe cards are displayed
    all_urls = generate_urls(
        base_url="https://ministryofcurry.com/recipe-search/?_paged={}", pages=20
    )

    # Generates a list of all recipe urls found on the food blog
    recipes = scrape_recipes(
        all_urls=all_urls,
        recipe_card_selector="div.fwpl-result",
        title_selector="div.fwpl-item.el-cjl7ci",
        image_selector="img",
        image_attr="data-lazy-src",
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0"
        },
    )

    # Create a dataframe to store the metadata for each recipe
    df_indian_recipes = parse_recipes(
        recipes=recipes,
        title_selector="h2.wprm-recipe-name",
        description_selector="div.wprm-recipe-summary.wprm-block-text-normal",
        time_selector="div.wprm-recipe-total-time-container",
        type_food_selector="div.wprm-recipe-tags-container",
        ingredients_selector="li.wprm-recipe-ingredient",
        nutrition_selector="span.wprm-nutrition-label-text-nutrition-container",
        instructions_selector="ul.wprm-recipe-instructions",
        headers={
            "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0"
        },
        check_recipe_exists=("a.wprm-recipe-jump", None),
    )

    # Convert lists to strings so df can be stored in sql db
    if "ingredients" in df_indian_recipes.columns:
        df_indian_recipes["ingredients"] = df_indian_recipes["ingredients"].apply(
            lambda x: "; ".join(x) if isinstance(x, list) else x
        )

    # Get the path to the main directory (one level up from the current script)
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

    # Construct the path to the database file
    db_path = os.path.join(base_dir, "data", "indian_recipes.db")

    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect(db_path)

    # Save DataFrame to SQL database
    df_indian_recipes.to_sql("recipes", conn, if_exists="replace", index=False)

    # Close the connection
    conn.close()

    print("Data saved to database!")
