#!/usr/bin/env node
/**
 * Pattern Extractor - 自适应模式提取
 *
 * 根据 S1 阶段的全量索引结果，自适应地提取每个组件/库的使用示例
 * 不依赖预设模式，完全由数据驱动
 *
 * 使用方式：
 *   node pattern-extractor.js [options]
 *
 * 选项：
 *   --dir <path>        项目目录，默认为当前目录
 *   --analysis <path>   S1 输出的分析结果文件路径（必须）
 *   --output <path>     输出文件路径，默认为 /tmp/_dev_patterns.json
 *   --max-examples <n>  每个组件/库最多提取几个示例，默认 3
 */

const fs = require("fs");
const path = require("path");

// 解析命令行参数
const args = process.argv.slice(2);
const options = {
  dir: ".",
  analysisFile: "/tmp/_codebase_analysis.json",
  output: "/tmp/_dev_patterns.json",
  maxExamples: 3,
};

for (let i = 0; i < args.length; i++) {
  switch (args[i]) {
    case "--dir":
      options.dir = args[++i];
      break;
    case "--analysis":
      options.analysisFile = args[++i];
      break;
    case "--output":
      options.output = args[++i];
      break;
    case "--max-examples":
      options.maxExamples = parseInt(args[++i], 10);
      break;
  }
}

// ============================================
// 加载 S1 分析结果
// ============================================

function loadAnalysis() {
  if (!fs.existsSync(options.analysisFile)) {
    console.error(`错误: 找不到分析文件 ${options.analysisFile}`);
    console.error(`请先运行 S1 阶段的 codebase-scanner.js`);
    process.exit(1);
  }

  return JSON.parse(fs.readFileSync(options.analysisFile, "utf-8"));
}

// ============================================
// 智能选择示例文件
// ============================================

/**
 * 为指定的组件/库选择最佳示例文件
 * 策略：
 * 1. 优先选择代码行数适中的文件（50-300行）
 * 2. 优先选择 pages/ 下的文件（更完整的业务逻辑）
 * 3. 避免选择 index.ts 等纯导出文件
 */
function selectBestExamples(usageMap, allFiles, maxExamples) {
  const candidates = [];

  for (const filePath of usageMap) {
    const fileInfo = allFiles.find((f) => f.path === filePath);
    if (!fileInfo) continue;

    let score = 0;

    // 代码行数评分（50-300行最佳）
    if (fileInfo.lines >= 50 && fileInfo.lines <= 300) {
      score += 30;
    } else if (fileInfo.lines >= 30 && fileInfo.lines <= 500) {
      score += 20;
    } else if (fileInfo.lines > 500) {
      score += 5; // 太长的文件不太适合作为示例
    }

    // 文件位置评分
    if (filePath.includes("pages/") || filePath.includes("views/")) {
      score += 20; // 页面文件通常更完整
    } else if (filePath.includes("components/")) {
      score += 15; // 组件文件也不错
    }

    // 排除纯导出文件
    if (/index\.(ts|tsx|js|jsx)$/.test(filePath) && fileInfo.lines < 20) {
      score -= 50;
    }

    // 排除测试文件
    if (/\.(test|spec)\.(ts|tsx|js|jsx)$/.test(filePath)) {
      score -= 100;
    }

    // 使用了更多组件/hooks 的文件可能更具代表性
    const componentCount = Object.keys(fileInfo.jsxComponents || {}).length;
    const hookCount = Object.keys(fileInfo.hooks || {}).length;
    score += Math.min(componentCount * 2, 10);
    score += Math.min(hookCount * 2, 10);

    candidates.push({ filePath, score, fileInfo });
  }

  // 按分数排序，取前 N 个
  candidates.sort((a, b) => b.score - a.score);
  return candidates.slice(0, maxExamples);
}

// ============================================
// 提取文件的关键代码段
// ============================================

/**
 * 提取文件中与目标组件相关的代码段
 */
function extractRelevantCode(filePath, targetComponent, maxLines = 200) {
  const fullPath = path.join(options.dir, filePath);
  if (!fs.existsSync(fullPath)) return null;

  const content = fs.readFileSync(fullPath, "utf-8");
  const lines = content.split("\n");

  // 如果文件较短，返回全部
  if (lines.length <= maxLines) {
    return {
      fullContent: content,
      truncated: false,
      totalLines: lines.length,
    };
  }

  // 智能截取：找到目标组件使用的位置，提取上下文
  const relevantRanges = [];

  // 查找 import 语句
  for (let i = 0; i < lines.length; i++) {
    if (lines[i].includes("import") && lines[i].includes(targetComponent)) {
      relevantRanges.push({ start: Math.max(0, i - 2), end: i + 2 });
    }
  }

  // 查找组件使用位置
  for (let i = 0; i < lines.length; i++) {
    if (
      lines[i].includes(`<${targetComponent}`) ||
      lines[i].includes(`${targetComponent}(`)
    ) {
      // 向上找到函数/组件定义的开始
      let start = i;
      for (let j = i; j >= 0; j--) {
        if (/^(export\s+)?(const|function|class)\s+/.test(lines[j])) {
          start = j;
          break;
        }
      }
      // 向下找到代码块结束
      let end = i;
      let braceCount = 0;
      for (let j = start; j < lines.length; j++) {
        braceCount += (lines[j].match(/{/g) || []).length;
        braceCount -= (lines[j].match(/}/g) || []).length;
        if (braceCount <= 0 && j > start + 5) {
          end = j;
          break;
        }
        if (j - start > 100) {
          end = j;
          break;
        }
      }
      relevantRanges.push({ start, end });
    }
  }

  // 合并重叠的范围
  if (relevantRanges.length === 0) {
    // 没找到相关代码，返回文件开头
    return {
      fullContent:
        lines.slice(0, maxLines).join("\n") +
        "\n// ... (截取前 " +
        maxLines +
        " 行)",
      truncated: true,
      totalLines: lines.length,
    };
  }

  // 合并范围并提取
  relevantRanges.sort((a, b) => a.start - b.start);
  const mergedRanges = [];
  for (const range of relevantRanges) {
    if (
      mergedRanges.length === 0 ||
      range.start > mergedRanges[mergedRanges.length - 1].end + 5
    ) {
      mergedRanges.push({ ...range });
    } else {
      mergedRanges[mergedRanges.length - 1].end = Math.max(
        mergedRanges[mergedRanges.length - 1].end,
        range.end,
      );
    }
  }

  // 提取代码
  const extractedLines = [];
  let lastEnd = -1;
  for (const range of mergedRanges) {
    if (lastEnd >= 0 && range.start > lastEnd + 1) {
      extractedLines.push(`\n// ... (省略 ${range.start - lastEnd - 1} 行)\n`);
    }
    for (let i = range.start; i <= range.end && i < lines.length; i++) {
      extractedLines.push(lines[i]);
    }
    lastEnd = range.end;
  }

  return {
    fullContent: extractedLines.join("\n"),
    truncated: true,
    totalLines: lines.length,
    extractedLines: extractedLines.length,
  };
}

// ============================================
// 分类组件/库
// ============================================

/**
 * 将组件/库分类到不同的开发场景
 */
function categorizeItems(analysis) {
  const categories = {
    // UI 组件库（表单、表格、弹窗等）
    uiComponents: {},
    // 状态管理
    stateManagement: {},
    // 路由
    routing: {},
    // 数据请求
    dataFetching: {},
    // Hooks
    hooks: {},
    // 工具函数
    utils: {},
    // 项目自定义组件
    customComponents: {},
    // 样式相关
    styling: {},
  };

  const {
    importSources,
    importedItems,
    jsxComponents,
    hooks,
    componentUsageMap,
    hookUsageMap,
    importUsageMap,
  } = analysis.summary;

  // 分析 import 来源，自动分类
  for (const [source, count] of Object.entries(importSources)) {
    // UI 库
    if (
      /antd|@ant-design|element-plus|@mui|@chakra-ui|arco-design/.test(source)
    ) {
      categories.uiComponents[source] = { count, type: "library" };
    }
    // 状态管理
    else if (/redux|zustand|mobx|pinia|jotai|recoil|valtio/.test(source)) {
      categories.stateManagement[source] = { count, type: "library" };
    }
    // 路由
    else if (
      /react-router|vue-router|next\/router|next\/navigation/.test(source)
    ) {
      categories.routing[source] = { count, type: "library" };
    }
    // 数据请求
    else if (
      /axios|swr|@tanstack\/react-query|umi-request|ahooks/.test(source)
    ) {
      categories.dataFetching[source] = { count, type: "library" };
    }
    // 项目内部模块
    else if (
      source.startsWith("@/") ||
      source.startsWith("~/") ||
      source.startsWith("./") ||
      source.startsWith("../")
    ) {
      // 判断是 service/api 还是组件
      if (/service|api/.test(source)) {
        categories.dataFetching[source] = { count, type: "internal" };
      } else if (/component|widget/.test(source)) {
        categories.customComponents[source] = { count, type: "internal" };
      } else if (/hook|use/.test(source)) {
        categories.hooks[source] = { count, type: "internal" };
      } else if (/util|helper|lib/.test(source)) {
        categories.utils[source] = { count, type: "internal" };
      } else if (/style|css|less|scss/.test(source)) {
        categories.styling[source] = { count, type: "internal" };
      }
    }
  }

  // 分析 JSX 组件使用
  for (const [comp, count] of Object.entries(jsxComponents)) {
    // 检查是否是常见 UI 库组件
    const isUIComponent =
      /^(Form|Table|Modal|Drawer|Button|Input|Select|DatePicker|Card|List|Tabs|Menu|Dropdown|Popover|Tooltip|Alert|Message|Notification|Spin|Skeleton|Avatar|Badge|Tag|Progress|Steps|Pagination|Breadcrumb|Layout|Row|Col|Space|Divider|Typography|Image|Upload|Checkbox|Radio|Switch|Slider|Rate|Transfer|Tree|TreeSelect|Cascader|TimePicker|Calendar|Carousel|Collapse|Descriptions|Empty|Result|Statistic|Timeline|Anchor|BackTop|Affix|ConfigProvider)/.test(
        comp,
      );

    if (isUIComponent) {
      categories.uiComponents[comp] = {
        count,
        type: "jsx",
        usageFiles: componentUsageMap[comp] || [],
      };
    } else {
      // 自定义组件
      categories.customComponents[comp] = {
        count,
        type: "jsx",
        usageFiles: componentUsageMap[comp] || [],
      };
    }
  }

  // 分析 Hooks 使用
  for (const [hook, count] of Object.entries(hooks)) {
    categories.hooks[hook] = {
      count,
      type: "hook",
      usageFiles: hookUsageMap[hook] || [],
    };
  }

  return categories;
}

// ============================================
// 生成开发模式文档
// ============================================

/**
 * 为每个分类的高频项目提取使用示例
 */
function extractPatterns(analysis, categories) {
  const allFiles = analysis.files;
  const patterns = {};

  for (const [category, items] of Object.entries(categories)) {
    patterns[category] = {
      name: getCategoryName(category),
      items: [],
    };

    // 按使用次数排序
    const sortedItems = Object.entries(items).sort(
      (a, b) => b[1].count - a[1].count,
    );

    for (const [itemName, itemInfo] of sortedItems) {
      // 获取使用该项的文件列表
      let usageFiles = itemInfo.usageFiles || [];

      // 如果没有直接的 usageFiles，尝试从 importUsageMap 获取
      if (usageFiles.length === 0 && analysis.summary.importUsageMap) {
        // 查找包含该 itemName 的 key
        for (const [key, files] of Object.entries(
          analysis.summary.importUsageMap,
        )) {
          if (key.includes(itemName)) {
            usageFiles = usageFiles.concat(files);
          }
        }
      }

      // 如果还是没有，尝试从 componentUsageMap 获取
      if (
        usageFiles.length === 0 &&
        analysis.summary.componentUsageMap &&
        analysis.summary.componentUsageMap[itemName]
      ) {
        usageFiles = analysis.summary.componentUsageMap[itemName];
      }

      // 去重
      usageFiles = [...new Set(usageFiles)];

      if (usageFiles.length === 0) continue;

      // 选择最佳示例文件
      const bestExamples = selectBestExamples(
        usageFiles,
        allFiles,
        options.maxExamples,
      );

      const itemPattern = {
        name: itemName,
        count: itemInfo.count,
        type: itemInfo.type,
        usageFiles: usageFiles.length,
        examples: [],
      };

      // 提取每个示例的代码
      for (const { filePath, score, fileInfo } of bestExamples) {
        const codeExtract = extractRelevantCode(filePath, itemName);
        if (codeExtract) {
          itemPattern.examples.push({
            filePath,
            score,
            lines: fileInfo.lines,
            ...codeExtract,
          });
        }
      }

      if (itemPattern.examples.length > 0) {
        patterns[category].items.push(itemPattern);
      }
    }
  }

  return patterns;
}

function getCategoryName(category) {
  const names = {
    uiComponents: "UI 组件",
    stateManagement: "状态管理",
    routing: "路由",
    dataFetching: "数据请求",
    hooks: "Hooks",
    utils: "工具函数",
    customComponents: "项目自定义组件",
    styling: "样式",
  };
  return names[category] || category;
}

// ============================================
// 生成开发场景示例
// ============================================

/**
 * 根据全量索引数据，识别并提取各种开发场景的示例
 */
function extractDevelopmentScenarios(analysis, categories, patterns) {
  const scenarios = {};

  // 1. 页面开发场景：找一个包含表格/表单的完整页面
  const tableComponents = Object.keys(categories.uiComponents).filter((c) =>
    /Table|List|Pro.*Table/.test(c),
  );
  if (tableComponents.length > 0) {
    const topTable = tableComponents[0];
    const tableUsageFiles = analysis.summary.componentUsageMap[topTable] || [];
    const bestPage = selectBestExamples(tableUsageFiles, analysis.files, 1)[0];
    if (bestPage) {
      scenarios.listPage = {
        name: "列表页开发",
        description: `使用 ${topTable} 的列表页示例`,
        component: topTable,
        example: {
          filePath: bestPage.filePath,
          code: extractRelevantCode(bestPage.filePath, topTable),
        },
      };
    }
  }

  // 2. 表单开发场景：找使用 Form 最多的文件
  const formUsageFiles = analysis.summary.componentUsageMap["Form"] || [];
  if (formUsageFiles.length > 0) {
    const bestForm = selectBestExamples(formUsageFiles, analysis.files, 1)[0];
    if (bestForm) {
      scenarios.formPage = {
        name: "表单开发",
        description: "表单页示例",
        component: "Form",
        example: {
          filePath: bestForm.filePath,
          code: extractRelevantCode(bestForm.filePath, "Form"),
        },
      };
    }
  }

  // 3. 弹窗场景：找使用 Modal/Drawer 的文件
  const modalUsageFiles = [
    ...(analysis.summary.componentUsageMap["Modal"] || []),
    ...(analysis.summary.componentUsageMap["Drawer"] || []),
  ];
  if (modalUsageFiles.length > 0) {
    const bestModal = selectBestExamples(
      [...new Set(modalUsageFiles)],
      analysis.files,
      1,
    )[0];
    if (bestModal) {
      scenarios.modalUsage = {
        name: "弹窗开发",
        description: "Modal/Drawer 使用示例",
        example: {
          filePath: bestModal.filePath,
          code: extractRelevantCode(bestModal.filePath, "Modal"),
        },
      };
    }
  }

  // 4. 接口调用场景：找从 service 目录导入最多的页面文件
  const serviceImports = Object.entries(analysis.summary.importUsageMap || {})
    .filter(([key]) => key.includes("service") || key.includes("api"))
    .flatMap(([, files]) => files);
  if (serviceImports.length > 0) {
    const pageCandidates = serviceImports.filter(
      (f) => f.includes("pages/") || f.includes("views/"),
    );
    if (pageCandidates.length > 0) {
      const bestApiUsage = selectBestExamples(
        [...new Set(pageCandidates)],
        analysis.files,
        1,
      )[0];
      if (bestApiUsage) {
        scenarios.apiUsage = {
          name: "接口调用",
          description: "API 调用示例",
          example: {
            filePath: bestApiUsage.filePath,
            code: extractRelevantCode(bestApiUsage.filePath, "service"),
          },
        };
      }
    }
  }

  // 5. Hooks 使用场景：找自定义 hooks 目录下的文件
  const hookFiles = analysis.files.filter((f) =>
    /hooks?\/use\w+\.(ts|tsx|js|jsx)$/.test(f.path),
  );
  if (hookFiles.length > 0) {
    const bestHook = hookFiles.sort((a, b) => {
      // 优先选择行数适中的
      const scoreA = a.lines >= 20 && a.lines <= 100 ? 100 : 50;
      const scoreB = b.lines >= 20 && b.lines <= 100 ? 100 : 50;
      return scoreB - scoreA;
    })[0];
    if (bestHook) {
      const fullPath = path.join(options.dir, bestHook.path);
      scenarios.customHook = {
        name: "自定义 Hook",
        description: "自定义 Hook 定义示例",
        example: {
          filePath: bestHook.path,
          code: fs.existsSync(fullPath)
            ? {
                fullContent: fs.readFileSync(fullPath, "utf-8"),
                totalLines: bestHook.lines,
              }
            : null,
        },
      };
    }
  }

  // 6. 接口定义场景：找 service 目录下的文件
  const serviceFiles = analysis.files.filter(
    (f) =>
      /service[s]?\/\w+\.(ts|js)$/.test(f.path) && !f.path.includes("request"),
  );
  if (serviceFiles.length > 0) {
    const bestService = serviceFiles.sort((a, b) => b.lines - a.lines)[0]; // 选择内容较多的
    if (bestService) {
      const fullPath = path.join(options.dir, bestService.path);
      scenarios.serviceDefinition = {
        name: "接口定义",
        description: "Service 文件定义示例",
        example: {
          filePath: bestService.path,
          code: fs.existsSync(fullPath)
            ? {
                fullContent: fs.readFileSync(fullPath, "utf-8").slice(0, 5000), // 限制长度
                totalLines: bestService.lines,
              }
            : null,
        },
      };
    }
  }

  // 7. 路由配置场景
  const routeFiles = analysis.files.filter(
    (f) =>
      /routes?\.(ts|tsx|js|jsx)$/.test(f.path) ||
      /router\/index\.(ts|tsx|js|jsx)$/.test(f.path),
  );
  if (routeFiles.length > 0) {
    const routeFile = routeFiles[0];
    const fullPath = path.join(options.dir, routeFile.path);
    scenarios.routeConfig = {
      name: "路由配置",
      description: "路由配置示例",
      example: {
        filePath: routeFile.path,
        code: fs.existsSync(fullPath)
          ? {
              fullContent: fs.readFileSync(fullPath, "utf-8"),
              totalLines: routeFile.lines,
            }
          : null,
      },
    };
  }

  // 8. 样式编写场景
  const styleFiles = analysis.files.filter(
    (f) => /\.(less|scss|css)$/.test(f.path) && !f.path.includes("global"),
  );
  if (styleFiles.length > 0) {
    const bestStyle = styleFiles.sort((a, b) => {
      const scoreA = a.lines >= 30 && a.lines <= 200 ? 100 : 50;
      const scoreB = b.lines >= 30 && b.lines <= 200 ? 100 : 50;
      return scoreB - scoreA;
    })[0];
    if (bestStyle) {
      const fullPath = path.join(options.dir, bestStyle.path);
      scenarios.styleWriting = {
        name: "样式编写",
        description: "样式文件示例",
        example: {
          filePath: bestStyle.path,
          code: fs.existsSync(fullPath)
            ? {
                fullContent: fs.readFileSync(fullPath, "utf-8"),
                totalLines: bestStyle.lines,
              }
            : null,
        },
      };
    }
  }

  return scenarios;
}

// ============================================
// 主函数
// ============================================

function main() {
  console.log(`=== Pattern Extractor (自适应模式) ===`);
  console.log(`分析文件: ${options.analysisFile}`);
  console.log(`项目目录: ${path.resolve(options.dir)}`);
  console.log(`输出文件: ${options.output}`);
  console.log();

  // 加载 S1 分析结果
  const analysis = loadAnalysis();
  console.log(`加载分析结果: ${analysis.summary.totalFiles} 个文件`);

  // 分类组件/库
  console.log(`\n分类组件和库...`);
  const categories = categorizeItems(analysis);

  // 提取模式
  console.log(`提取使用模式...`);
  const patterns = extractPatterns(analysis, categories);

  // 提取开发场景示例
  console.log(`提取开发场景示例...`);
  const scenarios = extractDevelopmentScenarios(analysis, categories, patterns);

  // 生成输出
  const output = {
    extractTime: new Date().toISOString(),
    rootDir: path.resolve(options.dir),
    analysisFile: options.analysisFile,

    // 全量物资清单
    inventory: {
      importSources: analysis.summary.importSources,
      jsxComponents: analysis.summary.jsxComponents,
      hooks: analysis.summary.hooks,
    },

    // 分类后的模式
    categories: patterns,

    // 开发场景示例（最重要的部分）
    developmentScenarios: scenarios,

    // 统计
    summary: {
      totalImportSources: Object.keys(analysis.summary.importSources).length,
      totalJsxComponents: Object.keys(analysis.summary.jsxComponents).length,
      totalHooks: Object.keys(analysis.summary.hooks).length,
      scenariosExtracted: Object.keys(scenarios).length,
    },
  };

  // 写入文件
  fs.writeFileSync(options.output, JSON.stringify(output, null, 2));

  // 打印摘要
  console.log(`\n=== 提取完成 ===`);
  console.log(`导入来源数: ${output.summary.totalImportSources}`);
  console.log(`JSX 组件数: ${output.summary.totalJsxComponents}`);
  console.log(`Hooks 数: ${output.summary.totalHooks}`);
  console.log(`开发场景数: ${output.summary.scenariosExtracted}`);

  console.log(`\n已提取的开发场景:`);
  for (const [key, scenario] of Object.entries(scenarios)) {
    console.log(
      `  - ${scenario.name}: ${scenario.example?.filePath || "无示例"}`,
    );
  }

  console.log(`\n输出文件: ${options.output}`);
}

main();
