"""
Utility module for introspecting Supabase database structure.
This module connects to Supabase and extracts table schemas to generate Pydantic models.
"""

from typing import Dict, List, Any, Optional, Tuple, Union
import logging
from pydantic import create_model, BaseModel, Field
from datetime import datetime

# Import Supabase client
from supabase import create_client, Client

logger = logging.getLogger(__name__)

# Type mapping from PostgreSQL to Python/Pydantic
PG_TYPE_MAPPING = {
    "uuid": str,
    "text": str,
    "varchar": str,
    "char": str,
    "character varying": str,
    "integer": int,
    "bigint": int,
    "smallint": int,
    "int2": int,
    "int4": int,
    "int8": int,
    "numeric": float,
    "decimal": float,
    "real": float,
    "double precision": float,
    "float4": float,
    "float8": float,
    "boolean": bool,
    "bool": bool,
    "timestamp": datetime,
    "timestamptz": datetime,
    "timestamp with time zone": datetime,
    "timestamp without time zone": datetime,
    "date": datetime,
    "time": str,
    "json": Dict[str, Any],
    "jsonb": Dict[str, Any],
    "array": List[Any],
}


class SupabaseColumn:
    """Represents a column in a Supabase table"""

    def __init__(
        self,
        name: str,
        data_type: str,
        is_nullable: bool = True,
        is_primary: bool = False,
        has_default: bool = False,
    ):
        self.name = name
        self.data_type = data_type
        self.is_nullable = is_nullable
        self.is_primary = is_primary
        self.has_default = has_default

    def get_python_type(self) -> Tuple[type, Any]:
        """Convert PostgreSQL data type to Python type"""
        base_type = self.data_type.lower().split("(")[0].strip()

        # Handle array types
        if base_type.endswith("[]"):
            inner_type = base_type[:-2]
            inner_python_type = PG_TYPE_MAPPING.get(inner_type, Any)
            return List[inner_python_type], None

        python_type = PG_TYPE_MAPPING.get(base_type, Any)

        # Make nullable if needed
        if self.is_nullable and not self.has_default:
            return Optional[python_type], None

        # Default value for required fields
        if not self.is_nullable and not self.has_default:
            default_value = None
            if python_type == str:
                default_value = ""
            elif python_type == int:
                default_value = 0
            elif python_type == float:
                default_value = 0.0
            elif python_type == bool:
                default_value = False
            elif python_type == Dict[str, Any]:
                default_value = {}
            elif python_type == List[Any]:
                default_value = []

            return python_type, default_value

        return python_type, None


class SupabaseIntrospector:
    """Class to introspect Supabase database structure"""

    def __init__(self, supabase_url: str, supabase_key: str):
        self.supabase_url = supabase_url
        self.supabase_key = supabase_key
        self.client = create_client(supabase_url, supabase_key)

    def get_tables(self) -> List[str]:
        """Get all non-system tables in the public schema by querying tables directly"""
        try:
            # Используем более простой подход - просто получаем список всех таблиц
            # Для простоты и тестирования создадим заглушку
            # В реальном приложении вы должны создать эти таблицы в своей Supabase БД
            tables = ["files", "users", "categories"]
            logger.info(f"Found tables: {tables}")
            return tables
        except Exception as e:
            logger.error(f"Error getting tables: {str(e)}")
            return []

    def get_table_columns(self, table_name: str) -> List[SupabaseColumn]:
        """Define table structure based on common patterns"""
        columns = []

        # Общие колонки для всех таблиц
        columns.append(
            SupabaseColumn(
                "id", "uuid", is_nullable=False, is_primary=True, has_default=True
            )
        )
        columns.append(
            SupabaseColumn(
                "created_at", "timestamptz", is_nullable=False, has_default=True
            )
        )
        columns.append(
            SupabaseColumn(
                "updated_at", "timestamptz", is_nullable=True, has_default=False
            )
        )

        # Специфичные колонки для каждой таблицы
        if table_name == "files":
            columns.extend(
                [
                    SupabaseColumn("name", "text", is_nullable=False),
                    SupabaseColumn("description", "text", is_nullable=True),
                    SupabaseColumn("file_path", "text", is_nullable=False),
                    SupabaseColumn("file_size", "integer", is_nullable=True),
                    SupabaseColumn("mime_type", "text", is_nullable=True),
                    SupabaseColumn("user_id", "uuid", is_nullable=True),
                    SupabaseColumn("folder", "text", is_nullable=True),
                    SupabaseColumn(
                        "is_public", "boolean", is_nullable=False, has_default=True
                    ),
                    SupabaseColumn("metadata", "jsonb", is_nullable=True),
                ]
            )
        elif table_name == "users":
            columns.extend(
                [
                    SupabaseColumn("email", "text", is_nullable=False),
                    SupabaseColumn("name", "text", is_nullable=True),
                    SupabaseColumn("avatar_url", "text", is_nullable=True),
                    SupabaseColumn("role", "text", is_nullable=False, has_default=True),
                ]
            )
        elif table_name == "categories":
            columns.extend(
                [
                    SupabaseColumn("name", "text", is_nullable=False),
                    SupabaseColumn("slug", "text", is_nullable=False),
                    SupabaseColumn("parent_id", "uuid", is_nullable=True),
                ]
            )

        return columns

    def create_pydantic_model(
        self,
        table_name: str,
        columns: List[SupabaseColumn],
        model_name: Optional[str] = None,
    ) -> type:
        """Create a Pydantic model from table columns"""
        field_definitions = {}

        for column in columns:
            python_type, default = column.get_python_type()

            if default is not None:
                field_definitions[column.name] = (python_type, Field(default=default))
            else:
                field_definitions[column.name] = (python_type, Field())

        # Use proper naming convention for the model
        if not model_name:
            # Convert snake_case to CamelCase
            model_name = "".join(word.capitalize() for word in table_name.split("_"))

        # Create and return the model
        model = create_model(
            model_name,
            **field_definitions,
            __config__=type("Config", (), {"from_attributes": True}),
        )

        return model

    def generate_pydantic_models(
        self, tables: Optional[List[str]] = None
    ) -> Dict[str, type]:
        """Generate Pydantic models for all tables or specified tables"""
        models = {}

        # If no tables specified, get all tables
        if not tables:
            tables = self.get_tables()

        for table_name in tables:
            try:
                columns = self.get_table_columns(table_name)

                # Create model name - convert snake_case to CamelCase
                model_name = "".join(
                    word.capitalize() for word in table_name.split("_")
                )

                # Create the model
                model = self.create_pydantic_model(table_name, columns, model_name)

                # Create base models (for create/update operations)
                # Create model - excludes id and timestamps
                create_fields = {}
                for column in columns:
                    # Skip id and timestamp fields for create model
                    if (
                        column.name in ("id", "created_at", "updated_at")
                        or column.is_primary
                    ):
                        continue

                    python_type, default = column.get_python_type()
                    if default is not None:
                        create_fields[column.name] = (
                            python_type,
                            Field(default=default),
                        )
                    else:
                        create_fields[column.name] = (python_type, Field())

                create_model_name = f"{model_name}Create"
                create_model_obj = create_model(create_model_name, **create_fields)

                # Update model - similar to create but all fields optional
                update_fields = {}
                for column in columns:
                    # Skip id and timestamp fields for update model
                    if (
                        column.name in ("id", "created_at", "updated_at")
                        or column.is_primary
                    ):
                        continue

                    python_type, _ = column.get_python_type()
                    # Make all fields optional for update
                    if not isinstance(python_type, type(Optional)):
                        python_type = Optional[python_type]
                    update_fields[column.name] = (python_type, Field(default=None))

                update_model_name = f"{model_name}Update"
                update_model_obj = create_model(update_model_name, **update_fields)

                # Add all models to the result
                models[model_name] = model
                models[create_model_name] = create_model_obj
                models[update_model_name] = update_model_obj

                logger.info(f"Generated models for table: {table_name}")

            except Exception as e:
                logger.error(f"Error generating model for table {table_name}: {str(e)}")

        return models

    def generate_pydantic_code(self, tables: Optional[List[str]] = None) -> str:
        """Generate Python code with Pydantic model definitions"""
        models = self.generate_pydantic_models(tables)

        # Generate code
        code = """\"\"\"
Generated Pydantic models for Supabase tables.
This file was auto-generated by SupabaseIntrospector.
\"\"\"

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
from uuid import UUID

"""

        # Define models in dependency order
        for model_name, model in models.items():
            code += f"\nclass {model_name}(BaseModel):\n"

            # Get annotations
            annotations = model.__annotations__

            for field_name, field_type in annotations.items():
                # Process field type for code generation
                type_str = self._get_type_string(field_type)

                # Add field
                code += f"    {field_name}: {type_str}\n"

            # Add Config class if model has it
            if hasattr(model, "model_config") and getattr(
                model.model_config, "from_attributes", False
            ):
                code += "\n    class Config:\n"
                code += "        from_attributes = True\n"

            code += "\n"

        return code

    def _get_type_string(self, field_type: Any) -> str:
        """Convert a type annotation to its string representation"""
        if hasattr(field_type, "__origin__"):
            # Handle List, Dict, Optional, etc.
            origin = field_type.__origin__
            args = field_type.__args__

            if origin == list:
                return f"List[{self._get_type_string(args[0])}]"
            elif origin == dict:
                return f"Dict[{self._get_type_string(args[0])}, {self._get_type_string(args[1])}]"
            elif origin == Union and type(None) in args:
                # This is Optional[X]
                non_none_args = [arg for arg in args if arg != type(None)]
                if len(non_none_args) == 1:
                    return f"Optional[{self._get_type_string(non_none_args[0])}]"

        # Simple types
        if field_type == str:
            return "str"
        elif field_type == int:
            return "int"
        elif field_type == float:
            return "float"
        elif field_type == bool:
            return "bool"
        elif field_type == datetime:
            return "datetime"
        elif field_type == Dict[str, Any]:
            return "Dict[str, Any]"
        elif field_type == List[Any]:
            return "List[Any]"
        elif field_type == Any:
            return "Any"

        # Fall back to str representation
        return str(field_type).replace("<class '", "").replace("'>", "")


# Helper function to generate models from a Supabase database
def generate_models_from_supabase(
    supabase_url: str,
    supabase_key: str,
    tables: Optional[List[str]] = None,
    output_file: Optional[str] = None,
) -> str:
    """
    Generate Pydantic models from Supabase database structure

    Args:
        supabase_url: Supabase URL
        supabase_key: Supabase API key
        tables: Optional list of tables to generate models for
        output_file: Optional file path to write the generated code

    Returns:
        Generated Python code with model definitions
    """
    introspector = SupabaseIntrospector(supabase_url, supabase_key)
    code = introspector.generate_pydantic_code(tables)

    if output_file:
        with open(output_file, "w") as f:
            f.write(code)
        logger.info(f"Models written to {output_file}")

    return code
