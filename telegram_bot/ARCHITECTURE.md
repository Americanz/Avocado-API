# Telegram Bot Architecture

## Overview
Telegram bot integrated with FastAPI project using PostgreSQL database.

## Architecture Principles

### 🏗️ Models Location
- **Models**: `src/features/telegram_bot/model.py` (FastAPI features)
- **Import in bot**: Direct import from features, no duplication
- **Database**: Shared PostgreSQL with main project

### 🔄 Service Layer
- **Universal Service**: `services/bonus_service_universal.py`
- **PostgreSQL Implementation**: `services/postgres/` 
- **Supabase Backup**: `services/supabase/` (legacy support)

### 📁 Project Structure
```
telegram_bot/
├── services/
│   ├── bonus_service_universal.py    # Abstract interface + factory
│   ├── postgres/                     # PostgreSQL implementation
│   └── supabase/                     # Supabase implementation (backup)
├── handlers/                         # Telegram message handlers
├── data/                            # Bot texts, keyboards, menus
├── navigation/                       # Navigation system
├── states/                          # User state management
└── middlewares/                     # Custom middlewares

src/features/telegram_bot/           # FastAPI integration
├── model.py                         # SQLAlchemy models (source of truth)
├── schemas.py                       # Pydantic schemas
├── controller.py                    # CRUD controllers
└── routes.py                        # Admin API endpoints
```

## Benefits

✅ **Single Source of Truth**: Models defined once in features  
✅ **Database Integration**: Shared PostgreSQL with FastAPI  
✅ **Scalability**: Can switch between PostgreSQL/Supabase  
✅ **Admin Interface**: Internal API for management  
✅ **Clean Architecture**: Separation of concerns

## Database Tables

- `telegram_bot_users` - Telegram user information
- `telegram_bonus_accounts` - User bonus balances  
- `telegram_bonus_transactions` - Transaction history

## Usage

```python
# In telegram bot handlers
from telegram_bot.services.bonus_service_universal import get_bonus_service

async def handler(message):
    service = get_bonus_service()
    user = await service.get_user_by_id(user_id)
    balance = await service.get_user_balance(user_id)
```

```python
# In FastAPI endpoints (internal)
from src.features.telegram_bot import telegram_bot_user, TelegramBotUser

def get_user(user_id: int, db: Session):
    return telegram_bot_user.get_by_telegram_id(db, user_id)
```

## Migration Notes

- ✅ Removed duplicate `bot_models.py`
- ✅ Direct imports from `src.features.telegram_bot.model`
- ✅ Maintained backward compatibility
- ✅ All tests passing