import threading
import time
import schedule
from update_data import update_data
import logging
import asyncio
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters.command import Command
import config
from functions import GSFunction, unique_names, update_statistics
from murkups import ikb_categories, ikb_brand_names, ikb_what_next
from aiogram.utils.formatting import Bold


logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.TOKEN)
dp = Dispatcher(skip_updates=True)
gs_function = GSFunction('data.json')

# statistics
statistics_by_categories = {}
statistics_by_brands = {}


@dp.message(Command("start"))
async def cmd_start(message: types.Message) -> None:
    key = 'Категория'
    unique_values = unique_names(gs_function.selecting_values_by_key(key))
    await message.answer('Выберите категорию в которой хотите получить скидку ⬇️',
                         reply_markup=ikb_categories(unique_values))


@dp.message(F.text == "statistic")
async def statistic_data(message: types.Message) -> None:
    text_cat = Bold("Категория: Уникальных посещений | Всего посещений\n\n")
    text_brand = Bold("Торговая марка: Уникальных посещений | Всего посещений\n\n")
    for key, value in statistics_by_categories.items():
        text_cat += f"{key}: {len(set(value))} | {len(value)}\n"
    for key, value in statistics_by_brands.items():
        text_brand += f"{key}: {len(set(value))} | {len(value)}\n"
    await message.answer(**text_cat.as_kwargs())
    await message.answer(**text_brand.as_kwargs())


@dp.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu(callback: types.CallbackQuery) -> None:
    category = 'Категория'
    unique_values = unique_names(gs_function.selecting_values_by_key(category))
    await callback.message.edit_text("Выберите категорию в которой хотите получить скидку ⬇️",
                                 reply_markup=ikb_categories(unique_values))


@dp.callback_query(F.data.startswith("category_"))
async def cb_category(callback: types.CallbackQuery) -> None:
    key = 'Категория'
    value = callback.data.replace('category_', '')
    update_statistics(statistics_by_categories, value, callback)
    gs_data = gs_function.selecting_dicts_by_tuple((key, value))
    brand_names = unique_names([item.get('Торговая марка') for item in gs_data])
    await callback.message.edit_text('Выбирайте 🥰', reply_markup=ikb_brand_names(brand_names))


@dp.callback_query(F.data.startswith("brand_name_"))
async def cb_brand_name(callback: types.CallbackQuery) -> None:
    key = 'Торговая марка'
    value = callback.data.replace('brand_name_', '')
    gs_data = gs_function.selecting_dicts_by_tuple((key, value))
    category = gs_data[0].get('Категория')
    update_statistics(statistics_by_brands, value, callback)
    await callback.message.answer('Чтобы воспользоваться акцией необходимо: перейти по ссылке или скопировать промокод и ввести его на сайте или приложении магазина')
    for item in gs_data:
        text = f'Название: {item.get("Торговая марка")}\n' \
               f'Скидка: {item.get("Скидка по промокоду")}\n' \
               f'Ссылка: {item.get("Ссылка для активации промокода")}\n' \
               f'Действует до: {item.get("Срок действия")}\n' \
               f'Регион: {item.get("Зона охвата")}\n' \
               f'Условия акции: {item.get("Условия для активации промокода")}\n' \
               f'Промокод ниже⬇️'
        await callback.message.answer(text=text)
        await callback.message.answer(text=item.get("Промокод"))
    await callback.message.answer(text='Куда отправимся за скидками дальше?', reply_markup=ikb_what_next(category))


def update_data_periodically():
    schedule.every(20).seconds.do(update_data)

    while True:
        schedule.run_pending()
        time.sleep(1)


async def main():
    update_thread = threading.Thread(target=update_data_periodically)
    update_thread.start()

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
