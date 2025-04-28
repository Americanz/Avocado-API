# Керівництво з імплементації універсальних API маршрутів

Це керівництво допоможе вам інтегрувати універсальні контролери та маршрути API для ваших моделей.

## Огляд

Нова система дозволяє автоматично створювати CRUD API для моделей, що істотно зменшує кількість повторюваного коду і стандартизує відповіді API.

Основні компоненти:
1. `GenericController` - універсальний контролер для CRUD операцій
2. `create_api_router` - функція для створення API маршрутів
3. `generic_module_loader` - система для автоматичного виявлення та створення маршрутів для моделей
4. Оновлена базова модель з підтримкою налаштувань для універсальних маршрутів

## Кроки для імплементації

### 1. Оновлення структури проекту

Розмістіть нові файли у відповідних каталогах:

```
src/
├── core/
│   ├── crud/
│   │   ├── __init__.py
│   │   ├── crud_base.py              # Існуючий файл
│   │   ├── generic_controller.py     # Новий файл з GenericController
│   │   ├── generic_routes.py         # Новий файл з функцією create_api_router
│   │   └── generic_module_loader.py  # Новий файл для автоматичного завантаження
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base_model.py             # Оновлений файл з підтримкою generic_routes
│   │   └── features_loader.py        # Оновлений файл з підтримкою generic_routes
│   │
│   └── schemas/
│       ├── __init__.py
│       ├── base.py                   # Існуючий файл
│       └── responses.py              # Новий файл для кастомних відповідей
```

### 2. Налаштування моделі для використання універсальних маршрутів

Щоб модель використовувала автоматичну генерацію CRUD API, додайте до неї відповідні атрибути:

```python
from src.core.models.base_model import BaseModel

class Product(BaseModel):
    """Модель продукту."""

    # Включаємо автоматичну генерацію CRUD API
    use_generic_routes = True

    # Налаштування для GenericController
    search_fields = ["name", "description", "sku"]
    default_order_by = ["name"]
    select_related = ["category"]

    # Поля моделі
    name = Column(String(255), nullable=False)
    # ... інші поля ...
```

Або можна використати метод `enable_generic_routes` для налаштування:

```python
class Product(BaseModel):
    """Модель продукту."""

    # Поля моделі
    name = Column(String(255), nullable=False)
    # ... інші поля ...

# Налаштовуємо універсальні маршрути для моделі
Product.enable_generic_routes(
    search_fields=["name", "description", "sku"],
    default_order_by=["name"],
    select_related=["category"],
    public_routes=False  # Чи маршрути публічні (без авторизації)
)
```

### 3. Створення схем для моделі

Для кожної моделі, яка використовує універсальні маршрути, необхідно створити схеми Pydantic:

```python
# src/features/catalog/product/schemas.py
from src.core.schemas.base import BaseSchema, BaseResponseSchema

class ProductCreate(BaseSchema):
    """Схема для створення продукту."""
    name: str
    price: float
    # ... інші поля ...

class ProductUpdate(BaseSchema):
    """Схема для оновлення продукту."""
    name: Optional[str] = None
    price: Optional[float] = None
    # ... інші поля ...

class ProductResponse(BaseResponseSchema):
    """Схема для відповіді з даними продукту."""
    name: str
    price: float
    # ... інші поля ...

    model_config = {"from_attributes": True}

```

### 4. Інтеграція з існуючим кодом

Якщо модель вже має власний контролер чи маршрути, ви можете:

- **Замінити існуючий підхід** універсальним (для простих моделей)
- **Розширити універсальний контролер** для додавання спеціальної логіки

```python
# Розширення універсального контролера
class ProductController(GenericController[Product, ProductCreate, ProductUpdate, ProductResponse]):
    """Контролер продуктів."""

    async def get_products_by_category(self, category_id: UUID) -> List[Product]:
        """Спеціалізований метод для отримання продуктів за категорією."""
        db = await self.get_db_session()
        # ... спеціалізована логіка ...
```

### 5. Додавання маршрутів вручну (якщо потрібно)

Ви також можете створити універсальні маршрути вручну:

```python
# src/features/catalog/product/routes.py
from src.core.crud.generic_routes import create_api_router
from src.core.crud.generic_controller import create_controller
from src.features.catalog.product.model import Product
from src.features.catalog.product.schemas import ProductCreate, ProductUpdate, ProductResponse

# Створюємо маршрутизатор
router = create_api_router(
    controller=create_controller(Product, ProductResponse),
    create_schema=ProductCreate,
    update_schema=ProductUpdate,
    response_schema=ProductResponse,
    prefix="/products",
    tags=["products"],
)

# Додаємо спеціалізовані маршрути
@router.get("/by-category/{category_id}")
async def get_products_by_category(category_id: UUID):
    """Отримати продукти за категорією."""
    # ... спеціалізована логіка ...
```

## Доступні CRUD операції

Універсальний API автоматично створює такі ендпоінти:

| Метод   | Шлях                   | Опис                        | Авторизація |
|---------|------------------------|-----------------------------|-------------|
| GET     | /                      | Отримати список з пагінацією| Залежить від налаштувань |
| GET     | /{item_id}             | Отримати один об'єкт за ID  | Залежить від налаштувань |
| POST    | /                      | Створити новий об'єкт       | Залежить від налаштувань |
| PATCH   | /{item_id}             | Оновити об'єкт              | Вимагається  |
| DELETE  | /{item_id}             | Видалити об'єкт             | Вимагається  |
| POST    | /bulk                  | Масове створення об'єктів   | Адміністратор |

## Кастомізація відповідей API

Всі відповіді універсальних маршрутів використовують єдиний формат:

```json
{
  "code": "0000",
  "msg": "OK",
  "data": { ... }
}
```

Для помилок:

```json
{
  "code": "4004",
  "msg": "Об'єкт не знайдено",
  "data": null
}
```

Для пагінованих відповідей:

```json
{
  "code": "0000",
  "msg": "OK",
  "data": [ ... ],
  "total": 100,
  "current": 1,
  "size": 20
}
```

## Висновок

Нова система універсальних маршрутів дозволяє:

1. **Скоротити обсяг коду** для стандартних операцій
2. **Стандартизувати відповіді API** з єдиним форматом
3. **Спростити розробку нових функцій** завдяки автоматизації
4. **Забезпечити гнучкість** через можливість розширення базової логіки

Використовуйте її для прискорення розробки та покращення якості коду.
