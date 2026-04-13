# Python Review Checklist

## Code Consistency

- [ ] **命名规范**:
  - 模块名: 小写，可用下划线
  - 类名: PascalCase
  - 函数/变量: snake_case
  - 常量: UPPER_SNAKE_CASE
  - 私有成员: _leading_underscore
- [ ] **函数长度**: 不超过50行
- [ ] **参数数量**: 不超过5个，使用dataclass或**kwargs
- [ ] **魔法数字**: 使用具名常量
- [ ] **类型注解**: 使用类型注解提高可读性

## Style Consistency (PEP 8)

- [ ] **缩进**: 使用4个空格
- [ ] **行长度**: 不超过88字符（Black默认）或79字符（PEP 8）
- [ ] **空行**: 函数/类定义间2个空行，方法间1个空行
- [ ] **导入**: 标准库、第三方、本地分组，按字母排序
- [ ] **空格**: 运算符前后、逗号后有空格
- [ ] **字符串引号**: 统一使用单引号或双引号

## Code Duplication

- [ ] **DRY原则**: 相同逻辑提取为函数或类
- [ ] **继承**: 合理使用继承，避免过度继承
- [ ] **Mixins**: 共享功能使用Mixin模式
- [ ] **工具函数**: 通用逻辑放入utils模块

## Security

- [ ] **SQL注入**: 使用参数化查询，禁止字符串拼接
- [ ] **命令注入**: 避免shell=True，使用列表传参
- [ ] **路径遍历**: 文件操作前验证路径
- [ ] **反序列化**: 不信任数据不使用pickle.load
- [ ] **敏感信息**: 使用环境变量或密钥管理工具
- [ ] **依赖安全**: 检查requirements.txt中的漏洞
- [ ] ** eval/exec**: 避免使用eval()和exec()
- [ ] **XML解析**: 使用defusedxml防御XXE

## Logic & Error Handling

- [ ] **异常类型**: 捕获具体异常，不捕获裸Exception
- [ ] **异常链**: 使用raise ... from ...保留异常链
- [ ] **空值检查**: 使用is None而非== None
- [ ] **EAFP原则**: 合理使用try/except而非if检查
- [ ] **上下文管理器**: 使用with语句管理资源
- [ ] **迭代器**: 优先使用生成器处理大数据
- [ ] **默认值**: 避免可变默认参数（list, dict）

## Performance

- [ ] **列表推导**: 简单循环使用列表/字典/集合推导
- [ ] **生成器**: 大数据使用生成器表达式
- [ ] **字符串拼接**: 大量使用+时改用join()
- [ ] **循环优化**: 避免循环中的重复计算
- [ ] **字典查找**: 合理使用dict.get()和setdefault()

## Testing

- [ ] **pytest**: 使用pytest框架
- [ ] **测试命名**: 函数名以test_开头，描述行为
- [ ] **fixture**: 使用pytest.fixture复用测试数据
- [ ] **mock**: 使用unittest.mock模拟依赖
- [ ] **参数化**: 使用pytest.mark.parametrize
- [ ] **覆盖率**: 核心业务覆盖率达到80%

## Documentation

- [ ] **Docstrings**: 模块、类、公共函数有docstrings
- [ ] **类型提示**: 函数参数和返回值有类型注解
- [ ] **复杂逻辑**: 复杂算法有注释说明
- [ ] **README**: 模块有使用说明

## Pythonic Code

- [ ] **魔术方法**: 合理使用__str__, __repr__, __eq__等
- [ ] **属性**: 使用@property替代getter/setter
- [ ] **迭代协议**: 实现__iter__和__next__支持迭代
- [ ] **上下文管理**: 实现__enter__和__exit__支持with
- [ ] **鸭子类型**: 遵循鸭子类型而非类型检查
