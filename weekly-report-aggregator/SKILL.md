---
name: weekly-report-aggregator
description: Process and aggregate weekly team reports from text input into Word-compatible table format. Use when users provide team member work summaries that need to be categorized, calculated (percentages to person-days), and formatted as structured tables with merged cells for department/business line grouping. Triggered by requests to "summarize weekly reports", "aggregate team reports", or "format work summaries into tables".
---

# Weekly Report Aggregator

## Overview

Transform raw weekly team report text into structured Word-compatible table data. Parse work summaries, apply business line classification rules, convert percentage allocations to person-days, and format output with proper cell merging for department groupings.

## Workflow

### Step 1: Parse Input Text

Extract the following information from user-provided text:

- Team member names (for internal tracking, not shown in output)
- Business lines / departments
- Time allocation (percentages or person-days)
- Project/iteration names
- Work content descriptions
- Project status/risks

### Step 2: Apply Classification Rules

**Critical Classification Logic:**

Transform business line categories using these rules:

1. **Explicit matches** - Map directly if text clearly indicates:
   - "客商" → 客商
   - "DTC" → DTC
   - "船东" → 船东
   - "散拼" → 散拼
   - "营销" → 营销
   - "履约" → 履约
   - "技术支撑" → 技术支撑
   - "财务" 或 "BMS" → 财务/BMS

2. **GM-based classification**:
   - ANY mention of "GM1" (in any context) → classify as "Saas软件"
   - ANY mention of "GM2" (in any context) → classify as "履约"

3. **Default classification**:
   - If none of the above matches → classify as "Saas软件"

**Examples:**

- "GM1新功能开发" → Saas软件
- "GM2订单处理" → 履约
- "系统维护" (no explicit match) → Saas软件
- "客商平台优化" → 客商
- "DTC渠道运营" → DTC

### Step 3: Calculate Person-Days

Convert percentage allocations to person-days using standard 5-day work week:

**Formula:** Percentage × 5 = Person-days

**Examples:**

- 30% = 0.30 × 5 = 1.5 人日
- 50% = 0.50 × 5 = 2.5 人日
- 100% = 1.00 × 5 = 5.0 人日
- 20% = 0.20 × 5 = 1.0 人日

If input is already in person-days, keep as-is.

### Step 4: Aggregate by Business Line

1. Group all entries by classified business line
2. Sum person-days for each business line
3. Prepare for merged cell output format

### Step 5: Format Output Table

Generate Word-compatible table with these specifications:

**Table Structure:**

| 小组/业务线 | 本期实际投入资源 | 项目/迭代 | 本期工作内容 | 项目进度/风险 |
| ----------- | ---------------- | --------- | ------------ | ------------- |

**Formatting Rules:**

1. **Cell Merging:** Identical "小组/业务线" values must be merged vertically
2. **Resource Totals:** Corresponding "本期实际投入资源" for merged business lines must also be merged and show the summed total
3. **No Names:** Do not include team member names in any output column
4. **Sort Order:** Group by business line (merged rows together)
5. **Number Format:** Person-days should show one decimal place (e.g., "1.5人日", "2.0人日")

**Output Format:**

Provide table data in markdown format that is easily convertible to Word tables. For rows that belong to the same business line:

- The first row shows the business line name and total person-days
- Subsequent rows use empty cells for business line and person-days columns
- Empty cells indicate these rows should be merged with the first row when creating the Word document

```
| 小组/业务线 | 本期实际投入资源 | 项目/迭代 | 本期工作内容 | 项目进度/风险 |
|:-----------|:---------------|:---------|:-----------|:------------|
| Saas软件 | 8.5人日 | 项目A | 完成用户模块开发 | 按计划进行 |
| | | 项目B | 系统性能优化 | 存在技术风险 |
| | | GM1功能 | 新功能设计评审 | 需求待确认 |
| 履约 | 3.5人日 | GM2订单系统 | 订单处理流程优化 | 已完成80% |
| | | 物流对接 | 第三方API集成 | 测试中 |
| 客商 | 2.0人日 | 客商门户 | 权限管理升级 | 按计划进行 |
```

**Important:** Do NOT add any text annotations like "(行合并)" in the output cells. Keep business line names and person-day values clean without any additional markers.

## Common Scenarios

### Scenario 1: Mixed Percentage and Person-Day Input

**Input:**

```
张三：GM1开发 30%，系统维护 20%
李四：客商平台 2.5人日
王五：GM2订单 50%，DTC渠道 1人日
```

**Processing:**

- 张三 GM1开发: 30% → 1.5人日, classify as Saas软件
- 张三 系统维护: 20% → 1.0人日, classify as Saas软件
- 李四 客商平台: 2.5人日, classify as 客商
- 王五 GM2订单: 50% → 2.5人日, classify as 履约
- 王五 DTC渠道: 1人日, classify as DTC

**Aggregation:**

- Saas软件: 1.5 + 1.0 = 2.5人日
- 客商: 2.5人日
- 履约: 2.5人日
- DTC: 1.0人日

### Scenario 2: Ambiguous Business Lines

**Input:**

```
开发人员A：新功能开发 40%
开发人员B：GM1模块 30%
开发人员C：平台维护 100%
```

**Processing:**

- "新功能开发" - no explicit match → Saas软件
- "GM1模块" - contains GM1 → Saas软件
- "平台维护" - no explicit match → Saas软件

All classify to Saas软件, total: (0.4×5) + (0.3×5) + (1.0×5) = 9.0人日

## Output Guidelines

1. Always provide table in markdown format where empty cells indicate merge requirements
2. Include aggregated person-day totals for each business line in the first row only
3. Maintain original work content and project status descriptions
4. Do not include personal names in any table column
5. Sort by business line to group merged cells together
6. Use consistent number formatting (one decimal place for person-days)
7. **CRITICAL:** Do NOT add any text like "(行合并)" in the output - keep cells clean

## Example Complete Workflow

**User Input:**

```
本周工作汇总：
- 张三：GM1用户模块 30%，完成登录功能开发，按计划推进
- 李四：客商平台权限 2人日，完成权限管理升级，已上线
- 王五：GM2订单系统 50%，订单流程优化，存在性能问题需优化
- 赵六：系统维护 20%，日常bug修复，正常
- 孙七：DTC渠道 1.5人日，渠道对接开发，测试阶段
```

**Output:**

```
| 小组/业务线 | 本期实际投入资源 | 项目/迭代 | 本期工作内容 | 项目进度/风险 |
|:-----------|:---------------|:---------|:-----------|:------------|
| Saas软件 | 2.5人日 | GM1用户模块 | 完成登录功能开发 | 按计划推进 |
| | | 系统维护 | 日常bug修复 | 正常 |
| 客商 | 2.0人日 | 客商平台权限 | 完成权限管理升级 | 已上线 |
| 履约 | 2.5人日 | GM2订单系统 | 订单流程优化 | 存在性能问题需优化 |
| DTC | 1.5人日 | DTC渠道 | 渠道对接开发 | 测试阶段 |
```

| DTC (行合并) | 1.5人日 (行合并) | DTC渠道 | 渠道对接开发 | 测试阶段 |

```

```
