#!/usr/bin/env node
/**
 * Codebase Scanner - 代码库扫描分析脚本
 *
 * 用于大规模代码库的自动化分析，避免 AI Agent 逐个读取文件导致上下文溢出
 *
 * 使用方式：
 *   node codebase-scanner.js [options]
 *
 * 选项：
 *   --dir <path>        要扫描的目录，默认为当前目录
 *   --output <path>     输出文件路径，默认为 _codebase_analysis.json
 *   --batch-size <n>    每批处理的文件数，默认 20
 *   --batch-output      是否分批输出（用于多代理协作），默认 false
 */

const fs = require("fs");
const path = require("path");

// 解析命令行参数
const args = process.argv.slice(2);
const options = {
  dir: ".",
  output: "_codebase_analysis.json",
  batchSize: 20,
  batchOutput: false,
};

for (let i = 0; i < args.length; i++) {
  switch (args[i]) {
    case "--dir":
      options.dir = args[++i];
      break;
    case "--output":
      options.output = args[++i];
      break;
    case "--batch-size":
      options.batchSize = parseInt(args[++i], 10);
      break;
    case "--batch-output":
      options.batchOutput = true;
      break;
  }
}

// 排除的目录和文件
const EXCLUDE_DIRS = [
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
];

const EXCLUDE_FILES = [
  /\.min\.js$/,
  /\.bundle\.js$/,
  /\.map$/,
  /\.lock$/,
  /package-lock\.json$/,
  /yarn\.lock$/,
  /pnpm-lock\.yaml$/,
];

// 支持的文件扩展名
const CODE_EXTENSIONS = [
  ".ts",
  ".tsx",
  ".js",
  ".jsx",
  ".vue",
  ".svelte",
  ".css",
  ".scss",
  ".less",
  ".sass",
  ".py",
  ".go",
  ".rs",
  ".java",
  ".kt",
];

const CONFIG_FILES = [
  "package.json",
  "tsconfig.json",
  "vite.config.ts",
  "vite.config.js",
  "next.config.js",
  "next.config.mjs",
  "webpack.config.js",
  ".eslintrc",
  ".eslintrc.js",
  ".eslintrc.json",
  "eslint.config.js",
  ".prettierrc",
  ".prettierrc.js",
  ".prettierrc.json",
  "biome.json",
  "tailwind.config.js",
  "tailwind.config.ts",
];

// 分析模式定义
const PATTERNS = {
  // React 组件形态
  reactClass: /class\s+\w+\s+extends\s+(React\.)?Component/g,
  reactFunction: /^(export\s+)?(default\s+)?function\s+[A-Z]\w*\s*\(/gm,
  reactArrow:
    /^(export\s+)?(const|let)\s+[A-Z]\w*\s*[=:]\s*(\([^)]*\)|[^=])*=>\s*[{(]/gm,
  reactHooks: /use[A-Z]\w*\s*\(/g,

  // Vue 组件形态
  vueOptionsApi:
    /export\s+default\s*\{[\s\S]*?(data|methods|computed|watch)\s*[:(]/g,
  vueCompositionApi: /defineComponent|<script\s+setup/g,

  // 样式方案
  styledComponents: /styled\.\w+`|styled\(\w+\)`/g,
  emotionCss: /css`|@emotion\/css/g,
  cssModules: /\.module\.(css|scss|less)$/,
  tailwindClasses:
    /className\s*=\s*["'`][^"'`]*(?:flex|grid|p-|m-|text-|bg-|border-|rounded)/g,

  // 状态管理
  reduxStore: /createStore|configureStore|createSlice/g,
  zustandStore: /create\s*\(\s*\(set|useStore/g,
  piniaStore: /defineStore/g,
  mobxStore: /makeObservable|makeAutoObservable|@observable/g,
  jotaiAtom: /atom\s*\(|useAtom/g,

  // 路由
  reactRouter:
    /BrowserRouter|createBrowserRouter|useNavigate|useParams|<Route/g,
  vueRouter: /createRouter|useRouter|useRoute|<router-view/g,
  nextRouter: /useRouter|next\/router|next\/navigation/g,

  // API 调用
  axiosImport: /import\s+.*axios|require\s*\(\s*['"]axios['"]\s*\)/g,
  fetchCall: /fetch\s*\(/g,
  reactQuery: /@tanstack\/react-query|useQuery|useMutation/g,
  swrHook: /useSWR|swr/g,

  // 导出方式
  namedExport: /^export\s+(const|function|class|type|interface)\s+/gm,
  defaultExport: /^export\s+default\s+/gm,

  // TypeScript 特性
  typeAnnotation:
    /:\s*(string|number|boolean|any|void|never|unknown|\w+\[\]|Array<|Promise<)/g,
  interfaceDef: /^(export\s+)?interface\s+\w+/gm,
  typeDef: /^(export\s+)?type\s+\w+\s*=/gm,
};

// 文件复杂度评估（用于动态批次大小）
function estimateComplexity(content) {
  const lines = content.split("\n").length;
  const imports = (content.match(/^import\s+/gm) || []).length;
  const functions = (
    content.match(
      /function\s+\w+|=>\s*[{(]|^\s*(async\s+)?(\w+)\s*\([^)]*\)\s*\{/gm,
    ) || []
  ).length;

  // 简单评分：行数/100 + 导入数/10 + 函数数/5
  return Math.ceil(lines / 100 + imports / 10 + functions / 5);
}

// 扫描目录获取所有文件
function scanDirectory(dir, files = []) {
  const entries = fs.readdirSync(dir, { withFileTypes: true });

  for (const entry of entries) {
    const fullPath = path.join(dir, entry.name);

    if (entry.isDirectory()) {
      if (!EXCLUDE_DIRS.includes(entry.name)) {
        scanDirectory(fullPath, files);
      }
    } else if (entry.isFile()) {
      const ext = path.extname(entry.name);
      const isExcluded = EXCLUDE_FILES.some((pattern) =>
        pattern.test(entry.name),
      );

      if (
        !isExcluded &&
        (CODE_EXTENSIONS.includes(ext) || CONFIG_FILES.includes(entry.name))
      ) {
        files.push(fullPath);
      }
    }
  }

  return files;
}

// 分析单个文件
function analyzeFile(filePath) {
  const content = fs.readFileSync(filePath, "utf-8");
  const ext = path.extname(filePath);
  const fileName = path.basename(filePath);
  const relativePath = path.relative(options.dir, filePath);

  const result = {
    path: relativePath,
    extension: ext,
    lines: content.split("\n").length,
    complexity: estimateComplexity(content),
    patterns: {},
  };

  // 根据文件类型选择性分析
  if ([".ts", ".tsx", ".js", ".jsx"].includes(ext)) {
    // JavaScript/TypeScript 文件
    for (const [name, pattern] of Object.entries(PATTERNS)) {
      const matches = content.match(pattern);
      if (matches && matches.length > 0) {
        result.patterns[name] = matches.length;
      }
    }

    // 提取导入的包
    const imports = content.match(/from\s+['"]([^'"]+)['"]/g) || [];
    result.imports = imports.map((m) => m.replace(/from\s+['"]|['"]/g, ""));
  } else if (ext === ".vue") {
    // Vue 文件
    const scriptMatch = content.match(/<script[^>]*>([\s\S]*?)<\/script>/);
    if (scriptMatch) {
      const scriptContent = scriptMatch[1];
      for (const [name, pattern] of Object.entries(PATTERNS)) {
        const matches = scriptContent.match(pattern);
        if (matches && matches.length > 0) {
          result.patterns[name] = matches.length;
        }
      }
    }
  } else if ([".css", ".scss", ".less"].includes(ext)) {
    // 样式文件
    result.patterns.cssRules = (content.match(/\{[^}]+\}/g) || []).length;
    result.patterns.cssVariables = (content.match(/--[\w-]+:/g) || []).length;
  } else if (fileName === "package.json") {
    // package.json 特殊处理
    try {
      const pkg = JSON.parse(content);
      result.packageInfo = {
        name: pkg.name,
        dependencies: Object.keys(pkg.dependencies || {}),
        devDependencies: Object.keys(pkg.devDependencies || {}),
      };
    } catch (e) {
      result.parseError = true;
    }
  }

  return result;
}

// 汇总分析结果
function aggregateResults(fileResults) {
  const summary = {
    totalFiles: fileResults.length,
    totalLines: 0,
    byExtension: {},
    byDirectory: {},
    patterns: {},
    technologies: {
      framework: null,
      styleMethod: [],
      stateManagement: [],
      routing: null,
      apiClient: [],
    },
    anomalies: [],
  };

  for (const file of fileResults) {
    // 统计行数
    summary.totalLines += file.lines;

    // 按扩展名统计
    summary.byExtension[file.extension] =
      (summary.byExtension[file.extension] || 0) + 1;

    // 按目录统计
    const dir = path.dirname(file.path).split(path.sep)[0] || ".";
    summary.byDirectory[dir] = (summary.byDirectory[dir] || 0) + 1;

    // 汇总模式统计
    for (const [pattern, count] of Object.entries(file.patterns || {})) {
      summary.patterns[pattern] = (summary.patterns[pattern] || 0) + count;
    }

    // 提取 package.json 信息
    if (file.packageInfo) {
      summary.packageInfo = file.packageInfo;
    }
  }

  // 推断技术栈
  const p = summary.patterns;

  // 框架推断
  if (p.reactHooks > 0 || p.reactFunction > 0 || p.reactArrow > 0) {
    summary.technologies.framework = "React";
  } else if (p.vueOptionsApi > 0 || p.vueCompositionApi > 0) {
    summary.technologies.framework = "Vue";
  }

  // 样式方案推断
  if (p.tailwindClasses > 0) summary.technologies.styleMethod.push("Tailwind");
  if (p.styledComponents > 0)
    summary.technologies.styleMethod.push("Styled-Components");
  if (p.emotionCss > 0) summary.technologies.styleMethod.push("Emotion");
  if (
    summary.byExtension[".module.css"] > 0 ||
    summary.byExtension[".module.scss"] > 0
  ) {
    summary.technologies.styleMethod.push("CSS Modules");
  }

  // 状态管理推断
  if (p.reduxStore > 0) summary.technologies.stateManagement.push("Redux");
  if (p.zustandStore > 0) summary.technologies.stateManagement.push("Zustand");
  if (p.piniaStore > 0) summary.technologies.stateManagement.push("Pinia");
  if (p.mobxStore > 0) summary.technologies.stateManagement.push("MobX");
  if (p.jotaiAtom > 0) summary.technologies.stateManagement.push("Jotai");

  // 路由推断
  if (p.nextRouter > 0) summary.technologies.routing = "Next.js Router";
  else if (p.reactRouter > 0) summary.technologies.routing = "React Router";
  else if (p.vueRouter > 0) summary.technologies.routing = "Vue Router";

  // API 客户端推断
  if (p.axiosImport > 0) summary.technologies.apiClient.push("Axios");
  if (p.fetchCall > 0) summary.technologies.apiClient.push("Fetch");
  if (p.reactQuery > 0) summary.technologies.apiClient.push("React Query");
  if (p.swrHook > 0) summary.technologies.apiClient.push("SWR");

  // 检测异常（多方案混用）
  if (summary.technologies.styleMethod.length > 1) {
    summary.anomalies.push({
      type: "multiple_style_methods",
      message: `检测到多种样式方案混用: ${summary.technologies.styleMethod.join(", ")}`,
      severity: "warning",
    });
  }

  if (summary.technologies.stateManagement.length > 1) {
    summary.anomalies.push({
      type: "multiple_state_management",
      message: `检测到多种状态管理方案混用: ${summary.technologies.stateManagement.join(", ")}`,
      severity: "warning",
    });
  }

  if (p.reactClass > 0 && (p.reactFunction > 0 || p.reactHooks > 0)) {
    summary.anomalies.push({
      type: "mixed_component_styles",
      message: `检测到类组件和函数组件混用 (类组件: ${p.reactClass}, 函数组件: ${(p.reactFunction || 0) + (p.reactArrow || 0)})`,
      severity: "info",
    });
  }

  return summary;
}

// 主函数
function main() {
  console.log(`Scanning directory: ${path.resolve(options.dir)}`);

  // 扫描文件
  const files = scanDirectory(options.dir);
  console.log(`Found ${files.length} files to analyze`);

  if (files.length === 0) {
    console.log("No files found to analyze");
    process.exit(0);
  }

  // 分析文件
  const fileResults = [];
  const batches = [];
  let currentBatch = [];
  let currentComplexity = 0;
  const maxBatchComplexity = options.batchSize * 3; // 动态批次：基于复杂度

  for (let i = 0; i < files.length; i++) {
    const result = analyzeFile(files[i]);
    fileResults.push(result);

    if (options.batchOutput) {
      currentBatch.push(result);
      currentComplexity += result.complexity;

      // 动态批次大小：基于复杂度或文件数
      if (
        currentComplexity >= maxBatchComplexity ||
        currentBatch.length >= options.batchSize
      ) {
        batches.push({
          batchIndex: batches.length,
          files: currentBatch,
          summary: aggregateResults(currentBatch),
        });
        currentBatch = [];
        currentComplexity = 0;
      }
    }

    // 进度显示
    if ((i + 1) % 50 === 0) {
      console.log(`Analyzed ${i + 1}/${files.length} files...`);
    }
  }

  // 处理剩余文件
  if (options.batchOutput && currentBatch.length > 0) {
    batches.push({
      batchIndex: batches.length,
      files: currentBatch,
      summary: aggregateResults(currentBatch),
    });
  }

  // 生成最终输出
  const output = {
    scanTime: new Date().toISOString(),
    rootDir: path.resolve(options.dir),
    totalFiles: files.length,
    summary: aggregateResults(fileResults),
  };

  if (options.batchOutput) {
    // 分批输出模式：输出多个文件
    const outputDir = path.dirname(options.output);
    const outputBase = path.basename(options.output, ".json");

    for (const batch of batches) {
      const batchFile = path.join(
        outputDir,
        `${outputBase}_batch_${batch.batchIndex}.json`,
      );
      fs.writeFileSync(batchFile, JSON.stringify(batch, null, 2));
      console.log(`Written batch ${batch.batchIndex} to ${batchFile}`);
    }

    // 输出汇总文件
    output.batches = batches.map((b) => ({
      batchIndex: b.batchIndex,
      fileCount: b.files.length,
      summary: b.summary,
    }));
    fs.writeFileSync(options.output, JSON.stringify(output, null, 2));
    console.log(`Written summary to ${options.output}`);
  } else {
    // 单文件输出模式
    output.files = fileResults;
    fs.writeFileSync(options.output, JSON.stringify(output, null, 2));
    console.log(`Written analysis to ${options.output}`);
  }

  // 输出简要统计
  console.log("\n=== Analysis Summary ===");
  console.log(`Total files: ${output.summary.totalFiles}`);
  console.log(`Total lines: ${output.summary.totalLines}`);
  console.log(
    `Framework: ${output.summary.technologies.framework || "Unknown"}`,
  );
  console.log(
    `Style methods: ${output.summary.technologies.styleMethod.join(", ") || "None detected"}`,
  );
  console.log(
    `State management: ${output.summary.technologies.stateManagement.join(", ") || "None detected"}`,
  );
  console.log(
    `Routing: ${output.summary.technologies.routing || "None detected"}`,
  );

  if (output.summary.anomalies.length > 0) {
    console.log("\n=== Anomalies Detected ===");
    for (const anomaly of output.summary.anomalies) {
      console.log(`[${anomaly.severity.toUpperCase()}] ${anomaly.message}`);
    }
  }
}

main();
