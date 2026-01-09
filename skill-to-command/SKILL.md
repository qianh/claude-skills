---
name: skill-to-command
description: 自动扫描 ~/.claude/skills 下的所有 skills，并将它们转换为符合 Claude Code 官方规范的 commands。支持命名空间（默认 john），检测已存在的 commands，只生成增量的新 commands。当用户需要将 skills 同步为 commands 时使用。
version: 1.1.0
---

# Skill to Command Converter

你是一个专门将 Claude Code Skills 转换为 Commands 的自动化助手。你的任务是扫描用户的 skills 目录，并为每个 skill 生成对应的 command 文件。

## 核心功能

1. **扫描 Skills**：自动发现 ~/.claude/skills 下的所有 SKILL.md 文件
2. **提取元数据**：从每个 skill 的 frontmatter 中提取 name 和 description
3. **命名空间支持**：生成到指定的子目录（默认：`john`），组织私人 commands
4. **检测冲突**：检查目标命名空间下是否已存在同名 command
5. **增量生成**：只为不存在的 skills 生成新的 command 文件

## 默认配置

- **命名空间**：`john`（所有 commands 生成到 `~/.claude/commands/john/`）
- **用户可覆盖**：在调用时可以指定其他命名空间或使用根目录

## 工作流程

### 1. 扫描 Skills 目录

```bash
# 查找所有 SKILL.md 文件
find ~/.claude/skills -type f -name "SKILL.md"
```

为每个找到的 SKILL.md 文件：

- 读取文件内容
- 解析 frontmatter（YAML 格式，位于 `---` 和 `---` 之间）
- 提取 `name` 和 `description` 字段

### 2. 检测已存在的 Commands

```bash
# 列出指定命名空间下所有已存在的 command 文件
# 默认命名空间：john
ls ~/.claude/commands/john/*.md 2>/dev/null | xargs -n1 basename
```

对于每个 skill name：

- 检查 `~/.claude/commands/john/{name}.md` 是否存在
- 如果存在，跳过该 skill（已有对应 command）
- 如果不存在，标记为待生成

### 3. 生成 Command 文件

对于每个需要生成的 skill，创建对应的 command 文件：

**文件位置**：`~/.claude/commands/john/{skill-name}.md`（默认命名空间）

**文件格式**：

```markdown
---
description: { skill description }
---

{skill description}

使用 Skill 工具调用此 skill：

Use the Skill tool with:

- skill: "{skill-name}"
- args: "{用户提供的参数}"
```

**生成规则**：

1. 使用 skill 的 `description` 作为 command 的 frontmatter description
2. 在 command 正文中说明如何使用 Skill 工具调用该 skill
3. 保持简洁，command 主要作为 skill 的快捷入口

### 4. 输出报告

生成完成后，向用户报告：

```
📊 Skill to Command 转换报告

扫描到的 Skills: {total} 个

已存在的 Commands (跳过): {skipped} 个
{skipped_list}

新生成的 Commands: {generated} 个
{generated_list}

✅ 转换完成！

现在你可以使用以下命令：
{command_usage_examples}
```

## 示例

### Skill 文件示例

文件：`~/.claude/skills/git-commit-helper/SKILL.md`

```markdown
---
name: git-commit-helper
description: 智能 Git 提交助手，自动分析未提交代码变更并生成中文总结
---

# Git Commit Helper

...
```

### 生成的 Command 文件

文件：`~/.claude/commands/john/git-commit-helper.md`

```markdown
---
description: 智能 Git 提交助手，自动分析未提交代码变更并生成中文总结
---

智能 Git 提交助手，自动分析未提交代码变更并生成中文总结，默认使用 feat 类型创建 commit，跳过 lint 检查（--no-verify），直接推送到远端。

使用 Skill 工具调用此 skill：

Use the Skill tool with:

- skill: "git-commit-helper"
- args: "{可选的提交类型，如 fix, docs 等}"
```

### 使用示例

生成后，用户可以通过两种方式使用：

1. **直接调用 command**（推荐）：

   ```
   /git-commit-helper
   ```

2. **通过 Skill 工具**（高级用法）：
   ```
   使用 git-commit-helper skill 进行提交
   ```

## 实现步骤

当用户请求转换 skills 时，按以下步骤执行：

1. **扫描阶段**

   ```bash
   find ~/.claude/skills -type f -name "SKILL.md"
   ```

   - 使用 Bash 工具查找所有 SKILL.md 文件
   - 记录找到的文件路径列表

2. **提取阶段**
   - 对每个 SKILL.md 文件使用 Read 工具读取内容
   - 解析 frontmatter 获取 name 和 description
   - 如果 frontmatter 缺少 name，使用目录名作为 skill name
   - 存储到一个 skills 列表中

3. **检测阶段**

   ```bash
   # 确保命名空间目录存在
   mkdir -p ~/.claude/commands/john

   # 列出命名空间下的现有 command 文件
   ls ~/.claude/commands/john/*.md 2>/dev/null
   ```

   - 列出指定命名空间下所有现有的 command 文件
   - 对比 skill name 和 command 文件名
   - 标记需要生成的 skills

4. **生成阶段**
   - 对每个需要生成的 skill：
     - 使用 Write 工具创建 `~/.claude/commands/john/{name}.md`
     - 按照上述格式填充内容
   - 记录生成的文件列表

5. **报告阶段**
   - 向用户展示转换报告
   - 列出跳过的和新生成的 commands
   - 提供使用示例

## 注意事项

1. **命名冲突**
   - 如果 skill name 已存在对应的 command，跳过不覆盖
   - 这样可以保护用户手动创建的自定义 commands

2. **Frontmatter 解析**
   - Frontmatter 位于文件开头的 `---` 和 `---` 之间
   - 使用 YAML 格式
   - 必须字段：`name`, `description`
   - 可选字段：`version`, `author` 等

3. **路径处理**
   - Skills 目录：`~/.claude/skills/`
   - Commands 目录：`~/.claude/commands/john/` (默认命名空间)
   - 使用绝对路径避免路径错误

4. **错误处理**
   - 如果 SKILL.md 缺少 name 或 description，报告错误但继续处理其他 skills
   - 如果 `~/.claude/commands/john` 不存在，自动创建

5. **增量更新**
   - 只生成新的 commands，不修改已存在的
   - 用户可以多次运行此 skill，只会生成增量内容

## 使用场景

- **初次设置**：用户刚安装了多个 skills，想快速生成对应的 commands
- **增量同步**：用户添加了新的 skills，想更新 commands
- **批量管理**：用户有多个 skills，希望统一管理它们的 command 入口

## 性能优化

- 使用单次 `find` 命令查找所有 SKILL.md，而不是多次文件系统操作
- 批量读取文件，减少工具调用次数
- 只在需要时创建新文件，避免不必要的写操作

## 输出格式

生成报告时使用清晰的格式：

```
📊 Skill to Command 转换报告

✅ 扫描到 8 个 Skills
📁 命名空间：john

⏭️  已存在的 Commands（跳过 3 个）：
   • git-commit-helper → /john/git-commit-helper (user:john)
   • prompt-coach → /john/prompt-coach (user:john)
   • slide-deck → /john/slide-deck (user:john)

🆕 新生成的 Commands（5 个）：
   • prd-to-frontend → /john/prd-to-frontend (user:john)
   • socratic-learning → /john/socratic-learning (user:john)
   • city-image-generator → /john/city-image-generator (user:john)
   • business-flowchart-designer → /john/business-flowchart-designer (user:john)
   • weekly-report-aggregator → /john/weekly-report-aggregator (user:john)

💡 使用方法：
   在对话中输入 /john/skill-name 或直接输入 /skill-name 即可调用
   输入 /john 可以过滤出所有私人 commands

   示例：
   • /john/prd-to-frontend - 将 PRD 和 Swagger 转换为前端代码
   • /john/socratic-learning - 使用苏格拉底式对话学习新知识
   • /john/city-image-generator - 生成城市主题的艺术海报

✅ 转换完成！所有 commands 已保存到 ~/.claude/commands/john/
```

## 自动化增强（可选）

未来可以考虑的增强功能：

1. **双向同步**：当 skill 的 description 更新时，同步更新对应的 command
2. **命名空间**：支持将 skills 按目录分类生成到 commands 子目录
3. **自定义模板**：允许用户自定义 command 生成模板
4. **配置文件**：支持 .skill-to-command.config 文件自定义转换规则

## 总结

这个 skill 让用户能够：

- 快速将所有 skills 转换为 commands
- 通过命名空间组织私人 commands（默认：`john`）
- 通过 `/john/command-name` 调用 skills，或使用 `/john` 过滤
- 保持 skills 和 commands 的同步
- 避免手动创建重复的 command 文件
- 将私人 commands 与系统/项目 commands 分离

节省时间，提高效率！

## 命名空间说明

根据 Claude Code 的 commands 规范：

- 子目录会在命令描述中显示为 `(user:john)`
- 命令可以通过子目录路径调用：`/john/skill-name`
- 也可以直接调用：`/skill-name`（如果没有同名冲突）
- 输入 `/john` 可以触发自动补全，过滤出该命名空间下的所有 commands
