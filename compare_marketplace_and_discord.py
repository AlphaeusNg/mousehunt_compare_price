import requests
import pandas as pd
import openpyxl
from tqdm import tqdm
from pandas import json_normalize
from datetime import datetime, timedelta

MARKETPLACE_INFO_URL = "https://api-dev.markethunt.win/items"
DISCORD_INFO_URL = "https://api.markethunt.win/otc/listings"
TARIFF = 0.9
SB_ITEM_ID = 114


def retrieve_info_from_web(url: str):
    try:
        # Fetch data from the URL
        response = requests.get(url)
        response.raise_for_status()

        # Parse JSON response
        data = response.json()

        # Flatten JSON and create a DataFrame
        df = json_normalize(data)

    except requests.exceptions.RequestException as e:
        print(f"Error: {e}")
        df = pd.DataFrame()

    return df


def get_current_price(item_id, dataframe) -> None or int:
    # Search for the item_id in the DataFrame
    item_row = dataframe[dataframe['item_info.item_id'] == item_id]

    # Check if the item is found
    if not item_row.empty:
        # Extract the current price from the found row
        price_column = item_row['latest_market_data.price']

        # Check for NaN values in the price column
        if price_column.isna().any():
            return None
        else:
            # Convert the current price to an integer
            return int(price_column.iloc[0])
    else:
        return None


def get_discord_sb_price(item_id, dataframe):
    # Search for the item_id in the DataFrame
    item_row = dataframe[dataframe['item.item_id'] == item_id]

    # Check if the item is found
    if not item_row.empty:
        # Extract the listing_type from the found row
        listing_type = item_row['listing_type'].iloc[0]

        # Retrieve information using the retrieved listing_type
        item_info_df = retrieve_info_from_web(f"https://api.markethunt.win/otc/listings/{listing_type}/{item_id}")
        result_data = get_newest_data(item_info_df)
        return result_data
    else:
        return None


def format_timestamp(timestamp):
    # Convert timestamp to datetime object
    datetime_obj = datetime.utcfromtimestamp(timestamp / 1000.0)

    # Format datetime as "hh/mm/ss + dd/mm/yy"
    formatted_timestamp = f"{datetime_obj.strftime('%H:%M:%S')}~{datetime_obj.strftime('%d/%m/%y')}"

    return formatted_timestamp


def get_newest_data(dataframe, days_ago=1):
    # Filter data within the last `days_ago`
    days_ago_date = datetime.utcnow() - timedelta(days=days_ago)
    filtered_data = dataframe[dataframe['timestamp'] >= days_ago_date.timestamp() * 1000]

    # Check if filtered_data is empty
    if filtered_data.empty:
        return [{"lowest_sb_price": None, "timestamp": None, "latest_sb_quote": None, "latest_timestamp": None}]

    # Sort data by timestamp in descending order
    sorted_data = filtered_data.sort_values(by='timestamp', ascending=False)

    # Get the newest sb_price and its timestamp
    newest_sb_price = sorted_data['sb_price'].iloc[0]
    newest_timestamp = format_timestamp(sorted_data['timestamp'].iloc[0])

    # Get the lowest prices and their timestamps
    lowest_prices_indices = sorted_data['sb_price'].nsmallest(1).index

    # Create a list of dictionaries with the required format
    result_data = [
        {"lowest_sb_price": sorted_data.loc[index, 'sb_price'],
         "timestamp": format_timestamp(sorted_data.loc[index, 'timestamp'])}
        for index in lowest_prices_indices
    ]
    result_data.append({"latest_sb_quote": newest_sb_price, "latest_timestamp": newest_timestamp})
    return result_data


def get_item_id(dataframe, item_name):
    item_row = dataframe[dataframe['item_info.name'] == item_name]

    # Check if the item is found
    if not item_row.empty:
        # Extract the listing_type from the found row
        item_id = item_row['item_info.item_id'].iloc[0]
        return item_id
    else:
        print(f"No such item: {item_name}")
        exit()


marketplace_info_df = retrieve_info_from_web(MARKETPLACE_INFO_URL)
discord_info_df = retrieve_info_from_web(DISCORD_INFO_URL)

# Get SB price
SB_MARKET_PRICE = get_current_price(SB_ITEM_ID, marketplace_info_df)


def get_single_item_info(item_name, sb_price=None):
    item_id_to_search = get_item_id(marketplace_info_df, item_name)
    discord_sb_price = get_discord_sb_price(item_id_to_search, discord_info_df) if sb_price is None else sb_price
    marketplace_gold_price = get_current_price(item_id_to_search, marketplace_info_df)

    if discord_sb_price is None and sb_price is None:
        print("No discord price was found for this item, consider manually inputting the latest SB price")
        print("marketplace_gold_price:", marketplace_gold_price)
    else:
        if sb_price is not None:
            discord_sb_price = [{'latest_sb_quote': sb_price}]
        print(
            f"Amount of SB to sell in Marketplace (factor * {TARIFF} tariffs) to buy item with gold from Marketplace vs just trading SB "
            "for item (Discord):\n" + "Marketplace:",
            round(marketplace_gold_price / (SB_MARKET_PRICE * TARIFF), 2), "Vs", "Discord price:",
            discord_sb_price[-1]['latest_sb_quote'])
        print(
            f"Amount of Gold to buy in Marketplace vs Gold equivalent of buying in Discord for item:\n"
            f"Marketplace:", marketplace_gold_price, "Vs", "Discord price:",
            int(discord_sb_price[-1]['latest_sb_quote']*SB_MARKET_PRICE), f"({SB_MARKET_PRICE}*{round(discord_sb_price[-1]['latest_sb_quote'],2)}SB)")


def generate_csv(filepath="marketplace_comparison"):
    current_datetime = datetime.now().strftime("%H-%M-%S_%d-%m-%Y")
    filepath = f"{filepath}_{current_datetime}"
    # Lists to store results
    latest_discord_sb_prices_list = []
    latest_discord_gold_prices_list = []
    latest_marketplace_gold_prices_list = []
    marketplace_minus_discord_gold_list = []
    marketplace_minus_discord_sb_list = []
    better_to_buy_from_discord_list = []

    # Iterate through each item in marketplace_info_df
    print("Generating comparison data...")
    for _, row in tqdm(marketplace_info_df.iterrows(), total=len(marketplace_info_df)):
        item_id_to_search = row['item_info.item_id']

        # Get Discord SB price
        discord_sb_price = get_discord_sb_price(item_id_to_search, discord_info_df)
        # Get Marketplace Gold price
        marketplace_gold_price = get_current_price(item_id_to_search, marketplace_info_df)

        if discord_sb_price is None or discord_sb_price[-1]['latest_sb_quote'] is None:
            # Handle case where Discord price is not found
            discord_sb_price = discord_gold_price = marketplace_minus_discord_sb = marketplace_minus_discord_gold = \
                better_to_buy_from_discord = None

        else:
            discord_sb_price = discord_sb_price[-1]['latest_sb_quote']
            discord_gold_price = discord_sb_price * SB_MARKET_PRICE * TARIFF

            # Calculate difference
            marketplace_minus_discord_gold = int(marketplace_gold_price - discord_sb_price * SB_MARKET_PRICE * (TARIFF + 0.2))
            marketplace_minus_discord_sb = round(marketplace_gold_price / (SB_MARKET_PRICE * TARIFF), 2) - discord_sb_price

            better_to_buy_from_discord = "Yessu" if marketplace_minus_discord_sb > 0 else "Nopey"

        # Append results to lists
        latest_discord_sb_prices_list.append(discord_sb_price)
        latest_discord_gold_prices_list.append(discord_gold_price)
        latest_marketplace_gold_prices_list.append(marketplace_gold_price)
        marketplace_minus_discord_gold_list.append(marketplace_minus_discord_gold)
        marketplace_minus_discord_sb_list.append(marketplace_minus_discord_sb)
        better_to_buy_from_discord_list.append(better_to_buy_from_discord)

    # Add new columns to the DataFrame
    marketplace_info_df['Discord_SB_Price'] = latest_discord_sb_prices_list
    marketplace_info_df['Discord_Gold_Price'] = latest_discord_gold_prices_list
    marketplace_info_df['Marketplace_Gold_Price'] = latest_marketplace_gold_prices_list
    marketplace_info_df['Difference in Marketplace - Discord (Gold)'] = marketplace_minus_discord_gold_list
    marketplace_info_df['Difference in Marketplace - Discord (SB)'] = marketplace_minus_discord_sb_list
    marketplace_info_df['Better to buy from Discord?'] = better_to_buy_from_discord_list

    # Apply row-wise styling based on the "Better to buy from Discord?" column
    def color_row(row):
        if row['Better to buy from Discord?'] == 'Nopey':
            # Light red color
            return ['background-color: #ff9999'] * len(row) # light red
        elif row['Better to buy from Discord?'] == 'Yessu':
            # Light green color
            return ['background-color: #99ff99'] * len(row) # light green
        else:
            return [''] * len(row)

     # Apply the style to the DataFrame
    styled_df = marketplace_info_df.style.apply(color_row, axis=1)

    # Save the styled DataFrame to a new HTML file
    styled_df.to_html(f"{filepath}.html", index=False)
    styled_df.to_excel(f"{filepath}.xlsx", index=False)