# SQL 窗口函数教程


## 基础入门

### 窗口函数概述与适用场景

窗口函数（Window Function）是一种在 SQL 中执行计算时，能够同时访问**多行数据**，且不改变结果集行数粒度的函数。它基于“窗口”（Window）概念，将数据按指定规则分区、排序后，在每一行上计算一个值。

窗口函数的核心特征：

- 为每一行计算一个结果，不聚合多行为单行。
- 计算范围由 `OVER()` 子句定义，称为“窗口”。
- 窗口可以随当前行动态移动，也可以静态划分。

适用场景主要包括：

- **排名与排序**：如按销售额降序获取各产品的销售名次。
- **累计与滚动统计**：计算截至当前行的累计总和、平均值等。
- **同比与环比分析**：获取上一行或下一行的值，计算差值或增长率。
- **分组内比较**：找出每个部门工资最高的员工，或每类商品价格最低的记录。
- **移动平均**：金融或运营数据分析中，计算最近 N 期的均值。
- **占比与分布**：计算每行数值在分组内的百分比或分布位置。

一个典型场景示例：查询每个部门中薪资排名前两名的员工信息。若使用普通分组聚合，无法直接保留多行明细；而窗口函数能够在保留原行的前提下完成分组内排序。

### 窗口函数与普通聚合函数的区别

普通聚合函数（如 `SUM()`, `AVG()`, `COUNT()`）与窗口函数最直观的区别是：**聚合函数将多行压缩为一行，窗口函数不改变行数**。

具体差异可通过对比表格说明：

| 对比项 | 普通聚合函数 | 窗口函数 |
| --- | --- | --- |
| 输出行数 | 多行输入，单行输出 | 一行输入，一行输出 |
| 是否受 `GROUP BY` 影响 | 是 | 否（但可与 `GROUP BY` 结合使用） |
| 能否在结果中保留明细列 | 通常不能 | 能保留所有原始列 |
| 执行顺序 | 在 `WHERE` 之后，`HAVING` 之前 | 在 `HAVING` 之后，`ORDER BY` 之前（逻辑顺序） |
| 语法结构 | 直接使用，或配合 `GROUP BY` | 必须使用 `OVER()` 子句 |

普通聚合函数在与 `GROUP BY` 一起使用时，分组内多行被折叠成一行。例如：

```sql
-- 统计每个部门的平均薪资，结果每个部门输出一行
SELECT
    department_id,
    AVG(salary) AS avg_salary
FROM employees
GROUP BY department_id;
```

窗口函数在每一行上执行计算，并保留明细数据。例如：

```sql
-- 为每一行都附加其所属部门的平均薪资，行数不变
SELECT
    employee_id,
    department_id,
    salary,
    AVG(salary) OVER (PARTITION BY department_id) AS dept_avg_salary
FROM employees;
```

另外，普通聚合函数中 `SUM()` 等不会逐行累加，除非借助自连接或子查询；而窗口函数天然支持逐行滚动计算。执行顺序上，窗口函数在 SQL 逻辑查询的“结果集确定后”才执行（在 `ORDER BY` 之前），因此不能直接在 `WHERE` 或 `HAVING` 子句中使用窗口函数进行过滤，通常需要借助子查询或 CTE。

### 窗口函数的基本语法结构

窗口函数的标准语法如下：

```sql
窗口函数名([表达式]) OVER (
    [PARTITION BY 分区列]
    [ORDER BY 排序列 [ASC | DESC]]
    [ROWS | RANGE 窗口边界]
)
```

各部分含义：

- **窗口函数名**：如 `ROW_NUMBER()`, `RANK()`, `DENSE_RANK()`, `SUM()`, `AVG()`, `LAG()`, `LEAD()` 等。
- **`OVER()` 子句**：定义窗口的规则，是窗口函数区别于普通函数的关键。
- **`PARTITION BY`**：可选，将数据按指定列分成多个逻辑分区，若无则将所有数据视为一个分区。
- **`ORDER BY`**：可选，控制窗口内的排序顺序，影响排名类函数及累计计算的先后。
- **`ROWS | RANGE`**：可选，进一步限定窗口的物理或逻辑行范围，例如 `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW` 表示当前行及前两行。

具体示例：

```sql
-- 按部门分组、按薪资降序排序，为每位员工分配部门内排名
SELECT
    employee_id,
    department_id,
    salary,
    ROW_NUMBER() OVER (
        PARTITION BY department_id
        ORDER BY salary DESC
    ) AS rank_in_dept
FROM employees;
```

若窗口函数是聚合函数，配合 `ORDER BY` 后可实现累计计算：

```sql
-- 按日期升序，计算截至当前日期的累计销售额
SELECT
    sale_date,
    amount,
    SUM(amount) OVER (
        ORDER BY sale_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_amount
FROM sales;
```

`LAG()` 与 `LEAD()` 用于访问同一分区内前后行的值：

```sql
-- 获取当前员工上一行（按入职日期排序）的薪资
SELECT
    employee_id,
    hire_date,
    salary,
    LAG(salary, 1, 0) OVER (
        ORDER BY hire_date
    ) AS prev_salary
FROM employees;
```

编写窗口函数时需注意：

- `PARTITION BY` 后的列用于分组，若同时存在 `GROUP BY`，窗口函数的分区独立于分组。
- `ORDER BY` 在窗口内排序，多个排序列用逗号分隔。
- 窗口边界语法仅在部分数据库（如 PostgreSQL、SQL Server、SQLite）完全支持；MySQL 8.0+ 支持但不支持部分 `RANGE` 变体。
- 若 `OVER()` 为空括号，则窗口为整个结果集，不分区不排序。

通过灵活组合这些子句，窗口函数可以解决绝大多数复杂的行间分析和排名问题。


## 窗口函数分类详解

### 聚合窗口函数：SUM、AVG、COUNT、MIN、MAX

聚合窗口函数在保留每一行原始数据的同时，基于一个可移动或固定的窗口范围进行聚合计算。与普通聚合函数（`GROUP BY`）不同，窗口函数不会合并多行输出，而是在结果集的每一行上附加一个聚合值，从而方便进行累计求和、移动平均、组内极值等分析。

#### 核心语法结构

```sql
-- 标准 SQL 窗口函数调用格式
聚合函数(列名) OVER (
    [PARTITION BY 分组列]
    [ORDER BY 排序列 [ASC | DESC]]
    [ROWS 或 RANGE 窗口帧子句]
) AS 别名
```

- `PARTITION BY`：将数据按指定列分组，聚合在每个分组内独立计算。
- `ORDER BY`：定义窗口内行的排序顺序，常用于累计型计算。
- `ROWS` / `RANGE`（窗口帧子句）：进一步限定参与运算的行范围，如 `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`。

#### 各函数详细说明

| 函数   | 作用说明                                                                 |
|--------|--------------------------------------------------------------------------|
| `SUM`  | 计算窗口内数值列的总和。                                                  |
| `AVG`  | 计算窗口内数值列的平均值，自动忽略 `NULL`。                                |
| `COUNT`| 统计窗口内的行数，`COUNT(expr)` 忽略 `NULL`，`COUNT(*)` 不忽略。           |
| `MIN`  | 返回窗口内指定列的最小值。                                                |
| `MAX`  | 返回窗口内指定列的最大值。                                                |

#### 示例

```sql
-- 创建销售数据表
CREATE TABLE sales (
    sales_id INT PRIMARY KEY,
    sales_person VARCHAR(50) NOT NULL,
    sale_amount DECIMAL(10, 2) NOT NULL,
    sale_date DATE NOT NULL
);

-- 插入测试数据
INSERT INTO sales VALUES
(1, '王磊', 500.00, '2025-01-01'),
(2, '王磊', 300.00, '2025-01-03'),
(3, '李静', 700.00, '2025-01-03'),
(4, '王磊', 800.00, '2025-01-06'),
(5, '李静', 200.00, '2025-01-08');

-- 查询每位销售员的累计销售额与总销售额
SELECT
    sales_id,
    sales_person,
    sale_amount,
    sale_date,
    -- 按日期排序后的累计销售总额（当前行及之前所有行）
    SUM(sale_amount) OVER (
        PARTITION BY sales_person
        ORDER BY sale_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_amount,
    -- 各销售员的销售额总和（未指定 ORDER BY 时，整个分区为一个窗口）
    SUM(sale_amount) OVER (
        PARTITION BY sales_person
    ) AS total_amount,
    -- 各销售员的平均销售额
    AVG(sale_amount) OVER (
        PARTITION BY sales_person
    ) AS avg_amount,
    -- 各销售员的订单次数
    COUNT(*) OVER (
        PARTITION BY sales_person
    ) AS order_count,
    -- 各销售员的最低销售额
    MIN(sale_amount) OVER (
        PARTITION BY sales_person
    ) AS min_amount,
    -- 各销售员的最高销售额
    MAX(sale_amount) OVER (
        PARTITION BY sales_person
    ) AS max_amount
FROM sales
ORDER BY sales_person, sale_date;
```

**执行结果示例：**

| sales_id | sales_person | sale_amount | sale_date   | cumulative_amount | total_amount | avg_amount | order_count | min_amount | max_amount |
|----------|--------------|-------------|-------------|-------------------|--------------|------------|-------------|------------|------------|
| 1        | 王磊         | 500.00      | 2025-01-01  | 500.00            | 1600.00      | 533.3333   | 3           | 300.00      | 800.00     |
| 2        | 王磊         | 300.00      | 2025-01-03  | 800.00            | 1600.00      | 533.3333   | 3           | 300.00      | 800.00     |
| 4        | 王磊         | 800.00      | 2025-01-06  | 1600.00           | 1600.00      | 533.3333   | 3           | 300.00      | 800.00     |
| 3        | 李静         | 700.00      | 2025-01-03  | 700.00            | 900.00       | 450.0000   | 2           | 200.00      | 700.00     |
| 5        | 李静         | 200.00      | 2025-01-08  | 900.00            | 900.00       | 450.0000   | 2           | 200.00      | 700.00     |

#### 窗口帧子句补充

若不指定 `ORDER BY`，聚合窗口函数默认将整个分区作为窗口。若指定了 `ORDER BY` 但未写窗口帧子句，则不同数据库默认行为通常为 `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`。实际开发中，如需行级别的精确控制，务必显式使用 `ROWS` 或 `RANGE` 子句。

---

### 排序窗口函数：ROW_NUMBER、RANK、DENSE_RANK、NTILE

排序窗口函数用于为结果集中的每个分区内的行生成序号或排名，广泛用于 Top-N 查询、去重保留最新记录、数据分桶等场景。

#### 各函数详细说明

| 函数          | 返回值类型 | 说明                                                                                         |
|---------------|------------|----------------------------------------------------------------------------------------------|
| `ROW_NUMBER()`| BIGINT     | 按顺序为每一行分配一个唯一递增的整数，即使排序值相同，序号也不同。                            |
| `RANK()`      | BIGINT     | 为每一行分配排序值，相同排序值获得相同排名，下一个排名会跳跃（如 1, 1, 3）。                  |
| `DENSE_RANK()`| BIGINT     | 为每一行分配排序值，相同排序值获得相同排名，下一个排名连续（如 1, 1, 2）。                    |
| `NTILE(n)`    | BIGINT     | 将分区内的有序行平均分为 `n` 组，并为每行标明所在组编号（1 ~ `n`）。                          |

#### 语法与注意事项

```sql
ROW_NUMBER() OVER ( [PARTITION BY 分组列] ORDER BY 排序列 [ASC | DESC] ) AS row_num
RANK()       OVER ( [PARTITION BY 分组列] ORDER BY 排序列 [ASC | DESC] ) AS rank_num
DENSE_RANK() OVER ( [PARTITION BY 分组列] ORDER BY 排序列 [ASC | DESC] ) AS dense_num
NTILE(分组数量) OVER ( [PARTITION BY 分组列] ORDER BY 排序列 [ASC | DESC] ) AS group_num
```

- `ORDER BY` 在排序窗口函数中为必选项。
- `NTILE` 的分组数量必须是正整数；当分区内行数不能被 `n` 整除时，前若干组会多一行。
- 上述函数不能直接与普通聚合函数混用在聚合后的行上，需搭配子查询或 CTE 使用。

#### 示例

```sql
-- 使用 ROW_NUMBER / RANK / DENSE_RANK 对学生成绩进行排名
WITH student_scores AS (
    SELECT '张三' AS student_name, 85 AS score
    UNION ALL SELECT '李四', 92
    UNION ALL SELECT '王五', 85
    UNION ALL SELECT '赵六', 78
    UNION ALL SELECT '孙七', 92
    UNION ALL SELECT '周八', 90
)
SELECT
    student_name,
    score,
    -- 行号：即使分数相同也强行编号
    ROW_NUMBER() OVER (ORDER BY score DESC) AS row_number,
    -- 标准排名：分数相同排名相同，后续排名跳跃
    RANK() OVER (ORDER BY score DESC) AS rank_num,
    -- 密集排名：分数相同排名相同，后续排名连续
    DENSE_RANK() OVER (ORDER BY score DESC) AS dense_rank_num,
    -- 分到 3 个桶中，用于数据分布分析
    NTILE(3) OVER (ORDER BY score DESC) AS ntile_group
FROM student_scores
ORDER BY score DESC, student_name;
```

**执行结果示例：**

| student_name | score | row_number | rank_num | dense_rank_num | ntile_group |
|--------------|-------|------------|----------|----------------|-------------|
| 李四         | 92    | 1          | 1        | 1              | 1           |
| 孙七         | 92    | 2          | 1        | 1              | 1           |
| 周八         | 90    | 3          | 3        | 2              | 1           |
| 张三         | 85    | 4          | 4        | 3              | 2           |
| 王五         | 85    | 5          | 4        | 3              | 2           |
| 赵六         | 78    | 6          | 6        | 4              | 3           |

#### 使用场景

- `ROW_NUMBER`：精确去重（如保留每组时间戳最新的记录）。
- `RANK` / `DENSE_RANK`：业务排名（竞赛名次、销量排行等）。
- `NTILE`：将用户按活跃度分为“高、中、低”等层级，或生成数据分桶用于直方图统计。

---

### 取值窗口函数：LAG、LEAD、FIRST_VALUE、LAST_VALUE

取值窗口函数用于在分区内基于行的相对或绝对位置访问同一结果集中其他行的数据，无需自连接即可完成跨行比较。

#### 各函数详细说明

| 函数            | 语法说明                                                                                     | 主要用途                             |
|-----------------|----------------------------------------------------------------------------------------------|--------------------------------------|
| `LAG(expr, offset, default)` | 返回当前行之前第 `offset` 行（向上偏移）的 `expr` 值。默认 `offset` 为 1，`default` 为 NULL。 | 环比计算、查询上一周期数据。          |
| `LEAD(expr, offset, default)`| 返回当前行之后第 `offset` 行（向下偏移）的 `expr` 值，参数意义同 `LAG`。                     | 后续趋势判断、查询下一周期数据。      |
| `FIRST_VALUE(expr)`           | 返回分区内第一行的 `expr` 值，需要配合窗口帧子句控制“第一行”的起始位置。                      | 计算组内初始值、标记基线数据。        |
| `LAST_VALUE(expr)`            | 返回分区内最后一行的 `expr` 值，但默认窗口帧会限制其仅能看到当前行，需指定完整窗口范围。      | 计算组内最终值、最新状态读取。        |

#### 语法与窗口帧注意事项

```sql
LAG(expr, offset, default) OVER ([PARTITION BY 分组列] ORDER BY 排序列) AS lag_value
LEAD(expr, offset, default) OVER ([PARTITION BY 分组列] ORDER BY 排序列) AS lead_value
FIRST_VALUE(expr) OVER ([PARTITION BY 分组列] ORDER BY 排序列 [窗口帧子句]) AS first_val
LAST_VALUE(expr) OVER ([PARTITION BY 分组列] ORDER BY 排序列[窗口帧子句]) AS last_val
```

- `LAG` 和 `LEAD` 只能使用 `offset` 正整数值，默认窗口帧不适用于这两个函数（它们始终基于当前行偏移）。
- 使用 `LAST_VALUE` 时必须显式指定窗口帧，例如 `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING`，才能获取整个分区的最后一行；否则默认只统计到当前行。
- 所有取值窗口函数均不忽略 `NULL`，也不需要能够与聚合函数混合使用。

#### 示例

```sql
-- 创建股票价格表
CREATE TABLE stock_prices (
    stock_code VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    close_price DECIMAL(10, 2) NOT NULL,
    PRIMARY KEY (stock_code, trade_date)
);

-- 插入样例数据
INSERT INTO stock_prices VALUES
('AAPL', '2025-03-01', 172.50),
('AAPL', '2025-03-02', 175.30),
('AAPL', '2025-03-03', 173.20),
('AAPL', '2025-03-04', 177.80),
('GOOG', '2025-03-01', 141.60),
('GOOG', '2025-03-02', 139.90),
('GOOG', '2025-03-03', 142.70);

-- 利用取值窗口函数分析股价涨跌及区间首末值
SELECT
    stock_code,
    trade_date,
    close_price,
    -- 上一交易日收盘价（无上一行则为 NULL）
    LAG(close_price, 1) OVER (
        PARTITION BY stock_code
        ORDER BY trade_date
    ) AS prev_close,
    -- 下一交易日收盘价
    LEAD(close_price, 1) OVER (
        PARTITION BY stock_code
        ORDER BY trade_date
    ) AS next_close,
    -- 每日涨跌额（当日价格与上一交易日之差额）
    close_price - LAG(close_price, 1) OVER (
        PARTITION BY stock_code
        ORDER BY trade_date
    ) AS price_change,
    -- 该股票从首日到当前日的累计最高记录（使用 FIRST_VALUE 时无需特殊窗口帧）
    FIRST_VALUE(close_price) OVER (
        PARTITION BY stock_code
        ORDER BY trade_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS first_close,
    -- 该股票在整个期间内的最后收盘价（需要完整窗口帧）
    LAST_VALUE(close_price) OVER (
        PARTITION BY stock_code
        ORDER BY trade_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    ) AS last_close
FROM stock_prices
ORDER BY stock_code, trade_date;
```

**执行结果示例：**

| stock_code | trade_date | close_price | prev_close | next_close | price_change | first_close | last_close |
|------------|------------|-------------|------------|------------|--------------|-------------|------------|
| AAPL       | 2025-03-01 | 172.50      | NULL       | 175.30     | NULL         | 172.50      | 177.80     |
| AAPL       | 2025-03-02 | 175.30      | 172.50     | 173.20     | 2.80         | 172.50      | 177.80     |
| AAPL       | 2025-03-03 | 173.20      | 175.30     | 177.80     | -2.10        | 172.50      | 177.80     |
| AAPL       | 2025-03-04 | 177.80      | 173.20     | NULL       | 4.60         | 172.50      | 177.80     |
| GOOG       | 2025-03-01 | 141.60      | NULL       | 139.90     | NULL         | 141.60      | 142.70     |
| GOOG       | 2025-03-02 | 139.90      | 141.60     | 142.70     | -1.70        | 141.60      | 142.70     |
| GOOG       | 2025-03-03 | 142.70      | 139.90     | NULL       | 2.80         | 141.60      | 142.70     |

#### 使用场景

- `LAG` / `LEAD`：环比增长、同比增速、相邻时间点差值、会话时长分析。
- `FIRST


# 窗口子句与高级控制

窗口函数（Window Function）可以同时保留“行的细节”与“聚合、排名、偏移量等计算结果”，其行为最终由 `OVER` 子句控制。`OVER` 子句的完整结构是：

```sql
OVER (
    [PARTITION BY <分区表达式>]
    [ORDER BY <排序表达式>]
    [<ROWS | RANGE> 窗口帧子句]
)
```

其中，`PARTITION BY` 决定“分哪些区”，`ORDER


```markdown
## 常用业务实践案例

### 分组 TopN 查询

**实现原理**

分组 TopN 是窗口函数最典型的应用场景。核心是使用 `ROW_NUMBER()`、`RANK()` 或 `DENSE_RANK()` 等排序函数，配合 `PARTITION BY` 对数据分组，再通过 `ORDER BY` 在组内排序。最终利用外层查询过滤排序序号，得到每个分组的前 N 条记录。

不同排序函数的区别：
- `ROW_NUMBER()`：依次递增，序号唯一，不重复。
- `RANK()`：同值同序，后续序号会跳跃。
- `DENSE_RANK()`：同值同序，后续序号不跳跃。

**示例**：查询每个部门薪资最高的前 3 名员工。

```sql
-- 使用 ROW_NUMBER 实现普通的 TopN
SELECT
    dept_id,
    emp_name,
    salary,
    row_num
FROM (
    SELECT
        dept_id,
        emp_name,
        salary,
        ROW_NUMBER() OVER (
            PARTITION BY dept_id          -- 按部门分组
            ORDER BY salary DESC, emp_id  -- 组内按薪资降序
        ) AS row_num
    FROM employee
) t
WHERE row_num <= 3;  -- 过滤出每组前 3 条
```

```sql
-- 若薪资相同需要并列名次，使用 RANK 或 DENSE_RANK
SELECT
    dept_id,
    emp_name,
    salary,
    rank_num
FROM (
    SELECT
        dept_id,
        emp_name,
        salary,
        RANK() OVER (
            PARTITION BY dept_id
            ORDER BY salary DESC
        ) AS rank_num
    FROM employee
) t
WHERE rank_num <= 3;
```

---

### 累计求和与移动平均

**实现原理**

累计求和利用 `ORDER BY` 与窗口帧（frame）定义，将计算范围从分区起始行扩展到当前行。语法为：

```sql
SUM(expr) OVER (
    PARTITION BY <分组字段>
    ORDER BY <排序字段>
    ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
)
```

移动平均则需要指定一个滑动窗口范围，例如计算近 3 天的平均值，可使用 `ROWS BETWEEN 2 PRECEDING AND CURRENT ROW`。

**示例**：统计每日销售额的累计值以及近 3 天移动平均。

```sql
-- 假设表 daily_sales 包含 sale_date、amount 字段
SELECT
    sale_date,
    amount,
    -- 累计求和：从第一天到当前日期的总额
    SUM(amount) OVER (
        ORDER BY sale_date
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS cumulative_amount,
    -- 移动平均：当前日期与前两天的平均值
    AVG(amount) OVER (
        ORDER BY sale_date
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_avg_3d
FROM daily_sales
ORDER BY sale_date;
```

注意事项：
- 省略 `ROWS` 子句时，不同数据库对累计求和默认窗口范围可能不同，建议显式声明。
- 若需要按部门或产品分类累计，可在 `PARTITION BY` 中指定分组字段。

---

### 同比环比与前后值对比

**实现原理**

前后值对比使用 `LAG()` 和 `LEAD()` 窗口函数，可以访问当前行之前或之后指定行数的数据。

- `LAG(column, offset)`：取当前行向前偏移 offset 行的 column 值。
- `LEAD(column, offset)`：取当前行向后偏移 offset 行的 column 值。

环比通常与上一周期（如上一月）比较，同比与上年同周期比较。通过 `PARTITION BY` 和 `ORDER BY` 的组合，可以精确控制对比范围。

**示例**：按月汇总销售额，并计算环比增长率与同比增长率。

```sql
-- 假设 monthly_sales 包含 month_date（每月最后一天）、amount
SELECT
    month_date,
    amount,
    -- 上月销售额（环比对比基准）
    LAG(amount, 1) OVER (
        ORDER BY month_date
    ) AS prev_month_amount,
    -- 环比增长率：(本月 - 上月) / 上月 * 100
    ROUND(
        (amount - LAG(amount, 1) OVER (ORDER BY month_date))
        / LAG(amount, 1) OVER (ORDER BY month_date) * 100,
        2
    ) AS mom_growth_rate,
    -- 去年同月销售额：利用月份序号差 12 个月
    LAG(amount, 12) OVER (
        ORDER BY month_date
    ) AS last_year_same_month_amount,
    -- 同比增长率
    ROUND(
        (amount - LAG(amount, 12) OVER (ORDER BY month_date))
        / LAG(amount, 12) OVER (ORDER BY month_date) * 100,
        2
    ) AS yoy_growth_rate
FROM monthly_sales
ORDER BY month_date;
```

若数据包含多个分组（如多个商品），请根据业务维度增加 `PARTITION BY`，例如：

```sql
LAG(amount, 1) OVER (PARTITION BY product_id ORDER BY month_date)
```

---

### 分组内占比与相对排名

**实现原理**

分组内占比的核心是：先通过 `SUM(expr) OVER (PARTITION BY group)` 得到该分组的总值，再除以当前行的分组总值。

相对排名则是指按某个度量的分布位置，常用窗口函数包括：
- `PERCENT_RANK()`：取值范围 0~1，反映当前行在分组内相对排名比例。
- `CUME_DIST()`：累计分布，返回小于等于当前值的行数占比。

**示例**：计算每个部门内各员工的销售金额占部门总额的百分比，并显示组内相对排名。

```sql
-- 假设 sales_order 包含 dept_id、emp_name、amount
SELECT
    dept_id,
    emp_name,
    amount,
    -- 部门销售总额
    SUM(amount) OVER (PARTITION BY dept_id) AS dept_total,
    -- 部门内占比（百分比）
    ROUND(
        100 * amount / SUM(amount) OVER (PARTITION BY dept_id),
        2
    ) AS pct_in_dept,
    -- 相对排名：值越大排名越靠前（使用降序时 cume_dist 越大代表累计占比越高）
    ROUND(
        CUME_DIST() OVER (
            PARTITION BY dept_id
            ORDER BY amount DESC
        ),
        4
    ) AS cume_rank
FROM sales_order;
```

注意点：
- 分组内占比的分母可以使用 `SUM(...) OVER (...)` 获得，避免子查询重复扫描。
- `PERCENT_RANK()` 和 `CUME_DIST()` 的排序方向取决于业务需求，需结合具体场景设计。

---

### 去重与保留最新记录

**实现原理**

通过 `ROW_NUMBER()` 对同一组内的记录进行编号，排序字段选择“更新时间”或“版本号”等可区分新旧的字段，并指定为倒序。然后在外层查询中只保留编号为 1 的行，从而实现每个分组只保留最新记录。

这一方案避免了复杂自连接或子查询，同时可以保留主表原始字段。

**示例**：订单变更日志表中有多条记录，每个订单只需保留最新状态。

```sql
-- 假设 order_log 包含 order_id、status、update_time
SELECT
    order_id,
    status,
    update_time
FROM (
    SELECT
        order_id,
        status,
        update_time,
        ROW_NUMBER() OVER (
            PARTITION BY order_id           -- 按订单分组
            ORDER BY update_time DESC, id DESC  -- 取最新时间
        ) AS rn
    FROM order_log
) t
WHERE rn = 1;
```

如果数据存在重复的业务主键，但希望保留最新时的完整记录（例如每个用户只保留最后一条登录记录），也可使用相同方法。

```sql
-- 用户登录记录去重，保留每个用户最新的登录信息
SELECT
    user_id,
    login_device,
    login_time
FROM (
    SELECT
        user_id,
        login_device,
        login_time,
        ROW_NUMBER() OVER (
            PARTITION BY user_id
            ORDER BY login_time DESC
        ) AS rn
    FROM user_login_log
) t
WHERE rn = 1;
```

性能建议：
- 在窗口函数前通过 `WHERE` 条件尽量缩小扫描范围，减少参与排序的数据量。
- 如需一次性去重多张关联表，可结合 `JOIN` 使用，仍以窗口函数作为核心过滤条件。
```


## 性能优化与注意事项

### 窗口函数对查询性能的影响

窗口函数（Window Function）的强大之处在于能够在不引起行合并的前提下，对与当前行相关的数据集进行聚合、排序、取值等操作。然而，这种便利性是有代价的。理解其内部执行逻辑，有助于把握性能消耗的关键点。

**主要性能开销来源：**

- **排序（Sort）**：绝大多数窗口函数都依赖于 `OVER (... ORDER BY ...)` 指定的排序规则。数据库需要对整个分区（`PARTITION BY`）内的数据按排序键进行排序。如果数据量巨大，且没有合适的索引支持，排序操作会消耗大量 CPU 和临时磁盘空间（如内存溢出后使用临时表）。
- **分区（Partition / Window）**：`PARTITION BY` 会将数据划分为多个独立窗口。数据库需要在内存中维护这些窗口的边界，并在窗口之间切换状态。如果分区数量极多，每个分区却很小，或者分区过大导致内存无法容纳，都可能造成额外的 I/O 开销。
- **帧（Frame）遍历**：若使用行型帧（如 `ROWS BETWEEN 3 PRECEDING AND CURRENT ROW`），数据库需精确定位帧内行；若使用范围型帧（如 `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`），则需要进行值匹配判断。复杂的帧定义可能导致对每个当前行执行额外的扫描。

**示例：一个典型的排名查询**

```sql
-- 对员工按部门分组，在组内按薪资降序排名
SELECT
    department_id,
    employee_name,
    salary,
    RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) AS rank_salary
FROM employees;
```

在绝大多数数据库实现中，上述查询会执行以下关键步骤：

1. 全表扫描 `employees`，获取所需字段。
2. 按 `department_id` 进行分组（如果现有索引不能直接提供正确分组顺序，则进行哈希或排序）。
3. 在每个分组内，按 `salary DESC` 进行排序。
4. 根据排序结果计算 `rank` 值，并输出。

**性能观察建议**：通过数据库的 `EXPLAIN` 功能，通常会在执行计划中看到 `Sort` 或 `WindowAgg` 节点。若发现排序操作涉及大量行且耗时占比高，则应考虑从排序键或分区的设计上进行优化。

---

### 合理设置分区与排序键

窗口函数的性能高度依赖于 `PARTITION BY` 和 `ORDER BY` 子句的配置。合理的键设计可以极大提升执行效率，不合理的设计则可能导致性能骤降。

**1. 分区键（PARTITION BY）的选取原则**

- **避免过多的小分区**：假设按“国家”和“省份”分区，而数据量本身不大，每个分区只有几行，这会增加窗口切换开销。应当尽量让分区数量适中，保证每个分区有足够的数据量，以便在内存中连续处理。
- **避免重复分区**：如果关联查询中已经按某字段过滤，且过滤后数据量很小，但窗口函数仍然按一个无关的高基数列分区，将导致大量空转。
- **善用索引前缀**：分区键与排序键在设计时需要与表的索引前缀匹配。例如，若经常使用 `PARTITION BY department_id ORDER BY salary`，则创建联合索引 `(department_id, salary)` 会带来明显收益。

```sql
-- 创建适合窗口函数的索引
CREATE INDEX idx_department_salary
ON employees(department_id, salary DESC);
```

索引的好处在于：

- 数据库可以直接按索引顺序读取数据，免去显式排序。
- 每个部门的数据在物理上连续存储，减少了分区切换所需的随机 I/O。

**2. 排序键（ORDER BY）的设定注意点**

- **排序键越多，排序代价越高**：尽量减少排序字段的数量，只保留必要的业务排序字段。如 `ROW_NUMBER()` 仅需要一个唯一性顺序，而非复杂的多字段降序组合。
- **明确排序方向**：如果索引构建为 `ASC`，而查询使用 `ORDER BY ... DESC`，索引可能无法直接倒序扫描（部分数据库支持向后索引扫描，但并非所有场景都适用）。此时可考虑在索引中显式声明 `DESC`（若数据库允许）。
- **避免对高开销表达式排序**：不要在 `ORDER BY` 或 `PARTITION BY` 中使用函数表达式（如 `DATE(order_time)`），否则会破坏索引匹配并强制全排序。若有此需求，可新增冗余列并在写入时预处理。

**3. 可考虑使用帧（Frame）减少排序范围**

当你只关心“当前行和之前/之后的一小部分”时，可以使用窗口帧限定参与运算的行数，从而减少计算负担：

```sql
-- 只计算每个分区内当前行及其前后各 1 行的移动平均值
SELECT
    sales_date,
    amount,
    AVG(amount) OVER (
        PARTITION BY product_id
        ORDER BY sales_date
        ROWS BETWEEN 1 PRECEDING AND 1 FOLLOWING
    ) AS moving_avg
FROM daily_sales;
```

此定义下，数据库无需计算全部分区内的所有行，只需在内存中保留最多 3 行的滑动窗口。

---

### 与自连接、子查询的替代方案对比

在窗口函数尚未普及或某些旧系统中，人们常使用自连接或子查询来模拟“跨行计算”或“分组内排名”。这些方案在正确性上没有太大问题，但往往存在性能差、可读性差等缺陷。

#### 典型问题：找出每个部门薪资最高的前两名员工

**自连接方案（不推荐）**

```sql
-- 使用自连接：找出小于等于当前员工的同部门高薪员工数，小于 2 则属于前两名
SELECT
    e.department_id,
    e.employee_name,
    e.salary
FROM employees e
WHERE (
    SELECT COUNT(DISTINCT e2.salary)
    FROM employees e2
    WHERE e2.department_id = e.department_id
      AND e2.salary > e.salary
) < 2
ORDER BY e.department_id, e.salary DESC;
```

- **性能问题**：对于外层每行记录，都需要执行一次相关子查询扫描整个 `department_id` 分区的所有行，时间复杂度近似为 `O(N × M)`，M 为分区内平均行数。
- **可读性差**：语义不够直白，很容易写错 `>、>=、<` 等符号。
- **去重处理复杂**：使用 `COUNT(DISTINCT ...)` 来应对薪资重复问题会进一步降低性能。

**窗口函数方案（推荐）**

```sql
-- 使用窗口函数
SELECT
    department_id,
    employee_name,
    salary
FROM (
    SELECT
        department_id,
        employee_name,
        salary,
        ROW_NUMBER() OVER (
            PARTITION BY department_id
            ORDER BY salary DESC
        ) AS rn
    FROM employees
) AS ranked
WHERE rn <= 2
ORDER BY department_id, salary DESC;
```

- **性能特点**：窗口函数只需要一次排序操作，所有行仅被扫描一次（不考虑数据库中实际并行执行的分区策略）。时间复杂度约为 `O(N log N)`，主要取决于排序开销。
- **可读性强**：逻辑非常清晰，易扩展为“前 N 名”或“排名区间”。

#### 模拟 LAG / LEAD（访问上一行 / 下一行）

旧方法常使用自连接：

```sql
-- 自连接获取上一行销售额
SELECT
    cur.sales_date,
    cur.amount,
    prev.amount AS prev_amount
FROM daily_sales cur
LEFT JOIN daily_sales prev
    ON cur.product_id = prev.product_id
   AND prev.sales_date = (
       SELECT MAX(sales_date)
       FROM daily_sales p2
       WHERE p2.product_id = cur.product_id
         AND p2.sales_date < cur.sales_date
   );
```

窗口函数一行完成：

```sql
SELECT
    sales_date,
    amount,
    LAG(amount) OVER (
        PARTITION BY product_id
        ORDER BY sales_date
    ) AS prev_amount
FROM daily_sales;
```

**结论**：相比自连接或嵌套子查询，窗口函数可以在几乎所有同等工作量中将代码行数减少 50% 以上，且执行计划更简洁，尤其是在分区列基数大时，优势更加明显。

---

### 版本兼容性与常见错误排查

**1. 版本兼容性**

窗口函数遵循 SQL:2003 及后续标准，但各数据库的完整支持情况并不完全一致：

| 数据库           | 主要支持版本         | 注意事项 |
| ---------------- | -------------------- | -------- |
| PostgreSQL       | 8.4+                | 支持较为完整，支持 `FILTER` 子句等扩展 |
| MySQL            | 8.0+                | 8.0 之前不支持，可改用变量模拟，但后期维护困难 |
| Oracle           | 9i+                 | 支持完整，包括 `RATIO_TO_REPORT` 等特有窗口函数 |
| SQL Server       | 2012+               | `FULL OUTER APPLY`? 不对，窗口函数完整支持需2005+，但 `LEAD/LAG` 需要 2012+ |
| SQLite           | 3.25+               | 较新版本才支持 |
| ClickHouse       | 20.3+               | 支持部分窗口函数，以及数组模拟方案 |

特别注意：

- **MySQL 5.x 及以下**：没有窗口函数，此时只能用用户变量或聚合子查询，无法利用索引优化。
- **SQL Server 2000/2005 早期**：缺少部分函数，且不能在 `OVER` 内使用聚合函数本身的别名。
- **Oracle 旧版与新版语法差异**：命名窗口（`WINDOW` 子句）及 `EXCLUDE` 等特性在部分版本不支持。

**2. 常见错误及排查方法**

| 序号 | 错误现象 | 原因与解决方案 |
| ---- | -------- | -------------- |
| 1    | `window function "row_number" requires an ORDER BY clause` | `ROW_NUMBER()`、`RANK()` 必须在 `OVER` 中显式编写 `ORDER BY`。即使不需要顺序，也必须写成 `ORDER BY (SELECT NULL)` 或使用常量。 |
| 2    | `window functions are only allowed in SELECT and ORDER BY` | 窗口函数不允许出现在 `WHERE` 、`GROUP BY` 、`HAVING`。若需要过滤基于窗口函数的结果，应使用子查询、CTE 包裹后再过滤。 |
| 3    | `PARTITION BY` 中的列冲突 | 列名在 `PARTITION BY` 和 `ORDER BY` 重复时，有些数据库要求加上表别名或引用具体表项，否则解析模糊。 |
| 4    | 在 `WHERE` 中引用窗口函数别名 | 在 `SELECT` 中设定别名后，不能在 `WHERE` 中直接引用（如 `WHERE rn = 1`）。需使用子查询或重新书写表达式。 |
| 5    | 聚合函数与窗口函数的区别被混淆 | `SUM(salary) OVER (...) 是窗口函数，而 SUM(salary) 是聚合函数。在 `SELECT` 中同时使用两者时，可能需要 `DISTINCT` 避免重复，但 `DISTINCT` 又会存在部分数据库限制（如 SQL Server 不允许 `DISTINCT` 与窗口函数共用相同表达式）。 |
| 6    | `ROWS` 与 `RANGE` 默认帧不同 | 若有 `ORDER BY`，默认帧为 `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`，这可能导致部分相等的行被计算进当前行。若不需要这种逻辑，请显式使用 `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`。 |
| 7    | 浮动精度（Floating Point Accumulation） | 对浮点列求移动和/平均值时，可能出现微小误差。如果需要精确计算，应先将列转换为 `DECIMAL` 类型。 |

**一个常见的综合错误示例：**

```sql
-- 错误写法：WHERE 引用窗口函数别名
SELECT
    employee_id,
    department_id,
    salary,
    ROW_NUMBER() OVER (
        PARTITION BY department_id
        ORDER BY salary DESC
    ) AS rn
FROM employees
WHERE rn = 1;
```

在多数数据库（如 PostgreSQL）中，此句会报错：`ERROR: column "rn" does not exist`。原因在于 `WHERE` 在窗口函数计算之前执行。正确做法是使用子查询：

```sql
-- 正确写法
SELECT *
FROM (
    SELECT
        employee_id,
        department_id,
        salary,
        ROW_NUMBER() OVER (
            PARTITION BY department_id
            ORDER BY salary DESC
        ) AS rn
    FROM employees
) AS ranked
WHERE rn = 1;
```

另一种常见问题是 `DISTINCT` 与窗口函数同时使用时的语法限制。例如某些数据库不允许 `SELECT DISTINCT ` 和窗口函数表达式中的列都显式出现在 `ORDER BY` 之外，这需要分析具体报错并优化查询逻辑。

**排查建议**：

- 始终查阅目标数据库的官方版本手册，确认窗口函数的语法准确度。
- 使用数据库提供的查询诊断工具（如 `EXPLAIN ANALYZE`）检查窗口计算是否出现额外的 `Sort` 操作。
- 将复杂逻辑拆分为 CTE，以逐步验证问题产生的步骤，便于隔离错误。


## 综合业务问题拆解与SQL编写

### 业务问题拆解通用方法论

窗口函数（Window Function）将“分组计算”与“多行访问”结合起来，适合处理“对每一行数据，同时看到与其相关的一组行”的问题。实际业务问题拆解时可遵循以下三步：

1. **明确需求粒度**：最终结果中每一行代表什么？代表单个明细行，还是某类汇总行？这决定了`SELECT`后需要保留的字段层次。
2. **识别分组边界与排序逻辑**：
   - 分组边界：利用`PARTITION BY`定义“组”。
   - 排序逻辑：利用`ORDER BY`定义“组内顺序”。
   - 滑动窗口范围：利用`ROWS`或`RANGE`定义“计算所用的行帧”。
3. **确定窗口函数**：
   - 排名/编号：`ROW_NUMBER()`、`RANK()`、`DENSE_RANK()`。
   - 移动/累计聚合：`SUM() OVER(...)`、`AVG() OVER(...)`。
   - 跨行访问：`LAG()`、`LEAD()`、`FIRST_VALUE()`、`LAST_VALUE()`。
   - 分位数切分：`NTILE()`。
   - 统计分布：`PERCENT_RANK()`、`CUME_DIST()`。

### 典型案例：求每个商品分类销量前 3 的商品

#### 业务需求拆解

1. 结果粒度：每个分类下筛选后的商品明细行。
2. 分组边界：商品分类 `category_id`。
3. 排序逻辑：按销量 `sales_amount` 降序。
4. 所需能力：组内排名，并过滤出 `rank <= 3`。

#### SQL 实现

```sql
-- 表：product_sales
-- 字段：product_id 商品ID，category_id 分类ID，sales_amount 销量

WITH ranked_products AS (
    SELECT
        product_id,
        category_id,
        sales_amount,
        -- 使用 DENSE_RANK 可保留并列名次
        DENSE_RANK() OVER (
            PARTITION BY category_id
            ORDER BY sales_amount DESC
        ) AS sales_rank
    FROM product_sales
)
SELECT
    product_id,
    category_id,
    sales_amount,
    sales_rank
FROM ranked_products
WHERE sales_rank <= 3;
```

### 跨组对比问题：各员工薪资与所在部门平均薪资之差

#### 拆解思路

用户希望看到“员工-部门”明细，同时附带部门平均薪资。因此不应该使用 `GROUP BY` 进行聚合，而是使用窗口函数在明细行上附加聚合值。

```sql
-- 表：employee
-- 字段：emp_name 姓名，dept_id 部门ID，salary 薪资

SELECT
    emp_name,
    dept_id,
    salary,
    -- 在同一部门分区内计算平均薪资，同时保持明细行不合并
    AVG(salary) OVER (
        PARTITION BY dept_id
    ) AS dept_avg_salary,
    salary - AVG(salary) OVER (
        PARTITION BY dept_id
    ) AS diff_salary
FROM employee;
```

---

## 多级窗口函数嵌套技巧

### 核心原则

SQL 执行顺序决定：窗口函数在 `WHERE`、`GROUP BY`、`HAVING` 之后执行，但无法直接嵌套使用，例如 `ROW_NUMBER() OVER (ORDER BY SUM(amount) OVER (...))` 是非法的。这是因为一个窗口函数的输出还不能立刻被另一个窗口函数引用。

解决方法是引入子查询或公用表表达式（CTE），将第一层窗口函数的计算结果暂时“物化”，再对结果执行第二层窗口函数。这种技巧常用在：

- 对排名结果再次进行聚合或筛选。
- 对每个分组取出的“顶部记录”再执行全局排序。
- 在两层级联的分组语境中，先算组内汇总值，再算跨组的移动平均。

### 示例：按年月汇总销售额后，计算每个月份相对于前两个月的移动平均

#### 业务拆解

1. 第一层窗口：按月份聚合销售额。
2. 第二层窗口：对月份序列做“2行向前”的窗口移动平均。

#### 错误写法（直接嵌套）

```sql
-- 许多数据库引擎会直接报语法错误
SELECT
    MONTH(order_date)  AS order_month,
    SUM(amount)        AS month_sales,
    AVG(SUM(amount)) OVER (
        ORDER BY MONTH(order_date)
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_avg
FROM orders
GROUP BY MONTH(order_date);
```

#### 正确写法（使用 CTE 分层）

```sql
-- 表：orders
-- 字段：order_date 订单日期，amount 订单金额

WITH monthly_sales AS (
    SELECT
        DATE_TRUNC('month', order_date) AS order_month,
        SUM(amount)                     AS month_sales
    FROM orders
    GROUP BY DATE_TRUNC('month', order_date)
)
SELECT
    order_month,
    month_sales,
    -- 第二层窗口：对聚合后的月份序列算移动平均
    AVG(month_sales) OVER (
        ORDER BY order_month
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ) AS moving_avg_3m
FROM monthly_sales
ORDER BY order_month;
```

### 示例：先对商品按价格排名，再对排名结果进行分档

#### 业务场景

商品库中有若干商品，先按价格降序得到全量排名，再根据排名切出“低价/中价/高价”标签，同时保留原排名。

```sql
-- 表：products
-- 字段：product_name 商品名称，price 单价

WITH price_ranked AS (
    SELECT
        product_name,
        price,
        RANK() OVER (ORDER BY price DESC) AS price_rank
    FROM products
)
SELECT
    product_name,
    price,
    price_rank,
    -- 嵌套窗口：基于第一次窗口得到的排名进行分桶
    NTILE(3) OVER (ORDER BY price_rank) AS price_group
FROM price_ranked
ORDER BY price_rank;
```

### 嵌套技巧注意事项

- **执行顺序**：第一层窗口函数的别名不能直接被 `SELECT` 中的另一个窗口函数引用，必须借助 `FROM` 子查询或 `WITH`。
- **数据稳定性**：多级窗口使用时，务必保证 `PARTITION BY` 和 `ORDER BY` 的确定性，否则结果可能不稳定。
- **性能**：每一层窗口函数都需要一次完整的排序/分区操作，多层意味多次扫描，应尽量减少层级或对底层数据预先过滤。

---

## 练习题与答案解析

### 练习题 1

有一张`student_scores`表，字段如下：

- `student_id`：学生ID。
- `subject`：学科。
- `score`：成绩。

**需求**：找出每个学科中成绩排名第 2 的学生ID。若某学科成绩完全并列，则同时输出。

**答案**：

```sql
-- 使用 DENSE_RANK 保证并列名次
SELECT
    student_id,
    subject,
    score
FROM (
    SELECT
        student_id,
        subject,
        score,
        DENSE_RANK() OVER (
            PARTITION BY subject
            ORDER BY score DESC
        ) AS rank_num
    FROM student_scores
) AS ranked
WHERE rank_num = 2;
```

**解析**：

- 使用`PARTITION BY subject`按学科分区。
- 使用`ORDER BY score DESC`保证成绩高者名次靠前。
- 外查询过滤 `rank_num = 2` 时，因为`DENSE_RANK`会为并列成绩分配相同名次，所以符合并列需求。

---

### 练习题 2

有一张`sales`表，字段如下：

- `sale_date`：销售日期（ DATE 类型）。
- `emp_id`：销售人员ID。
- `amount`：销售额。

**需求**：计算每位销售人员“截至今日”的累计销售额，并从所有销售员中筛选出累计销售额超过 1000 的销售员及累计值。

**答案**：

```sql
WITH cumulative_sales AS (
    SELECT
        emp_id,
        sale_date,
        -- 按日期升序排序，计算每个销售员自己的累计销售额
        SUM(amount) OVER (
            PARTITION BY emp_id
            ORDER BY sale_date
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) AS cum_amount
    FROM sales
)
-- 直接筛选累计销售额是否达到目标
SELECT DISTINCT
    emp_id,
    cum_amount
FROM cumulative_sales
WHERE cum_amount > 1000;
```

**解析**：

- 窗口函数在 `PARTITION BY emp_id` 后，通过 `ORDER BY sale_date` 产生“组内排序”，再使用累计行帧 `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` 计算每日累计值。
- 若只想判断最终累计值是否超过1000，需要根据业务时间点确定最后一天是否满足条件，也可将 `cumulative_sales` 外层增加 `ROW_NUMBER()` 取每位销售员最晚一条。此处使用 `DISTINCT` 仅为演示简单筛选方法，实际中可根据具体日期来限定。

---

### 练习题 3

有一张`stocks`表，记录某股票每日收盘价，字段如下：

- `trade_date`：交易日（ DATE）。
- `close_price`：收盘价。

**需求**：求股票每个交易日，与其前一个交易日相比的涨跌幅百分比，并筛选出涨幅超过 5% 的交易日。若无前一日则忽略。

**答案**：

```sql
WITH price_lag AS (
    SELECT
        trade_date,
        close_price,
        -- 获取前一个交易日的收盘价
        LAG(close_price, 1) OVER (
            ORDER BY trade_date
        ) AS prev_close_price
    FROM stocks
)
SELECT
    trade_date,
    close_price,
    prev_close_price,
    -- 计算涨跌幅百分比（保留两位小数）
    ROUND(
        (close_price - prev_close_price) * 100.0 / prev_close_price,
        2
    ) AS change_percent
FROM price_lag
WHERE prev_close_price IS NOT NULL
  AND (close_price - prev_close_price) * 100.0 / prev_close_price > 5;
```

**解析**：

- `LAG(close_price, 1) OVER (ORDER BY trade_date)` 将每一行的前一行数据作为新列，用来模拟“前后交易日”。
- 外查询将空的前一收盘价排掉，因为首日没有涨跌幅。
- 涨跌幅计算公式可以复用，但若需要对计算结果进行额外算术过滤，需将公式写成布尔表达式或使用同名的 `WHERE` 中的临时计算值。