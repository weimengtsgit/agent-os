# 第 1 页｜背景与问题（Why）

## 为什么需要 Agent 底座（Agent OS）

**背景**

* 公司现有产品正在系统性引入 AI 能力
* 随着推进，会持续出现：

  * 需求分析 Agent
  * 测试生成 Agent
  * 发布评估 Agent
  * 运维分析 Agent
  * 客服 / 运营 Agent

**核心问题**

* 如果每个团队各自实现 Agent：

  * 架构碎片化
  * 成本不可控
  * 安全、审计、合规难以统一
  * 长期维护风险极高

**结论**

> Agent 会越来越多，但 Agent 的运行方式、治理方式必须统一。

---

# 第 2 页｜目标与原则（What）

## 我们要构建什么样的 Agent 底座

### 🎯 建设目标

* 支撑 **多个业务领域 Agent 并行开发**
* Agent 行为 **可治理、可观测、可审计**
* 平台 **不绑定单一 AI 框架或 Runtime**

### 🧭 设计原则

* **Spec-first**：先定义清晰契约，再谈实现
* **Runtime 可替换**：Agent 不应依赖具体框架
* **人始终在关键决策点**（Human-in-the-loop）
* **平台最小化**：只统一“必须统一的能力”

---

# 第 3 页｜总体方案概览（How）

## Agent OS 的总体思路

### 核心设计

* 构建一个 **Agent OS（Agent 底座）**

  * 控制面：定义、治理、观测
  * 数据面：Agent 实际运行

### 技术选型策略

* 采用 **agno** 作为 **Agent Runtime 的一种实现**
* 平台层通过抽象适配 Runtime，而不是直接绑定

### 一句话定位

> agno 是“发动机”，Agent OS 是“整车平台”。

---

# 第 4 页｜平台架构（简化版）

## Agent OS 分层架构

### 架构分层

* **稳定契约层**

  * Agent Spec
  * Tool Spec
  * Policy Spec
  * Run / Trace Event
* **平台抽象层（PAL）**

  * Runtime 抽象
  * Tool 抽象
  * LLM / Memory / Observability 抽象
* **Runtime 层**

  * agno Adapter
  * 未来可接入其它 Runtime
* **事实层**

  * 事件流
  * Trace / Cost / Audit

### 关键约束

* 业务 Agent **不得直接依赖 agno**
* Runtime 可并存、可替换、可演练切换

---

# 第 5 页｜样板 Agent 选择（MVP）

## 为什么选择「测试用例生成 Agent」

### 选择原因

* **业务价值直观**

  * 研发、测试都能立刻感知价值
* **工具链清晰**

  * 需求 → 用例 → 回写
* **天然需要人审**

  * 非黑盒自动化，符合合规要求

### MVP 闭环

1. 输入需求（ID / 文本）
2. 拉取需求信息
3. 生成结构化测试用例
4. 规则校验
5. 人工审核
6. 回写与审计
7. 全流程可观测

---

# 第 6 页｜30 天计划（Phase 1）

## 30 天：跑通闭环，证明平台价值

### 交付内容

* 测试用例生成 Agent 上线
* Agent / Tool / Policy 的标准 Spec
* agno Runtime Adapter
* 最小 Console（Run / 事件 / 人审 / 成本）

### 能力边界

* 不追求复杂 UI
* 不追求多租户
* 只做 **“能跑、能看、能回放”**

### 验收标准

* Agent 全流程可回放
* 人审可控
* Demo 可 5–8 分钟讲清楚

---

# 第 7 页｜60 天计划（Phase 2）

## 60 天：平台化，多 Agent 并存

### 核心能力

* Agent Registry / Catalog
* Agent 生命周期（dev / canary / prod）
* Prompt / Model / Tool 动态配置
* Session / State 持久化
* 平台级 Observability

### 业务效果

* 新 Agent 接入 ≤ 1 天
* 多 Agent 并行运行互不影响
* 平台不成为业务瓶颈

---

# 第 8 页｜90 天计划（Phase 3）

## 90 天：生产可用 & 可迁移

### 生产化能力

* 并发 / 限流 / 取消 / 熔断
* 工具级雪崩保护
* 成本预算与限额
* 安全审计与数据脱敏

### 架构韧性

* Runtime Router
* Shadow Run（双跑）
* GameDay 演练（Runtime 切换）

### 核心目标

> 不只是“能用”，而是“敢长期用”。

---

# 第 9 页｜组织协作模式（Who）

## 平台组 + 业务组协作模型

### 平台组职责

* Agent OS 架构
* Spec / Runtime / 治理
* 稳定性、安全、成本兜底

### 业务组职责

* 业务 Agent 设计
* Prompt / Tool / 业务规则
* 输出质量负责

### 关键边界

> 平台组不写业务 Agent，业务组不碰 Runtime。

---

# 第 10 页｜风险与决策建议（Decision）

## 风险是否可控？是否值得投入？

### 主要风险

* 平台过重 → **分阶段推进**
* 技术锁死 → **解耦设计 + 演练**
* 成本失控 → **限额 + 观测**

### 决策建议

* 批准 **3 个月试点**
* 以测试用例生成 Agent 为样板
* agno 作为 Runtime 实现之一
* 3 个月后基于结果决定是否扩大
