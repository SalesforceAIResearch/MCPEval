#!/usr/bin/env uv run
import os
import sys
import sqlite3
import logging
import json
import tempfile
from contextlib import closing
from pathlib import Path
from typing import Dict, Any, List, Optional, Literal

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp_sqlite = FastMCP("SQLite Database Assistant")
mcp_tool = mcp_sqlite.tool

# Global database path
_db_path = None
_insights = []

def get_db_path():
    """Get or create the database path."""
    global _db_path
    if _db_path is None:
        # Use a temporary database file if no path is specified
        db_dir = os.path.expanduser("~/.mcp_sqlite")
        os.makedirs(db_dir, exist_ok=True)
        _db_path = os.path.join(db_dir, "mcp_database.db")
    return _db_path

def execute_query(query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Execute a SQL query and return results as a list of dictionaries."""
    logger.debug(f"Executing query: {query}")
    try:
        db_path = get_db_path()
        with closing(sqlite3.connect(db_path)) as conn:
            conn.row_factory = sqlite3.Row
            with closing(conn.cursor()) as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE', 'CREATE', 'DROP', 'ALTER')):
                    conn.commit()
                    affected = cursor.rowcount
                    logger.debug(f"Write query affected {affected} rows")
                    return [{"affected_rows": affected, "status": "success"}]

                results = [dict(row) for row in cursor.fetchall()]
                logger.debug(f"Read query returned {len(results)} rows")
                return results
    except Exception as e:
        logger.error(f"Database error executing query: {e}")
        raise

@mcp_tool()
async def list_tables() -> Dict[str, Any]:
    """
    List all tables in the SQLite database.
    
    Returns:
        Dictionary containing the list of tables and their information.
    """
    try:
        results = execute_query("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row['name'] for row in results]
        
        return {
            "status": "success",
            "total_tables": len(tables),
            "tables": tables
        }
    except Exception as e:
        logger.error(f"Error listing tables: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error listing tables: {str(e)}"
        }

@mcp_tool()
async def describe_table(table_name: str) -> Dict[str, Any]:
    """
    Get the schema information for a specific table.
    
    Args:
        table_name: Name of the table to describe
        
    Returns:
        Dictionary containing table schema information.
    """
    try:
        # Get table info using PRAGMA
        results = execute_query(f"PRAGMA table_info({table_name})")
        
        if not results:
            return {
                "status": "error",
                "error_message": f"Table '{table_name}' does not exist"
            }
        
        columns = []
        for row in results:
            columns.append({
                "column_id": row['cid'],
                "name": row['name'],
                "type": row['type'],
                "not_null": bool(row['notnull']),
                "default_value": row['dflt_value'],
                "primary_key": bool(row['pk'])
            })
        
        return {
            "status": "success",
            "table_name": table_name,
            "columns": columns
        }
    except Exception as e:
        logger.error(f"Error describing table: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error describing table: {str(e)}"
        }

@mcp_tool()
async def execute_select_query(query: str) -> Dict[str, Any]:
    """
    Execute a SELECT query on the SQLite database.
    
    Args:
        query: SELECT SQL query to execute
        
    Returns:
        Dictionary containing query results.
    """
    try:
        # Validate that it's a SELECT query
        query_upper = query.strip().upper()
        if not query_upper.startswith("SELECT"):
            return {
                "status": "error",
                "error_message": "Only SELECT queries are allowed for this tool"
            }
        
        results = execute_query(query)
        
        return {
            "status": "success",
            "query": query,
            "total_rows": len(results),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error executing SELECT query: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error executing query: {str(e)}"
        }

@mcp_tool()
async def execute_write_query(query: str) -> Dict[str, Any]:
    """
    Execute an INSERT, UPDATE, or DELETE query on the SQLite database.
    
    Args:
        query: SQL query to execute (INSERT, UPDATE, DELETE)
        
    Returns:
        Dictionary containing execution results.
    """
    try:
        # Validate that it's not a SELECT query
        query_upper = query.strip().upper()
        if query_upper.startswith("SELECT"):
            return {
                "status": "error",
                "error_message": "SELECT queries are not allowed for this tool. Use execute_select_query instead."
            }
        
        results = execute_query(query)
        
        return {
            "status": "success",
            "query": query,
            "affected_rows": results[0]["affected_rows"] if results else 0
        }
    except Exception as e:
        logger.error(f"Error executing write query: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error executing query: {str(e)}"
        }

@mcp_tool()
async def create_table(query: str) -> Dict[str, Any]:
    """
    Create a new table in the SQLite database.
    
    Args:
        query: CREATE TABLE SQL statement
        
    Returns:
        Dictionary containing creation results.
    """
    try:
        # Validate that it's a CREATE TABLE statement
        query_upper = query.strip().upper()
        if not query_upper.startswith("CREATE TABLE"):
            return {
                "status": "error",
                "error_message": "Only CREATE TABLE statements are allowed for this tool"
            }
        
        execute_query(query)
        
        return {
            "status": "success",
            "message": "Table created successfully",
            "query": query
        }
    except Exception as e:
        logger.error(f"Error creating table: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error creating table: {str(e)}"
        }

@mcp_tool()
async def get_database_stats() -> Dict[str, Any]:
    """
    Get general statistics about the database.
    
    Returns:
        Dictionary containing database statistics.
    """
    try:
        # Get list of tables
        tables_result = execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [row['name'] for row in tables_result]
        
        # Get row counts for each table
        table_stats = []
        total_rows = 0
        
        for table_name in table_names:
            try:
                count_result = execute_query(f"SELECT COUNT(*) as count FROM {table_name}")
                row_count = count_result[0]['count'] if count_result else 0
                total_rows += row_count
                
                table_stats.append({
                    "table_name": table_name,
                    "row_count": row_count
                })
            except Exception as e:
                logger.warning(f"Could not get row count for table {table_name}: {e}")
                table_stats.append({
                    "table_name": table_name,
                    "row_count": "unknown"
                })
        
        # Get database file size
        db_path = get_db_path()
        file_size = os.path.getsize(db_path) if os.path.exists(db_path) else 0
        
        return {
            "status": "success",
            "database_path": db_path,
            "file_size_bytes": file_size,
            "total_tables": len(table_names),
            "total_rows": total_rows,
            "table_statistics": table_stats
        }
    except Exception as e:
        logger.error(f"Error getting database stats: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error getting database statistics: {str(e)}"
        }

@mcp_tool()
async def add_sample_data(dataset: Literal["employees", "products", "customers"] = "employees") -> Dict[str, Any]:
    """
    Add sample data to the database for testing and demonstration purposes.
    
    Args:
        dataset: Type of sample data to add (employees, products, or customers)
        
    Returns:
        Dictionary containing the results of adding sample data.
    """
    try:
        if dataset == "employees":
            # Create employees table and add sample data
            create_query = """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                salary REAL NOT NULL,
                hire_date TEXT NOT NULL,
                email TEXT UNIQUE
            )
            """
            execute_query(create_query)
            
            # Sample employee data
            employees_data = [
                ("Alice Johnson", "Engineering", 95000, "2023-01-15", "alice.johnson@company.com"),
                ("Bob Smith", "Marketing", 75000, "2023-03-01", "bob.smith@company.com"),
                ("Carol Davis", "Engineering", 105000, "2022-07-10", "carol.davis@company.com"),
                ("David Wilson", "Sales", 80000, "2023-05-20", "david.wilson@company.com"),
                ("Eve Brown", "HR", 70000, "2023-02-14", "eve.brown@company.com"),
                ("Frank Miller", "Engineering", 90000, "2022-11-30", "frank.miller@company.com"),
                ("Grace Lee", "Marketing", 72000, "2023-04-18", "grace.lee@company.com"),
                ("Henry Taylor", "Sales", 85000, "2023-01-08", "henry.taylor@company.com")
            ]
            
            for emp in employees_data:
                insert_query = "INSERT OR IGNORE INTO employees (name, department, salary, hire_date, email) VALUES (?, ?, ?, ?, ?)"
                execute_query(insert_query, dict(zip(['name', 'department', 'salary', 'hire_date', 'email'], emp)))
            
            return {
                "status": "success",
                "message": f"Sample {dataset} data added successfully",
                "records_added": len(employees_data),
                "table_created": "employees"
            }
            
        elif dataset == "products":
            # Create products table and add sample data
            create_query = """
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                price REAL NOT NULL,
                stock_quantity INTEGER NOT NULL,
                description TEXT
            )
            """
            execute_query(create_query)
            
            # Sample product data
            products_data = [
                ("Laptop Pro", "Electronics", 1299.99, 25, "High-performance laptop for professionals"),
                ("Wireless Mouse", "Electronics", 29.99, 150, "Ergonomic wireless mouse with long battery life"),
                ("Office Chair", "Furniture", 249.99, 40, "Comfortable ergonomic office chair"),
                ("Desk Lamp", "Furniture", 89.99, 75, "LED desk lamp with adjustable brightness"),
                ("Coffee Mug", "Kitchenware", 12.99, 200, "Ceramic coffee mug with company logo"),
                ("Notebook Set", "Stationery", 19.99, 100, "Set of 3 professional notebooks"),
                ("Smartphone", "Electronics", 699.99, 30, "Latest model smartphone with advanced features"),
                ("Standing Desk", "Furniture", 399.99, 15, "Height-adjustable standing desk")
            ]
            
            for prod in products_data:
                insert_query = "INSERT OR IGNORE INTO products (name, category, price, stock_quantity, description) VALUES (?, ?, ?, ?, ?)"
                execute_query(insert_query, dict(zip(['name', 'category', 'price', 'stock_quantity', 'description'], prod)))
            
            return {
                "status": "success",
                "message": f"Sample {dataset} data added successfully",
                "records_added": len(products_data),
                "table_created": "products"
            }
            
        elif dataset == "customers":
            # Create customers table and add sample data
            create_query = """
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                phone TEXT,
                city TEXT,
                state TEXT,
                registration_date TEXT NOT NULL
            )
            """
            execute_query(create_query)
            
            # Sample customer data
            customers_data = [
                ("John Doe", "john.doe@email.com", "(555) 123-4567", "New York", "NY", "2023-01-10"),
                ("Jane Smith", "jane.smith@email.com", "(555) 234-5678", "Los Angeles", "CA", "2023-02-15"),
                ("Mike Johnson", "mike.johnson@email.com", "(555) 345-6789", "Chicago", "IL", "2023-03-20"),
                ("Sarah Williams", "sarah.williams@email.com", "(555) 456-7890", "Houston", "TX", "2023-04-25"),
                ("Tom Brown", "tom.brown@email.com", "(555) 567-8901", "Phoenix", "AZ", "2023-05-30"),
                ("Lisa Davis", "lisa.davis@email.com", "(555) 678-9012", "Philadelphia", "PA", "2023-06-05"),
                ("Chris Wilson", "chris.wilson@email.com", "(555) 789-0123", "San Antonio", "TX", "2023-07-10"),
                ("Amy Taylor", "amy.taylor@email.com", "(555) 890-1234", "San Diego", "CA", "2023-08-15")
            ]
            
            for cust in customers_data:
                insert_query = "INSERT OR IGNORE INTO customers (name, email, phone, city, state, registration_date) VALUES (?, ?, ?, ?, ?, ?)"
                execute_query(insert_query, dict(zip(['name', 'email', 'phone', 'city', 'state', 'registration_date'], cust)))
            
            return {
                "status": "success",
                "message": f"Sample {dataset} data added successfully",
                "records_added": len(customers_data),
                "table_created": "customers"
            }
        
        else:
            return {
                "status": "error",
                "error_message": f"Unknown dataset type: {dataset}. Available options: employees, products, customers"
            }
            
    except Exception as e:
        logger.error(f"Error adding sample data: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error adding sample data: {str(e)}"
        }

@mcp_tool()
async def clear_database() -> Dict[str, Any]:
    """
    Clear all data from the database (drop all tables).
    
    Returns:
        Dictionary containing the results of clearing the database.
    """
    try:
        # Get list of all tables
        tables_result = execute_query("SELECT name FROM sqlite_master WHERE type='table'")
        table_names = [row['name'] for row in tables_result]
        
        # Drop each table
        dropped_tables = []
        for table_name in table_names:
            try:
                execute_query(f"DROP TABLE {table_name}")
                dropped_tables.append(table_name)
            except Exception as e:
                logger.warning(f"Could not drop table {table_name}: {e}")
        
        return {
            "status": "success",
            "message": "Database cleared successfully",
            "dropped_tables": dropped_tables,
            "total_dropped": len(dropped_tables)
        }
    except Exception as e:
        logger.error(f"Error clearing database: {str(e)}")
        return {
            "status": "error",
            "error_message": f"Error clearing database: {str(e)}"
        }

# Main function to run the server
if __name__ == "__main__":
    try:
        logger.info("Starting SQLite MCP Server")
        mcp_sqlite.run()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise
