#!/usr/bin/env node
/**
 * Sample Extractor - 代码示例提取脚本
 *
 * 用于从大型代码库中智能抽样，提取代表性的代码示例
 * 供 AI Agent 进行定性分析（理解代码风格、模式等）
 *
 * 使用方式：
 *   node sample-extractor.js [options]
 *
 * 选项：
 *   --dir <path>        要扫描的目录，默认为当前目录
 *   --output <path>     输出文件路径，默认为 _code_samples.json
 *   --max-samples <n>   最大抽样文件数，默认 10
 *   --analysis <path>   使用 codebase-scanner.js 的分析结果来智能选择样本
 */

const fs = require("fs");
const path = require("path");

// 解析命令行参数
const args = process.argv.slice(2);
const options = {
  dir: ".",
  output: "_code_samples.json",
  maxSamples: 10,
  analysisFile: null,
};

for (let i = 0; i < args.length; i++) {
  switch (args[i]) {
    case "--dir":
      options.dir = args[++i];
      break;
    case "--output":
      options.output = args[++i];
      break;
    case "--max-samples":
      options.maxSamples = parseInt(args[++i], 10);
      break;
    case "--analysis":
      options.analysisFile = args[++i];
      break;
  }
}

// 关键文件模式 - 用于理解项目结构和风格
const KEY_FILE_PATTERNS = [
  // 入口文件
  {
    pattern: /^src\/(index|main|app)\.(ts|tsx|js|jsx)$/,
    priority: 10,
    category: "entry",
  },
  {
    pattern: /^(index|main|app)\.(ts|tsx|js|jsx)$/,
    priority: 9,
    category: "entry",
  },

  // 布局文件
  {
    pattern: /layouts?\/(index|default|root)\.(ts|tsx|js|jsx|vue)$/,
    priority: 8,
    category: "layout",
  },
  { pattern: /_app\.(ts|tsx|js|jsx)$/, priority: 8, category: "layout" },
  { pattern: /app\/layout\.(ts|tsx|js|jsx)$/, priority: 8, category: "layout" },

  // 路由配置
  {
    pattern: /router\/(index|routes)\.(ts|tsx|js|jsx)$/,
    priority: 8,
    category: "routing",
  },
  { pattern: /routes\.(ts|tsx|js|jsx)$/, priority: 7, category: "routing" },

  // 状态管理
  {
    pattern: /store\/(index|root)\.(ts|tsx|js|jsx)$/,
    priority: 7,
    category: "state",
  },
  { pattern: /stores?\/\w+\.(ts|tsx|js|jsx)$/, priority: 6, category: "state" },

  // API 封装
  {
    pattern: /(api|services?|request)\/(index|client|http)\.(ts|tsx|js|jsx)$/,
    priority: 7,
    category: "api",
  },
  {
    pattern: /utils?\/(request|http|fetch)\.(ts|tsx|js|jsx)$/,
    priority: 6,
    category: "api",
  },

  // 组件示例
  {
    pattern: /components?\/[A-Z]\w+\/(index|[A-Z]\w+)\.(ts|tsx|js|jsx|vue)$/,
    priority: 5,
    category: "component",
  },
  {
    pattern: /components?\/[A-Z]\w+\.(ts|tsx|js|jsx|vue)$/,
    priority: 5,
    category: "component",
  },

  // 页面示例
  {
    pattern: /pages?\/(index|home|dashboard)\.(ts|tsx|js|jsx|vue)$/,
    priority: 6,
    category: "page",
  },
  { pattern: /app\/page\.(ts|tsx|js|jsx)$/, priority: 6, category: "page" },

  // Hooks
  {
    pattern: /hooks?\/use\w+\.(ts|tsx|js|jsx)$/,
    priority: 5,
    category: "hook",
  },
  {
    pattern: /composables?\/use\w+\.(ts|tsx|js|jsx)$/,
    priority: 5,
    category: "hook",
  },

  // 类型定义
  {
    pattern: /types?\/(index|global|common)\.(ts|d\.ts)$/,
    priority: 4,
    category: "types",
  },

  // 样式
  {
    pattern: /styles?\/(global|main|index)\.(css|scss|less)$/,
    priority: 4,
    category: "styles",
  },
  { pattern: /tailwind\.config\.(js|ts)$/, priority: 5, category: "styles" },
];

// 排除的目录
const EXCLUDE_DIRS = [
  "node_modules",
  "dist",
  "build",
  ".next",
  ".nuxt",
  ".git",
  "coverage",
  ".cache",
  "__pycache__",
  "venv",
];

// 扫描目录获取所有文件
function scanDirectory(dir, files = []) {
  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      const relativePath = path.relative(options.dir, fullPath);

      if (entry.isDirectory()) {
        if (!EXCLUDE_DIRS.includes(entry.name)) {
          scanDirectory(fullPath, files);
        }
      } else if (entry.isFile()) {
        files.push(relativePath);
      }
    }
  } catch (e) {
    // 忽略访问错误
  }

  return files;
}

// 根据模式匹配文件并排序
function matchAndRankFiles(files) {
  const rankedFiles = [];

  for (const file of files) {
    const normalizedPath = file.replace(/\\/g, "/");

    for (const { pattern, priority, category } of KEY_FILE_PATTERNS) {
      if (pattern.test(normalizedPath)) {
        rankedFiles.push({
          path: file,
          priority,
          category,
        });
        break; // 每个文件只匹配一个模式
      }
    }
  }

  // 按优先级排序
  rankedFiles.sort((a, b) => b.priority - a.priority);

  return rankedFiles;
}

// 确保每个类别至少有一个样本
function selectDiverseSamples(rankedFiles, maxSamples) {
  const selected = [];
  const categories = new Set();
  const seenPaths = new Set();

  // 第一轮：每个类别选一个最高优先级的
  for (const file of rankedFiles) {
    if (!categories.has(file.category) && !seenPaths.has(file.path)) {
      selected.push(file);
      categories.add(file.category);
      seenPaths.add(file.path);

      if (selected.length >= maxSamples) break;
    }
  }

  // 第二轮：如果还有名额，按优先级补充
  if (selected.length < maxSamples) {
    for (const file of rankedFiles) {
      if (!seenPaths.has(file.path)) {
        selected.push(file);
        seenPaths.add(file.path);

        if (selected.length >= maxSamples) break;
      }
    }
  }

  return selected;
}

// 提取文件内容的关键部分
function extractFileContent(filePath, maxLines = 150) {
  const fullPath = path.join(options.dir, filePath);
  const content = fs.readFileSync(fullPath, "utf-8");
  const lines = content.split("\n");

  // 如果文件较短，返回全部
  if (lines.length <= maxLines) {
    return {
      content,
      truncated: false,
      totalLines: lines.length,
    };
  }

  // 智能截取：保留开头（imports、类型定义）和中间的主要逻辑
  const headLines = Math.min(50, Math.floor(maxLines * 0.4));
  const tailLines = Math.min(30, Math.floor(maxLines * 0.2));
  const midLines = maxLines - headLines - tailLines;

  const head = lines.slice(0, headLines);
  const midStart = Math.floor((lines.length - midLines) / 2);
  const mid = lines.slice(midStart, midStart + midLines);
  const tail = lines.slice(-tailLines);

  const truncatedContent = [
    ...head,
    "",
    `// ... [省略 ${midStart - headLines} 行] ...`,
    "",
    ...mid,
    "",
    `// ... [省略 ${lines.length - midStart - midLines - tailLines} 行] ...`,
    "",
    ...tail,
  ].join("\n");

  return {
    content: truncatedContent,
    truncated: true,
    totalLines: lines.length,
    extractedLines: maxLines,
  };
}

// 根据分析结果选择有代表性的文件
function selectFromAnalysis(analysisData, allFiles) {
  const samples = [];
  const analysis = analysisData.summary || analysisData;

  // 如果检测到特定技术，优先选择相关文件
  const techs = analysis.technologies || {};

  // 选择策略
  const strategies = [];

  // 状态管理文件
  if (techs.stateManagement && techs.stateManagement.length > 0) {
    strategies.push({
      pattern: /stores?\/|redux|zustand|pinia|mobx/i,
      category: "state",
      max: 2,
    });
  }

  // API 相关文件
  if (techs.apiClient && techs.apiClient.length > 0) {
    strategies.push({
      pattern: /api|services?|request|http/i,
      category: "api",
      max: 2,
    });
  }

  // 根据框架选择组件
  if (techs.framework === "React") {
    strategies.push({
      pattern: /components?\/.*\.(tsx|jsx)$/i,
      category: "component",
      max: 3,
    });
  } else if (techs.framework === "Vue") {
    strategies.push({
      pattern: /components?\/.*\.vue$/i,
      category: "component",
      max: 3,
    });
  }

  // 应用策略
  for (const strategy of strategies) {
    let count = 0;
    for (const file of allFiles) {
      if (strategy.pattern.test(file) && count < strategy.max) {
        samples.push({
          path: file,
          category: strategy.category,
          reason: `Matches ${strategy.category} pattern based on detected technologies`,
        });
        count++;
      }
    }
  }

  return samples;
}

// 主函数
function main() {
  console.log(`Scanning directory: ${path.resolve(options.dir)}`);

  // 扫描所有文件
  const allFiles = scanDirectory(options.dir);
  console.log(`Found ${allFiles.length} total files`);

  // 匹配和排序
  const rankedFiles = matchAndRankFiles(allFiles);
  console.log(`Matched ${rankedFiles.length} files against key patterns`);

  // 如果有分析结果，结合使用
  let additionalSamples = [];
  if (options.analysisFile && fs.existsSync(options.analysisFile)) {
    console.log(`Loading analysis from ${options.analysisFile}`);
    const analysisData = JSON.parse(
      fs.readFileSync(options.analysisFile, "utf-8"),
    );
    additionalSamples = selectFromAnalysis(analysisData, allFiles);
    console.log(
      `Selected ${additionalSamples.length} additional samples from analysis`,
    );
  }

  // 合并并选择最终样本
  const allRanked = [...rankedFiles, ...additionalSamples];
  const selectedFiles = selectDiverseSamples(allRanked, options.maxSamples);

  console.log(`\nSelected ${selectedFiles.length} files for sampling:`);

  // 提取内容
  const samples = [];
  for (const file of selectedFiles) {
    console.log(`  - [${file.category}] ${file.path}`);

    try {
      const extracted = extractFileContent(file.path);
      samples.push({
        path: file.path,
        category: file.category,
        priority: file.priority,
        ...extracted,
      });
    } catch (e) {
      console.log(`    Error reading file: ${e.message}`);
    }
  }

  // 输出结果
  const output = {
    extractTime: new Date().toISOString(),
    rootDir: path.resolve(options.dir),
    totalFilesScanned: allFiles.length,
    samplesExtracted: samples.length,
    samples,
  };

  fs.writeFileSync(options.output, JSON.stringify(output, null, 2));
  console.log(`\nWritten samples to ${options.output}`);

  // 输出类别统计
  const categoryCount = {};
  for (const sample of samples) {
    categoryCount[sample.category] = (categoryCount[sample.category] || 0) + 1;
  }

  console.log("\n=== Sample Categories ===");
  for (const [category, count] of Object.entries(categoryCount)) {
    console.log(`  ${category}: ${count}`);
  }
}

main();
