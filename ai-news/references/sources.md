# AI 新闻源与搜索策略

本文档定义了 AI 新闻收集的主要来源和对应的搜索策略。

## 新闻源概览

共 **12 类来源**，覆盖官方发布、社区讨论、专业媒体、学术研究等多个维度。

---

## 1. 官方博客（第一手信息）

最权威的信息来源，优先级最高。

| 来源 | URL | 关注重点 |
|------|-----|---------|
| **OpenAI Blog** | openai.com/blog | 模型发布、研究、政策 |
| **Anthropic Blog** | anthropic.com/news | Claude 更新、安全研究 |
| **Google AI Blog** | blog.google/technology/ai | Gemini、研究突破 |
| **Meta AI Blog** | ai.meta.com/blog | LLaMA、开源发布 |
| **Microsoft AI Blog** | blogs.microsoft.com/ai | Copilot、Azure AI |
| **DeepMind Blog** | deepmind.google/discover/blog | 前沿研究、AlphaFold |
| **Hugging Face Blog** | huggingface.co/blog | 开源模型、工具更新 |

**搜索策略**:
```
site:openai.com/blog OR site:anthropic.com OR site:ai.meta.com
时间: 指定范围
```

---

## 2. 社交媒体平台

**X (Twitter)**
- **关注重点**: 实时动态、行业领袖观点、产品发布
- **关键账号**: @OpenAI, @AnthropicAI, @GoogleAI, @ylecun, @kaboroevich, @sama
- **搜索策略**:
  ```
  query: "AI OR GPT OR LLM OR Claude (announced OR released OR launching) -job -hiring -course"
  时间: 指定范围
  ```
- **特点**: 最快速的信息源，需要筛选噪音

---

## 3. 技术社区

### Hacker News
- **关注重点**: 技术讨论、开源项目、学术论文
- **搜索策略**:
  ```
  site:news.ycombinator.com (AI OR "machine learning" OR LLM OR GPT OR transformer)
  ```
- **特点**: 高质量技术讨论，开发者视角

### Reddit
- **关注子版**:
  - r/MachineLearning - 学术讨论、论文解读
  - r/LocalLLaMA - 本地部署、开源模型
  - r/artificial - 综合 AI 讨论
  - r/ChatGPT - 产品使用、更新
  - r/ClaudeAI - Claude 相关
  - r/singularity - AI 前沿与影响
- **搜索策略**:
  ```
  site:reddit.com/r/MachineLearning OR site:reddit.com/r/LocalLLaMA
  ```
- **特点**: 社区讨论深入，开源动态快

### GitHub
- **关注重点**: AI/ML 趋势项目、新框架发布
- **搜索策略**:
  ```
  site:github.com (AI OR LLM OR "machine learning") stars:>1000
  ```
- **特点**: 开源项目第一时间发布

---

## 4. 新闻聚合平台

**Google News**
- **关注重点**: 主流媒体报道、政策法规、行业动态
- **搜索策略**:
  - 英文: `"artificial intelligence" OR "AI" (breakthrough OR regulation OR startup)`
  - 中文: `"人工智能" OR "大模型" (突破 OR 发布 OR 融资)`
- **特点**: 覆盖面广，多语言

---

## 5. 科技媒体（英文）

| 媒体 | 关注重点 | 搜索关键词 |
|------|---------|-----------|
| **TechCrunch** | 创业、融资、产品 | AI startup, funding, product launch |
| **VentureBeat** | 企业 AI、行业趋势 | enterprise AI, AI adoption |
| **The Verge** | 消费级产品、科技文化 | AI product, AI tool, ChatGPT |
| **Wired** | 深度报道、AI 影响 | AI, machine learning, future |
| **MIT Technology Review** | 技术深度、前沿趋势 | AI, emerging tech |
| **Ars Technica** | 技术分析、产品评测 | AI, machine learning |

**搜索策略**:
```
site:(techcrunch.com OR venturebeat.com OR theverge.com OR wired.com OR technologyreview.com) AI
时间: 指定范围
```

---

## 6. 科技媒体（中文）

| 媒体 | 关注重点 | 特点 |
|------|---------|------|
| **机器之心** | 技术解读、论文翻译 | 技术深度高 |
| **量子位** | 行业动态、产品发布 | 更新快 |
| **新智元** | 综合 AI 资讯 | 覆盖面广 |
| **36氪 AI 频道** | 创业、融资、产业 | 商业视角 |
| **雷峰网** | 技术+商业 | 深度报道 |
| **AI 科技评论** | 技术前沿 | 学术导向 |

**搜索策略**:
```
site:(jiqizhixin.com OR qbitai.com OR 36kr.com) 人工智能 OR AI OR 大模型
时间: 指定范围
```

---

## 7. Newsletter（策划精选）

高质量策划内容，适合快速了解行业动态。

| Newsletter | 作者/机构 | 频率 | 特点 |
|------------|----------|------|------|
| **Ben's Bites** | Ben Tossell | 每日 | AI 产品和工具 |
| **The Batch** | Andrew Ng / DeepLearning.AI | 每周 | 技术+行业 |
| **TLDR AI** | TLDR | 每日 | 简洁摘要 |
| **AI Weekly** | Weights & Biases | 每周 | 技术深度 |
| **The Neuron** | - | 每日 | 商业视角 |
| **Import AI** | Jack Clark | 每周 | 政策+安全 |
| **Last Week in AI** | - | 每周 | 综合回顾 |

**搜索策略**:
```
site:bensbites.co OR "The Batch" deeplearning.ai OR site:tldr.tech/ai
```

---

## 8. 学术平台

### arXiv (预印本)
- **分类**: cs.AI, cs.LG, cs.CL, cs.CV, cs.RO
- **搜索策略**:
  ```
  site:arxiv.org (cs.AI OR cs.LG OR cs.CL OR cs.CV)
  ```
- **特点**: 学术前沿，预印本

### Papers With Code
- **关注重点**: 论文 + 代码实现
- **搜索策略**:
  ```
  site:paperswithcode.com (SOTA OR benchmark OR "state of the art")
  ```
- **特点**: 论文与代码结合

### Hugging Face Daily Papers
- **关注重点**: 每日精选论文
- **URL**: huggingface.co/papers
- **特点**: 社区投票，热门论文

### Semantic Scholar
- **关注重点**: 论文引用、影响力分析
- **搜索策略**:
  ```
  site:semanticscholar.org "artificial intelligence" OR "large language model"
  ```

---

## 9. 开源社区动态

### Hugging Face
- **关注重点**: 模型发布、Spaces、数据集
- **搜索策略**:
  ```
  site:huggingface.co (model OR release OR trending)
  ```

### GitHub Trending
- **关注重点**: AI/ML 热门项目
- **URL**: github.com/trending?since=daily (筛选 AI/ML)

### Model 发布追踪
- Ollama 新模型
- LM Studio 支持
- 各大模型 API 更新

---

## 10. 视频与播客

| 频道/播客 | 平台 | 特点 |
|----------|------|------|
| **Two Minute Papers** | YouTube | 论文快速解读 |
| **Yannic Kilcher** | YouTube | 深度论文讲解 |
| **AI Explained** | YouTube | AI 概念解释 |
| **Lex Fridman Podcast** | Podcast | 深度访谈 |
| **Latent Space** | Podcast | AI 工程实践 |
| **Practical AI** | Podcast | 应用案例 |
| **The AI Podcast (NVIDIA)** | Podcast | 行业领袖 |

**搜索策略**:
```
site:youtube.com ("Two Minute Papers" OR "Yannic Kilcher" OR "AI Explained") 最新
```

---

## 11. 产品与工具

### Product Hunt
- **关注重点**: AI 新产品发布
- **搜索策略**:
  ```
  site:producthunt.com AI OR "artificial intelligence" OR GPT
  ```

### AI 工具目录
- There's An AI For That (theresanaiforthat.com)
- Futurepedia (futurepedia.io)
- AI Tool Directory

---

## 12. 行业报告与分析

| 来源 | 类型 | 关注重点 |
|------|------|---------|
| **Stanford HAI** | 学术 | AI Index 年度报告 |
| **McKinsey** | 咨询 | 企业 AI 采用 |
| **Gartner** | 分析 | 技术成熟度曲线 |
| **CB Insights** | 研究 | AI 投资趋势 |
| **a]6z** | VC | AI 市场分析 |
| **State of AI Report** | 独立 | 年度综合报告 |

---

## 搜索时间范围策略

| 场景 | 推荐范围 | 说明 |
|------|---------|------|
| 日常追踪 | 24 小时 | 工作日使用 |
| 周末补课 | 48-72 小时 | 覆盖周末 |
| 周报整理 | 7 天 | 周度回顾 |
| 趋势分析 | 30 天 | 月度趋势 |

---

## 综合搜索策略模板

### 快速全面搜索
```
("artificial intelligence" OR AI OR LLM OR GPT OR Claude OR Gemini)
(announced OR released OR launched OR breakthrough OR research)
-job -hiring -course -tutorial -"how to" -affiliate -sponsored
```

### 技术突破专项
```
(GPT-5 OR Claude OR Gemini OR LLaMA OR Mistral OR "open source model")
(release OR benchmark OR SOTA OR "state of the art")
site:(arxiv.org OR openai.com OR anthropic.com OR ai.meta.com)
```

### 行业应用专项
```
("AI in" OR "AI for") (healthcare OR finance OR education OR manufacturing)
(case study OR deployment OR implementation OR ROI)
```

### 政策法规专项
```
("AI regulation" OR "AI policy" OR "AI Act" OR "AI safety")
(government OR legislation OR compliance OR ethics)
```

---

## 信息质量评估标准

### 来源可信度层级
1. **Tier 1** - 官方博客、公司公告
2. **Tier 2** - 主流科技媒体、知名记者
3. **Tier 3** - 社区讨论、用户反馈
4. **Tier 4** - 自媒体、未经证实消息

### 评估维度
1. **时效性** - 发布时间越近越好
2. **原创性** - 一手信息 > 转述报道
3. **深度** - 技术细节 > 概念介绍
4. **影响力** - 行业级 > 公司级 > 产品级
5. **可验证性** - 有数据、有来源 > 无依据

### 过滤规则
- ❌ 排除招聘广告（hiring, job opening, career）
- ❌ 排除教程内容（tutorial, course, "how to"）
- ❌ 排除营销软文（affiliate, sponsored, "best AI tools"）
- ❌ 排除低质量内容（listicle, clickbait）
- ✅ 优先官方发布和一手来源
- ✅ 合并同一事件的多个报道
