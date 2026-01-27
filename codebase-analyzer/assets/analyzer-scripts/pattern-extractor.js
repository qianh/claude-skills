#!/usr/bin/env node
/**
 * Pattern Extractor - 开发模式提取脚本
 *
 * 按开发场景提取项目中的最佳实践代码示例，生成实操开发手册
 *
 * 使用方式：
 *   node pattern-extractor.js [options]
 *
 * 选项：
 *   --dir <path>        要扫描的目录，默认为当前目录
 *   --output <path>     输出文件路径，默认为 /tmp/_dev_patterns.json
 *   --config <path>     自定义配置文件路径（可选）
 */

const fs = require("fs");
const path = require("path");

// 解析命令行参数
const args = process.argv.slice(2);
const options = {
  dir: ".",
  output: "/tmp/_dev_patterns.json",
  configFile: null,
};

for (let i = 0; i < args.length; i++) {
  switch (args[i]) {
    case "--dir":
      options.dir = args[++i];
      break;
    case "--output":
      options.output = args[++i];
      break;
    case "--config":
      options.configFile = args[++i];
      break;
  }
}

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
  ".umi",
];

// ============================================
// 开发场景配置 - 定义要提取的模式
// ============================================
const DEFAULT_PATTERNS = {
  // 1. 页面开发场景
  pageCreation: {
    name: "页面开发",
    description: "如何创建一个新页面",
    searchPatterns: [
      { dir: "src/pages", extensions: [".tsx", ".jsx"], maxFiles: 3 },
    ],
    // 优先选择的文件特征
    preferPatterns: [/export\s+default/, /React\.FC|FC</, /useEffect|useState/],
    // 排除的文件
    excludePatterns: [
      /\.test\.|\.spec\.|__test__|__mock__/,
      /index\.ts$/, // 纯导出文件
    ],
    extractSections: ["imports", "component", "hooks", "render"],
  },

  // 2. 组件开发场景
  componentCreation: {
    name: "组件开发",
    description: "如何创建一个可复用组件",
    searchPatterns: [
      { dir: "src/components", extensions: [".tsx", ".jsx"], maxFiles: 3 },
    ],
    preferPatterns: [
      /interface\s+\w+Props/,
      /React\.FC<\w+Props>/,
      /export\s+(default\s+)?function/,
    ],
    excludePatterns: [/\.test\.|\.spec\./, /index\.ts$/],
    extractSections: ["imports", "types", "component", "props"],
  },

  // 3. 表单场景
  formUsage: {
    name: "表单开发",
    description: "如何创建和处理表单",
    searchPatterns: [{ dir: "src", extensions: [".tsx", ".jsx"], maxFiles: 3 }],
    requiredPatterns: [/Form\.useForm\(\)|useForm\(\)/, /Form\.Item|FormItem/],
    preferPatterns: [
      /onFinish|handleSubmit/,
      /form\.validateFields|form\.submit/,
    ],
    excludePatterns: [/\.test\.|\.spec\./],
    extractSections: ["imports", "formSetup", "formItems", "submit"],
  },

  // 4. 表格场景
  tableUsage: {
    name: "表格开发",
    description: "如何创建数据表格",
    searchPatterns: [{ dir: "src", extensions: [".tsx", ".jsx"], maxFiles: 3 }],
    requiredPatterns: [/Table|ProTable|TableTemplate/],
    preferPatterns: [/columns\s*[=:]/, /dataSource|pagination/],
    excludePatterns: [/\.test\.|\.spec\./],
    extractSections: ["imports", "columns", "tableSetup", "dataFetch"],
  },

  // 5. 接口请求场景
  apiService: {
    name: "接口定义",
    description: "如何定义和封装 API 接口",
    searchPatterns: [
      { dir: "src/service", extensions: [".ts", ".js"], maxFiles: 3 },
      { dir: "src/services", extensions: [".ts", ".js"], maxFiles: 3 },
      { dir: "src/api", extensions: [".ts", ".js"], maxFiles: 3 },
    ],
    preferPatterns: [
      /export\s+(async\s+)?function/,
      /request\(|axios\.|fetch\(/,
    ],
    excludePatterns: [/\.test\.|\.spec\./, /index\.ts$/],
    extractSections: ["imports", "serviceDefinition", "requestConfig"],
  },

  // 6. 接口调用场景
  apiUsage: {
    name: "接口调用",
    description: "如何在组件中调用接口",
    searchPatterns: [
      { dir: "src/pages", extensions: [".tsx", ".jsx"], maxFiles: 3 },
    ],
    requiredPatterns: [/import.*from\s+['"]@\/service|\.\.\/service/],
    preferPatterns: [
      /useEffect.*\{[\s\S]*?fetch|load|get/i,
      /async|await/,
      /try\s*\{|\.catch\(/,
    ],
    excludePatterns: [/\.test\.|\.spec\./],
    extractSections: ["imports", "apiCall", "errorHandling", "dataDisplay"],
  },

  // 7. 样式编写场景
  styleWriting: {
    name: "样式编写",
    description: "如何编写组件样式",
    searchPatterns: [
      {
        dir: "src",
        extensions: [".less", ".scss", ".css", ".module.css"],
        maxFiles: 3,
      },
    ],
    preferPatterns: [/@import|@mixin|@include/, /\.[\w-]+\s*\{/],
    excludePatterns: [/global\.less|reset\.css|normalize/],
    extractSections: ["imports", "variables", "selectors", "mixins"],
  },

  // 8. 路由配置场景
  routeConfig: {
    name: "路由配置",
    description: "如何配置页面路由",
    searchPatterns: [
      {
        dir: ".",
        files: [
          "config/routes.ts",
          "config/routes.js",
          "src/routes.ts",
          "src/routes.js",
          "src/router/index.ts",
          "src/router/index.tsx",
        ],
        maxFiles: 1,
      },
    ],
    preferPatterns: [/path\s*:/, /component\s*:/, /routes\s*:/],
    excludePatterns: [],
    extractSections: ["routeStructure", "routeConfig"],
  },

  // 9. 状态管理场景
  stateManagement: {
    name: "状态管理",
    description: "如何使用全局状态",
    searchPatterns: [
      { dir: "src/store", extensions: [".ts", ".tsx", ".js"], maxFiles: 2 },
      { dir: "src/stores", extensions: [".ts", ".tsx", ".js"], maxFiles: 2 },
      { dir: "src/models", extensions: [".ts", ".tsx", ".js"], maxFiles: 2 },
    ],
    preferPatterns: [
      /createSlice|createStore|defineStore/,
      /useSelector|useDispatch|useStore/,
    ],
    excludePatterns: [/\.test\.|\.spec\./],
    extractSections: ["storeDefinition", "actions", "selectors", "usage"],
  },

  // 10. 弹窗/对话框场景
  modalUsage: {
    name: "弹窗开发",
    description: "如何使用 Modal/Drawer",
    searchPatterns: [{ dir: "src", extensions: [".tsx", ".jsx"], maxFiles: 3 }],
    requiredPatterns: [/Modal|Drawer/],
    preferPatterns: [/visible|open/, /onCancel|onClose/, /onOk|onConfirm/],
    excludePatterns: [/\.test\.|\.spec\./],
    extractSections: ["imports", "modalSetup", "modalContent", "callbacks"],
  },

  // 11. Hooks 使用场景
  hooksUsage: {
    name: "Hooks 使用",
    description: "常用 Hooks 的使用方式",
    searchPatterns: [
      { dir: "src/hooks", extensions: [".ts", ".tsx"], maxFiles: 3 },
      { dir: "src/utils/hooks", extensions: [".ts", ".tsx"], maxFiles: 3 },
    ],
    preferPatterns: [
      /^export\s+(const|function)\s+use[A-Z]/m,
      /useState|useEffect|useCallback|useMemo/,
    ],
    excludePatterns: [/\.test\.|\.spec\./],
    extractSections: ["hookDefinition", "params", "returnValue", "usage"],
  },

  // 12. 类型定义场景
  typeDefinition: {
    name: "类型定义",
    description: "如何定义 TypeScript 类型",
    searchPatterns: [
      { dir: "src/types", extensions: [".ts", ".d.ts"], maxFiles: 3 },
      { dir: "src/typings", extensions: [".ts", ".d.ts"], maxFiles: 3 },
    ],
    preferPatterns: [/^export\s+(interface|type)\s+/m, /extends|implements/],
    excludePatterns: [],
    extractSections: ["interfaces", "types", "enums"],
  },
};

// ============================================
// 工具函数
// ============================================

// 递归扫描目录
function scanDirectory(dir, extensions, files = []) {
  if (!fs.existsSync(dir)) return files;

  try {
    const entries = fs.readdirSync(dir, { withFileTypes: true });

    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);

      if (entry.isDirectory()) {
        if (!EXCLUDE_DIRS.includes(entry.name)) {
          scanDirectory(fullPath, extensions, files);
        }
      } else if (entry.isFile()) {
        const ext = path.extname(entry.name);
        if (extensions.includes(ext)) {
          files.push(fullPath);
        }
      }
    }
  } catch (e) {
    // 忽略访问错误
  }

  return files;
}

// 检查文件是否匹配模式
function matchesPatterns(content, patterns) {
  if (!patterns || patterns.length === 0) return true;
  return patterns.some((pattern) => pattern.test(content));
}

// 检查文件是否被排除
function isExcluded(filePath, patterns) {
  if (!patterns || patterns.length === 0) return false;
  return patterns.some((pattern) => pattern.test(filePath));
}

// 计算文件匹配分数（用于排序）
function calculateScore(content, filePath, config) {
  let score = 0;

  // 必需模式匹配
  if (config.requiredPatterns) {
    const allRequired = config.requiredPatterns.every((p) => p.test(content));
    if (!allRequired) return -1; // 必需模式未匹配，排除
  }

  // 优选模式匹配
  if (config.preferPatterns) {
    for (const pattern of config.preferPatterns) {
      if (pattern.test(content)) score += 10;
    }
  }

  // 代码行数适中（50-300行最佳）
  const lines = content.split("\n").length;
  if (lines >= 50 && lines <= 300) score += 20;
  else if (lines >= 30 && lines <= 500) score += 10;
  else if (lines > 800) score -= 10; // 太长扣分

  // 有注释加分
  if (/\/\*\*[\s\S]*?\*\/|\/\//.test(content)) score += 5;

  // 文件名规范加分
  if (/^[A-Z][a-zA-Z]+\.(tsx|jsx)$/.test(path.basename(filePath))) score += 5;

  return score;
}

// 提取文件的关键代码段
function extractCodeSections(content, filePath) {
  const ext = path.extname(filePath);
  const lines = content.split("\n");
  const sections = {};

  // 提取 imports
  const importLines = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (
      /^import\s+/.test(line) ||
      /^import\s*\{/.test(line) ||
      /^import\s*\(/.test(line)
    ) {
      importLines.push(line);
    } else if (
      importLines.length > 0 &&
      !/^\s*$/.test(line) &&
      !/^import/.test(line)
    ) {
      break;
    }
  }
  if (importLines.length > 0) {
    sections.imports = importLines.join("\n");
  }

  // 提取类型定义
  const typeMatch = content.match(
    /^(export\s+)?(interface|type)\s+\w+[\s\S]*?^\}/gm,
  );
  if (typeMatch) {
    sections.types = typeMatch.slice(0, 3).join("\n\n");
  }

  // 提取组件定义（函数组件）
  const componentMatch = content.match(
    /^(export\s+)?(default\s+)?(const|function)\s+[A-Z]\w*[\s\S]*?^(\}\s*;?\s*$|\)\s*;?\s*$)/gm,
  );
  if (componentMatch) {
    sections.component = componentMatch[0];
  }

  // 提取 columns 定义（表格场景）
  const columnsMatch = content.match(
    /const\s+columns[\s\S]*?(?=\n\s*\n|\nconst\s|\nfunction\s|\nexport\s)/,
  );
  if (columnsMatch) {
    sections.columns = columnsMatch[0].trim();
  }

  // 提取 Form.Item 结构
  const formItemMatch = content.match(/<Form[\s\S]*?<\/Form>/);
  if (formItemMatch) {
    sections.formStructure = formItemMatch[0];
  }

  // 如果没有提取到特定段落，返回整个文件（截取前 150 行）
  if (Object.keys(sections).length <= 1) {
    sections.fullContent = lines.slice(0, 150).join("\n");
    if (lines.length > 150) {
      sections.fullContent += `\n\n// ... (共 ${lines.length} 行，已截取前 150 行)`;
    }
  }

  return sections;
}

// ============================================
// 主要逻辑
// ============================================

// 处理单个场景
function processPattern(patternKey, config) {
  console.log(`\nProcessing: ${config.name}`);

  const candidates = [];

  // 扫描所有匹配的文件
  for (const searchConfig of config.searchPatterns) {
    let files = [];

    if (searchConfig.files) {
      // 指定文件列表
      for (const file of searchConfig.files) {
        const fullPath = path.join(options.dir, file);
        if (fs.existsSync(fullPath)) {
          files.push(fullPath);
        }
      }
    } else if (searchConfig.dir) {
      // 扫描目录
      const searchDir = path.join(options.dir, searchConfig.dir);
      files = scanDirectory(
        searchDir,
        searchConfig.extensions || [".ts", ".tsx", ".js", ".jsx"],
      );
    }

    // 筛选和评分
    for (const filePath of files) {
      if (isExcluded(filePath, config.excludePatterns)) continue;

      try {
        const content = fs.readFileSync(filePath, "utf-8");
        const score = calculateScore(content, filePath, config);

        if (score >= 0) {
          candidates.push({
            path: path.relative(options.dir, filePath),
            score,
            content,
            lines: content.split("\n").length,
          });
        }
      } catch (e) {
        // 忽略读取错误
      }
    }
  }

  // 按分数排序，取前 N 个
  candidates.sort((a, b) => b.score - a.score);
  const maxFiles = config.searchPatterns[0]?.maxFiles || 3;
  const selected = candidates.slice(0, maxFiles);

  console.log(
    `  Found ${candidates.length} candidates, selected ${selected.length}`,
  );

  // 提取代码段
  const examples = selected.map((file) => {
    const sections = extractCodeSections(file.content, file.path);
    return {
      filePath: file.path,
      lines: file.lines,
      score: file.score,
      sections,
    };
  });

  return {
    name: config.name,
    description: config.description,
    exampleCount: examples.length,
    examples,
  };
}

// 主函数
function main() {
  console.log(`Pattern Extractor`);
  console.log(`Scanning: ${path.resolve(options.dir)}`);
  console.log(`Output: ${options.output}`);

  // 加载自定义配置（如果有）
  let patterns = DEFAULT_PATTERNS;
  if (options.configFile && fs.existsSync(options.configFile)) {
    console.log(`Loading custom config: ${options.configFile}`);
    const customConfig = JSON.parse(
      fs.readFileSync(options.configFile, "utf-8"),
    );
    patterns = { ...patterns, ...customConfig };
  }

  // 处理每个场景
  const results = {
    extractTime: new Date().toISOString(),
    rootDir: path.resolve(options.dir),
    patterns: {},
  };

  for (const [key, config] of Object.entries(patterns)) {
    try {
      results.patterns[key] = processPattern(key, config);
    } catch (e) {
      console.log(`  Error processing ${key}: ${e.message}`);
      results.patterns[key] = {
        name: config.name,
        description: config.description,
        error: e.message,
        examples: [],
      };
    }
  }

  // 统计
  const totalExamples = Object.values(results.patterns).reduce(
    (sum, p) => sum + (p.exampleCount || 0),
    0,
  );

  results.summary = {
    totalPatterns: Object.keys(results.patterns).length,
    totalExamples,
    patternsWithExamples: Object.values(results.patterns).filter(
      (p) => p.exampleCount > 0,
    ).length,
  };

  // 输出结果
  fs.writeFileSync(options.output, JSON.stringify(results, null, 2));

  console.log(`\n=== Summary ===`);
  console.log(`Patterns processed: ${results.summary.totalPatterns}`);
  console.log(
    `Patterns with examples: ${results.summary.patternsWithExamples}`,
  );
  console.log(`Total examples extracted: ${results.summary.totalExamples}`);
  console.log(`\nOutput written to: ${options.output}`);
}

main();
