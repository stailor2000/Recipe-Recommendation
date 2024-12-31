import sqlite3
import streamlit as st
import pandas as pd
from utils import count_unique_vals


# Define a list of common ingredients typically available at home
COMMON_INGREDIENTS = [
    "Salt",
    "Soy Sauce",
    "Sugar",
    "Water",
    "Garlic",
    "Ginger",
    "Oil",
    "Black Pepper",
    "Rice",
    "Butter",
    "White Pepper",
    "Chili Powder",
    "Cumin",
    "Chili Pepper Flakes",
    "Garam Masala",
]


def load_recipe_data(db_path="./data/standardised_recipes.db"):
    """
    Loads recipe data from an SQLite database and preprocesses the recipe DataFrame by converting specific columns to lists.

    Parameters:
        db_path (str): Path to the SQLite database.

    Returns:
        pd.DataFrame: DataFrame containing recipe data.
    """
    conn = sqlite3.connect(db_path)
    query = "SELECT * FROM recipes"
    df = pd.read_sql_query(query, conn)
    conn.close()

    df["normalised_ingredients"] = df["normalised_ingredients"].apply(
        lambda x: [ingredient.strip() for ingredient in x.split(";")]
    )
    df["course"] = df["course"].apply(
        lambda x: [course.strip() for course in x.split(",")]
    )
    df["cuisine"] = df["cuisine"].apply(
        lambda x: [cuisine.strip() for cuisine in x.split(",")]
    )
    return df


def filter_recipes(df, cuisines, courses, max_time, ingredients, missing_count):
    """
    Filters the recipes based on user criteria.

    Parameters:
        df (pd.DataFrame): The DataFrame containing recipes.
        cuisines (list): Selected cuisines.
        courses (list): Selected courses.
        max_time (int): Maximum cooking time in minutes.
        ingredients (list): Ingredients the user has at home.
        missing_count (int): Maximum number of missing ingredients.

    Returns:
        tuple: Two DataFrames (recipes with all ingredients, recipes with missing ingredients).
    """
    all_ingredients_df = df[
        df["cuisine"].apply(lambda x: any(cuisine in x for cuisine in cuisines))
        & df["course"].apply(lambda x: any(course in x for course in courses))
        & (df["total_time_minutes"] <= max_time)
        & df["normalised_ingredients"].apply(
            lambda ing: all(ingredient in ingredients for ingredient in ing)
        )
    ]

    missing_ingredients_df = df[
        df["cuisine"].apply(lambda x: any(cuisine in x for cuisine in cuisines))
        & df["course"].apply(lambda x: any(course in x for course in courses))
        & (df["total_time_minutes"] <= max_time)
        & df["normalised_ingredients"].apply(
            lambda ing: 0
            < sum(1 for ingredient in ing if ingredient not in ingredients)
            <= missing_count
        )
    ]

    return all_ingredients_df, missing_ingredients_df


def populate_recipes(df, ingredients, missing=False):
    """
    Displays recipes in a grid format, showing images and details.

    Parameters:
        df (pd.DataFrame): The DataFrame containing recipe data.
        ingredients (list): User-selected ingredients.
        missing (bool): Whether to display missing ingredients.
    """
    num_recipes_per_row = 2
    for i in range(0, len(df), num_recipes_per_row):
        cols = st.columns(num_recipes_per_row)
        for j, col in enumerate(cols):
            if i + j < len(df):
                recipe = df.iloc[i + j]
                with col:
                    image_col, text_col = st.columns([1, 2])

                    with image_col:
                        st.image(recipe["image_url"], use_container_width=True)

                    with text_col:
                        st.markdown(f"#### [{recipe['title']}]({recipe['link']})")
                        st.write(recipe["description"])

                        if missing:
                            missing_items = [
                                item
                                for item in recipe["normalised_ingredients"]
                                if item not in ingredients
                            ]
                            st.write(f"Missing ingredients: {', '.join(missing_items)}")


if __name__ == "__main__":
    # Load and preprocess data
    df_recipes = load_recipe_data()

    # Extract unique values
    unique_cuisine = list(count_unique_vals(df_recipes, "cuisine").keys())
    unique_course = list(count_unique_vals(df_recipes, "course").keys())
    unique_ingredients = list(
        count_unique_vals(df_recipes, "normalised_ingredients").keys()
    )

    # Set up Streamlit app
    st.set_page_config(layout="wide")
    st.title("Asian Recipe Recommendation")

    st.write(
        """
        This app helps you find delicious Asian recipes based on the ingredients you have at home. Simply input the ingredients available in your kitchen, select your preferred cuisines and courses, and let the app recommend recipes that match your ingredients. You can also filter recipes based on maximum cooking time and the number of missing ingredients, making it easy to find the perfect dish, even if you're missing a few items.
        """
    )

    with st.expander("Search and Filter", expanded=True):
        selection_cuisine = st.pills(
            "Select Cuisines:", unique_cuisine, selection_mode="multi"
        )
        selection_course = st.pills(
            "Select Courses:", unique_course, selection_mode="multi"
        )
        selection_time = st.number_input(
            "Maximum cooking time [minutes]:", min_value=0, max_value=10000, step=1
        )
        missing_count = st.number_input(
            "Maximum number of missing ingredients:", min_value=0, max_value=5, step=1
        )
        selection_ingredients = st.multiselect(
            "Input ingredients you have at home:",
            unique_ingredients,
            default=COMMON_INGREDIENTS,
        )

    # Filter recipes
    filtered_data, missing_data = filter_recipes(
        df_recipes,
        selection_cuisine,
        selection_course,
        selection_time,
        selection_ingredients,
        missing_count,
    )

    # Display tabs
    if not filtered_data.empty or not missing_data.empty:
        tab_names = ["Recipes with all ingredients available"]
        if missing_count > 0:
            tab_names.append("Recipes with missing ingredients")

        tabs = st.tabs(tab_names)
        for tab, name in zip(tabs, tab_names):
            if name == "Recipes with all ingredients available":
                with tab:
                    populate_recipes(filtered_data, selection_ingredients)
            else:
                with tab:
                    populate_recipes(missing_data, selection_ingredients, missing=True)
