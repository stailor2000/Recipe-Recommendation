import sqlite3
from scraping_utils import scrape_recipes, generate_urls, parse_recipes


if __name__ == "__main__":

    # Generate a list of urls which are the pages on which recipe cards are displayed
    all_urls = generate_urls(
        base_url="https://www.justonecookbook.com/recipes/page/{}/", pages=19
    )

    # Generates a list of all recipe urls found on the food blog
    recipes = scrape_recipes(
        all_urls=all_urls,
        recipe_card_selector="article.post-filter.post-sm.post-abbr",
        title_selector="h3.article-title",
        image_selector="img",
        image_attr="src",
    )

    # Create a dataframe to store the metadata for each recipe
    df_japanese_recipes = parse_recipes(
        recipes=recipes,
        title_selector="h2.wprm-recipe-name.wprm-block-text-bold",
        description_selector="div.wprm-recipe-summary.wprm-block-text-normal",
        time_selector="div.wprm-recipe-total-time-container",
        type_food_selector="div.wprm-recipe-meta-container",
        ingredients_selector="li.wprm-recipe-ingredient",
        nutrition_selector="span.wprm-nutrition-label-text-nutrition-container",
        instructions_selector="div.wprm-recipe-instructions-container",
        check_recipe_exists=("span.jump-text", "Jump to Recipe"),
    )

    # Convert lists to strings so df can be stored in sql db
    if "ingredients" in df_japanese_recipes.columns:
        df_japanese_recipes["ingredients"] = df_japanese_recipes["ingredients"].apply(
            lambda x: "; ".join(x) if isinstance(x, list) else x
        )

    # Connect to SQLite database (or create it if it doesn't exist)
    conn = sqlite3.connect("./data/japanese_recipes.db")

    # Save DataFrame to SQL database
    df_japanese_recipes.to_sql("recipes", conn, if_exists="replace", index=False)

    # Close the connection
    conn.close()

    print("Data saved to database!")
