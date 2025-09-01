"""
HTML Report Generator for Sales Analysis
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Any
from jinja2 import Template


class HTMLReportGenerator:
    """Генератор HTML звітів для аналізу продажів"""

    def __init__(self, output_dir: str = "analysis/reports"):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def create_main_report(self, analysis_results: Dict[str, Any]) -> str:
        """Створює головний HTML звіт"""

        template_html = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 Звіт аналізу продажів</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }

        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }

        .header {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            text-align: center;
        }

        .header h1 {
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }

        .header .date {
            color: #7f8c8d;
            font-size: 1.1em;
        }

        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }

        .stat-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
            text-align: center;
            transition: transform 0.3s ease;
        }

        .stat-card:hover {
            transform: translateY(-5px);
        }

        .stat-card .icon {
            font-size: 3em;
            margin-bottom: 15px;
        }

        .stat-card .value {
            font-size: 2em;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 5px;
        }

        .stat-card .label {
            color: #7f8c8d;
            font-size: 1.1em;
        }

        .section {
            background: white;
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        }

        .section h2 {
            color: #2c3e50;
            font-size: 1.8em;
            margin-bottom: 20px;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }

        .table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }

        .table th, .table td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #ecf0f1;
        }

        .table th {
            background: #f8f9fa;
            font-weight: bold;
            color: #2c3e50;
        }

        .table tr:hover {
            background: #f8f9fa;
        }

        .chart-container {
            margin: 20px 0;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 10px;
        }

        .progress-bar {
            background: #ecf0f1;
            border-radius: 10px;
            overflow: hidden;
            height: 10px;
            margin: 5px 0;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #3498db, #2ecc71);
            border-radius: 10px;
            transition: width 0.5s ease;
        }

        .footer {
            text-align: center;
            margin-top: 50px;
            color: white;
            font-size: 1.1em;
        }

        .analysis-section {
            margin-bottom: 40px;
        }

        .insight {
            background: #e8f6f3;
            border-left: 4px solid #1abc9c;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }

        .alert {
            background: #fdf2e9;
            border-left: 4px solid #e67e22;
            padding: 15px;
            margin: 15px 0;
            border-radius: 5px;
        }

        .highlight {
            background: linear-gradient(120deg, #ffecd2 0%, #fcb69f 100%);
            padding: 20px;
            border-radius: 10px;
            margin: 20px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <!-- Заголовок -->
        <div class="header">
            <h1>📊 Звіт аналізу продажів</h1>
            <div class="date">Створено: {{ report_date }}</div>
        </div>

        <!-- Основні показники -->
        <div class="stats-grid">
            <div class="stat-card">
                <div class="icon">💰</div>
                <div class="value">{{ main_stats.total_revenue | default('N/A') }}</div>
                <div class="label">Загальний дохід</div>
            </div>
            <div class="stat-card">
                <div class="icon">🛒</div>
                <div class="value">{{ main_stats.total_transactions | default('N/A') }}</div>
                <div class="label">Кількість транзакцій</div>
            </div>
            <div class="stat-card">
                <div class="icon">📈</div>
                <div class="value">{{ main_stats.avg_check | default('N/A') }}</div>
                <div class="label">Середній чек</div>
            </div>
            <div class="stat-card">
                <div class="icon">👥</div>
                <div class="value">{{ main_stats.unique_clients | default('N/A') }}</div>
                <div class="label">Унікальних клієнтів</div>
            </div>
        </div>

        <!-- Аналіз по точках продажу -->
        {% if spots_analysis %}
        <div class="section">
            <h2>🏪 Аналіз по точках продажу</h2>
            {% for spot in spots_analysis %}
            <div class="highlight">
                <h3>{{ spot.name }}</h3>
                <p><strong>Дохід:</strong> {{ spot.revenue }} грн</p>
                <p><strong>Транзакції:</strong> {{ spot.transactions }}</p>
                <p><strong>Середній чек:</strong> {{ spot.avg_check }} грн</p>
                <div class="progress-bar">
                    <div class="progress-fill" style="width: {{ spot.revenue_percent }}%"></div>
                </div>
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <!-- Топ продукти -->
        {% if top_products %}
        <div class="section">
            <h2>🛍️ Топ продукти</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Продукт</th>
                        <th>Продажі (грн)</th>
                        <th>Кількість</th>
                        <th>Частка (%)</th>
                    </tr>
                </thead>
                <tbody>
                    {% for product in top_products %}
                    <tr>
                        <td>{{ product.name }}</td>
                        <td>{{ product.sales }}</td>
                        <td>{{ product.quantity }}</td>
                        <td>{{ product.percentage }}%</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}

        <!-- Аналіз клієнтів -->
        {% if clients_analysis %}
        <div class="section">
            <h2>👥 Аналіз клієнтів</h2>
            <div class="insight">
                <strong>💡 Ключові інсайти:</strong>
                <ul>
                    {% for insight in clients_analysis.insights %}
                    <li>{{ insight }}</li>
                    {% endfor %}
                </ul>
            </div>

            {% if clients_analysis.top_clients %}
            <h3>🌟 Топ клієнти</h3>
            <table class="table">
                <thead>
                    <tr>
                        <th>Клієнт</th>
                        <th>Витрачено (грн)</th>
                        <th>Транзакції</th>
                        <th>Середній чек</th>
                    </tr>
                </thead>
                <tbody>
                    {% for client in clients_analysis.top_clients %}
                    <tr>
                        <td>{{ client.name }}</td>
                        <td>{{ client.spent }}</td>
                        <td>{{ client.transactions }}</td>
                        <td>{{ client.avg_check }}</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
            {% endif %}
        </div>
        {% endif %}

        <!-- Тренди -->
        {% if trends_analysis %}
        <div class="section">
            <h2>📈 Аналіз трендів</h2>
            {% for trend in trends_analysis %}
            <div class="alert">
                <strong>{{ trend.title }}:</strong> {{ trend.description }}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <!-- Аналіз бонусної системи -->
        {% if bonus_analysis %}
        <div class="section">
            <h2>🎁 Аналіз бонусної системи</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="icon">💰</div>
                    <div class="value">{{ bonus_analysis.total_bonus_amount | default('N/A') }}</div>
                    <div class="label">Загальна сума бонусів</div>
                </div>
                <div class="stat-card">
                    <div class="icon">🎯</div>
                    <div class="value">{{ bonus_analysis.transactions_with_bonus | default('N/A') }}</div>
                    <div class="label">Транзакцій з бонусами</div>
                </div>
                <div class="stat-card">
                    <div class="icon">📊</div>
                    <div class="value">{{ bonus_analysis.avg_bonus_percent | default('N/A') }}</div>
                    <div class="label">Середній % бонусу</div>
                </div>
                <div class="stat-card">
                    <div class="icon">⭐</div>
                    <div class="value">{{ bonus_analysis.max_bonus_percent | default('N/A') }}</div>
                    <div class="label">Максимальний % бонусу</div>
                </div>
            </div>

            <div class="stats-grid">
                <div class="stat-card">
                    <div class="icon">💵</div>
                    <div class="value">{{ bonus_analysis.avg_bonus_amount | default('N/A') }}</div>
                    <div class="label">Середня сума бонусу</div>
                </div>
                <div class="stat-card">
                    <div class="icon">🔥</div>
                    <div class="value">{{ bonus_analysis.max_bonus_amount | default('N/A') }}</div>
                    <div class="label">Максимальна сума бонусу</div>
                </div>
                <div class="stat-card">
                    <div class="icon">📋</div>
                    <div class="value">{{ bonus_analysis.bonus_transaction_percentage | default('N/A') }}</div>
                    <div class="label">% транзакцій з бонусами</div>
                </div>
                <div class="stat-card">
                    <div class="icon">🛒</div>
                    <div class="value">{{ bonus_analysis.avg_transaction_with_bonus | default('N/A') }}</div>
                    <div class="label">Середній чек з бонусами</div>
                </div>
            </div>

            <div class="insight">
                <strong>💡 Ключові інсайти:</strong>
                <ul>
                    {% for insight in bonus_analysis.insights %}
                    <li>{{ insight }}</li>
                    {% endfor %}
                </ul>
            </div>
        </div>
        {% endif %}

        <!-- Тренди продажів по місяцях -->
        {% if sales_trends %}
        <div class="section">
            <h2>📈 Тренди продажів по місяцях</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Період</th>
                        <th>Місяць</th>
                        <th>Дохід (грн)</th>
                        <th>Транзакції</th>
                        <th>Середній чек</th>
                    </tr>
                </thead>
                <tbody>
                    {% for trend in sales_trends %}
                    <tr>
                        <td>{{ trend.period }}</td>
                        <td>{{ trend.month_name }}</td>
                        <td>{{ trend.revenue }}</td>
                        <td>{{ trend.transactions }}</td>
                        <td>{{ trend.avg_check }} грн</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}

        <!-- Комплексна статистика -->
        {% if comprehensive_stats %}
        <div class="section">
            <h2>📋 Комплексна статистика</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="icon">🛍️</div>
                    <div class="value">{{ comprehensive_stats.total_products | default('N/A') }}</div>
                    <div class="label">Унікальних продуктів</div>
                </div>
                <div class="stat-card">
                    <div class="icon">🏪</div>
                    <div class="value">{{ comprehensive_stats.total_spots | default('N/A') }}</div>
                    <div class="label">Точок продажу</div>
                </div>
                <div class="stat-card">
                    <div class="icon">🔝</div>
                    <div class="value">{{ comprehensive_stats.max_transaction | default('N/A') }}</div>
                    <div class="label">Найбільша транзакція</div>
                </div>
                <div class="stat-card">
                    <div class="icon">🛒</div>
                    <div class="value">{{ comprehensive_stats.avg_products_per_transaction | default('N/A') }}</div>
                    <div class="label">Середньо товарів в чеку</div>
                </div>
            </div>
            <div class="insight">
                <strong>💡 Додаткові інсайти:</strong>
                <ul>
                    {% for insight in comprehensive_stats.insights %}
                    <li>{{ insight }}</li>
                    {% endfor %}
                </ul>
            </div>
        </div>
        {% endif %}

        <!-- Детальний аналіз продуктів по категоріях -->
        {% if detailed_product_analysis %}
        <div class="section">
            <h2>🏷️ Аналіз продуктів по категоріях</h2>
            <table class="table">
                <thead>
                    <tr>
                        <th>Категорія</th>
                        <th>Продажі (грн)</th>
                        <th>Кількість</th>
                        <th>Унікальних продуктів</th>
                        <th>Частка (%)</th>
                    </tr>
                </thead>
                <tbody>
                    {% for category in detailed_product_analysis %}
                    <tr>
                        <td>{{ category.category }}</td>
                        <td>{{ category.sales }}</td>
                        <td>{{ category.quantity }}</td>
                        <td>{{ category.unique_products }}</td>
                        <td>{{ category.percentage }}%</td>
                    </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
        {% endif %}

        <!-- Рекомендації -->
        {% if recommendations %}
        <div class="section">
            <h2>💡 Рекомендації</h2>
            {% for rec in recommendations %}
            <div class="insight">
                <strong>{{ rec.title }}:</strong> {{ rec.description }}
            </div>
            {% endfor %}
        </div>
        {% endif %}

        <div class="footer">
            <p>🚀 Згенеровано системою аналізу Avocado API</p>
            <p>{{ report_date }}</p>
        </div>
    </div>

    <script>
        // Додаємо анімації при завантаженні
        document.addEventListener('DOMContentLoaded', function() {
            const cards = document.querySelectorAll('.stat-card, .section');
            cards.forEach((card, index) => {
                card.style.opacity = '0';
                card.style.transform = 'translateY(20px)';
                setTimeout(() => {
                    card.style.transition = 'all 0.5s ease';
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, index * 100);
            });
        });
    </script>
</body>
</html>
        """

        template = Template(template_html)

        # Підготовка даних для шаблону
        template_data = {
            "report_date": datetime.now().strftime("%d.%m.%Y %H:%M"),
            "main_stats": analysis_results.get("main_stats", {}),
            "spots_analysis": analysis_results.get("spots_analysis", []),
            "top_products": analysis_results.get("top_products", []),
            "clients_analysis": analysis_results.get("clients_analysis", {}),
            "trends_analysis": analysis_results.get("trends_analysis", []),
            "bonus_analysis": analysis_results.get("bonus_analysis", {}),
            "sales_trends": analysis_results.get("sales_trends", []),
            "comprehensive_stats": analysis_results.get("comprehensive_stats", {}),
            "detailed_product_analysis": analysis_results.get(
                "detailed_product_analysis", []
            ),
            "recommendations": analysis_results.get("recommendations", []),
        }

        html_content = template.render(**template_data)

        # Зберігаємо файл
        output_file = os.path.join(
            self.output_dir,
            f"sales_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
        )
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_file

    def create_charts_data(self, data: Dict[str, Any]) -> str:
        """Створює JSON файл з даними для графіків"""
        charts_file = os.path.join(self.output_dir, "charts_data.json")
        with open(charts_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return charts_file
