# 输入清理(XSS防护)实现计划

**任务**: 实现输入清理(XSS防护)
**日期**: 2026-03-30
**优先级**: P0

---

## 一、需求分析

### 1.1 目标
- 防止XSS攻击，清理用户输入中的恶意脚本
- 在关键接口应用输入清理
- 确保数据存储和展示的安全性

### 1.2 需要保护的端点
- 用户管理: 创建用户、更新用户（用户名、邮箱、部门）
- 项目管理: 创建项目、更新项目（项目名称、描述）
- 数据同步: 同步配置（数据源名称、配置参数）

---

## 二、实现方案

### 2.1 核心清理函数

文件: `backend/app/core/security.py`

```python
def sanitize_html(text: str | None) -> str | None:
    """清理HTML标签，防止XSS攻击."""

def sanitize_input(text: str | None, max_length: int = 255) -> str | None:
    """通用输入清理：去除HTML标签、控制长度、去除危险字符."""
```

### 2.2 Pydantic验证器

文件: `backend/app/core/validators.py` (已存在，添加新验证器)

```python
def validate_username(v: str) -> str:
    """验证用户名：只允许字母、数字、下划线、连字符."""

def validate_email(v: str) -> str:
    """验证邮箱格式."""

def validate_no_html(v: str | None) -> str | None:
    """验证字段不包含HTML标签."""
```

### 2.3 Schema集成

文件: `backend/app/schemas/user.py`
- 为UserCreate和UserUpdate添加验证器

文件: `backend/app/schemas/project.py` (如需要创建)
- 为ProjectCreate和ProjectUpdate添加验证器

---

## 三、任务列表

### Task 1: 实现核心清理函数
**文件**: `backend/app/core/security.py`
**工作**:
1. 添加`sanitize_html()`函数，使用bleach或正则表达式清理HTML
2. 添加`sanitize_input()`函数，组合多种清理逻辑
3. 添加`strip_dangerous_chars()`辅助函数

**验收标准**:
- 函数能正确清理`<script>`标签和事件处理器
- 函数能限制输入长度
- 所有函数有完整类型注解和文档字符串

### Task 2: 实现Pydantic验证器
**文件**: `backend/app/core/validators.py`
**工作**:
1. 添加`validate_username()`验证器
2. 添加`validate_email()`验证器（正则表达式）
3. 添加`validate_no_html()`验证器
4. 添加`validate_project_name()`验证器

**验收标准**:
- 用户名只允许字母、数字、下划线、连字符，长度3-50
- 邮箱符合标准邮箱格式
- 验证器能在Pydantic v2中正常工作

### Task 3: 更新User Schema
**文件**: `backend/app/schemas/user.py`
**工作**:
1. 在UserCreate模型中添加字段验证器
2. 在UserUpdate模型中添加字段验证器
3. 使用`@field_validator`装饰器

**验收标准**:
- 用户名、邮箱、部门字段都有验证
- 创建和更新用户时自动触发验证

### Task 4: 创建Project Schema
**文件**: `backend/app/schemas/project.py`
**工作**:
1. 创建ProjectCreate模型
2. 创建ProjectUpdate模型
3. 创建ProjectResponse模型
4. 添加字段验证器

**验收标准**:
- 项目名称、描述字段有验证
- 响应模型与数据库模型对应

### Task 5: 编写测试
**文件**: `backend/tests/test_security.py`
**工作**:
1. 测试`sanitize_html()`各种XSS payload
2. 测试`sanitize_input()`边界情况
3. 测试验证器功能

**文件**: `backend/tests/test_validators.py`
**工作**:
1. 测试用户名验证（有效和无效输入）
2. 测试邮箱验证（有效和无效输入）
3. 测试HTML检测

**验收标准**:
- 测试覆盖率>90%
- 包含常见XSS攻击向量的测试用例
- 所有测试通过

---

## 四、技术细节

### 4.1 XSS防护策略

1. **输入验证**: Pydantic模型级别验证
2. **输入清理**: 清理函数去除危险字符
3. **输出编码**: 前端负责，后端提供安全数据

### 4.2 正则表达式模式

```python
# 用户名: 字母、数字、下划线、连字符，3-50字符
USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9_-]{3,50}$')

# 邮箱: 标准邮箱格式
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# HTML标签检测
HTML_PATTERN = re.compile(r'<[^>]+>')
```

### 4.3 危险HTML标签和属性

```python
DANGEROUS_TAGS = ['script', 'iframe', 'object', 'embed', 'form']
DANGEROUS_ATTRS = ['onerror', 'onload', 'onclick', 'onmouseover', 'javascript:']
```

---

## 五、验收标准

| 验收标准 | 验证方式 |
|----------|----------|
| 所有用户输入字段都有验证 | 代码审查 + 测试 |
| XSS payload被正确清理 | 测试用例验证 |
| 验证失败返回400错误 | API测试 |
| 测试覆盖率>90% | pytest覆盖率报告 |

---

## 六、风险与注意事项

1. **过度清理**: 确保合法输入不被误杀
2. **性能影响**: 验证器不应显著影响API响应时间
3. **兼容性**: 确保与现有数据兼容

---

**计划创建时间**: 2026-03-30
**预计总工时**: 10小时
