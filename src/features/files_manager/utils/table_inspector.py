"""
Utility module for inspecting existing Supabase tables and generating Pydantic models.
"""

import logging
from typing import List, Dict, Any, Optional
from supabase import create_client
from pydantic import create_model, Field, BaseModel
import json

from ..config.supabase_config import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

class SupabaseTableInspector:
    """Class for inspecting existing tables in Supabase and generating Pydantic models"""
    
    def __init__(self, table_name: str):
        self.table_name = table_name
        self.supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        
    async def get_table_sample(self, limit: int = 5) -> List[Dict[str, Any]]:
        """Fetch sample data from the table to infer its structure"""
        try:
            response = self.supabase.table(self.table_name).select("*").limit(limit).execute()
            if response.data:
                logger.info(f"Successfully fetched {len(response.data)} sample rows from '{self.table_name}'")
                return response.data
            else:
                logger.warning(f"Table '{self.table_name}' exists but has no data")
                return []
        except Exception as e:
            logger.error(f"Error fetching sample data from '{self.table_name}': {str(e)}")
            raise ValueError(f"Could not access table '{self.table_name}'. Error: {str(e)}")
    
    async def infer_schema_from_data(self, sample_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Infer the schema structure from sample data"""
        if not sample_data:
            logger.warning(f"No sample data available to infer schema for '{self.table_name}'")
            return {}
        
        # Use the first record to infer types
        schema = {}
        
        for key, value in sample_data[0].items():
            field_type = self._get_python_type(value)
            # Check if the field can be null by examining other samples
            is_nullable = any(record.get(key) is None for record in sample_data if key in record)
            
            schema[key] = {
                "type": field_type,
                "nullable": is_nullable
            }
            
        logger.info(f"Inferred schema with {len(schema)} fields for table '{self.table_name}'")
        return schema
    
    def _get_python_type(self, value: Any) -> type:
        """Map a value to its Python type"""
        if value is None:
            return type(None)
        elif isinstance(value, str):
            return str
        elif isinstance(value, int):
            return int
        elif isinstance(value, float):
            return float
        elif isinstance(value, bool):
            return bool
        elif isinstance(value, dict):
            return dict
        elif isinstance(value, list):
            return list
        else:
            return type(value)
    
    async def generate_pydantic_models(self) -> Dict[str, type]:
        """Generate Pydantic models for the table"""
        # Fetch sample data
        sample_data = await self.get_table_sample()
        
        # Infer schema from data
        schema = await self.infer_schema_from_data(sample_data)
        
        if not schema:
            logger.error(f"Could not generate models for '{self.table_name}': No schema information available")
            return {}
        
        # Generate Pydantic field definitions
        field_definitions = {}
        
        for field_name, field_info in schema.items():
            field_type = field_info["type"]
            is_nullable = field_info["nullable"]
            
            if is_nullable and field_type != type(None):
                # For nullable fields, use Optional[type]
                field_definitions[field_name] = (Optional[field_type], Field(default=None))
            else:
                # For required fields
                field_definitions[field_name] = (field_type, Field(...))
        
        # Create the main model
        model_name = ''.join(word.capitalize() for word in self.table_name.split('_'))
        main_model = create_model(
            model_name,
            **field_definitions,
            __config__=type('Config', (), {'from_attributes': True})
        )
        
        # Create create/update models
        create_field_definitions = {}
        update_field_definitions = {}
        
        for field_name, field_info in schema.items():
            field_type = field_info["type"]
            is_nullable = field_info["nullable"]
            
            # Skip id and timestamp fields for create/update models
            if field_name in ['id', 'created_at', 'updated_at']:
                continue
                
            # For create model
            if is_nullable:
                create_field_definitions[field_name] = (Optional[field_type], Field(default=None))
            else:
                create_field_definitions[field_name] = (field_type, Field(...))
                
            # For update model - all fields are optional
            update_field_definitions[field_name] = (Optional[field_type], Field(default=None))
        
        # Create the models
        create_model_name = f"{model_name}Create"
        update_model_name = f"{model_name}Update"
        
        create_model_obj = create_model(
            create_model_name,
            **create_field_definitions
        )
        
        update_model_obj = create_model(
            update_model_name,
            **update_field_definitions
        )
        
        # Return all models
        models = {
            model_name: main_model,
            create_model_name: create_model_obj,
            update_model_name: update_model_obj
        }
        
        logger.info(f"Generated {len(models)} models for table '{self.table_name}'")
        return models
    
    async def generate_models_code(self) -> str:
        """Generate Python code with Pydantic model definitions"""
        models = await self.generate_pydantic_models()
        
        if not models:
            return "# No models could be generated"
        
        # Generate code
        code = f"""\"\"\"
Generated Pydantic models for Supabase table '{self.table_name}'.
This file was auto-generated by SupabaseTableInspector.
\"\"\"

from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

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
            if hasattr(model, 'model_config') and getattr(model.model_config, 'from_attributes', False):
                code += "\n    class Config:\n"
                code += "        from_attributes = True\n"
            
            code += "\n"
            
        return code
    
    def _get_type_string(self, field_type: Any) -> str:
        """Convert a type annotation to its string representation"""
        if hasattr(field_type, "__origin__"):
            # Handle Optional, List, Dict, etc.
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
        elif field_type == dict:
            return "Dict[str, Any]"
        elif field_type == list:
            return "List[Any]"
        
        # Fall back to string representation
        return str(field_type).replace("<class '", "").replace("'>", "")