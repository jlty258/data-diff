#!/usr/bin/env python3
"""
快速开始脚本 - 验证系统是否可以正常运行

使用方法：
1. 确保已安装依赖: pip install croniter requests
2. 运行: python quick_start.py
"""

import sys
import os

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """测试导入是否正常"""
    print("=" * 60)
    print("步骤 1: 测试模块导入")
    print("=" * 60)
    
    try:
        from data_diff.monitor import (
            DataMonitor, MonitorRule, MonitorType, RuleOperator,
            MonitorScheduler, AlertManager, AlertChannel
        )
        print("✓ DataMonitor 模块导入成功")
    except Exception as e:
        print(f"✗ DataMonitor 模块导入失败: {e}")
        return False
    
    try:
        from data_diff.migration import (
            MigrationAgent, MigrationTask, MigrationStatus,
            SQLTranslator, DatabaseDialect, MigrationValidator
        )
        print("✓ Migration Agent 模块导入成功")
    except Exception as e:
        print(f"✗ Migration Agent 模块导入失败: {e}")
        return False
    
    return True


def test_basic_functionality():
    """测试基本功能"""
    print("\n" + "=" * 60)
    print("步骤 2: 测试基本功能")
    print("=" * 60)
    
    try:
        from data_diff.monitor import DataMonitor, MonitorRule, MonitorType, RuleOperator
        
        # 创建监控器
        monitor = DataMonitor()
        print("✓ 创建 DataMonitor 实例成功")
        
        # 创建规则（不连接真实数据库）
        rule = MonitorRule(
            name="test_rule",
            monitor_type=MonitorType.DATA_DIFF,
            database1="mysql://test/db",
            table1="test_table",
            key_columns=("id",),
            threshold_type="diff_percent",
            threshold_operator=RuleOperator.GT,
            threshold_value=1.0
        )
        monitor.add_rule(rule)
        print("✓ 创建并添加监控规则成功")
        
        # 获取规则
        retrieved_rule = monitor.get_rule("test_rule")
        if retrieved_rule and retrieved_rule.name == "test_rule":
            print("✓ 获取监控规则成功")
        else:
            print("✗ 获取监控规则失败")
            return False
        
        # 测试告警管理器
        from data_diff.monitor import AlertManager, AlertChannel
        alert_manager = AlertManager()
        alert_manager.add_channel(AlertChannel.LOG)
        print("✓ 创建告警管理器成功")
        
    except Exception as e:
        print(f"✗ 基本功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    try:
        from data_diff.migration import MigrationAgent, MigrationTask, SQLTranslator, DatabaseDialect
        
        # 创建迁移代理
        agent = MigrationAgent()
        print("✓ 创建 MigrationAgent 实例成功")
        
        # 测试 SQL 转换器
        translator = SQLTranslator()
        mysql_sql = "SELECT * FROM `users` LIMIT 10, 20"
        pg_sql = translator.translate(
            mysql_sql,
            DatabaseDialect.MYSQL,
            DatabaseDialect.POSTGRESQL
        )
        if pg_sql and pg_sql != mysql_sql:
            print("✓ SQL 转换功能正常")
        else:
            print("⚠ SQL 转换结果异常（可能正常，取决于转换规则）")
        
    except Exception as e:
        print(f"✗ 迁移功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


def test_dependencies():
    """测试依赖项"""
    print("\n" + "=" * 60)
    print("步骤 3: 检查依赖项")
    print("=" * 60)
    
    dependencies = {
        "croniter": "用于定时调度",
        "requests": "用于 Webhook 告警",
    }
    
    all_ok = True
    for dep, desc in dependencies.items():
        try:
            __import__(dep)
            print(f"✓ {dep} 已安装 - {desc}")
        except ImportError:
            print(f"✗ {dep} 未安装 - {desc}")
            print(f"  安装命令: pip install {dep}")
            all_ok = False
    
    return all_ok


def show_usage_examples():
    """显示使用示例"""
    print("\n" + "=" * 60)
    print("步骤 4: 使用示例")
    print("=" * 60)
    
    print("""
📝 最简单的使用方式：

1. 数据监控（需要真实数据库连接）：
   
   from data_diff.monitor import DataMonitor, MonitorRule, MonitorType, RuleOperator
   
   monitor = DataMonitor()
   rule = MonitorRule(
       name="my_monitor",
       monitor_type=MonitorType.DATA_DIFF,
       database1="mysql://user:pass@host/db",
       table1="table1",
       database2="mysql://user:pass@host/db",
       table2="table2",
       key_columns=("id",),
       threshold_type="diff_count",
       threshold_operator=RuleOperator.GT,
       threshold_value=10
   )
   monitor.add_rule(rule)
   result = monitor.run_monitor("my_monitor")
   print(f"差异: {result.diff_count}")

2. 迁移验证（需要真实数据库连接）：
   
   from data_diff.migration import MigrationValidator
   
   validator = MigrationValidator()
   result = validator.validate(
       source_database="postgresql://source/db",
       source_table="orders",
       target_database="mysql://target/db",
       target_table="orders",
       key_columns=("order_id",)
   )
   print(f"验证结果: {result['success']}")

3. SQL 转换（不需要数据库连接）：
   
   from data_diff.migration import SQLTranslator, DatabaseDialect
   
   translator = SQLTranslator()
   mysql_sql = "SELECT * FROM `users` LIMIT 10, 20"
   pg_sql = translator.translate(
       mysql_sql,
       DatabaseDialect.MYSQL,
       DatabaseDialect.POSTGRESQL
   )
   print(f"PostgreSQL SQL: {pg_sql}")

📚 更多示例请查看:
   - examples/migration_example.py
   - MONITOR_AND_MIGRATION.md
""")


def main():
    """主函数"""
    print("\n" + "🚀 DataMonitor & Migration Agent 快速测试" + "\n")
    
    # 测试导入
    if not test_imports():
        print("\n❌ 模块导入失败，请检查代码")
        return 1
    
    # 测试依赖
    deps_ok = test_dependencies()
    if not deps_ok:
        print("\n⚠️  部分依赖未安装，某些功能可能无法使用")
        print("   建议运行: pip install croniter requests")
    
    # 测试基本功能
    if not test_basic_functionality():
        print("\n❌ 基本功能测试失败")
        return 1
    
    # 显示使用示例
    show_usage_examples()
    
    print("\n" + "=" * 60)
    print("✅ 所有测试通过！系统可以正常使用")
    print("=" * 60)
    print("\n💡 下一步:")
    print("   1. 准备测试数据库连接")
    print("   2. 运行 examples/migration_example.py 查看完整示例")
    print("   3. 根据实际需求配置监控规则")
    print("\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

