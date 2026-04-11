#!/usr/bin/env uv run
import os
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Literal
from zoneinfo import ZoneInfo

from mcp.server.fastmcp import FastMCP

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initialize the MCP server
mcp = FastMCP("DateTime Tools")

# Public holidays by country (fixed dates only for determinism)
HOLIDAYS = {
    "US": {
        "New Year's Day": "01-01",
        "Independence Day": "07-04",
        "Veterans Day": "11-11",
        "Christmas Day": "12-25",
        "Juneteenth": "06-19",
    },
    "UK": {
        "New Year's Day": "01-01",
        "Christmas Day": "12-25",
        "Boxing Day": "12-26",
    },
    "DE": {
        "New Year's Day": "01-01",
        "Labour Day": "05-01",
        "German Unity Day": "10-03",
        "Christmas Day": "12-25",
        "St. Stephen's Day": "12-26",
    },
    "FR": {
        "New Year's Day": "01-01",
        "Labour Day": "05-01",
        "Bastille Day": "07-14",
        "Armistice Day": "11-11",
        "Christmas Day": "12-25",
    },
    "JP": {
        "New Year's Day": "01-01",
        "National Foundation Day": "02-11",
        "Emperor's Birthday": "02-23",
        "Showa Day": "04-29",
        "Constitution Memorial Day": "05-03",
        "Greenery Day": "05-04",
        "Children's Day": "05-05",
        "Mountain Day": "08-11",
        "Culture Day": "11-03",
        "Labour Thanksgiving Day": "11-23",
    },
}


def _parse_date(date_str: str) -> datetime:
    """Parse a date string in ISO format (YYYY-MM-DD)."""
    for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Cannot parse date: '{date_str}'. Expected format: YYYY-MM-DD or YYYY-MM-DDTHH:MM:SS")


def _get_holidays_for_year(year: int, country_code: str) -> set:
    """Get holiday dates for a given year and country."""
    holidays = set()
    country_holidays = HOLIDAYS.get(country_code, {})
    for _, md in country_holidays.items():
        month, day = md.split("-")
        holidays.add(datetime(year, int(month), int(day)).date())
    return holidays


@mcp.tool()
async def convert_timezone(
    datetime_str: str,
    from_tz: str,
    to_tz: str
) -> Dict[str, Any]:
    """
    Convert a datetime from one timezone to another.

    Args:
        datetime_str: The datetime string in ISO 8601 format (e.g., '2024-03-15T14:30:00')
        from_tz: Source IANA timezone name (e.g., 'America/New_York', 'Europe/London', 'Asia/Tokyo')
        to_tz: Target IANA timezone name (e.g., 'America/Los_Angeles', 'Europe/Berlin', 'Asia/Shanghai')
    """
    try:
        dt = _parse_date(datetime_str)
        source_tz = ZoneInfo(from_tz)
        target_tz = ZoneInfo(to_tz)
        dt_source = dt.replace(tzinfo=source_tz)
        dt_target = dt_source.astimezone(target_tz)
        offset_hours = dt_target.utcoffset().total_seconds() / 3600

        return {
            "status": "success",
            "original_datetime": datetime_str,
            "original_timezone": from_tz,
            "converted_datetime": dt_target.strftime("%Y-%m-%dT%H:%M:%S"),
            "target_timezone": to_tz,
            "utc_offset_hours": offset_hours,
        }
    except KeyError as e:
        return {"status": "error", "error_message": f"Invalid timezone: {e}. Use IANA timezone names like 'America/New_York'."}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def calculate_date_difference(
    start_date: str,
    end_date: str,
    unit: Literal["days", "weeks", "months", "years"] = "days"
) -> Dict[str, Any]:
    """
    Calculate the difference between two dates.

    Args:
        start_date: The start date in YYYY-MM-DD format
        end_date: The end date in YYYY-MM-DD format
        unit: The unit for the result - 'days', 'weeks', 'months', or 'years'
    """
    try:
        dt_start = _parse_date(start_date)
        dt_end = _parse_date(end_date)
        delta = dt_end - dt_start
        total_days = delta.days

        if unit == "days":
            difference = total_days
        elif unit == "weeks":
            difference = round(total_days / 7, 2)
        elif unit == "months":
            difference = round(total_days / 30.4375, 2)
        elif unit == "years":
            difference = round(total_days / 365.25, 2)

        return {
            "status": "success",
            "start_date": start_date,
            "end_date": end_date,
            "difference": difference,
            "unit": unit,
            "total_days": total_days,
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def add_to_date(
    date_str: str,
    amount: int,
    unit: Literal["days", "weeks", "months", "years"] = "days"
) -> Dict[str, Any]:
    """
    Add or subtract a time duration from a date. Use negative amount to subtract.

    Args:
        date_str: The starting date in YYYY-MM-DD format
        amount: The number of units to add (negative to subtract)
        unit: The time unit - 'days', 'weeks', 'months', or 'years'
    """
    try:
        dt = _parse_date(date_str)

        if unit == "days":
            result = dt + timedelta(days=amount)
        elif unit == "weeks":
            result = dt + timedelta(weeks=amount)
        elif unit == "months":
            month = dt.month + amount
            year = dt.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            day = min(dt.day, [31, 29 if year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else 28,
                                31, 30, 31, 30, 31, 31, 30, 31, 30, 31][month - 1])
            result = dt.replace(year=year, month=month, day=day)
        elif unit == "years":
            year = dt.year + amount
            day = min(dt.day, 29 if dt.month == 2 and year % 4 == 0 and (year % 100 != 0 or year % 400 == 0) else
                      28 if dt.month == 2 else dt.day)
            result = dt.replace(year=year, day=day)

        return {
            "status": "success",
            "original_date": date_str,
            "amount": amount,
            "unit": unit,
            "result_date": result.strftime("%Y-%m-%d"),
            "day_of_week": result.strftime("%A"),
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def get_business_days(
    start_date: str,
    end_date: str,
    exclude_holidays: bool = False,
    country_code: Optional[Literal["US", "UK", "DE", "FR", "JP"]] = None
) -> Dict[str, Any]:
    """
    Count the number of business days (weekdays) between two dates, optionally excluding public holidays.

    Args:
        start_date: The start date in YYYY-MM-DD format
        end_date: The end date in YYYY-MM-DD format
        exclude_holidays: Whether to exclude public holidays from the count
        country_code: Country code for public holidays (US, UK, DE, FR, JP). Required if exclude_holidays is True.
    """
    try:
        dt_start = _parse_date(start_date).date()
        dt_end = _parse_date(end_date).date()

        if exclude_holidays and not country_code:
            return {"status": "error", "error_message": "country_code is required when exclude_holidays is True"}

        holidays = set()
        if exclude_holidays and country_code:
            for year in range(dt_start.year, dt_end.year + 1):
                holidays.update(_get_holidays_for_year(year, country_code))

        business_days = 0
        holidays_excluded = 0
        current = dt_start
        while current <= dt_end:
            if current.weekday() < 5:  # Monday=0 to Friday=4
                if current in holidays:
                    holidays_excluded += 1
                else:
                    business_days += 1
            current += timedelta(days=1)

        total_days = (dt_end - dt_start).days + 1

        result = {
            "status": "success",
            "start_date": start_date,
            "end_date": end_date,
            "business_days": business_days,
            "total_calendar_days": total_days,
            "weekend_days": total_days - business_days - holidays_excluded,
        }
        if exclude_holidays:
            result["holidays_excluded"] = holidays_excluded
            result["country_code"] = country_code

        return result
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def get_day_of_week(
    date_str: str
) -> Dict[str, Any]:
    """
    Get the day of the week for a given date.

    Args:
        date_str: The date in YYYY-MM-DD format
    """
    try:
        dt = _parse_date(date_str)
        return {
            "status": "success",
            "date": date_str,
            "day_of_week": dt.strftime("%A"),
            "day_number": dt.isoweekday(),  # 1=Monday, 7=Sunday
            "iso_week_number": dt.isocalendar()[1],
            "day_of_year": dt.timetuple().tm_yday,
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def is_business_day(
    date_str: str,
    country_code: Optional[Literal["US", "UK", "DE", "FR", "JP"]] = None
) -> Dict[str, Any]:
    """
    Check if a given date is a business day (weekday and not a public holiday).

    Args:
        date_str: The date in YYYY-MM-DD format
        country_code: Optional country code to also check public holidays (US, UK, DE, FR, JP)
    """
    try:
        dt = _parse_date(date_str).date()
        is_weekday = dt.weekday() < 5
        is_holiday = False
        holiday_name = None

        if country_code:
            country_holidays = HOLIDAYS.get(country_code, {})
            date_md = dt.strftime("%m-%d")
            for name, md in country_holidays.items():
                if md == date_md:
                    is_holiday = True
                    holiday_name = name
                    break

        is_business = is_weekday and not is_holiday

        result = {
            "status": "success",
            "date": date_str,
            "day_of_week": dt.strftime("%A"),
            "is_weekday": is_weekday,
            "is_business_day": is_business,
        }
        if country_code:
            result["country_code"] = country_code
            result["is_public_holiday"] = is_holiday
            if holiday_name:
                result["holiday_name"] = holiday_name

        return result
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


@mcp.tool()
async def format_date(
    date_str: str,
    output_format: Literal["iso", "us", "eu", "long", "short"] = "iso"
) -> Dict[str, Any]:
    """
    Format a date string into various common formats.

    Args:
        date_str: The date in YYYY-MM-DD format
        output_format: The desired output format:
            - 'iso': 2024-03-15
            - 'us': 03/15/2024
            - 'eu': 15/03/2024
            - 'long': March 15, 2024
            - 'short': Mar 15, 2024
    """
    try:
        dt = _parse_date(date_str)

        format_map = {
            "iso": "%Y-%m-%d",
            "us": "%m/%d/%Y",
            "eu": "%d/%m/%Y",
            "long": "%B %d, %Y",
            "short": "%b %d, %Y",
        }

        formatted = dt.strftime(format_map[output_format])

        return {
            "status": "success",
            "original_date": date_str,
            "formatted_date": formatted,
            "format": output_format,
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


if __name__ == "__main__":
    mcp.run()
