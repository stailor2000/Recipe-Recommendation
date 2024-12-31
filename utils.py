import re
from collections import Counter


def find_unique_vals(df, column_name):
    """
    Finds all unique words in a column, regardless of the entries being lists of words.

    Parameters:
        df (pd.DataFrame): The input DataFrame.
        column_name (str): The column to analyze.

    Returns:
        set: A set of unique words from the column.
    """
    unique_list = set(
        word.strip()
        for courses in df[column_name]
        if courses is not None  # Skip None values
        for word in courses.split(";")
    )
    return unique_list


def clean_column(column, removal_list):
    """
    Cleans a column by removing undesired words.

    Parameters:
        column (str): The input string to clean.
        removal_list (list): A list of words to remove from the column.

    Returns:
        str or None: The cleaned string, or None if the entry should be discarded.
    """
    # Handle None or NaN values
    if not isinstance(column, str):
        return None  # Skip if the column value is not a string

    # Split the string into a list
    col_list = [c.strip() for c in column.split(";")]

    # If the list has only one value and it is in removal_list, return None
    if len(col_list) == 1 and col_list[0] in removal_list:
        return None  # Mark for deletion

    # Remove unwanted entries from the list
    if len(col_list) > 1:
        col_list = [c for c in col_list if c not in removal_list]

    # Rejoin the list into a string
    return "; ".join(col_list)


def map_to_main_category(entry, mapping):
    """
    Maps a string of items to their main categories based on a mapping dictionary.
    Synonyms in the string are replaced by their corresponding main categories,
    and duplicate entries are removed while preserving order.

    Parameters:
        entry (str): A comma-separated string of items to map.
        mapping (dict): A dictionary where keys are main categories and values are lists of synonyms.

    Returns:
        str or None: A comma-separated string of mapped main categories, or None if no matches were found.
    """
    reverse_mapping = {
        synonym: main_category
        for main_category, synonyms in mapping.items()
        for synonym in synonyms
    }
    # Split the string into a list
    entry_list = [item.strip() for item in entry.split(",")]
    # Replace each item in the list
    mapped_list = [
        reverse_mapping[item] for item in entry_list if item in reverse_mapping
    ]
    # Remove duplicates while preserving order
    unique_list = list(dict.fromkeys(mapped_list))
    # Return None if no matches
    if not unique_list:
        return None
    return ", ".join(unique_list)


def clean_ingredient(ingredient):
    # Remove anything that is not a letter or space
    return re.sub(r"[^a-zA-Z\s]", "", ingredient).strip()


def count_unique_vals(df, column_name):
    """
    Counts the unique values in a specified column of a DataFrame, where each entry in the column is a list of items.

    Parameters:
        df (pd.DataFrame): The input DataFrame containing the column to analyze.
        column_name (str): The name of the column in the DataFrame where each row is a list of items.

    Returns:
        Counter: A Counter object with the counts of each unique item in the column.

    Example:
        >>> df = pd.DataFrame({"ingredients": [["apple", "banana"], ["apple", "carrot"], ["banana"]]})
        >>> count_unique_vals(df, "ingredients")
        Counter({"apple": 2, "banana": 2, "carrot": 1})
    """
    # Flatten all words into a single list
    all_ingredients = [
        ingredient.strip()  # Strip any extra spaces from ingredients
        for ingredients in df[column_name]  # Iterate over the rows in the column
        for ingredient in ingredients  # Iterate over each ingredient in the list
        if ingredient is not None  # Skip None values
    ]

    # Count occurrences of each unique ingredient
    ingredient_counts = Counter(all_ingredients)

    return ingredient_counts


def convert_to_minutes_extended(time_str):
    """
    Converts a time duration string into the total number of minutes.

    The function handles time strings that include days, hours, and minutes (both singular and plural forms).
    Invalid or non-string inputs return None by default.

    Parameters:
        time_str (str): A string representing the time duration.
                        Example: "2 days 3 hours 15 minutes"

    Returns:
        int: The total number of minutes represented by the time string.
             Returns None for invalid or non-string inputs.
    """
    # Handle None or NaN values
    if not isinstance(time_str, str):
        return None  # Or 0, if you want to return 0 minutes for invalid entries

    time_str = time_str.lower()
    days = 0
    hours = 0
    minutes = 0

    # Extract days
    if "day" in time_str:
        days_match = re.search(r"(\d+)\s*day", time_str)
        if days_match:
            days = int(days_match.group(1))

    # Extract hours
    if "hour" in time_str:
        hours_match = re.search(r"(\d+)\s*hour", time_str)
        if hours_match:
            hours = int(hours_match.group(1))

    # Extract minutes
    if "minute" in time_str:
        minutes_match = re.search(r"(\d+)\s*minute", time_str)
        if minutes_match:
            minutes = int(minutes_match.group(1))

    # Convert to total minutes
    return days * 1440 + hours * 60 + minutes  # 1 day = 1440 minutes
