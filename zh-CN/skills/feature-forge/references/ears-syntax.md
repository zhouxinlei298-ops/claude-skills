# EARS 语法

## EARS 格式

Easy Approach to Requirements Syntax（简单方法需求语法），用于清晰、无歧义的需求描述。

### 基本模式

```
While <precondition>, when <trigger>, the system shall <response>.
```

### 模式类型

**Ubiquitous (总是适用)**
```
The system shall [action].
```
示例：The system shall encrypt all passwords using bcrypt.

**Event-Driven (事件驱动)**
```
When [trigger], the system shall [action].
```
示例：When the user clicks "Submit", the system shall save the form data.

**State-Driven (状态驱动)**
```
While [state], the system shall [action].
```
示例：While the user is logged in, the system shall display the dashboard.

**Conditional (条件性 - 最常用)**
```
While [state], when [trigger], the system shall [action].
```
示例：While the cart contains items, when the user clicks "Checkout", the system shall navigate to the payment page.

**Optional (可选功能)**
```
Where [feature enabled], the system shall [action].
```
示例：Where two-factor authentication is enabled, the system shall require a verification code.

## 按领域分类的示例

### 身份验证

```markdown
**FR-AUTH-001**: Login
While credentials are valid, when POST /auth/login is called,
the system shall return JWT access token (15min) and refresh token (7d).

**FR-AUTH-002**: Invalid Login
When invalid credentials are provided,
the system shall return 401 and increment failed login counter.

**FR-AUTH-003**: Account Lockout
While failed login count exceeds 5, when login is attempted,
the system shall reject the attempt and require password reset.
```

### 电子商务

```markdown
**FR-CART-001**: Add to Cart
While user is logged in, when they click "Add to Cart",
the system shall add the item and update the cart badge count.

**FR-CART-002**: Apply Coupon
While the cart contains items, when a valid coupon code is applied,
the system shall reduce the total by the discount amount.

**FR-ORDER-001**: Checkout
While payment method is valid, when user confirms order,
the system shall create order, charge payment, and send confirmation email.
```

### 数据管理

```markdown
**FR-EXPORT-001**: CSV Export
While user has data access permission, when they click "Export",
the system shall generate a CSV file and initiate download.

**FR-DELETE-001**: Soft Delete
When a resource is deleted,
the system shall set deleted_at timestamp instead of removing the record.
```

## 快速参考

| 类型 | 结构 | 使用场景 |
|------|------|----------|
| Ubiquitous (总是适用) | shall [动作] | 总是适用 |
| Event (事件驱动) | When [X], shall | 在触发时 |
| State (状态驱动) | While [X], shall | 持续状态 |
| Conditional (条件性) | While [X], when [Y], shall | 状态 + 触发器 |
| Optional (可选功能) | Where [X], shall | 功能开关 |