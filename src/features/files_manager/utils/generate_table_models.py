"""
Script to inspect an existing Supabase table and generate Pydantic models.
Run this to generate models from your existing Supabase tables.
"""

import asyncio
import logging
import os
import argparse
from pathlib import Path
from .table_inspector import SupabaseTableInspector

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def generate_models_for_table(table_name: str, output_file: str = None):
    """
    Generate Pydantic models for a specific Supabase table
    
    Args:
        table_name: Name of the table to inspect
        output_file: Optional file path to save the generated code
    
    Returns:
        Generated Python code with model definitions
    """
    try:
        # Create inspector
        inspector = SupabaseTableInspector(table_name)
        
        # Generate models code
        logger.info(f"Generating models for table: {table_name}")
        models_code = await inspector.generate_models_code()
        
        # Save to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(models_code)
            logger.info(f"Models saved to {output_file}")
        
        # Return the generated code
        return models_code
    
    except Exception as e:
        logger.error(f"Error generating models: {str(e)}")
        raise

def main():
    """Main function to run the script"""
    parser = argparse.ArgumentParser(description="Generate Pydantic models from an existing Supabase table")
    parser.add_argument("table", help="Name of the Supabase table to inspect")
    parser.add_argument("--output", "-o", help="Output file path (default: auto-generated based on table name)")
    args = parser.parse_args()
    
    # If output file not specified, create a default path
    if not args.output:
        # Get the module path
        module_path = Path(__file__).parent.parent
        schemas_path = module_path / "schemas"
        
        # Create schemas directory if it doesn't exist
        os.makedirs(schemas_path, exist_ok=True)
        
        # Default output file
        output_path = schemas_path / f"{args.table}_models.py"
    else:
        output_path = Path(args.output)
        
        # Create parent directories if they don't exist
        os.makedirs(output_path.parent, exist_ok=True)
    
    # Run the async function
    asyncio.run(generate_models_for_table(
        table_name=args.table,
        output_file=str(output_path)
    ))
    
    logger.info(f"Generated models for {args.table} successfully")

if __name__ == "__main__":
    main()