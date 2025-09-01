#!/usr/bin/env python3
"""
Головний скрипт для запуску всіх аналізів продажів
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
import argparse

# Додаємо корневу папку до шляху
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


async def run_all_analysis():
    """Запуск всіх аналізів послідовно"""

    print("🚀 ЗАПУСК ПОВНОГО АНАЛІЗУ ПРОДАЖІВ")
    print("=" * 80)
    print(f"⏰ Початок: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    # Імпортуємо всі аналізи
    try:
        from analysis.comprehensive_sales_analysis import comprehensive_sales_analysis
        from analysis.sales_by_spots_analysis import analyze_sales_by_spots
        from analysis.products_sales_analysis import analyze_products_sales
        from analysis.clients_behavior_analysis import analyze_clients_behavior
        from analysis.sales_trends_analysis import analyze_sales_trends
        from analysis.bonus_analysis import bonus_analysis
        from analysis.corrected_bonus_analysis import corrected_bonus_analysis
        from analysis.simple_bonus_analysis import simple_bonus_analysis
        from analysis.deep_duplicate_analysis import deep_duplicate_analysis
        from analysis.detailed_phone_analysis import detailed_phone_analysis
        from analysis.extended_phone_analysis import extended_phone_analysis

        # 1. Комплексний аналіз (загальний огляд)
        print("\n🎯 1/10: ЗАГАЛЬНИЙ ОГЛЯД")
        print("-" * 40)
        await comprehensive_sales_analysis()

        # 2. Аналіз по точках продажу
        print("\n🏪 2/10: АНАЛІЗ ПО ТОЧКАХ ПРОДАЖУ")
        print("-" * 40)
        await analyze_sales_by_spots()

        # 3. Аналіз по товарах
        print("\n🛍️  3/10: АНАЛІЗ ПО ТОВАРАХ")
        print("-" * 40)
        await analyze_products_sales()

        # 4. Аналіз клієнтів
        print("\n👥 4/10: АНАЛІЗ КЛІЄНТІВ")
        print("-" * 40)
        await analyze_clients_behavior()

        # 5. Аналіз трендів
        print("\n📈 5/10: АНАЛІЗ ТРЕНДІВ")
        print("-" * 40)
        await analyze_sales_trends()

        # 6. Аналіз бонусів (основний)
        print("\n💰 6/10: АНАЛІЗ БОНУСІВ")
        print("-" * 40)
        await bonus_analysis()

        # 7. Скорегований аналіз бонусів
        print("\n💎 7/10: СКОРЕГОВАНИЙ АНАЛІЗ БОНУСІВ")
        print("-" * 40)
        await corrected_bonus_analysis()

        # 8. Простий аналіз бонусів
        print("\n💵 8/10: ПРОСТИЙ АНАЛІЗ БОНУСІВ")
        print("-" * 40)
        await simple_bonus_analysis()

        # 9. Глибокий аналіз дублікатів
        print("\n🔍 9/10: АНАЛІЗ ДУБЛІКАТІВ КЛІЄНТІВ")
        print("-" * 40)
        await deep_duplicate_analysis()

        # 10. Детальний аналіз телефонів
        print("\n📱 10/10: АНАЛІЗ ТЕЛЕФОННИХ НОМЕРІВ")
        print("-" * 40)
        await detailed_phone_analysis()

        # Додатковий: Розширений аналіз телефонів
        print("\n📞 ДОДАТКОВО: РОЗШИРЕНИЙ АНАЛІЗ ТЕЛЕФОНІВ")
        print("-" * 40)
        await extended_phone_analysis()

        print("\n" + "=" * 80)
        print("✅ УСІ АНАЛІЗИ ЗАВЕРШЕНО УСПІШНО!")
        print(f"⏰ Завершено: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)

    except Exception as e:
        print(f"❌ Помилка при виконанні аналізу: {e}")
        import traceback

        traceback.print_exc()


def run_single_analysis(analysis_name):
    """Запуск окремого аналізу"""

    analyses = {
        "comprehensive": (
            "comprehensive_sales_analysis",
            "comprehensive_sales_analysis",
        ),
        "spots": ("sales_by_spots_analysis", "analyze_sales_by_spots"),
        "products": ("products_sales_analysis", "analyze_products_sales"),
        "clients": ("clients_behavior_analysis", "analyze_clients_behavior"),
        "trends": ("sales_trends_analysis", "analyze_sales_trends"),
        "bonus": ("bonus_analysis", "bonus_analysis"),
        "bonus-corrected": ("corrected_bonus_analysis", "corrected_bonus_analysis"),
        "bonus-simple": ("simple_bonus_analysis", "simple_bonus_analysis"),
        "duplicates": ("deep_duplicate_analysis", "deep_duplicate_analysis"),
        "phones": ("detailed_phone_analysis", "detailed_phone_analysis"),
        "phones-extended": ("extended_phone_analysis", "extended_phone_analysis"),
    }

    if analysis_name not in analyses:
        print(f"❌ Невідомий аналіз: {analysis_name}")
        print(f"✅ Доступні аналізи: {', '.join(analyses.keys())}")
        return

    module_name, function_name = analyses[analysis_name]

    try:
        # Динамічний імпорт
        module = __import__(f"analysis.{module_name}", fromlist=[function_name])
        analysis_function = getattr(module, function_name)

        print(f"🚀 Запуск аналізу: {analysis_name}")
        print("=" * 50)
        asyncio.run(analysis_function())
        print("=" * 50)
        print("✅ Аналіз завершено!")

    except Exception as e:
        print(f"❌ Помилка при запуску аналізу {analysis_name}: {e}")
        import traceback

        traceback.print_exc()


def show_help():
    """Показ довідки по доступним аналізам"""

    print("🚀 СИСТЕМА АНАЛІЗУ ПРОДАЖІВ AVOCADO")
    print("=" * 60)
    print("📊 Доступні аналізи:")
    print()

    print("📈 ОСНОВНІ АНАЛІЗИ:")
    print("  comprehensive     - Комплексний огляд продажів")
    print("  spots            - Аналіз по точках продажу")
    print("  products         - Аналіз по товарах")
    print("  clients          - Поведінка клієнтів")
    print("  trends           - Тренди продажів")
    print()

    print("💰 АНАЛІЗ БОНУСІВ:")
    print("  bonus            - Основний аналіз бонусів")
    print("  bonus-corrected  - Скорегований аналіз бонусів")
    print("  bonus-simple     - Простий аналіз бонусів")
    print()

    print("🔍 АНАЛІЗ ЯКОСТІ ДАНИХ:")
    print("  duplicates       - Пошук дублікатів клієнтів")
    print("  phones           - Детальний аналіз телефонів")
    print("  phones-extended  - Розширений аналіз телефонів")
    print()

    print("💡 ВИКОРИСТАННЯ:")
    print("  python run_analysis.py                    # Запуск всіх аналізів")
    print("  python run_analysis.py comprehensive      # Окремий аналіз")
    print("  python run_analysis.py help               # Ця довідка")
    print("=" * 60)


def main():
    """Головна функція"""

    if len(sys.argv) > 1:
        analysis_name = sys.argv[1].lower()

        if analysis_name in ["help", "--help", "-h"]:
            show_help()
        else:
            # Запуск окремого аналізу
            run_single_analysis(analysis_name)
    else:
        # Запуск всіх аналізів
        asyncio.run(run_all_analysis())


if __name__ == "__main__":
    main()
