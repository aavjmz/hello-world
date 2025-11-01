#!/usr/bin/env python3
"""
Test script for ASC Parser
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.asc_parser import ASCParser, CANMessage


def test_asc_parser():
    """Test ASC parser functionality"""
    print("=" * 60)
    print("ASC Parser 测试")
    print("=" * 60)
    print()

    # Get test file path
    test_file = os.path.join(
        os.path.dirname(__file__),
        'test_data.asc'
    )

    # Check if test file exists
    if not os.path.exists(test_file):
        print(f"✗ 测试文件不存在: {test_file}")
        return False

    print(f"✓ 测试文件: {test_file}")
    print()

    # Create parser
    parser = ASCParser()
    print("✓ 创建ASCParser实例")
    print()

    # Parse file
    try:
        messages = parser.parse_file(test_file)
        print(f"✓ 文件解析成功")
        print(f"  解析到 {len(messages)} 条CAN报文")
        print()
    except Exception as e:
        print(f"✗ 文件解析失败: {e}")
        return False

    # Display statistics
    stats = parser.get_statistics()
    print("统计信息:")
    print(f"  总报文数: {stats['total_messages']}")
    print(f"  时间范围: {stats['time_range'][0]:.6f}s - {stats['time_range'][1]:.6f}s")
    print(f"  持续时间: {stats['duration']:.6f}s")
    print(f"  唯一ID数: {stats['unique_ids']}")
    print(f"  接收报文: {stats['rx_count']}")
    print(f"  发送报文: {stats['tx_count']}")
    print()

    # Display unique CAN IDs
    unique_ids = parser.get_unique_can_ids()
    print("唯一CAN ID列表:")
    for can_id in unique_ids:
        print(f"  - 0x{can_id:03X} ({can_id})")
    print()

    # Display first 5 messages
    print("前5条报文详情:")
    for i, msg in enumerate(messages[:5]):
        print(f"  [{i+1}] {msg}")
    print()

    # Test filtering by CAN ID
    test_id = 0x123
    filtered = parser.filter_by_can_id(test_id)
    print(f"CAN ID 0x{test_id:03X} 的报文:")
    print(f"  共 {len(filtered)} 条")
    for i, msg in enumerate(filtered[:3]):
        print(f"  [{i+1}] t={msg.timestamp:.6f}s, Data=[{msg.to_dict()['data_hex']}]")
    print()

    # Verify specific message parsing
    print("报文解析验证:")
    if len(messages) > 0:
        msg = messages[0]
        print(f"  第1条报文:")
        print(f"    时间戳: {msg.timestamp:.6f}s")
        print(f"    CAN ID: 0x{msg.can_id:03X}")
        print(f"    方向: {msg.direction}")
        print(f"    DLC: {msg.dlc}")
        print(f"    数据: {msg.to_dict()['data_hex']}")

        # Expected values for first message
        expected = {
            'timestamp': 0.010000,
            'can_id': 0x123,
            'direction': 'Rx',
            'dlc': 8,
            'data_hex': '00 01 02 03 04 05 06 07'
        }

        checks = [
            (abs(msg.timestamp - expected['timestamp']) < 0.000001, '时间戳'),
            (msg.can_id == expected['can_id'], 'CAN ID'),
            (msg.direction == expected['direction'], '方向'),
            (msg.dlc == expected['dlc'], 'DLC'),
            (msg.to_dict()['data_hex'] == expected['data_hex'], '数据')
        ]

        print()
        print("  验证结果:")
        all_pass = True
        for passed, name in checks:
            status = "✓" if passed else "✗"
            print(f"    {status} {name}")
            all_pass = all_pass and passed

        print()

    # Summary
    print("=" * 60)
    if all_pass:
        print("✓ ASC Parser 测试通过!")
    else:
        print("✗ ASC Parser 测试失败!")
    print("=" * 60)
    print()

    return all_pass


if __name__ == "__main__":
    success = test_asc_parser()
    sys.exit(0 if success else 1)
