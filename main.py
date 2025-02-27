import json
import asyncio
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.types import InlineKeyboardButton, CallbackQuery, InlineKeyboardMarkup, Message
from aiogram.filters import Command

API_TOKEN = '7867910538:AAHPdAyWLSBLRm4UZCRF_aks_bz7d7onqTY'

bot = Bot(token=API_TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

# Загружаем данные меню
with open('menu.json', 'r', encoding='utf-8') as f:
    menu_data = json.load(f)
cart = []  # Корзина с блюдами


def make_keyboard(buttons: list):
    """Формирует клавиатуру с кнопками в столбик"""
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=callback)]
                                                 for text, callback in buttons])


@router.message(Command("start"))
async def start(message: types.Message):
    keyboard = make_keyboard([("Рассчитать КБЖУ", "calculate_kbju")])
    await message.answer("Выберите действие:", reply_markup=keyboard)


@router.callback_query(F.data == "calculate_kbju")
async def calculate_kbju(callback: CallbackQuery):
    keyboard = make_keyboard([
        ("Добавить блюдо", "add_dish"),
        ("Изменить блюдо", "edit_dish"),
        ("Удалить блюдо", "remove_dish"),
        ("Итого", "final_kbju"),
    ])
    await callback.message.edit_text("Выберите действие:", reply_markup=keyboard)


@router.callback_query(F.data == "add_dish")
async def add_dish(callback: CallbackQuery):
    keyboard = make_keyboard([(dish["name"], f'add_{dish["id"]}') for dish in menu_data["dishes"]] +
                             [("Сохранить", "save_cart")])
    await callback.message.edit_text("Выберите блюдо:", reply_markup=keyboard)


@router.callback_query(F.data.startswith('add_'))
async def add_dish_to_cart(callback: CallbackQuery):
    dish_id = callback.data[4:]  # Получаем ID блюда из callback
    selected_dish = next((dish for dish in menu_data["dishes"] if str(dish["id"]) == dish_id), None)

    if selected_dish:
        # Формируем структуру с КБЖУ
        dish_data = {
            "id": selected_dish["id"],
            "name": selected_dish["name"],
            "ingredients": [
                {
                    "id": ing.get("id"),
                    "name": ing.get("ingredient", "Без названия"),
                    "kcal": ing.get("kcal", 0),
                    "proteins": ing.get("proteins", 0),
                    "fats": ing.get("fats", 0),
                    "carbs": ing.get("carbs", 0),
                }
                for ing in selected_dish.get("ingredients", [])
            ]
        }
        cart.append(dish_data)

        await callback.answer(f'Блюдо "{selected_dish["name"]}" добавлено в корзину.')
    else:
        await callback.answer("Ошибка при добавлении блюда.")


@router.callback_query(F.data == "edit_dish")
async def edit_dish(callback: CallbackQuery):
    if not cart:
        await callback.answer("Корзина пуста!")
        return

    keyboard = make_keyboard([(dish["name"], f'edit_{dish["id"]}') for dish in cart] +
                             [("Назад", "calculate_kbju")])
    await callback.message.edit_text("Выберите блюдо для изменения:", reply_markup=keyboard)

@router.callback_query(F.data.startswith('edit_'))
async def edit_dish_ingredients(callback: CallbackQuery):
    dish_id = int(callback.data[5:])
    dish = next((d for d in cart if d["id"] == dish_id), None)

    if not dish or "ingredients" not in dish:
        await callback.answer("Нет ингредиентов для редактирования!")
        return

    # Корректное восстановление имен ингредиентов
    for ingr in dish["ingredients"]:
        if not isinstance(ingr, dict):
            print(f"Ошибка: элемент не является словарем: {ingr}")
        if "name" in ingr and "ingredient" not in ingr:
            ingr["ingredient"] = ingr["name"]  # Восстанавливаем название ингредиента
        elif "ingredient" not in ingr:
            ingr["ingredient"] = "Неизвестный ингредиент"  # Предотвращаем отсутствие имени

    keyboard = make_keyboard([(f"❌ {ingr['ingredient']}", f'del_ingr_{dish_id}_{ingr["id"]}')
                              for ingr in dish["ingredients"]] +
                             [("Сохранить изменения", f'save_edit_{dish_id}'), ("Назад", "edit_dish")])

    await callback.message.edit_text(f"Редактирование {dish['name']}:", reply_markup=keyboard)


@router.callback_query(F.data.startswith('del_ingr_'))
async def delete_ingredient(callback: CallbackQuery):
    print(f"DEBUG: callback.data = {callback.data}")  # Логируем входные данные

    # Отрезаем 'del_ingr_' и разбиваем оставшуюся строку по '_'
    data_parts = callback.data[len('del_ingr_'):].split('_', 1)

    if len(data_parts) != 2:
        print(f"Ошибка: некорректный формат callback.data -> {callback.data}")
        await callback.answer("Ошибка: некорректный формат данных.")
        return

    dish_id_str, ingredient_id_str = data_parts

    if not dish_id_str.isdigit() or not ingredient_id_str.isdigit():
        print(f"Ошибка: dish_id или ingredient_id не числа -> {dish_id_str}, {ingredient_id_str}")
        await callback.answer("Ошибка: неверный формат ID.")
        return

    dish_id = int(dish_id_str)
    ingredient_id = int(ingredient_id_str)

    print(f"DEBUG: Преобразовано -> dish_id: {dish_id}, ingredient_id: {ingredient_id}")

    dish = next((d for d in cart if d["id"] == dish_id), None)

    if not dish:
        print(f"Ошибка: блюдо с ID {dish_id} не найдено!")
        await callback.answer("Ошибка: блюдо не найдено.")
        return

    if "ingredients" not in dish or not isinstance(dish["ingredients"], list):
        print(f"Ошибка: блюдо {dish['name']} не содержит список ингредиентов!")
        await callback.answer("Ошибка: ингредиенты отсутствуют.")
        return

    print(f"DEBUG: ингредиенты перед удалением -> {dish['ingredients']}")

    # Проверяем, существует ли ингредиент с таким ID
    ingredient_exists = any(ingr["id"] == ingredient_id for ingr in dish["ingredients"])

    if not ingredient_exists:
        print(f"Ошибка: ингредиент с ID {ingredient_id} не найден в {dish['name']}!")
        await callback.answer("Ошибка: ингредиент не найден.")
        return

    # Удаляем ингредиент
    dish["ingredients"] = [ingr for ingr in dish["ingredients"] if ingr["id"] != ingredient_id]
    print(f"DEBUG: ингредиенты после удаления -> {dish['ingredients']}")

    # Проверяем, осталось ли блюдо в корзине
    if not dish["ingredients"]:
        cart.remove(dish)
        await callback.answer(f'Все ингредиенты из "{dish["name"]}" удалены. Блюдо убрано из корзины.')
        await edit_dish(callback)  # Обновляем список блюд
    else:
        await callback.answer("Ингредиент удален.")
        await edit_dish_ingredients(dish_id, callback.message)


async def edit_dish_ingredients(dish_id: int, message: Message):
    dish = next((d for d in cart if d["id"] == dish_id), None)

    if not dish or "ingredients" not in dish:
        return

    keyboard = make_keyboard([(f"❌ {ingr['ingredient']}", f'del_ingr_{dish_id}_{ingr["id"]}')
                              for ingr in dish["ingredients"]] +
                             [("Сохранить изменения", f'save_edit_{dish_id}'), ("Назад", "edit_dish")])

    await message.edit_text(f"Редактирование {dish['name']}:", reply_markup=keyboard)


@router.callback_query(F.data.startswith('save_edit_'))
async def save_edited_dish(callback: CallbackQuery):
    dish_id = int(callback.data[10:])
    dish = next((d for d in cart if d["id"] == dish_id), None)

    if dish:
        # Удаляем блюдо, если в нём не осталось ингредиентов
        if not dish["ingredients"]:
            cart.remove(dish)
            await callback.answer(f'Все ингредиенты из "{dish["name"]}" удалены. Блюдо убрано из корзины.')
        else:
            # Проверяем наличие КБЖУ у всех ингредиентов
            missing_kbju = any(
                "kcal" not in ingr or "proteins" not in ingr or "fats" not in ingr or "carbs" not in ingr
                for ingr in dish["ingredients"]
            )

            if not missing_kbju:
                # Пересчитываем КБЖУ для блюда
                dish["kcal"] = sum(ingr.get("kcal", 0) for ingr in dish["ingredients"])
                dish["proteins"] = sum(ingr.get("proteins", 0) for ingr in dish["ingredients"])
                dish["fats"] = sum(ingr.get("fats", 0) for ingr in dish["ingredients"])
                dish["carbs"] = sum(ingr.get("carbs", 0) for ingr in dish["ingredients"])
                await callback.answer(f'Изменения в "{dish["name"]}" сохранены.')
            else:
                await callback.answer(f'Ошибка: у некоторых ингредиентов "{dish["name"]}" отсутствуют КБЖУ. '
                                      'Добавьте ингредиенты с КБЖУ или удалите блюдо.')

    # Обновляем клавиатуру только если корзина не пуста
    if cart:
        await edit_dish(callback)
    else:
        await callback.message.edit_text(
            "Корзина пуста!",
            reply_markup=make_keyboard([("Назад", "calculate_kbju")])
        )




@router.callback_query(F.data == "remove_dish")
async def remove_dish(callback: CallbackQuery):
    if not cart:
        await callback.answer("Корзина пуста!")
        return

    keyboard = make_keyboard([(dish["name"], f'remove_{dish["name"]}') for dish in cart] +
                             [("Назад", "calculate_kbju"), ("Сохранить", "save_cart")])
    await callback.message.edit_text("Выберите блюдо для удаления:", reply_markup=keyboard)


@router.callback_query(F.data.startswith('remove_'))
async def remove_dish_from_cart(callback: CallbackQuery):
    dish_name = callback.data[7:]
    global cart
    cart = [dish for dish in cart if dish["name"] != dish_name]
    await callback.answer(f'Блюдо "{dish_name}" удалено из корзины.')
    await remove_dish(callback)


@router.callback_query(F.data == "save_cart")
async def save_cart(callback: CallbackQuery):
    keyboard = make_keyboard([
        ("Добавить блюдо", "add_dish"),
        ("Изменить блюдо", "edit_dish"),
        ("Удалить блюдо", "remove_dish"),
        ("Итого", "final_kbju")
    ])
    await callback.message.edit_text("Корзина сохранена. Выберите действие:", reply_markup=keyboard)


@router.callback_query(F.data == "final_kbju")
async def final_kbju(callback: CallbackQuery):
    if not cart:
        await callback.answer("Корзина пуста!")
        return

    # 🔍 Проверяем, что в cart
    print("Содержимое корзины (cart):", cart)

    total_kcal, total_proteins, total_fats, total_carbs = 0, 0, 0, 0
    order_text = "📌 Ваш заказ:\n\n"

    for dish in cart:
        dish_name = dish.get("name", "Неизвестное блюдо")
        order_text += f'🍽 {dish_name}:\n'

        ingredients = dish.get("ingredients", [])

        # Проверка, что ингредиенты есть и это список
        if not ingredients or not isinstance(ingredients, list):
            order_text += "  - ⚠️ Нет ингредиентов!\n"
            print(f"⚠️ Ошибка: у {dish_name} нет ингредиентов или они в неверном формате:", ingredients)
            continue

        for ingredient in ingredients:
            if isinstance(ingredient, dict):  # ✅ Проверяем, что ingredient — словарь
                name = ingredient.get("name", "Неизвестный ингредиент")  # Исправленный ключ
                kcal = float(ingredient.get("kcal", 0))
                proteins = float(ingredient.get("proteins", 0))
                fats = float(ingredient.get("fats", 0))
                carbs = float(ingredient.get("carbs", 0))

                order_text += f'  - {name}\n'
                total_kcal += kcal
                total_proteins += proteins
                total_fats += fats
                total_carbs += carbs
            else:
                order_text += "  - ❌ Ошибка в ингредиенте!\n"
                print(f"⚠️ Ошибка: неверный формат ингредиента в {dish_name}:", ingredient)

        order_text += "\n"

    order_text += (
        f"🔹 Итоговое КБЖУ:\n"
        f"🔸 Калории: {int(total_kcal)} ккал\n"
        f"🔸 Белки: {int(total_proteins)} г\n"
        f"🔸 Жиры: {int(total_fats)} г\n"
        f"🔸 Углеводы: {int(total_carbs)} г"
    )

    cart.clear()
    keyboard = make_keyboard([("Рассчитать КБЖУ", "calculate_kbju")])

    await callback.message.answer(order_text)
    await callback.message.answer("Хорошего дня!", reply_markup=keyboard)



async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
