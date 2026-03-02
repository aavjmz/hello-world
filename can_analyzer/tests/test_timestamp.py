#!/usr/bin/env python3
"""
Test script for Timestamp Formatter
"""

import os
import sys
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.timestamp_formatter import (
    TimestampFormatter,
    TimestampFormat,
    TimestampConverter
)


def test_timestamp_formatter():
    """Test timestamp formatting functionality"""
    print("=" * 60)
    print("时间戳格式化器测试")
    print("=" * 60)
    print()

    # Test timestamp value
    test_timestamp = 123.456789

    print(f"测试时间戳: {test_timestamp} 秒")
    print()

    # Test different formats
    print("不同格式输出:")

    formats = [
        (TimestampFormat.RAW, "原始格式"),
        (TimestampFormat.SECONDS, "秒格式"),
        (TimestampFormat.MILLISECONDS, "毫秒格式"),
        (TimestampFormat.MICROSECONDS, "微秒格式"),
        (TimestampFormat.RELATIVE, "相对时间"),
    ]

    formatter = TimestampFormatter()

    for fmt, desc in formats:
        formatter.set_format(fmt)
        result = formatter.format(test_timestamp)
        print(f"  {desc:12s}: {result}")

    print()

    # Test time of day format
    print("绝对时间格式:")
    base_time = datetime(2021, 11, 1, 10, 30, 0)
    formatter.set_format(TimestampFormat.TIME_OF_DAY)
    formatter.set_base_datetime(base_time)
    result = formatter.format(test_timestamp)
    print(f"  基准时间: {base_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  偏移: {test_timestamp}s")
    print(f"  绝对时间: {result}")
    print()

    # Test relative time
    print("相对时间测试:")
    start_time = 100.0
    formatter.set_format(TimestampFormat.RELATIVE)
    formatter.set_start_time(start_time)

    test_times = [100.0, 150.5, 200.123]
    for t in test_times:
        result = formatter.format(t)
        print(f"  时间戳 {t}s -> {result}")
    print()

    # Test timestamp range formatting
    print("时间范围格式化:")
    formatter.set_format(TimestampFormat.MILLISECONDS)
    range_str = formatter.format_range(10.5, 25.8)
    print(f"  {range_str}")
    print()

    # Test timestamp parsing
    print("时间戳解析测试:")
    test_strings = [
        "123.456",
        "5000.000ms",
        "3s",
        "1500000us"
    ]

    for ts_str in test_strings:
        try:
            parsed = TimestampFormatter.parse_timestamp(ts_str)
            print(f"  '{ts_str}' -> {parsed:.6f}s")
        except ValueError as e:
            print(f"  '{ts_str}' -> 解析失败: {e}")
    print()

    # Test TimestampConverter
    print("时间戳转换器测试:")
    test_value = 1.234567

    conversions = [
        (TimestampConverter.to_milliseconds(test_value), "秒转毫秒"),
        (TimestampConverter.to_microseconds(test_value), "秒转微秒"),
        (TimestampConverter.from_milliseconds(1234.567), "毫秒转秒"),
        (TimestampConverter.from_microseconds(1234567), "微秒转秒"),
    ]

    for value, desc in conversions:
        print(f"  {desc}: {value:.6f}")
    print()

    # Test duration formatting
    print("持续时间格式化:")
    durations = [0.123, 5.678, 90.5, 3725.123]

    for duration in durations:
        formatted = TimestampConverter.format_duration(duration)
        print(f"  {duration}s -> {formatted}")
    print()

    # Validation tests
    print("验证测试:")
    checks = []

    # Test millisecond conversion
    formatter.set_format(TimestampFormat.MILLISECONDS)
    result = formatter.format(1.234)
    expected = "1234.000ms"
    checks.append((result == expected, f"毫秒格式: {result} == {expected}"))

    # Test seconds conversion
    formatter.set_format(TimestampFormat.SECONDS)
    result = formatter.format(5.678)
    expected = "5s"
    checks.append((result == expected, f"秒格式: {result} == {expected}"))

    # Test raw format precision
    formatter.set_format(TimestampFormat.RAW)
    result = formatter.format(123.456789)
    expected = "123.456789"
    checks.append((result == expected, f"原始格式: {result} == {expected}"))

    all_pass = True
    for passed, desc in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {desc}")
        all_pass = all_pass and passed

    print()

    # Summary
    print("=" * 60)
    if all_pass:
        print("✓ 时间戳格式化器测试通过!")
    else:
        print("✗ 时间戳格式化器测试失败!")
    print("=" * 60)
    print()

    return all_pass


if __name__ == "__main__":
    success = test_timestamp_formatter()
    sys.exit(0 if success else 1)
