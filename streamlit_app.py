import sqlite3
import streamlit as st
import pandas as pd
from collections import Counter

# Determine the common ingredients everyone tends to have in their house
common_ingredients = [
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


def count_unique_vals(df, column_name):
    # Flatten all words into a single list
    all_unique_values = [
        value.strip()  # Strip any extra spaces from ingredients
        for column_values in df[column_name]  # Iterate over the rows in the column
        for value in column_values  # Iterate over each ingredient in the list
        if value is not None  # Skip None values
    ]

    # Count occurrences of each unique ingredient
    unique_counts = Counter(all_unique_values)

    return unique_counts


# Retrieve recipes data from db
conn = sqlite3.connect("./data/standardised_recipes.db")
query = "SELECT * FROM recipes"
df_recipes = pd.read_sql_query(query, conn)
conn.close()

# Convert the 'normalised_ingredients', 'cuisine' and 'course' columns from string to list
df_recipes["normalised_ingredients"] = df_recipes["normalised_ingredients"].apply(
    lambda x: [ingredient.strip() for ingredient in x.split(";")]
)
df_recipes["course"] = df_recipes["course"].apply(
    lambda x: [course.strip() for course in x.split(",")]
)
df_recipes["cuisine"] = df_recipes["cuisine"].apply(
    lambda x: [cuisine.strip() for cuisine in x.split(",")]
)

# Create a list of the unique values for 'normalised_ingredients', 'cuisine' and 'course' columns
unique_cuisine = list(count_unique_vals(df_recipes, "cuisine").keys())
unique_course = list(count_unique_vals(df_recipes, "course").keys())
unique_ingredients = list(
    count_unique_vals(df_recipes, "normalised_ingredients").keys()
)

# Create a Streamlit app
st.set_page_config(layout="wide")
st.title("Asian Recipe Recommendation")


# Expander for search and filter options
with st.expander("Search and Filter", expanded=True):
    # Allows user to choose the cuisine they want
    selection_cuisine = st.pills(
        "Select Cuisines:", unique_cuisine, selection_mode="multi"
    )

    # Allows user to choose the type of meal they'd like
    selection_course = st.pills(
        "Select Courses:", unique_course, selection_mode="multi"
    )

    # Allows users to select maximum time the recipe takes to cook

    selection_time = st.number_input(
        "How long can you spend cooking [minutes]?:", 0, 10000
    )

    # Create a separate DataFrame for recipes that the user can make with up to `missing_count` missing ingredients
    missing_count = st.number_input(
        "Give the maximum number of ingredients that can be missing from a recipe:",
        min_value=0,
        max_value=5,
        step=1,
        value=0,
    )

    selection_ingredients = st.multiselect(
        "Input the ingredients you have at home: ",
        unique_ingredients,
        default=common_ingredients,
    )


# Filter the DataFrame to get recipes with all ingredients
filtered_data = df_recipes[
    df_recipes["cuisine"].apply(
        lambda x: any(cuisine in x for cuisine in selection_cuisine)
    )
    & df_recipes["course"].apply(
        lambda x: any(course in x for course in selection_course)
    )
    & (df_recipes["total_time_minutes"] <= selection_time)
    & df_recipes["normalised_ingredients"].apply(
        lambda ingredients: all(
            ingredient in selection_ingredients for ingredient in ingredients
        )
    )
]


# # # Display the data in a table
# st.write("Data from SQL Database:")
# st.write(filtered_data)


# Filter for recipes that the user can make with up to `missing_count` missing ingredients
missing_ingredients_df = df_recipes[
    df_recipes["cuisine"].apply(
        lambda x: any(cuisine in x for cuisine in selection_cuisine)
    )
    & df_recipes["course"].apply(
        lambda x: any(course in x for course in selection_course)
    )
    & (df_recipes["total_time_minutes"] <= selection_time)
    & df_recipes["normalised_ingredients"].apply(
        lambda ingredients: 0
        < sum(
            1 for ingredient in ingredients if ingredient not in selection_ingredients
        )
        <= missing_count
    )
]

# # Display the filtered DataFrame
# st.write(f"Recipes with up to {missing_count} missing ingredients:")
# st.dataframe(missing_ingredients_df)


########

tab_names = ["Recipes with all ingredients available"]


if missing_count != 0:
    tab_names.append("Recipes with missing ingredients")


def populate_recipes(df, missing=False):
    # Number of recipes per row
    num_recipes_per_row = 2

    # Display recipes in a two-per-row layout
    for i in range(0, len(df), num_recipes_per_row):
        cols = st.columns(num_recipes_per_row)  # Create columns for the current row
        for j, col in enumerate(cols):
            if i + j < len(df):  # Ensure we don't go out of bounds
                recipe = df.iloc[i + j]
                with col:
                    # Create a layout with two columns: image on the left, details on the right
                    image_col, text_col = st.columns([1, 2])

                    # Image column
                    with image_col:
                        st.image(recipe["image_url"], use_container_width=True)

                    # Text column
                    with text_col:
                        # st.subheader(recipe["title"])  # Recipe title

                        st.markdown(f"#### [{recipe['title']}]({recipe['link']})")
                        st.write(recipe["description"])  # Recipe description

                        if missing:
                            missing_items = [
                                item
                                for item in recipe["normalised_ingredients"]
                                if item not in selection_ingredients
                            ]
                            ingredients_str = ", ".join(missing_items)
                            st.write(f"Missing ingredients: {ingredients_str}")


if not filtered_data.empty or not missing_ingredients_df.empty:
    if tab_names:
        tab_objects = st.tabs(tab_names)

        # Populate each tab with its content
        for tab, name in zip(tab_objects, tab_names):
            if name == tab_names[0]:
                with tab:
                    populate_recipes(filtered_data)
            else:
                with tab:
                    populate_recipes(missing_ingredients_df, missing=True)
