#!/usr/bin/env python3
"""
Test script for Unified Message Parser
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.message_parser import MessageParser
from parsers.blf_parser import BLFParser


def test_message_parser():
    """Test unified message parser"""
    print("=" * 60)
    print("统一报文解析器测试")
    print("=" * 60)
    print()

    # Test supported formats
    print("支持的文件格式:")
    formats = MessageParser.get_supported_formats()
    for ext, fmt in formats.items():
        print(f"  {ext} -> {fmt}")
    print()

    # Create parser
    parser = MessageParser()
    print("✓ 创建MessageParser实例")
    print()

    # Test ASC file parsing
    test_asc_file = os.path.join(
        os.path.dirname(__file__),
        'test_data.asc'
    )

    if os.path.exists(test_asc_file):
        print(f"测试ASC文件解析:")
        print(f"  文件: {os.path.basename(test_asc_file)}")

        try:
            messages = parser.parse_file(test_asc_file)
            detected_format = parser.get_format()
            print(f"  ✓ 检测到格式: {detected_format}")
            print(f"  ✓ 解析成功: {len(messages)} 条报文")

            # Get statistics
            stats = parser.get_parser().get_statistics()
            print(f"  统计信息:")
            print(f"    - 总报文数: {stats['total_messages']}")
            print(f"    - 持续时间: {stats['duration']:.6f}s")
            print(f"    - 唯一ID数: {stats['unique_ids']}")
            print()

        except Exception as e:
            print(f"  ✗ 解析失败: {e}")
            print()

    # Test format detection
    print("文件格式检测测试:")
    test_files = [
        'test.asc',
        'test.blf',
        'test.log',
        'test.txt'
    ]

    for filename in test_files:
        is_supported = MessageParser.is_format_supported(filename)
        status = "✓" if is_supported else "✗"
        print(f"  {status} {filename}: {'支持' if is_supported else '不支持'}")
    print()

    # Test BLF parser availability
    print("BLF解析器检查:")
    blf_available = BLFParser.is_available()
    if blf_available:
        print("  ✓ python-can库已安装，BLF解析可用")
    else:
        print("  ✗ python-can库未安装，BLF解析不可用")
        print("    安装命令: pip install python-can")
    print()

    # Summary
    print("=" * 60)
    print("✓ 统一报文解析器测试完成!")
    print("=" * 60)
    print()
    print("功能特性:")
    print("  ✓ 自动检测文件格式")
    print("  ✓ 支持ASC格式")
    print(f"  {'✓' if blf_available else '✗'} 支持BLF格式")
    print("  ✓ 统一的解析接口")
    print()


if __name__ == "__main__":
    test_message_parser()
