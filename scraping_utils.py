import requests
from bs4 import BeautifulSoup
import pandas as pd


def generate_urls(base_url=None, pages=None, categories=None, pages_per_category=None):
    """
    Generates a list of URLs based on pagination or categories.

    Parameters:
        base_url (str): Base URL for pagination (e.g., "https://example.com/page/{}/").
        pages (int): Number of pages to iterate over (used with base_url).
        categories (list): List of category slugs (e.g., ["thai-soups", "thai-desserts"]).
        pages_per_category (list): Number of pages for each category (used with categories).

    Returns:
        list: A list of generated URLs.
    """
    urls = []

    if base_url and pages:
        # Generate URLs for paginated pages
        urls = [base_url.format(page) for page in range(1, pages + 1)]

    elif base_url and categories and pages_per_category:
        # Generate URLs for categories with page counts
        for i, category in enumerate(categories):
            for page in range(1, pages_per_category[i] + 1):
                urls.append(base_url.format(category, page))

    else:
        raise ValueError(
            "Invalid input: Provide either (base_url and pages) or (base_url, categories, and pages_per_category)."
        )

    return urls


def scrape_recipes(
    all_urls,
    recipe_card_selector=None,
    title_selector=None,
    image_selector=None,
    image_attr="src",
    headers=None,
):
    """
    Scrapes recipe links from a list of URLs on food blogs.

    Parameters:
        all_urls (list): List of URLs to scrape.
        recipe_card_selector (str): CSS selector for finding recipe cards.
        title_selector (str): CSS selector for extracting the title.
        image_selector (str): CSS selector for extracting the image tag.
        image_attr (str): Attribute in the image tag that contains the image URL (default is "src").
        headers (dict): Headers to include in requests.

    Returns:
        list: A list of dictionaries containing recipe data (title, link, image_url, image_data).
    """
    recipes = []
    for url in all_urls:
        print(f"Scraping {url}")
        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"Failed to fetch {url}")
            continue

        soup = BeautifulSoup(response.content, "html.parser")
        recipe_cards = soup.select(recipe_card_selector)
        for card in recipe_cards:
            title_tag = card.select_one(title_selector)
            title = title_tag.text.strip() if title_tag else "No title"
            link_tag = title_tag.find("a") if title_tag else None
            link = link_tag["href"] if link_tag else None

            image_tag = card.select_one(image_selector)
            image_url = (
                image_tag[image_attr]
                if image_tag and image_attr in image_tag.attrs
                else None
            )

            recipes.append(
                {
                    "title": title,
                    "link": link,
                    "image_url": image_url,
                }
            )

        print(f"Finished scraping {url}")

    return recipes


def parse_recipes(
    recipes,
    title_selector,
    description_selector,
    time_selector,
    type_food_selector,
    ingredients_selector,
    nutrition_selector,
    instructions_selector,
    headers=None,
    check_recipe_exists=None,
    check_recipe_text=None,
):
    """
    Parse detailed recipe information from a list of recipe URLs.

    Parameters:
        recipes (list): List of dictionaries containing 'link' for each recipe.
        title_selector (str): CSS selector for the recipe title.
        description_selector (str): CSS selector for the recipe description.
        time_selector (str): CSS selector for the recipe time block.
        type_food_selector (str): CSS selector for the type of food block.
        ingredients_selector (str): CSS selector for the ingredient items.
        nutrition_selector (str): CSS selector for the nutrition items.
        instructions_selector (str): CSS selector for the instructions block.
        headers (dict): Optional headers for HTTP requests.
        check_recipe_exists (tuple): A tuple containing a selector to check if a recipe exists and optional expected text.
        check_recipe_text (str): Text to match if `check_recipe_exists` is not None.

    Returns:
        DataFrame: A Pandas DataFrame containing the parsed recipes.
    """
    parsed_recipes = []

    for i, current_recipe in enumerate(recipes):
        url = current_recipe["link"]
        print(f"\rProgress: {i+1}/{len(recipes)}, URL: {url}", end="")

        response = requests.get(url, headers=headers)
        if response.status_code != 200:
            print(f"\nFailed to fetch {url}")
            continue

        soup = BeautifulSoup(response.content, "html.parser")

        # Check if recipe exists
        if check_recipe_exists:
            exists_block = soup.select_one(check_recipe_exists[0])
            if not exists_block or (
                check_recipe_text and exists_block.text.strip() != check_recipe_text
            ):
                continue

        # Extract Title
        title_block = soup.select_one(title_selector)
        if title_block:
            current_recipe["title"] = title_block.text.strip()

        # Extract Description
        description_block = soup.select_one(description_selector)
        if description_block:
            current_recipe["description"] = description_block.text.strip()

        # Extract Time
        time_block = soup.select_one(time_selector)
        if time_block:
            time_list = time_block.text.strip().split()
            if len(time_list) >= 4:  # Handle missing or short time strings
                label = " ".join(time_list[0:2])
                value = " ".join(time_list[2:4])
                current_recipe[label] = value

        # Extract Type of Food
        type_food_block = soup.select_one(type_food_selector)
        if type_food_block:
            type_cards = type_food_block.select(".wprm-recipe-tag-container")
            for card in type_cards:
                label = card.select_one(".wprm-recipe-tag-label")
                value = card.select_one(".wprm-block-text-normal")
                if label and value:
                    current_recipe[label.text.strip()] = value.text.strip()

        # Extract Ingredients
        ingredients = []
        ingredient_cards = soup.select(ingredients_selector)
        for card in ingredient_cards:
            ingredient_block = card.select_one(".wprm-recipe-ingredient-name")
            if ingredient_block:
                ingredients.append(ingredient_block.text.strip())
        current_recipe["ingredients"] = ingredients

        # Extract Nutrition
        nutrition_cards = soup.select(nutrition_selector)
        for card in nutrition_cards:
            label = card.select_one(".wprm-nutrition-label-text-nutrition-label")
            value = card.select_one(".wprm-nutrition-label-text-nutrition-value")
            unit = card.select_one(".wprm-nutrition-label-text-nutrition-unit")
            if label and value and unit:
                current_recipe[label.text.strip()] = (
                    f"{value.text.strip()} {unit.text.strip()}"
                )

        # Extract Instructions
        instructions_block = soup.select_one(instructions_selector)
        if instructions_block:
            current_recipe["instructions"] = instructions_block.text.strip()

        parsed_recipes.append(current_recipe)

    return pd.DataFrame(parsed_recipes)
