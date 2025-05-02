"""
CLI script to generate Pydantic models from Supabase database structure.
Run this script to automatically create models based on your Supabase tables.
"""

import os
import argparse
import logging
from pathlib import Path
from typing import List, Optional
from src.config.settings import settings
from src.features.files_manager.utils.supabase_introspector import generate_models_from_supabase

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    parser = argparse.ArgumentParser(description="Generate Pydantic models from Supabase tables")
    parser.add_argument(
        "--tables", 
        nargs="+", 
        help="Specific tables to generate models for (default: all tables)"
    )
    parser.add_argument(
        "--output", 
        default="src/features/files_manager/schemas/supabase_models.py",
        help="Output file path for generated models"
    )
    parser.add_argument(
        "--url", 
        default=settings.SUPABASE_URL,
        help="Supabase URL (default: from settings)"
    )
    parser.add_argument(
        "--key", 
        default=settings.SUPABASE_KEY,
        help="Supabase API key (default: from settings)"
    )
    
    args = parser.parse_args()
    
    # Ensure output directory exists
    output_path = Path(args.output)
    os.makedirs(output_path.parent, exist_ok=True)
    
    try:
        # Generate models
        logger.info(f"Generating models from Supabase database at {args.url}")
        if args.tables:
            logger.info(f"Using specific tables: {', '.join(args.tables)}")
        
        code = generate_models_from_supabase(
            supabase_url=args.url,
            supabase_key=args.key,
            tables=args.tables,
            output_file=str(output_path)
        )
        
        logger.info(f"Pydantic models successfully generated and saved to {args.output}")
        logger.info(f"Generated {code.count('class ')} models")
        
    except Exception as e:
        logger.error(f"Error generating models: {str(e)}")
        raise

if __name__ == "__main__":
    main()