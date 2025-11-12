#!/usr/bin/env python3
"""
测试 SQL 转换功能（不需要数据库连接）

这是最快验证系统是否工作的方式
"""

from data_diff.migration import SQLTranslator, DatabaseDialect

def test_sql_translation():
    """测试 SQL 转换"""
    print("=" * 60)
    print("SQL 转换功能测试（不需要数据库连接）")
    print("=" * 60)
    
    translator = SQLTranslator()
    
    # 测试用例
    test_cases = [
        {
            "name": "MySQL LIMIT 语法",
            "sql": "SELECT * FROM `users` LIMIT 10, 20",
            "from": DatabaseDialect.MYSQL,
            "to": DatabaseDialect.POSTGRESQL
        },
        {
            "name": "MySQL 反引号",
            "sql": "SELECT `id`, `name` FROM `users`",
            "from": DatabaseDialect.MYSQL,
            "to": DatabaseDialect.POSTGRESQL
        },
        {
            "name": "MySQL AUTO_INCREMENT",
            "sql": "CREATE TABLE test (id INT AUTO_INCREMENT PRIMARY KEY)",
            "from": DatabaseDialect.MYSQL,
            "to": DatabaseDialect.POSTGRESQL
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {test['name']}")
        print(f"原始 SQL ({test['from'].value}):")
        print(f"  {test['sql']}")
        
        try:
            translated = translator.translate(
                test['sql'],
                test['from'],
                test['to']
            )
            print(f"转换后 SQL ({test['to'].value}):")
            print(f"  {translated}")
            print("✓ 转换成功")
        except Exception as e:
            print(f"✗ 转换失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ SQL 转换功能测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_sql_translation()

