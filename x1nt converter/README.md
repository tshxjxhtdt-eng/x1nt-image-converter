# Image Converter

Настольное приложение для конвертации изображений между форматами (PNG, JPEG, BMP, GIF, TIFF, WEBP, ICO). Перетащите файлы мышью или выберите через диалог, укажите формат — и готово.

## Возможности

- Перетаскивание файлов (drag & drop) прямо в окно
- Пакетная конвертация нескольких файлов за раз
- Форматы: PNG, JPEG, BMP, GIF, TIFF, WEBP, ICO
- Настройка качества для JPEG/WEBP
- Выбор папки сохранения
- Индикатор прогресса и журнал операций
- Автоматическая обработка прозрачности при конвертации в форматы без альфа-канала

## Установка

Требуется Python 3.8+.

```bash
git clone https://github.com/<your-username>/image-converter.git
cd image-converter
pip install -r requirements.txt
```

## Запуск

```bash
python image_converter_app.py
```

Если пакет `tkinterdnd2` не установился, приложение всё равно запустится — просто добавляйте файлы через кнопку «Добавить файлы...» вместо перетаскивания.

## Готовые сборки (Windows)

Скачать `.exe`, не устанавливая Python, можно на странице [Releases](https://github.com/<your-username>/image-converter/releases).

## Лицензия

[MIT](LICENSE)
