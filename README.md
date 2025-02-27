# Telegram Bot for KBJU Calculation

## Description
This Telegram bot allows users to calculate the caloric and nutritional value (KBJU) of their meals. Users can add, edit, and remove dishes from their cart and get a final breakdown of total calories, proteins, fats, and carbohydrates.

## Features
- Start command (`/start`) to display options
- Inline keyboard menu for easy navigation
- Add dishes from `menu.json` with detailed KBJU breakdown
- Edit and remove ingredients from selected dishes
- Display the total nutritional value of selected dishes

## Installation
### Prerequisites
- Python 3.8+
- `aiogram` library

### Steps
1. Clone this repository:
   ```sh
   git clone https://github.com/your-repo/kbju-bot.git
   cd kbju-bot
   ```
2. Install dependencies:
   ```sh
   pip install aiogram
   ```
3. Create a `menu.json` file with dish data in the following format:
   ```json
   {
       "dishes": [
           {
               "id": 1,
               "name": "Chicken Salad",
               "ingredients": [
                   {"id": 1, "ingredient": "Chicken", "kcal": 200, "proteins": 30, "fats": 5, "carbs": 0},
                   {"id": 2, "ingredient": "Lettuce", "kcal": 10, "proteins": 1, "fats": 0, "carbs": 2}
               ]
           }
       ]
   }
   ```
4. Replace `API_TOKEN` in the script with your actual Telegram bot token.
5. Run the bot:
   ```sh
   python bot.py
   ```

## Usage
1. Start the bot by sending `/start`.
2. Select "Calculate KBJU" from the menu.
3. Choose options to add, edit, or remove dishes.
4. View the final KBJU breakdown of selected dishes.



