#!/usr/bin/env node
/**
 * Codebase Scanner - 全量索引模式
 *
 * 暴力扫描项目中所有文件，提取所有 import 语句，生成完整的"项目物资清单"
 * 不依赖任何预设关键词，数据驱动分析
 *
 * 使用方式：
 *   node codebase-scanner.js [options]
 *
 * 选项：
 *   --dir <path>        要扫描的目录，默认为当前目录
 *   --output <path>     输出文件路径，默认为 /tmp/_codebase_analysis.json
 */

const fs = require("fs");
const path = require("path");

// 解析命令行参数
const args = process.argv.slice(2);
const options = {
  dir: ".",
  output: "/tmp/_codebase_analysis.json",
};

for (let i = 0; i < args.length; i++) {
  switch (args[i]) {
    case "--dir":
      options.dir = args[++i];
      break;
    case "--output":
      options.output = args[++i];
      break;
  }
}

// 排除的目录
const EXCLUDE_DIRS = new Set([
  "node_modules",
  "dist",
  "build",
  ".next",
  ".nuxt",
  ".git",
  "coverage",
  ".cache",
  ".turbo",
  ".vercel",
  ".output",
  "__pycache__",
  "venv",
  ".venv",
  "env",
  ".umi",
  ".umi-production",
]);

// 排除的文件模式
const EXCLUDE_FILE_PATTERNS = [
  /\.min\.js$/,
  /\.bundle\.js$/,
  /\.map$/,
  /\.lock$/,
  /package-lock\.json$/,
  /yarn\.lock$/,
  /pnpm-lock\.yaml$/,
  /\.d\.ts$/, // 类型声明文件通常不包含使用示例
];

// 代码文件扩展名
const CODE_EXTENSIONS = new Set([
  ".ts",
  ".tsx",
  ".js",
  ".jsx",
  ".vue",
  ".svelte",
]);

// 样式文件扩展名
const STYLE_EXTENSIONS = new Set([".css", ".scss", ".less", ".sass", ".styl"]);

// 配置文件扩展名
const CONFIG_EXTENSIONS = new Set([".json", ".yaml", ".yml", ".toml"]);

// ============================================
// 全量索引：提取所有 import 语句
// ============================================

/**
 * 解析文件中的所有 import 语句
 * 返回格式: [{ source: 'react', imports: ['useState', 'useEffect'], type: 'named' }, ...]
 */
function parseImports(content, filePath) {
  const imports = [];

  // 1. ES6 named imports: import { X, Y } from 'source'
  const namedImportRegex = /import\s*\{([^}]+)\}\s*from\s*['"]([^'"]+)['"]/g;
  let match;
  while ((match = namedImportRegex.exec(content)) !== null) {
    const importedItems = match[1]
      .split(",")
      .map((item) => {
        // 处理 as 别名: X as Y
        const parts = item.trim().split(/\s+as\s+/);
        return {
          original: parts[0].trim(),
          alias: parts[1]?.trim() || parts[0].trim(),
        };
      })
      .filter((item) => item.original);

    imports.push({
      source: match[2],
      imports: importedItems,
      type: "named",
      raw: match[0],
    });
  }

  // 2. Default imports: import X from 'source'
  const defaultImportRegex =
    /import\s+([A-Za-z_$][\w$]*)\s+from\s*['"]([^'"]+)['"]/g;
  while ((match = defaultImportRegex.exec(content)) !== null) {
    // 排除已经被 named import 匹配的（避免重复）
    if (!match[0].includes("{")) {
      imports.push({
        source: match[2],
        imports: [{ original: "default", alias: match[1] }],
        type: "default",
        raw: match[0],
      });
    }
  }

  // 3. Namespace imports: import * as X from 'source'
  const namespaceImportRegex =
    /import\s*\*\s*as\s+(\w+)\s+from\s*['"]([^'"]+)['"]/g;
  while ((match = namespaceImportRegex.exec(content)) !== null) {
    imports.push({
      source: match[2],
      imports: [{ original: "*", alias: match[1] }],
      type: "namespace",
      raw: match[0],
    });
  }

  // 4. Side effect imports: import 'source'
  const sideEffectImportRegex = /import\s*['"]([^'"]+)['"]\s*;?/g;
  while ((match = sideEffectImportRegex.exec(content)) !== null) {
    // 排除已经被其他模式匹配的
    if (
      !match[0].includes("from") &&
      !match[0].includes("{") &&
      !match[0].includes("*")
    ) {
      imports.push({
        source: match[1],
        imports: [],
        type: "side-effect",
        raw: match[0],
      });
    }
  }

  // 5. Dynamic imports: import('source') 或 require('source')
  const dynamicImportRegex = /(?:import|require)\s*\(\s*['"]([^'"]+)['"]\s*\)/g;
  while ((match = dynamicImportRegex.exec(content)) !== null) {
    imports.push({
      source: match[1],
      imports: [],
      type: "dynamic",
      raw: match[0],
    });
  }

  return imports;
}

/**
 * 提取文件中的组件使用（JSX 标签）
 */
function parseJSXComponents(content) {
  const components = new Map();

  // 匹配 JSX 组件标签: <ComponentName 或 <Component.SubComponent
  const jsxRegex =
    /<([A-Z][a-zA-Z0-9]*(?:\.[A-Z][a-zA-Z0-9]*)?)\s*(?:[^>]*?)(?:\/?>)/g;
  let match;
  while ((match = jsxRegex.exec(content)) !== null) {
    const componentName = match[1];
    components.set(componentName, (components.get(componentName) || 0) + 1);
  }

  return components;
}

/**
 * 提取 Hooks 使用
 */
function parseHooksUsage(content) {
  const hooks = new Map();

  // 匹配 useXxx( 形式的 Hook 调用
  const hooksRegex = /\b(use[A-Z][a-zA-Z0-9]*)\s*\(/g;
  let match;
  while ((match = hooksRegex.exec(content)) !== null) {
    const hookName = match[1];
    hooks.set(hookName, (hooks.get(hookName) || 0) + 1);
  }

  return hooks;
}

/**
 * 提取样式类名使用
 */
function parseStyleClasses(content) {
  const classes = new Map();

  // className="xxx" 或 className='xxx'
  const classNameRegex = /className\s*=\s*["']([^"']+)["']/g;
  let match;
  while ((match = classNameRegex.exec(content)) !== null) {
    const classNames = match[1].split(/\s+/).filter((c) => c);
    for (const className of classNames) {
      classes.set(className, (classes.get(className) || 0) + 1);
    }
  }

  // className={styles.xxx} (CSS Modules)
  const cssModulesRegex = /className\s*=\s*\{?\s*styles\.(\w+)\s*\}?/g;
  while ((match = cssModulesRegex.exec(content)) !== null) {
    const className = `[CSS Module] ${match[1]}`;
    classes.set(className, (classes.get(className) || 0) + 1);
  }

  return classes;
}

// ============================================
// 文件扫描
// ============================================

function shouldExcludeFile(filePath) {
  return EXCLUDE_FILE_PATTERNS.some((pattern) => pattern.test(filePath));
}

function scanDirectory(dir, files = []) {
  if (!fs.existsSync(dir)) return files;

  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        if (!EXCLUDE_DIRS.has(entry.name)) {
          scanDirectory(fullPath, files);
        }
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name);
        if (
          (CODE_EXTENSIONS.has(ext) || STYLE_EXTENSIONS.has(ext)) &&
          !shouldExcludeFile(entry.name)
        ) {
          files.push(fullPath);
        }
      }
    }
  } catch (e) {
    console.error(`Error scanning ${dir}: ${e.message}`);
  }

  return files;
}

// ============================================
// 主分析逻辑
// ============================================

function analyzeFile(filePath, rootDir) {
  const content = fs.readFileSync(filePath, "utf-8");
  const relativePath = path.relative(rootDir, filePath);
  const ext = path.extname(filePath);
  const lines = content.split("\n").length;

  const result = {
    path: relativePath,
    extension: ext,
    lines,
    imports: [],
    jsxComponents: {},
    hooks: {},
    styleClasses: {},
  };

  // 只对代码文件进行详细分析
  if (CODE_EXTENSIONS.has(ext)) {
    // 提取所有 import
    result.imports = parseImports(content, filePath);

    // 提取 JSX 组件使用
    const jsxComponents = parseJSXComponents(content);
    result.jsxComponents = Object.fromEntries(jsxComponents);

    // 提取 Hooks 使用
    const hooks = parseHooksUsage(content);
    result.hooks = Object.fromEntries(hooks);

    // 提取样式类名
    const styleClasses = parseStyleClasses(content);
    result.styleClasses = Object.fromEntries(styleClasses);
  }

  return result;
}

function aggregateResults(fileResults) {
  const summary = {
    totalFiles: fileResults.length,
    totalLines: 0,
    byExtension: {},
    byDirectory: {},

    // 全量索引结果
    importSources: {}, // 所有导入来源及其使用次数
    importedItems: {}, // 所有导入项及其使用次数
    jsxComponents: {}, // 所有 JSX 组件及其使用次数
    hooks: {}, // 所有 Hooks 及其使用次数
    styleClasses: {}, // 所有样式类名及其使用次数

    // 每个导入项的使用位置（用于 S2 查找范例）
    importUsageMap: {}, // { 'TableTemplatePro': ['src/pages/a.tsx', 'src/pages/b.tsx', ...] }
    componentUsageMap: {}, // { 'Modal': ['src/pages/a.tsx', ...] }
    hookUsageMap: {}, // { 'useRequest': ['src/pages/a.tsx', ...] }
  };

  for (const file of fileResults) {
    // 基础统计
    summary.totalLines += file.lines;
    summary.byExtension[file.extension] =
      (summary.byExtension[file.extension] || 0) + 1;

    const topDir = file.path.split(path.sep)[0] || ".";
    summary.byDirectory[topDir] = (summary.byDirectory[topDir] || 0) + 1;

    // 汇总 imports
    for (const imp of file.imports) {
      // 统计导入来源
      summary.importSources[imp.source] =
        (summary.importSources[imp.source] || 0) + 1;

      // 统计每个导入项
      for (const item of imp.imports) {
        const key = `${item.alias} (from ${imp.source})`;
        summary.importedItems[key] = (summary.importedItems[key] || 0) + 1;

        // 记录使用位置
        if (!summary.importUsageMap[key]) {
          summary.importUsageMap[key] = [];
        }
        if (!summary.importUsageMap[key].includes(file.path)) {
          summary.importUsageMap[key].push(file.path);
        }
      }
    }

    // 汇总 JSX 组件
    for (const [comp, count] of Object.entries(file.jsxComponents)) {
      summary.jsxComponents[comp] = (summary.jsxComponents[comp] || 0) + count;

      if (!summary.componentUsageMap[comp]) {
        summary.componentUsageMap[comp] = [];
      }
      if (!summary.componentUsageMap[comp].includes(file.path)) {
        summary.componentUsageMap[comp].push(file.path);
      }
    }

    // 汇总 Hooks
    for (const [hook, count] of Object.entries(file.hooks)) {
      summary.hooks[hook] = (summary.hooks[hook] || 0) + count;

      if (!summary.hookUsageMap[hook]) {
        summary.hookUsageMap[hook] = [];
      }
      if (!summary.hookUsageMap[hook].includes(file.path)) {
        summary.hookUsageMap[hook].push(file.path);
      }
    }

    // 汇总样式类名
    for (const [cls, count] of Object.entries(file.styleClasses)) {
      summary.styleClasses[cls] = (summary.styleClasses[cls] || 0) + count;
    }
  }

  // 按使用次数排序
  const sortByCount = (obj) => {
    return Object.entries(obj)
      .sort((a, b) => b[1] - a[1])
      .reduce((acc, [k, v]) => ({ ...acc, [k]: v }), {});
  };

  summary.importSources = sortByCount(summary.importSources);
  summary.importedItems = sortByCount(summary.importedItems);
  summary.jsxComponents = sortByCount(summary.jsxComponents);
  summary.hooks = sortByCount(summary.hooks);

  return summary;
}

// ============================================
// 主函数
// ============================================

function main() {
  console.log(`=== Codebase Scanner (全量索引模式) ===`);
  console.log(`Scanning: ${path.resolve(options.dir)}`);
  console.log(`Output: ${options.output}`);
  console.log();

  // 扫描文件
  const files = scanDirectory(options.dir);
  console.log(`Found ${files.length} files to analyze`);

  if (files.length === 0) {
    console.log("No files found to analyze");
    process.exit(0);
  }

  // 分析每个文件
  const fileResults = [];
  for (let i = 0; i < files.length; i++) {
    try {
      const result = analyzeFile(files[i], options.dir);
      fileResults.push(result);
    } catch (e) {
      console.error(`Error analyzing ${files[i]}: ${e.message}`);
    }

    // 进度显示
    if ((i + 1) % 100 === 0) {
      console.log(`Analyzed ${i + 1}/${files.length} files...`);
    }
  }

  // 汇总结果
  const summary = aggregateResults(fileResults);

  // 生成输出
  const output = {
    scanTime: new Date().toISOString(),
    rootDir: path.resolve(options.dir),
    summary,
    files: fileResults, // 包含每个文件的详细信息，供 S2 使用
  };

  // 写入文件
  fs.writeFileSync(options.output, JSON.stringify(output, null, 2));

  // 打印摘要
  console.log(`\n=== 扫描完成 ===`);
  console.log(`总文件数: ${summary.totalFiles}`);
  console.log(`总代码行数: ${summary.totalLines}`);
  console.log(`\n导入来源 TOP 20:`);
  Object.entries(summary.importSources)
    .slice(0, 20)
    .forEach(([source, count]) => {
      console.log(`  ${source}: ${count} 次`);
    });

  console.log(`\nJSX 组件 TOP 20:`);
  Object.entries(summary.jsxComponents)
    .slice(0, 20)
    .forEach(([comp, count]) => {
      console.log(`  <${comp}>: ${count} 次`);
    });

  console.log(`\nHooks TOP 20:`);
  Object.entries(summary.hooks)
    .slice(0, 20)
    .forEach(([hook, count]) => {
      console.log(`  ${hook}(): ${count} 次`);
    });

  console.log(`\n输出文件: ${options.output}`);
}

main();
