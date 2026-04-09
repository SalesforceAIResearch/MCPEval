#!/usr/bin/env uv run
import logging
from typing import Dict, Any, Literal

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp = FastMCP("Unit Converter")

# Conversion factors to a base unit for each category
LENGTH_TO_METERS = {
    "mm": 0.001,
    "cm": 0.01,
    "m": 1.0,
    "km": 1000.0,
    "in": 0.0254,
    "ft": 0.3048,
    "yd": 0.9144,
    "mi": 1609.344,
}

WEIGHT_TO_GRAMS = {
    "mg": 0.001,
    "g": 1.0,
    "kg": 1000.0,
    "oz": 28.3495,
    "lb": 453.592,
    "ton": 907184.74,  # US short ton
}

VOLUME_TO_ML = {
    "ml": 1.0,
    "l": 1000.0,
    "gal": 3785.41,
    "qt": 946.353,
    "pt": 473.176,
    "cup": 236.588,
    "fl_oz": 29.5735,
}

SPEED_TO_MS = {
    "m/s": 1.0,
    "km/h": 1 / 3.6,
    "mph": 0.44704,
    "knots": 0.514444,
}

DATA_TO_BYTES = {
    "B": 1,
    "KB": 1024,
    "MB": 1024 ** 2,
    "GB": 1024 ** 3,
    "TB": 1024 ** 4,
    "PB": 1024 ** 5,
}


def _convert(value: float, from_unit: str, to_unit: str, factors: dict, base_unit_name: str) -> Dict[str, Any]:
    """Generic conversion using a factor table."""
    if from_unit == to_unit:
        return {
            "status": "success",
            "input_value": value,
            "input_unit": from_unit,
            "output_value": value,
            "output_unit": to_unit,
        }
    base_value = value * factors[from_unit]
    result = base_value / factors[to_unit]
    return {
        "status": "success",
        "input_value": value,
        "input_unit": from_unit,
        "output_value": round(result, 6),
        "output_unit": to_unit,
    }


@mcp.tool()
async def convert_length(
    value: float,
    from_unit: Literal["mm", "cm", "m", "km", "in", "ft", "yd", "mi"],
    to_unit: Literal["mm", "cm", "m", "km", "in", "ft", "yd", "mi"]
) -> Dict[str, Any]:
    """
    Convert a length value between different units of measurement.

    Args:
        value: The numeric value to convert
        from_unit: The source unit (mm, cm, m, km, in, ft, yd, mi)
        to_unit: The target unit (mm, cm, m, km, in, ft, yd, mi)
    """
    try:
        return _convert(value, from_unit, to_unit, LENGTH_TO_METERS, "meters")
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def convert_weight(
    value: float,
    from_unit: Literal["mg", "g", "kg", "oz", "lb", "ton"],
    to_unit: Literal["mg", "g", "kg", "oz", "lb", "ton"]
) -> Dict[str, Any]:
    """
    Convert a weight/mass value between different units of measurement.

    Args:
        value: The numeric value to convert
        from_unit: The source unit (mg, g, kg, oz, lb, ton)
        to_unit: The target unit (mg, g, kg, oz, lb, ton)
    """
    try:
        return _convert(value, from_unit, to_unit, WEIGHT_TO_GRAMS, "grams")
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def convert_temperature(
    value: float,
    from_unit: Literal["celsius", "fahrenheit", "kelvin"],
    to_unit: Literal["celsius", "fahrenheit", "kelvin"]
) -> Dict[str, Any]:
    """
    Convert a temperature value between Celsius, Fahrenheit, and Kelvin.

    Args:
        value: The temperature value to convert
        from_unit: The source unit (celsius, fahrenheit, kelvin)
        to_unit: The target unit (celsius, fahrenheit, kelvin)
    """
    try:
        # Convert to Celsius first
        if from_unit == "celsius":
            celsius = value
        elif from_unit == "fahrenheit":
            celsius = (value - 32) * 5 / 9
        elif from_unit == "kelvin":
            celsius = value - 273.15

        # Convert from Celsius to target
        if to_unit == "celsius":
            result = celsius
        elif to_unit == "fahrenheit":
            result = celsius * 9 / 5 + 32
        elif to_unit == "kelvin":
            result = celsius + 273.15

        return {
            "status": "success",
            "input_value": value,
            "input_unit": from_unit,
            "output_value": round(result, 4),
            "output_unit": to_unit,
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def convert_volume(
    value: float,
    from_unit: Literal["ml", "l", "gal", "qt", "pt", "cup", "fl_oz"],
    to_unit: Literal["ml", "l", "gal", "qt", "pt", "cup", "fl_oz"]
) -> Dict[str, Any]:
    """
    Convert a volume value between different units of measurement.

    Args:
        value: The numeric value to convert
        from_unit: The source unit (ml, l, gal, qt, pt, cup, fl_oz)
        to_unit: The target unit (ml, l, gal, qt, pt, cup, fl_oz)
    """
    try:
        return _convert(value, from_unit, to_unit, VOLUME_TO_ML, "milliliters")
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def convert_speed(
    value: float,
    from_unit: Literal["m/s", "km/h", "mph", "knots"],
    to_unit: Literal["m/s", "km/h", "mph", "knots"]
) -> Dict[str, Any]:
    """
    Convert a speed value between different units of measurement.

    Args:
        value: The numeric value to convert
        from_unit: The source unit (m/s, km/h, mph, knots)
        to_unit: The target unit (m/s, km/h, mph, knots)
    """
    try:
        return _convert(value, from_unit, to_unit, SPEED_TO_MS, "m/s")
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def convert_data_size(
    value: float,
    from_unit: Literal["B", "KB", "MB", "GB", "TB", "PB"],
    to_unit: Literal["B", "KB", "MB", "GB", "TB", "PB"]
) -> Dict[str, Any]:
    """
    Convert a digital data size between different units (using binary/IEC standard: 1 KB = 1024 B).

    Args:
        value: The numeric value to convert
        from_unit: The source unit (B, KB, MB, GB, TB, PB)
        to_unit: The target unit (B, KB, MB, GB, TB, PB)
    """
    try:
        return _convert(value, from_unit, to_unit, DATA_TO_BYTES, "bytes")
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


if __name__ == "__main__":
    mcp.run()
