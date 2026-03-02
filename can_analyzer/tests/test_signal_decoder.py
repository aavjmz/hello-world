#!/usr/bin/env python3
"""
Test script for Signal Decoder
"""

import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parsers.asc_parser import CANMessage
from utils.dbc_manager import DBCManager
from utils.signal_decoder import SignalDecoder, SignalValue, DecodedMessage


def test_signal_decoder():
    """Test signal decoder functionality"""
    print("=" * 60)
    print("信号解析器测试")
    print("=" * 60)
    print()

    # Check cantools availability
    try:
        import cantools
        cantools_available = True
        print("✓ cantools库已安装")
    except ImportError:
        cantools_available = False
        print("✗ cantools库未安装，跳过DBC相关测试")
        print()
        return True

    # Get test DBC file
    test_dbc = os.path.join(
        os.path.dirname(__file__),
        'test_data.dbc'
    )

    if not os.path.exists(test_dbc):
        print(f"✗ 测试DBC文件不存在: {test_dbc}")
        return False

    print(f"✓ 测试DBC文件: {os.path.basename(test_dbc)}")
    print()

    # Create DBC manager and load DBC
    print("初始化DBC管理器:")
    dbc_manager = DBCManager()
    db_name = dbc_manager.add_dbc(test_dbc, load=True)
    print(f"  ✓ 加载DBC: {db_name}")
    print()

    # Create signal decoder
    decoder = SignalDecoder(dbc_manager)
    print("✓ 创建SignalDecoder实例")
    print()

    # Test 1: Create test messages
    print("测试1: 创建测试报文")
    # EngineData (0x123):
    # EngineSpeed: 2000 rpm (encoded as 2000/0.25 = 8000 = 0x1F40)
    # EngineTemp: 90°C (encoded as (90+40)/1 = 130 = 0x82)
    # ThrottlePos: 50% (encoded as 50/0.4 = 125 = 0x7D)
    # EngineLoad: 75% (encoded as 75 = 0x4B)
    engine_msg = CANMessage(
        timestamp=0.010,
        can_id=0x123,
        direction='Rx',
        data=bytes([0x40, 0x1F, 0x82, 0x7D, 0x4B, 0x00, 0x00, 0x00]),
        channel=1
    )

    # VehicleSpeed (0x200):
    # Speed: 100 km/h (encoded as 100/0.01 = 10000 = 0x2710)
    vehicle_msg = CANMessage(
        timestamp=0.020,
        can_id=0x200,
        direction='Rx',
        data=bytes([0x10, 0x27]),
        channel=1
    )

    print(f"  创建报文: 0x{engine_msg.can_id:03X} (EngineData)")
    print(f"  创建报文: 0x{vehicle_msg.can_id:03X} (VehicleSpeed)")
    print()

    # Test 2: Decode messages
    print("测试2: 解码CAN报文")
    decoded_engine = decoder.decode_message(engine_msg)
    decoded_vehicle = decoder.decode_message(vehicle_msg)

    if decoded_engine:
        print(f"  ✓ EngineData 解码成功:")
        print(f"    报文名称: {decoded_engine.message_name}")
        print(f"    信号数量: {decoded_engine.get_signal_count()}")
        for signal in decoded_engine.signals.values():
            print(f"    - {signal.format_full()}")
    else:
        print(f"  ✗ EngineData 解码失败")

    print()

    if decoded_vehicle:
        print(f"  ✓ VehicleSpeed 解码成功:")
        print(f"    报文名称: {decoded_vehicle.message_name}")
        print(f"    信号数量: {decoded_vehicle.get_signal_count()}")
        for signal in decoded_vehicle.signals.values():
            print(f"    - {signal.format_full()}")
    else:
        print(f"  ✗ VehicleSpeed 解码失败")

    print()

    # Test 3: Signal summary
    print("测试3: 获取信号摘要")
    if decoded_engine:
        summary = decoder.get_signal_summary(decoded_engine, max_signals=2)
        print(f"  摘要 (最多2个信号): {summary}")

        full_summary = decoder.get_signal_summary(decoded_engine, max_signals=10)
        print(f"  完整摘要: {full_summary}")
    print()

    # Test 4: Get all signals as text
    print("测试4: 获取所有信号文本")
    if decoded_engine:
        text = decoder.get_all_signals_text(decoded_engine)
        print(text)
    print()

    # Test 5: Get signal names
    print("测试5: 获取信号名称列表")
    signal_names = decoder.get_signal_names(0x123)
    print(f"  CAN ID 0x123 的信号:")
    for name in signal_names:
        print(f"    - {name}")
    print()

    # Test 6: Check if can decode
    print("测试6: 检查是否可以解码")
    test_ids = [0x123, 0x200, 0x456, 0x999]
    for can_id in test_ids:
        can_decode = decoder.can_decode(can_id)
        status = "✓" if can_decode else "✗"
        print(f"  {status} CAN ID 0x{can_id:03X}: {'可解码' if can_decode else '不可解码'}")
    print()

    # Test 7: Decode multiple messages
    print("测试7: 批量解码多条报文")
    messages = [engine_msg, vehicle_msg]
    decoded_list = decoder.decode_messages(messages)

    decoded_count = sum(1 for d in decoded_list if d is not None)
    print(f"  总报文数: {len(messages)}")
    print(f"  成功解码: {decoded_count}")
    print(f"  解码率: {decoded_count/len(messages)*100:.1f}%")
    print()

    # Test 8: Signal value formatting
    print("测试8: 信号值格式化")
    if decoded_engine:
        engine_speed = decoded_engine.get_signal('EngineSpeed')
        if engine_speed:
            print(f"  信号对象: {engine_speed}")
            print(f"  短格式: {engine_speed.format_short()}")
            print(f"  完整格式: {engine_speed.format_full()}")
            print(f"  字典格式: {engine_speed.to_dict()}")
    print()

    # Test 9: Decoded message to dict
    print("测试9: 解码报文转字典")
    if decoded_engine:
        msg_dict = decoded_engine.to_dict()
        print(f"  字典格式:")
        print(f"    CAN ID: 0x{msg_dict['can_id']:03X}")
        print(f"    报文名: {msg_dict['message_name']}")
        print(f"    信号数: {msg_dict['signal_count']}")
        print(f"    信号列表: {list(msg_dict['signals'].keys())}")
    print()

    # Validation tests
    print("验证测试:")
    checks = []

    # Check 1: EngineSpeed value
    if decoded_engine:
        engine_speed = decoded_engine.get_signal('EngineSpeed')
        checks.append((
            engine_speed and engine_speed.value == 2000,
            f"EngineSpeed = 2000 rpm (实际: {engine_speed.value if engine_speed else 'N/A'})"
        ))

        # Check 2: EngineTemp value
        engine_temp = decoded_engine.get_signal('EngineTemp')
        checks.append((
            engine_temp and engine_temp.value == 90,
            f"EngineTemp = 90 degC (实际: {engine_temp.value if engine_temp else 'N/A'})"
        ))

        # Check 3: Unit is present
        checks.append((
            engine_speed and engine_speed.unit == 'rpm',
            f"EngineSpeed单位 = 'rpm' (实际: '{engine_speed.unit if engine_speed else 'N/A'}')"
        ))

    # Check 4: VehicleSpeed value
    if decoded_vehicle:
        speed = decoded_vehicle.get_signal('Speed')
        checks.append((
            speed and speed.value == 100,
            f"VehicleSpeed = 100 km/h (实际: {speed.value if speed else 'N/A'})"
        ))

    all_pass = True
    for passed, desc in checks:
        status = "✓" if passed else "✗"
        print(f"  {status} {desc}")
        all_pass = all_pass and passed

    print()

    # Summary
    print("=" * 60)
    if all_pass:
        print("✓ 信号解析器测试通过!")
    else:
        print("✗ 信号解析器测试失败!")
    print("=" * 60)
    print()

    return all_pass


if __name__ == "__main__":
    success = test_signal_decoder()
    sys.exit(0 if success else 1)
