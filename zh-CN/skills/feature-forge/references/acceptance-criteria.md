# 验收标准

## Given-When-Then 格式

```markdown
### AC-001: [Scenario Name]
Given [context/precondition]
When [action taken]
Then [expected result]
```

## 按类型分类的示例

### 正常路径

```markdown
### AC-001: Successful Login
Given a registered user with valid credentials
When they submit the login form
Then they are redirected to the dashboard
And a success message is displayed
And their session is created

### AC-002: Add Item to Cart
Given a logged-in user viewing a product
When they click "Add to Cart"
Then the item appears in their cart
And the cart badge updates with the count
And a confirmation toast is shown
```

### 错误情况

```markdown
### AC-003: Invalid Login
Given a user with incorrect password
When they submit the login form
Then an error message "Invalid credentials" is displayed
And the password field is cleared
And they remain on the login page

### AC-004: Duplicate Email Registration
Given an email already exists in the system
When a new user tries to register with that email
Then an error message "Email already registered" is displayed
And the form is not submitted
```

### 边缘情况

```markdown
### AC-005: Empty Cart Checkout
Given a user with an empty cart
When they navigate to checkout
Then they see "Your cart is empty" message
And a "Continue Shopping" button is displayed

### AC-006: Session Expiry
Given a user whose session has expired
When they try to perform any authenticated action
Then they are redirected to login
And a message "Session expired, please log in again" is shown
And their intended action is preserved for after login
```

### 授权

```markdown
### AC-007: Admin-Only Access
Given a regular user (non-admin)
When they try to access /admin/users
Then they receive a 403 Forbidden response
And are redirected to the home page
And an "Access denied" message is shown

### AC-008: Own Resource Only
Given a user viewing another user's profile
When they try to edit the profile
Then the edit button is not visible
And direct URL access returns 403
```

## INVEST 标准

好的验收标准遵循 INVEST：

| 标准 | 描述 | 检查项 |
|------|------|--------|
| **I**ndependent (独立) | 可以单独测试 | 不依赖于其他验收标准 |
| **N**egotiable (可协商) | 细节可以讨论 | 不过度指定 |
| **V**aluable (有价值) | 提供用户价值 | 与需求相关联 |
| **E**stimable (可估算) | 可以估算工作量 | 范围清晰 |
| **S**mall (小) | 可在一次会话中测试 | 不太宽泛 |
| **T**estable (可测试) | 通过/失败是清晰的 | 客观标准 |

## 快速参考

| 场景类型 | Given (给定) | When (当) | Then (那么) |
|----------|-------------|-----------|-----------|
| 正常路径 | 有效状态 | 有效动作 | 成功结果 |
| 错误 | 无效状态/输入 | 动作 | 错误消息 |
| 边缘情况 | 边界条件 | 动作 | 优雅处理 |
| 授权 | 用户角色 | 受保护操作 | 适当访问 |
| 并发 | 多个参与者 | 同时动作 | 一致状态 |