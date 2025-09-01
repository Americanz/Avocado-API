#!/usr/bin/env python3
"""
Універсальний скрипт для очищення проекту від порожніх файлів
Видаляє всі порожні файли крім тих, що потрібні для структури проекту
"""

import os
import glob
from pathlib import Path


class ProjectCleaner:
    """Очищувач проекту від непотрібних порожніх файлів"""

    def __init__(self, project_root=None):
        self.project_root = (
            Path(project_root) if project_root else Path(__file__).parent
        )

        # Файли які НЕ потрібно видаляти, навіть якщо вони порожні
        self.keep_empty_files = {
            "__init__.py",  # Python пакети
            ".gitkeep",  # Git placeholder файли
            ".keep",  # Інші placeholder файли
            "requirements.txt",  # Може бути тимчасово порожнім
            "README.md",  # Може бути в процесі написання
            ".env.example",  # Приклад конфігурації
        }

        # Директорії які НЕ потрібно перевіряти
        self.skip_directories = {
            ".venv",
            "venv",
            ".git",
            "__pycache__",
            ".pytest_cache",
            "node_modules",
            ".idea",
            ".vscode",
            "dist",
            "build",
            ".eggs",
            "*.egg-info",
            ".coverage",
            "htmlcov",
            ".mypy_cache",
            ".tox",
            "logs",  # Лог файли можуть бути порожніми
        }

        # Типи файлів для перевірки
        self.file_extensions = {
            "*.py",
            "*.js",
            "*.ts",
            "*.css",
            "*.html",
            "*.md",
            "*.txt",
            "*.json",
            "*.yaml",
            "*.yml",
            "*.xml",
            "*.sql",
            "*.sh",
            "*.bat",
            "*.ps1",
        }

    def should_skip_directory(self, dir_path):
        """Перевіряє чи потрібно пропустити директорію"""
        dir_name = dir_path.name

        # Перевіряємо точні назви
        if dir_name in self.skip_directories:
            return True

        # Перевіряємо патерни
        for pattern in self.skip_directories:
            if "*" in pattern and dir_name.startswith(pattern.replace("*", "")):
                return True

        return False

    def should_keep_file(self, file_path):
        """Перевіряє чи потрібно зберегти файл навіть якщо він порожній"""
        filename = file_path.name

        # Точні назви файлів
        if filename in self.keep_empty_files:
            return True

        # Спеціальні випадки
        if filename.startswith(".env"):
            return True

        if filename.endswith(".example"):
            return True

        return False

    def is_file_empty(self, file_path):
        """Перевіряє чи файл порожній або містить лише пробіли"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                return len(content) == 0
        except (UnicodeDecodeError, PermissionError):
            # Якщо не можемо прочитати файл, не видаляємо його
            return False

    def find_empty_files(self):
        """Знаходить всі порожні файли в проекті"""
        empty_files = []

        print(f"🔍 Сканування проекту: {self.project_root}")
        print("=" * 60)

        for root, dirs, files in os.walk(self.project_root):
            root_path = Path(root)

            # Видаляємо з обходу директорії які потрібно пропустити
            dirs[:] = [d for d in dirs if not self.should_skip_directory(root_path / d)]

            for file in files:
                file_path = root_path / file

                # Перевіряємо тип файлу
                file_matches = any(
                    file_path.match(pattern) for pattern in self.file_extensions
                )
                if not file_matches:
                    continue

                # Перевіряємо чи файл порожній
                if self.is_file_empty(file_path):
                    # Перевіряємо чи потрібно зберегти файл
                    if self.should_keep_file(file_path):
                        print(
                            f"⚪ ЗБЕРЕЖЕНО (потрібний): {file_path.relative_to(self.project_root)}"
                        )
                    else:
                        empty_files.append(file_path)
                        print(
                            f"🔴 ЗНАЙДЕНО порожній: {file_path.relative_to(self.project_root)}"
                        )

        return empty_files

    def delete_empty_files(self, empty_files, confirm=True):
        """Видаляє порожні файли"""
        if not empty_files:
            print("\n✅ Порожніх файлів для видалення не знайдено!")
            return

        print(f"\n📋 ЗНАЙДЕНО {len(empty_files)} порожніх файлів для видалення:")
        for file_path in empty_files:
            print(f"   🗑️  {file_path.relative_to(self.project_root)}")

        if confirm:
            answer = (
                input(f"\n❓ Видалити {len(empty_files)} файлів? (y/N): ")
                .strip()
                .lower()
            )
            if answer not in ["y", "yes", "так", "да"]:
                print("❌ Видалення скасовано")
                return

        deleted_count = 0
        for file_path in empty_files:
            try:
                file_path.unlink()
                print(f"✅ Видалено: {file_path.relative_to(self.project_root)}")
                deleted_count += 1
            except Exception as e:
                print(
                    f"❌ Помилка видалення {file_path.relative_to(self.project_root)}: {e}"
                )

        print(f"\n🎯 РЕЗУЛЬТАТ: Видалено {deleted_count} з {len(empty_files)} файлів")

    def clean_project(self, auto_confirm=False):
        """Основна функція очищення проекту"""
        print("🧹 ОЧИЩЕННЯ ПРОЕКТУ ВІД ПОРОЖНІХ ФАЙЛІВ")
        print("=" * 60)

        empty_files = self.find_empty_files()

        if empty_files:
            self.delete_empty_files(empty_files, confirm=not auto_confirm)

        print("\n" + "=" * 60)
        print("✅ ОЧИЩЕННЯ ЗАВЕРШЕНО")
        print("=" * 60)


def main():
    """Головна функція"""
    import argparse

    parser = argparse.ArgumentParser(description="Очищення проекту від порожніх файлів")
    parser.add_argument(
        "--path", "-p", help="Шлях до проекту (за замовчуванням поточна директорія)"
    )
    parser.add_argument(
        "--auto",
        "-a",
        action="store_true",
        help="Автоматичне видалення без підтвердження",
    )
    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Тільки показати файли, не видаляти",
    )

    args = parser.parse_args()

    cleaner = ProjectCleaner(args.path)

    if args.dry_run:
        print("🔍 РЕЖИМ ПЕРЕГЛЯДУ (файли не будуть видалені)")
        print("=" * 60)
        empty_files = cleaner.find_empty_files()
        if empty_files:
            print(f"\n📋 Буде видалено {len(empty_files)} файлів:")
            for file_path in empty_files:
                print(f"   🗑️  {file_path.relative_to(cleaner.project_root)}")
    else:
        cleaner.clean_project(auto_confirm=args.auto)


if __name__ == "__main__":
    main()
