#!/usr/bin/env python3
"""
Конвертер изображений — настольное приложение.

Установка зависимостей:
    pip install Pillow tkinterdnd2

Запуск:
    python image_converter_app.py

Если пакет tkinterdnd2 не установлен, приложение всё равно запустится,
но перетаскивание файлов мышью будет недоступно — используйте кнопку
"Добавить файлы...".
"""

import threading
from pathlib import Path

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
    DND_AVAILABLE = True
except ImportError:
    DND_AVAILABLE = False

from PIL import Image

SUPPORTED_INPUT_EXT = {
    ".jpg", ".jpeg", ".png", ".bmp", ".gif",
    ".tiff", ".tif", ".webp", ".ico",
}

OUTPUT_FORMATS = {
    "PNG":  {"ext": "png",  "pil_format": "PNG"},
    "JPEG": {"ext": "jpg",  "pil_format": "JPEG"},
    "BMP":  {"ext": "bmp",  "pil_format": "BMP"},
    "GIF":  {"ext": "gif",  "pil_format": "GIF"},
    "TIFF": {"ext": "tiff", "pil_format": "TIFF"},
    "WEBP": {"ext": "webp", "pil_format": "WEBP"},
    "ICO":  {"ext": "ico",  "pil_format": "ICO"},
}

FORMATS_NO_ALPHA = {"JPEG", "BMP"}


class ImageConverterApp:
    def __init__(self, root):
        self.root = root
        root.title("Конвертер изображений")
        root.geometry("640x540")
        root.minsize(560, 480)

        self.files = []  # list[Path]
        self.output_dir = tk.StringVar(value="")
        self.selected_format = tk.StringVar(value="PNG")
        self.quality = tk.IntVar(value=90)

        self._build_ui()

    # ------------------------------------------------------------------ UI

    def _build_ui(self):
        main = ttk.Frame(self.root, padding=10)
        main.pack(fill="both", expand=True)

        # Список файлов
        list_frame = ttk.LabelFrame(main, text="Файлы для конвертации", padding=6)
        list_frame.pack(fill="both", expand=True)

        self.listbox = tk.Listbox(list_frame, selectmode="extended")
        self.listbox.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.listbox.yview)
        scrollbar.pack(side="right", fill="y")
        self.listbox.config(yscrollcommand=scrollbar.set)

        if DND_AVAILABLE:
            self.listbox.drop_target_register(DND_FILES)
            self.listbox.dnd_bind("<<Drop>>", self._on_drop)

        # Кнопки под списком
        btns = ttk.Frame(main)
        btns.pack(fill="x", pady=(6, 10))
        ttk.Button(btns, text="Добавить файлы...", command=self._add_files).pack(side="left")
        ttk.Button(btns, text="Удалить выбранное", command=self._remove_selected).pack(side="left", padx=6)
        ttk.Button(btns, text="Очистить список", command=self._clear_all).pack(side="left")
        self.count_label = ttk.Label(btns, text="Файлов: 0")
        self.count_label.pack(side="right")

        # Параметры
        opts = ttk.LabelFrame(main, text="Параметры", padding=8)
        opts.pack(fill="x", pady=(0, 10))

        row1 = ttk.Frame(opts)
        row1.pack(fill="x", pady=2)
        ttk.Label(row1, text="Конвертировать в:", width=20).pack(side="left")
        fmt_combo = ttk.Combobox(
            row1, textvariable=self.selected_format,
            values=list(OUTPUT_FORMATS.keys()), state="readonly", width=10
        )
        fmt_combo.pack(side="left")

        row2 = ttk.Frame(opts)
        row2.pack(fill="x", pady=2)
        ttk.Label(row2, text="Качество (JPEG/WEBP):", width=20).pack(side="left")
        self.quality_scale = ttk.Scale(
            row2, from_=10, to=100, orient="horizontal",
            variable=self.quality, command=self._on_quality_change
        )
        self.quality_scale.pack(side="left", fill="x", expand=True, padx=6)
        self.quality_value_label = ttk.Label(row2, text="90", width=4)
        self.quality_value_label.pack(side="left")

        row3 = ttk.Frame(opts)
        row3.pack(fill="x", pady=2)
        ttk.Label(row3, text="Папка сохранения:", width=20).pack(side="left")
        self.output_entry = ttk.Entry(row3, textvariable=self.output_dir)
        self.output_entry.pack(side="left", fill="x", expand=True, padx=6)
        ttk.Button(row3, text="Обзор...", command=self._choose_output_dir).pack(side="left")

        # Конвертация
        conv_row = ttk.Frame(main)
        conv_row.pack(fill="x", pady=(0, 6))
        self.convert_btn = ttk.Button(conv_row, text="Конвертировать", command=self._start_conversion)
        self.convert_btn.pack(side="left")
        self.progress = ttk.Progressbar(conv_row, orient="horizontal", mode="determinate")
        self.progress.pack(side="left", fill="x", expand=True, padx=8)

        # Журнал
        log_frame = ttk.LabelFrame(main, text="Журнал", padding=4)
        log_frame.pack(fill="both", expand=False)
        self.log_text = tk.Text(log_frame, height=7, state="disabled", wrap="word")
        self.log_text.pack(fill="both", expand=True)

        if not DND_AVAILABLE:
            self._log(
                "Подсказка: установите пакет tkinterdnd2 (pip install tkinterdnd2), "
                "чтобы можно было перетаскивать файлы мышью."
            )

    # ------------------------------------------------------------ файлы

    def _add_files(self):
        paths = filedialog.askopenfilenames(
            title="Выберите изображения",
            filetypes=[
                ("Изображения", "*.jpg *.jpeg *.png *.bmp *.gif *.tiff *.tif *.webp *.ico"),
                ("Все файлы", "*.*"),
            ],
        )
        for p in paths:
            self._add_file(Path(p))

    def _on_drop(self, event):
        paths = self.root.tk.splitlist(event.data)
        for p in paths:
            self._add_file(Path(p))

    def _add_file(self, path: Path):
        if not path.is_file():
            return
        if path.suffix.lower() not in SUPPORTED_INPUT_EXT:
            self._log(f"Пропущено (неподдерживаемый формат): {path.name}")
            return
        if path in self.files:
            return
        self.files.append(path)
        self.listbox.insert("end", path.name)
        self._update_count()

    def _remove_selected(self):
        selected = list(self.listbox.curselection())
        for idx in reversed(selected):
            self.listbox.delete(idx)
            del self.files[idx]
        self._update_count()

    def _clear_all(self):
        self.listbox.delete(0, "end")
        self.files.clear()
        self._update_count()

    def _update_count(self):
        self.count_label.config(text=f"Файлов: {len(self.files)}")

    # ----------------------------------------------------------- опции

    def _on_quality_change(self, value):
        self.quality_value_label.config(text=str(int(float(value))))

    def _choose_output_dir(self):
        d = filedialog.askdirectory(title="Выберите папку для сохранения")
        if d:
            self.output_dir.set(d)

    # ------------------------------------------------------- конвертация

    def _start_conversion(self):
        if not self.files:
            messagebox.showinfo("Нет файлов", "Сначала добавьте изображения.")
            return

        out_dir = self.output_dir.get().strip()
        if not out_dir:
            fmt_ext = OUTPUT_FORMATS[self.selected_format.get()]["ext"]
            out_dir = str(self.files[0].parent / f"converted_{fmt_ext}")
            self.output_dir.set(out_dir)
        Path(out_dir).mkdir(parents=True, exist_ok=True)

        self.convert_btn.config(state="disabled")
        self.progress["value"] = 0
        self.progress["maximum"] = len(self.files)

        thread = threading.Thread(target=self._convert_worker, args=(out_dir,), daemon=True)
        thread.start()

    def _convert_worker(self, out_dir):
        fmt_key = self.selected_format.get()
        fmt_info = OUTPUT_FORMATS[fmt_key]
        quality = self.quality.get()
        ok, fail = 0, 0

        for i, path in enumerate(self.files, start=1):
            try:
                with Image.open(path) as img:
                    if fmt_info["pil_format"] in FORMATS_NO_ALPHA and img.mode in ("RGBA", "P", "LA"):
                        img = img.convert("RGB")
                    if fmt_info["pil_format"] == "ICO":
                        img = img.copy()
                        img.thumbnail((256, 256))

                    out_path = Path(out_dir) / f"{path.stem}.{fmt_info['ext']}"
                    save_kwargs = {}
                    if fmt_info["pil_format"] in ("JPEG", "WEBP"):
                        save_kwargs["quality"] = quality
                    img.save(out_path, format=fmt_info["pil_format"], **save_kwargs)

                ok += 1
                self._log(f"OK: {path.name} -> {out_path.name}")
            except Exception as e:
                fail += 1
                self._log(f"Ошибка: {path.name} ({e})")

            self.root.after(0, self._update_progress, i)

        self.root.after(0, self._conversion_done, ok, fail, out_dir)

    def _update_progress(self, value):
        self.progress["value"] = value

    def _conversion_done(self, ok, fail, out_dir):
        self.convert_btn.config(state="normal")
        messagebox.showinfo("Готово", f"Успешно: {ok}\nС ошибками: {fail}\n\nПапка: {out_dir}")

    def _log(self, message):
        def append():
            self.log_text.config(state="normal")
            self.log_text.insert("end", message + "\n")
            self.log_text.see("end")
            self.log_text.config(state="disabled")

        if threading.current_thread() is threading.main_thread():
            append()
        else:
            self.root.after(0, append)


def main():
    if DND_AVAILABLE:
        root = TkinterDnD.Tk()
    else:
        root = tk.Tk()
    ImageConverterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
