# SOQL 和 SOSL

---

## SOQL 基础

### 基本查询结构

```sql
SELECT Id, Name, Industry, AnnualRevenue
FROM Account
WHERE Industry = 'Technology'
AND AnnualRevenue > 1000000
ORDER BY AnnualRevenue DESC NULLS LAST
LIMIT 100
OFFSET 0
```

### 管理器限制

| 限制 | 同步 | 异步 |
|------|------|------|
| SOQL 查询总数 | 100 | 200 |
| 检索的记录总数 | 50,000 | 50,000 |
| 聚合中的查询行数 | 50,000 | 50,000 |
| SOSL 查询 | 20 | 20 |

---

## 查询优化

### 选择性查询

查询必须具有选择性以避免全表扫描。当查询使用索引字段且过滤到的记录少于 10%（对于大对象为 333,333 条记录）时，该查询是选择性的。

**标准索引字段：**
- Id
- Name
- OwnerId
- CreatedDate
- SystemModstamp
- RecordTypeId
- 外部 ID 字段
- 查找/主详细信息字段

```apex
// GOOD - Uses indexed field (Id)
List<Account> accounts = [
    SELECT Id, Name
    FROM Account
    WHERE Id IN :accountIds
];

// GOOD - Uses indexed field (OwnerId)
List<Account> accounts = [
    SELECT Id, Name
    FROM Account
    WHERE OwnerId = :UserInfo.getUserId()
];

// BAD - Non-indexed field with leading wildcard
List<Account> accounts = [
    SELECT Id, Name
    FROM Account
    WHERE Name LIKE '%Corp'
];

// BETTER - Trailing wildcard is acceptable
List<Account> accounts = [
    SELECT Id, Name
    FROM Account
    WHERE Name LIKE 'Acme%'
];
```

### 批量化模式

```apex
// BAD - SOQL inside loop (will hit governor limits)
for (Contact c : contacts) {
    Account acc = [SELECT Id, Name FROM Account WHERE Id = :c.AccountId];
    // Process account
}

// GOOD - Bulkified query
Set<Id> accountIds = new Set<Id>();
for (Contact c : contacts) {
    accountIds.add(c.AccountId);
}

Map<Id, Account> accountMap = new Map<Id, Account>([
    SELECT Id, Name
    FROM Account
    WHERE Id IN :accountIds
]);

for (Contact c : contacts) {
    Account acc = accountMap.get(c.AccountId);
    // Process account
}
```

### 查询计划分析

在 Developer Console 中使用查询计划工具分析查询性能。

```apex
// Check if query is selective
String query = 'SELECT Id FROM Account WHERE Industry = \'Technology\'';

// In Developer Console: Query Editor > Query Plan
// Look for:
// - Cost < 1 (selective)
// - Leading operation type (Index vs TableScan)
// - Cardinality (estimated rows)
```

---

## 关系查询

### 父到子（子查询）

从父对象查询子记录。

```apex
// Query Accounts with their Contacts
List<Account> accounts = [
    SELECT Id, Name,
           (SELECT Id, FirstName, LastName, Email
            FROM Contacts
            WHERE IsActive__c = true
            ORDER BY LastName
            LIMIT 100)
    FROM Account
    WHERE Industry = 'Technology'
];

// Access child records
for (Account acc : accounts) {
    System.debug('Account: ' + acc.Name);
    for (Contact c : acc.Contacts) {
        System.debug('  Contact: ' + c.FirstName + ' ' + c.LastName);
    }
}
```

### 子到父（点表示法）

从子对象查询父字段。

```apex
// Query Contacts with Account information
List<Contact> contacts = [
    SELECT Id, FirstName, LastName,
           Account.Name,
           Account.Industry,
           Account.Owner.Name,
           Account.Parent.Name
    FROM Contact
    WHERE Account.Industry = 'Technology'
];

// Access parent fields
for (Contact c : contacts) {
    System.debug('Contact: ' + c.FirstName + ' ' + c.LastName);
    System.debug('  Account: ' + c.Account.Name);
    System.debug('  Owner: ' + c.Account.Owner.Name);
}
```

### 多级关系

```apex
// Up to 5 levels of parent relationships
// Up to 1 level of child relationship per query

// Complex relationship query
List<Contact> contacts = [
    SELECT Id, Name,
           Account.Name,
           Account.Parent.Name,
           Account.Parent.Parent.Name,
           Account.Owner.Profile.Name,
           (SELECT Id, Subject FROM Tasks WHERE IsClosed = false LIMIT 5)
    FROM Contact
    WHERE Account.Industry = 'Technology'
    AND Account.Parent.AnnualRevenue > 1000000
];
```

### 多态关系

处理可以引用多个对象类型的字段（如 WhoId、WhatId）。

```apex
// Query Tasks with polymorphic WhoId
List<Task> tasks = [
    SELECT Id, Subject,
           Who.Type,
           Who.Name,
           TYPEOF Who
               WHEN Contact THEN FirstName, LastName, Account.Name
               WHEN Lead THEN FirstName, LastName, Company
           END
    FROM Task
    WHERE CreatedDate = TODAY
];

for (Task t : tasks) {
    if (t.Who instanceof Contact) {
        Contact c = (Contact)t.Who;
        System.debug('Contact: ' + c.FirstName + ' ' + c.LastName);
    } else if (t.Who instanceof Lead) {
        Lead l = (Lead)t.Who;
        System.debug('Lead: ' + l.FirstName + ' ' + l.LastName);
    }
}
```

---

## 聚合查询

### COUNT、SUM、AVG、MIN、MAX

```apex
// Simple count
Integer accountCount = [SELECT COUNT() FROM Account WHERE Industry = 'Technology'];

// Aggregate functions with GROUP BY
List<AggregateResult> results = [
    SELECT Industry,
           COUNT(Id) recordCount,
           SUM(AnnualRevenue) totalRevenue,
           AVG(AnnualRevenue) avgRevenue,
           MIN(AnnualRevenue) minRevenue,
           MAX(AnnualRevenue) maxRevenue
    FROM Account
    WHERE AnnualRevenue != null
    GROUP BY Industry
    HAVING COUNT(Id) > 5
    ORDER BY SUM(AnnualRevenue) DESC
];

for (AggregateResult ar : results) {
    String industry = (String)ar.get('Industry');
    Integer count = (Integer)ar.get('recordCount');
    Decimal totalRevenue = (Decimal)ar.get('totalRevenue');

    System.debug(industry + ': ' + count + ' accounts, $' + totalRevenue);
}
```

### 带 ROLLUP 和 CUBE 的 GROUP BY

```apex
// GROUP BY ROLLUP - hierarchical subtotals
List<AggregateResult> results = [
    SELECT Industry, Type,
           COUNT(Id) cnt,
           SUM(AnnualRevenue) revenue
    FROM Account
    GROUP BY ROLLUP(Industry, Type)
];

// GROUP BY CUBE - all combinations
List<AggregateResult> results = [
    SELECT Industry, Rating,
           COUNT(Id) cnt
    FROM Account
    GROUP BY CUBE(Industry, Rating)
];
```

### COUNT_DISTINCT

```apex
// Count unique values
List<AggregateResult> results = [
    SELECT COUNT_DISTINCT(Industry) uniqueIndustries,
           COUNT_DISTINCT(OwnerId) uniqueOwners
    FROM Account
];
```

---

## 动态 SOQL

### 动态构建查询

```apex
public class DynamicQueryBuilder {

    public static List<SObject> search(
        String objectName,
        List<String> fields,
        Map<String, Object> filters,
        String orderBy,
        Integer limitCount
    ) {
        // Build SELECT clause
        String query = 'SELECT ' + String.join(fields, ', ');
        query += ' FROM ' + String.escapeSingleQuotes(objectName);

        // Build WHERE clause
        List<String> conditions = new List<String>();
        for (String field : filters.keySet()) {
            Object value = filters.get(field);

            if (value instanceof String) {
                conditions.add(field + ' = \'' + String.escapeSingleQuotes((String)value) + '\'');
            } else if (value instanceof Set<Id>) {
                conditions.add(field + ' IN :filterIds');
            } else if (value instanceof Date) {
                conditions.add(field + ' = ' + ((Date)value).format());
            } else if (value != null) {
                conditions.add(field + ' = ' + value);
            }
        }

        if (!conditions.isEmpty()) {
            query += ' WHERE ' + String.join(conditions, ' AND ');
        }

        // Add ORDER BY
        if (String.isNotBlank(orderBy)) {
            query += ' ORDER BY ' + String.escapeSingleQuotes(orderBy);
        }

        // Add LIMIT
        if (limitCount != null && limitCount > 0) {
            query += ' LIMIT ' + limitCount;
        }

        System.debug('Dynamic Query: ' + query);

        // Execute query
        return Database.query(query);
    }
}

// Usage
Map<String, Object> filters = new Map<String, Object>{
    'Industry' => 'Technology',
    'AnnualRevenue' => 1000000
};

List<Account> accounts = (List<Account>)DynamicQueryBuilder.search(
    'Account',
    new List<String>{'Id', 'Name', 'Industry'},
    filters,
    'Name ASC',
    100
);
```

### 动态 SOQL 安全

```apex
public with sharing class SecureDynamicQuery {

    public static List<SObject> queryWithFLS(
        String objectName,
        List<String> fields,
        String whereClause
    ) {
        // Check object accessibility
        Schema.DescribeSObjectResult objDescribe =
            Schema.getGlobalDescribe().get(objectName).getDescribe();

        if (!objDescribe.isAccessible()) {
            throw new SecurityException('No access to object: ' + objectName);
        }

        // Filter to accessible fields only
        Map<String, Schema.SObjectField> fieldMap = objDescribe.fields.getMap();
        List<String> accessibleFields = new List<String>();

        for (String field : fields) {
            Schema.SObjectField fieldToken = fieldMap.get(field);
            if (fieldToken != null && fieldToken.getDescribe().isAccessible()) {
                accessibleFields.add(field);
            }
        }

        if (accessibleFields.isEmpty()) {
            throw new SecurityException('No accessible fields');
        }

        String query = 'SELECT ' + String.join(accessibleFields, ', ');
        query += ' FROM ' + String.escapeSingleQuotes(objectName);

        if (String.isNotBlank(whereClause)) {
            query += ' WHERE ' + whereClause;
        }

        // WITH SECURITY_ENFORCED ensures FLS/CRUD
        query += ' WITH SECURITY_ENFORCED';

        return Database.query(query);
    }
}
```

---

## SOSL（Salesforce 对象搜索语言）

### 基本 SOSL 语法

```apex
// Search across multiple objects
List<List<SObject>> searchResults = [
    FIND 'Acme*' IN ALL FIELDS
    RETURNING
        Account(Id, Name, Industry WHERE Industry = 'Technology'),
        Contact(Id, FirstName, LastName, Email),
        Opportunity(Id, Name, Amount)
    LIMIT 100
];

List<Account> accounts = (List<Account>)searchResults[0];
List<Contact> contacts = (List<Contact>)searchResults[1];
List<Opportunity> opportunities = (List<Opportunity>)searchResults[2];
```

### 搜索范围选项

```apex
// ALL FIELDS - Search all searchable text fields
FIND 'Acme' IN ALL FIELDS

// NAME FIELDS - Search only name fields
FIND 'Acme' IN NAME FIELDS

// EMAIL FIELDS - Search only email fields
FIND 'john@acme.com' IN EMAIL FIELDS

// PHONE FIELDS - Search only phone fields
FIND '555-1234' IN PHONE FIELDS

// SIDEBAR FIELDS - Search fields displayed in sidebar
FIND 'Acme' IN SIDEBAR FIELDS
```

### 搜索词语法

```apex
// Wildcard search (trailing only for SOSL)
FIND 'Acme*'

// Phrase search (exact match)
FIND '"Acme Corporation"'

// Boolean operators
FIND 'Acme AND Technology'
FIND 'Acme OR Technology'
FIND 'Acme AND NOT Closed'

// Grouping
FIND '(Acme OR Globex) AND Technology'
```

### 动态 SOSL

```apex
public class GlobalSearch {

    public static Map<String, List<SObject>> search(
        String searchTerm,
        List<String> objectNames
    ) {
        if (String.isBlank(searchTerm) || searchTerm.length() < 2) {
            return new Map<String, List<SObject>>();
        }

        // Sanitize search term
        String sanitized = String.escapeSingleQuotes(searchTerm);

        // Build RETURNING clause
        List<String> returningClauses = new List<String>();
        for (String objName : objectNames) {
            returningClauses.add(objName + '(Id, Name LIMIT 20)');
        }

        String sosl = 'FIND \'' + sanitized + '*\' IN ALL FIELDS RETURNING ' +
                      String.join(returningClauses, ', ') +
                      ' LIMIT 100';

        List<List<SObject>> results = Search.query(sosl);

        // Map results to object names
        Map<String, List<SObject>> resultMap = new Map<String, List<SObject>>();
        for (Integer i = 0; i < objectNames.size(); i++) {
            resultMap.put(objectNames[i], results[i]);
        }

        return resultMap;
    }
}

// Usage
Map<String, List<SObject>> results = GlobalSearch.search(
    'Acme',
    new List<String>{'Account', 'Contact', 'Opportunity'}
);
```

---

## 性能模式

### 避免常见反模式

```apex
// ANTI-PATTERN 1: SOQL in loops
// BAD
for (Contact c : contacts) {
    Account acc = [SELECT Id FROM Account WHERE Id = :c.AccountId];
}

// GOOD
Map<Id, Account> accounts = new Map<Id, Account>([
    SELECT Id FROM Account WHERE Id IN :contactAccountIds
]);

// ANTI-PATTERN 2: Querying all fields
// BAD
List<Account> accounts = [SELECT FIELDS(ALL) FROM Account LIMIT 100];

// GOOD - Query only needed fields
List<Account> accounts = [SELECT Id, Name, Industry FROM Account LIMIT 100];

// ANTI-PATTERN 3: Not using bind variables
// BAD - Risk of SOQL injection
String query = 'SELECT Id FROM Account WHERE Name = \'' + userInput + '\'';

// GOOD - Use bind variables
String accountName = userInput;
List<Account> accounts = [SELECT Id FROM Account WHERE Name = :accountName];

// ANTI-PATTERN 4: Querying without limits on unbounded queries
// BAD
List<Account> allAccounts = [SELECT Id FROM Account];

// GOOD
List<Account> accounts = [SELECT Id FROM Account LIMIT 10000];
```

### 大数据量策略

```apex
public class LargeDataVolumeQuery {

    // Strategy 1: Query with date ranges
    public static List<Account> getRecentAccounts() {
        return [
            SELECT Id, Name
            FROM Account
            WHERE CreatedDate = LAST_N_DAYS:30
            ORDER BY CreatedDate DESC
            LIMIT 1000
        ];
    }

    // Strategy 2: Use QueryLocator for batch processing
    public Database.QueryLocator getQueryLocator() {
        return Database.getQueryLocator([
            SELECT Id, Name, Industry
            FROM Account
            WHERE Industry = 'Technology'
        ]);
    }

    // Strategy 3: Skinny tables for specific fields
    // (Must be enabled by Salesforce Support for the object)

    // Strategy 4: Custom indexes on frequently queried fields
    // (Request via Salesforce Support)

    // Strategy 5: Archive old records
    // Use Big Objects for historical data
}
```

### QueryLocator vs List

```apex
// Use QueryLocator for Batch Apex (up to 50 million records)
public Database.QueryLocator start(Database.BatchableContext bc) {
    return Database.getQueryLocator([
        SELECT Id, Name FROM Account
    ]);
}

// Use List for smaller datasets (up to 50,000 records)
public List<Account> start(Database.BatchableContext bc) {
    return [SELECT Id, Name FROM Account LIMIT 50000];
}
```

---

## 日期函数和字面量

### 日期字面量

```apex
// Relative date literals
WHERE CreatedDate = TODAY
WHERE CreatedDate = YESTERDAY
WHERE CreatedDate = TOMORROW
WHERE CreatedDate = LAST_WEEK
WHERE CreatedDate = THIS_WEEK
WHERE CreatedDate = NEXT_WEEK
WHERE CreatedDate = LAST_MONTH
WHERE CreatedDate = THIS_MONTH
WHERE CreatedDate = NEXT_MONTH
WHERE CreatedDate = LAST_90_DAYS
WHERE CreatedDate = NEXT_90_DAYS
WHERE CreatedDate = LAST_N_DAYS:30
WHERE CreatedDate = NEXT_N_DAYS:30
WHERE CreatedDate = THIS_QUARTER
WHERE CreatedDate = LAST_QUARTER
WHERE CreatedDate = NEXT_QUARTER
WHERE CreatedDate = THIS_YEAR
WHERE CreatedDate = LAST_YEAR
WHERE CreatedDate = NEXT_YEAR
WHERE CreatedDate = THIS_FISCAL_QUARTER
WHERE CreatedDate = THIS_FISCAL_YEAR
```

### 日期函数

```apex
// Calendar functions in GROUP BY
SELECT CALENDAR_MONTH(CreatedDate) month, COUNT(Id) cnt
FROM Account
GROUP BY CALENDAR_MONTH(CreatedDate)

SELECT CALENDAR_YEAR(CloseDate) year, SUM(Amount) total
FROM Opportunity
WHERE IsWon = true
GROUP BY CALENDAR_YEAR(CloseDate)

// Fiscal functions
SELECT FISCAL_QUARTER(CloseDate) quarter, SUM(Amount)
FROM Opportunity
GROUP BY FISCAL_QUARTER(CloseDate)

// Week functions
SELECT WEEK_IN_MONTH(CreatedDate) week, COUNT(Id)
FROM Lead
GROUP BY WEEK_IN_MONTH(CreatedDate)

// Hour functions (for DateTime fields)
SELECT HOUR_IN_DAY(CreatedDate) hour, COUNT(Id)
FROM Case
GROUP BY HOUR_IN_DAY(CreatedDate)
```

---

## 何时使用

- **SOQL**：使用已知条件检索特定记录
- **SOSL**：跨多个对象的全文搜索
- **聚合查询**：报表、仪表板、摘要计算
- **动态 SOQL**：用户可配置的查询、通用工具
- **关系查询**：单个查询中的父子数据

## 何时不使用

- **循环中的 SOQL**：始终在循环外批量化
- **SELECT ***：只查询所需字段
- **非选择性查询**：添加索引字段过滤器
- **SOSL 用于精确匹配**：使用 SOQL 进行精确条件
- **聚合用于单个记录**：对单个记录使用标准查询