"""
Input Validation for Saju Birth DateTime

Validates:
- Date ranges (year, month, day)
- Time ranges (hour, minute, second)
- Invalid times (24:00, 12:60, etc.)
- Leap year February 29
- Month day counts
- Out-of-range dates for data coverage

Prevents:
- Crashes from invalid input
- Silent calculation errors
- User confusion from bad data
"""

import calendar
from datetime import datetime
from typing import Dict, Optional, Tuple


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


class BirthDateTimeValidator:
    """Validate birth date and time inputs for saju calculation."""

    # Data coverage range (based on canonical_v1)
    MIN_YEAR = 1900
    MAX_YEAR = 2050

    @staticmethod
    def validate_year(year: int) -> Tuple[bool, Optional[str]]:
        """
        Validate year.

        Returns:
            (is_valid, error_message)
        """
        if not isinstance(year, int):
            return False, f"Year must be an integer, got {type(year).__name__}"

        if year < BirthDateTimeValidator.MIN_YEAR:
            return (
                False,
                f"Year {year} is before data coverage (minimum: {BirthDateTimeValidator.MIN_YEAR})",
            )

        if year > BirthDateTimeValidator.MAX_YEAR:
            return (
                False,
                f"Year {year} is beyond data coverage (maximum: {BirthDateTimeValidator.MAX_YEAR})",
            )

        return True, None

    @staticmethod
    def validate_month(month: int) -> Tuple[bool, Optional[str]]:
        """
        Validate month (1-12).

        Returns:
            (is_valid, error_message)
        """
        if not isinstance(month, int):
            return False, f"Month must be an integer, got {type(month).__name__}"

        if month < 1 or month > 12:
            return False, f"Month must be 1-12, got {month}"

        return True, None

    @staticmethod
    def validate_day(year: int, month: int, day: int) -> Tuple[bool, Optional[str]]:
        """
        Validate day for given year and month.

        Handles:
        - Month day counts (30/31 days)
        - Leap year February 29
        - Invalid day 0 or negative

        Returns:
            (is_valid, error_message)
        """
        if not isinstance(day, int):
            return False, f"Day must be an integer, got {type(day).__name__}"

        if day < 1:
            return False, f"Day must be >= 1, got {day}"

        # Get max days in month
        max_day = calendar.monthrange(year, month)[1]

        if day > max_day:
            month_name = calendar.month_name[month]
            if month == 2 and day == 29:
                return False, f"{year} is not a leap year, February only has 28 days"
            return False, f"{month_name} {year} only has {max_day} days, got day {day}"

        return True, None

    @staticmethod
    def validate_hour(hour: int, allow_24: bool = False) -> Tuple[bool, Optional[str]]:
        """
        Validate hour (0-23, optionally 24).

        Args:
            hour: Hour value
            allow_24: If True, allow 24:00 (converts to next day 00:00)

        Returns:
            (is_valid, error_message)
        """
        if not isinstance(hour, int):
            return False, f"Hour must be an integer, got {type(hour).__name__}"

        max_hour = 24 if allow_24 else 23

        if hour < 0 or hour > max_hour:
            return False, f"Hour must be 0-{max_hour}, got {hour}"

        if hour == 24 and allow_24:
            # Valid but should be converted to next day 00:00
            return True, None

        return True, None

    @staticmethod
    def validate_minute(minute: int) -> Tuple[bool, Optional[str]]:
        """
        Validate minute (0-59).

        Returns:
            (is_valid, error_message)
        """
        if not isinstance(minute, int):
            return False, f"Minute must be an integer, got {type(minute).__name__}"

        if minute < 0 or minute > 59:
            return False, f"Minute must be 0-59, got {minute}"

        return True, None

    @staticmethod
    def validate_second(second: int) -> Tuple[bool, Optional[str]]:
        """
        Validate second (0-59, or 60 for leap second).

        Returns:
            (is_valid, error_message)
        """
        if not isinstance(second, int):
            return False, f"Second must be an integer, got {type(second).__name__}"

        if second < 0 or second > 60:
            return False, f"Second must be 0-59 (or 60 for leap second), got {second}"

        if second == 60:
            # Leap second - rare but valid
            return True, None

        return True, None

    @staticmethod
    def validate_datetime(
        year: int,
        month: int,
        day: int,
        hour: int,
        minute: int,
        second: int = 0,
        allow_24_hour: bool = False,
    ) -> Tuple[bool, Optional[str], Optional[datetime]]:
        """
        Validate complete datetime.

        Args:
            year: Year (1900-2050)
            month: Month (1-12)
            day: Day (1-31, depending on month)
            hour: Hour (0-23, or 0-24 if allow_24_hour)
            minute: Minute (0-59)
            second: Second (0-59)
            allow_24_hour: If True, convert 24:00 to next day 00:00

        Returns:
            (is_valid, error_message, corrected_datetime)
        """
        # Validate year
        valid, error = BirthDateTimeValidator.validate_year(year)
        if not valid:
            return False, error, None

        # Validate month
        valid, error = BirthDateTimeValidator.validate_month(month)
        if not valid:
            return False, error, None

        # Validate day
        valid, error = BirthDateTimeValidator.validate_day(year, month, day)
        if not valid:
            return False, error, None

        # Validate hour
        valid, error = BirthDateTimeValidator.validate_hour(hour, allow_24_hour)
        if not valid:
            return False, error, None

        # Validate minute
        valid, error = BirthDateTimeValidator.validate_minute(minute)
        if not valid:
            return False, error, None

        # Validate second
        valid, error = BirthDateTimeValidator.validate_second(second)
        if not valid:
            return False, error, None

        # Handle 24:00 conversion
        if hour == 24:
            if minute != 0 or second != 0:
                return (
                    False,
                    "24:00 must have minute=0 and second=0 (use 24:00:00 for next day midnight)",
                    None,
                )

            # Convert 24:00 to next day 00:00
            try:
                dt = datetime(year, month, day, 0, 0, 0)
                from datetime import timedelta

                dt = dt + timedelta(days=1)
                return True, None, dt
            except ValueError as e:
                return False, f"Failed to convert 24:00 to next day: {e}", None

        # Handle leap second (60)
        if second == 60:
            # Convert to next minute 00:00
            try:
                dt = datetime(year, month, day, hour, minute, 0)
                from datetime import timedelta

                dt = dt + timedelta(minutes=1)
                return True, None, dt
            except ValueError as e:
                return False, f"Failed to handle leap second: {e}", None

        # Create datetime
        try:
            dt = datetime(year, month, day, hour, minute, second)
            return True, None, dt
        except ValueError as e:
            return False, f"Invalid datetime: {e}", None

    @staticmethod
    def validate_datetime_object(dt: datetime) -> Tuple[bool, Optional[str]]:
        """
        Validate datetime object.

        Returns:
            (is_valid, error_message)
        """
        if not isinstance(dt, datetime):
            return False, f"Expected datetime object, got {type(dt).__name__}"

        # Check year range
        valid, error = BirthDateTimeValidator.validate_year(dt.year)
        if not valid:
            return False, error

        return True, None


def validate_birth_input(
    year: int, month: int, day: int, hour: int, minute: int, second: int = 0, strict: bool = True
) -> Dict:
    """
    Validate birth input and return result.

    Args:
        year: Year (1900-2050)
        month: Month (1-12)
        day: Day (1-31)
        hour: Hour (0-23, or 24 if not strict)
        minute: Minute (0-59)
        second: Second (0-59)
        strict: If False, auto-correct 24:00 to next day

    Returns:
        {
            'valid': bool,
            'error': Optional[str],
            'datetime': Optional[datetime],
            'corrected': bool,
            'correction_note': Optional[str]
        }
    """
    validator = BirthDateTimeValidator()

    valid, error, corrected_dt = validator.validate_datetime(
        year, month, day, hour, minute, second, allow_24_hour=(not strict)
    )

    result = {
        "valid": valid,
        "error": error,
        "datetime": corrected_dt,
        "corrected": False,
        "correction_note": None,
    }

    # Check if correction was applied
    if valid and corrected_dt:
        original_would_be = (year, month, day, hour, minute, second)
        actual_is = (
            corrected_dt.year,
            corrected_dt.month,
            corrected_dt.day,
            corrected_dt.hour,
            corrected_dt.minute,
            corrected_dt.second,
        )

        if original_would_be != actual_is:
            result["corrected"] = True
            if hour == 24:
                result["correction_note"] = (
                    f"24:00 converted to next day {corrected_dt.strftime('%Y-%m-%d 00:00:00')}"
                )
            elif second == 60:
                result["correction_note"] = (
                    f"Leap second (:60) converted to {corrected_dt.strftime('%H:%M:00')}"
                )

    return result


# Convenience function for quick validation
def is_valid_birth_datetime(year: int, month: int, day: int, hour: int, minute: int) -> bool:
    """Quick boolean check if datetime is valid."""
    result = validate_birth_input(year, month, day, hour, minute, strict=True)
    return result["valid"]
