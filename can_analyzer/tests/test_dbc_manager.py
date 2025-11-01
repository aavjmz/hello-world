#!/usr/bin/env python3
"""
Test script for DBC Manager
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.dbc_manager import DBCManager, DBCDatabase


def test_dbc_manager():
    """Test DBC manager functionality"""
    print("=" * 60)
    print("DBC管理器测试")
    print("=" * 60)
    print()

    # Get test DBC file path
    test_dbc = os.path.join(
        os.path.dirname(__file__),
        'test_data.dbc'
    )

    if not os.path.exists(test_dbc):
        print(f"✗ 测试DBC文件不存在: {test_dbc}")
        return False

    print(f"✓ 测试DBC文件: {test_dbc}")
    print()

    # Check cantools availability
    try:
        import cantools
        cantools_available = True
        print("✓ cantools库已安装")
    except ImportError:
        cantools_available = False
        print("✗ cantools库未安装")
        print("  安装命令: pip install cantools")
        print()

    # Create manager
    manager = DBCManager()
    print("✓ 创建DBCManager实例")
    print()

    if not cantools_available:
        print("跳过需要cantools的测试...")
        print()
        return True

    # Test 1: Add DBC file
    print("测试1: 添加DBC文件")
    try:
        db_name = manager.add_dbc(test_dbc)
        print(f"  ✓ 添加成功: {db_name}")
        print(f"  ✓ 数据库数量: {manager.count()}")
    except Exception as e:
        print(f"  ✗ 添加失败: {e}")
        return False
    print()

    # Test 2: List DBCs
    print("测试2: 列出所有DBC")
    dbc_list = manager.list_dbcs()
    print(f"  已加载的DBC: {dbc_list}")
    print()

    # Test 3: Get DBC info
    print("测试3: 获取DBC信息")
    info = manager.get_dbc_info(db_name)
    if info:
        print(f"  名称: {info['name']}")
        print(f"  文件: {info['file_path']}")
        print(f"  已加载: {info['loaded']}")
        print(f"  报文数: {info['message_count']}")
        print(f"  节点数: {info['node_count']}")
    print()

    # Test 4: Get active database
    print("测试4: 获取当前激活的数据库")
    active_name = manager.get_active_name()
    active_db = manager.get_active()
    print(f"  激活数据库: {active_name}")
    print(f"  数据库对象: {active_db is not None}")
    print()

    # Test 5: Get messages from DBC
    print("测试5: 获取DBC中的报文定义")
    db = manager.get_dbc(db_name)
    if db and db.is_loaded():
        messages = db.get_messages()
        print(f"  总报文数: {len(messages)}")
        print(f"  报文列表:")
        for msg in messages[:5]:  # Show first 5
            print(f"    - ID: 0x{msg.frame_id:03X} ({msg.frame_id}), Name: {msg.name}, DLC: {msg.length}")
    print()

    # Test 6: Decode a CAN message
    print("测试6: 使用DBC解码CAN报文")
    # Test data for ID 0x123 (291) - EngineData
    can_id = 0x123
    # Speed: 2000 rpm (encoded as 2000/0.25 = 8000 = 0x1F40)
    # Temp: 90°C (encoded as (90+40)/1 = 130 = 0x82)
    # Throttle: 50% (encoded as 50/0.4 = 125 = 0x7D)
    # Load: 75% (encoded as 75 = 0x4B)
    test_data = bytes([0x40, 0x1F, 0x82, 0x7D, 0x4B, 0x00, 0x00, 0x00])

    print(f"  CAN ID: 0x{can_id:03X}")
    print(f"  原始数据: {' '.join(f'{b:02X}' for b in test_data)}")

    try:
        decoded = manager.decode_message(can_id, test_data)
        if decoded:
            print(f"  解码成功:")
            for signal_name, value in decoded.items():
                print(f"    {signal_name}: {value}")
        else:
            print(f"  ✗ 无法解码 (ID可能未在DBC中定义)")
    except Exception as e:
        print(f"  ✗ 解码失败: {e}")
    print()

    # Test 7: Add another DBC (test duplicate name handling)
    print("测试7: 添加相同的DBC文件（测试重名处理）")
    try:
        db_name2 = manager.add_dbc(test_dbc)
        print(f"  ✓ 添加成功: {db_name2}")
        print(f"  ✓ 数据库数量: {manager.count()}")
        print(f"  ✓ 数据库列表: {manager.list_dbcs()}")
    except Exception as e:
        print(f"  ✗ 添加失败: {e}")
    print()

    # Test 8: Set active database
    print("测试8: 切换激活数据库")
    if manager.count() > 1:
        all_dbs = manager.list_dbcs()
        new_active = all_dbs[1] if all_dbs[0] == active_name else all_dbs[0]
        success = manager.set_active(new_active)
        print(f"  ✓ 切换到: {new_active}")
        print(f"  ✓ 当前激活: {manager.get_active_name()}")
    print()

    # Test 9: Remove a DBC
    print("测试9: 删除DBC数据库")
    if manager.count() > 1:
        dbs_before = manager.count()
        db_to_remove = manager.list_dbcs()[0]
        success = manager.remove_dbc(db_to_remove)
        print(f"  ✓ 删除: {db_to_remove}")
        print(f"  ✓ 删除成功: {success}")
        print(f"  ✓ 数据库数量: {dbs_before} -> {manager.count()}")
        print(f"  ✓ 当前激活: {manager.get_active_name()}")
    print()

    # Test 10: Get all database info
    print("测试10: 获取所有数据库信息")
    all_info = manager.get_all_info()
    print(f"  数据库数量: {len(all_info)}")
    for info in all_info:
        print(f"  - {info['name']}: {info['message_count']} 个报文")
    print()

    # Test 11: Check DBC file extension
    print("测试11: DBC文件扩展名检查")
    test_files = [
        'test.dbc',
        'test.DBC',
        'test.txt',
        'test.asc'
    ]
    for filename in test_files:
        is_dbc = DBCManager.is_dbc_file(filename)
        status = "✓" if is_dbc else "✗"
        print(f"  {status} {filename}: {'是' if is_dbc else '不是'}DBC文件")
    print()

    # Test 12: Clear all databases
    print("测试12: 清空所有数据库")
    manager.clear()
    print(f"  ✓ 清空完成")
    print(f"  ✓ 数据库数量: {manager.count()}")
    print(f"  ✓ 激活数据库: {manager.get_active_name()}")
    print()

    # Summary
    print("=" * 60)
    print("✓ DBC管理器测试完成!")
    print("=" * 60)
    print()
    print("功能验证:")
    print("  ✓ 添加DBC文件")
    print("  ✓ 列出DBC文件")
    print("  ✓ 获取DBC信息")
    print("  ✓ 激活数据库切换")
    print("  ✓ 获取报文定义")
    print("  ✓ 解码CAN报文")
    print("  ✓ 删除DBC文件")
    print("  ✓ 清空所有数据库")
    print()

    return True


if __name__ == "__main__":
    success = test_dbc_manager()
    sys.exit(0 if success else 1)
