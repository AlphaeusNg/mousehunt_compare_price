# mousehunt_compare_price
Compare discord vs marketplace price to determine the cheaper option

## Setup Instructions
1. Clone the Repository
```bash
git clone https://github.com/AlphaeusNg/mousehunt_compare_price.git
cd mousehunt_compare_price
```
2. Set Up Virtual Environment
```bash
# Install virtualenv if you haven't already
pip install virtualenv

# Create a virtual environment
python -m venv .venv

# Activate the virtual environment
# On Windows
.venv\Scripts\activate
# On macOS/Linux
source .venv/bin/activate
```
3. Install Dependencies
```bash
# Install required dependencies
pip install -r requirements.txt
```

## Running the Script
To run the script, follow these steps:

```bash
python main.py <function_name> <item_name>
```
Replace `<function_name>` with either `get_single_item_info` or `generate_csv`, and `<item_name>` with the name of the item you want to retrieve information for.

## Examples:

**Get information for a single item**
```bash
python main.py get_single_item_info "Ful'Mina's Tooth"
```
**Output of 25/4/24 10:01pm**
```
Marketplace: 260.95 Vs Discord price: 260.0
Amount of Gold to buy in Marketplace vs Gold equivalent of buying in Discord for item:
Marketplace: 3414107 Vs Discord price: 3779620 (14537*260.0SB)
```

**Generate CSV**
```bash
python main.py generate_csv
```

**Output**: Creates a CSV and HTML file that contains all the different price points. 


ctrl-f `yessu` to find items that are cheaper to purchase in discord, and `nopey` for items that are cheaper to purchase on the marketplace.