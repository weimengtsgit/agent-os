## 1️⃣ 本轮产出摘要（B6）

1. 明确 **平台化目标**：在不牺牲稳定性与治理的前提下，支持**多团队并行开发、多 Agent 并存运行**
2. 给出 **平台组 + 业务组** 的清晰分工模型（RACI），避免“平台越做越重/业务绕平台走”
3. 输出 **6 大平台化能力模块** 的落地清单（Registry、配置、Session/State、权限、多观测、Eval）
4. 每个模块都给出：**目标 → 最小实现 → 推荐技术路径 → 常见坑**（能直接排期）
5. 定义 **Agent 生命周期与治理门禁**：注册、发布、运行、变更、下线
6. 给出 **从 B5 MVP 平滑演进到多 Agent 平台** 的实施顺序

---

## 2️⃣ 可执行 TODO 清单（P0 / P1 / P2，≥12）

### P0（多 Agent 并存的前提）

1. 建立 **Agent Registry / Catalog**（统一 Agent/Tool/Policy 的注册与发现）
2. 明确 **Agent 生命周期状态机**（draft → active → deprecated → disabled）
3. 实现 **AgentSpec / ToolSpec 的版本不可变**（新版本=新对象）
4. 建立 **运行路由规则**：默认只路由 `stage=prod` 的 Agent
5. 在 Runtime 前强制 **Policy Check**（工具/模型/限额）
6. 建立 **统一事件流与 Trace 规范**（RunEvent + TraceSpan）

### P1（平台可用性与治理）

7. 实现 **动态配置**（prompt/model/tool 参数化 + 灰度）
8. 建立 **Session / State 存储与回放**（最少可审计）
9. 引入 **多团队权限模型**（Agent/Tool 级 Owner + 最小权限）
10. 提供 **平台级观测面板**（成功率、耗时、成本、失败原因）
11. 建立 **Agent 模板与脚手架**（业务组 10 分钟起步）
12. 明确 **Agent 上线门禁**（校验/测试/审批）

### P2（规模化预留）

13. 多租户（tenant）与资源隔离
14. 自动 Eval / 回归（基于样板 Agent 数据集）
15. Agent 能力复用（Workflow/Skill 库）
16. 平台 SLA / SLO 与告警

---

## 3️⃣ 平台化能力模块（逐项落地）

---

### 🗂️ 1. Agent Registry / Catalog

**目标**

* 平台知道“现在有哪些 Agent/Tool/Policy，谁负责，是否可用”

**最小实现（MVP+）**

* Registry 表：`name / version / kind / owner / stage / status / createdAt`
* API：register / list / get / deprecate
* stage 只允许：`dev | canary | prod`

**推荐路径**

* 存储：SQLite → PostgreSQL
* API：control-plane/registry/service.py
* Console：Agent 列表页 + 状态标签

**常见坑**

* 允许“覆盖版本” → **禁止**，版本必须不可变
* 不区分 stage → 导致测试 Agent 被误用

---

### ⚙️ 2. 动态配置（Prompt / Model / Tool）

**目标**

* 不改代码即可调整 Agent 行为；支持灰度与回滚

**最小实现**

* Spec 中只引用 `promptRef/modelRef`
* promptRef 支持版本目录：`prompts/v1/`, `prompts/v2/`
* 灰度规则：`labels.stage=canary` + 手工路由

**推荐路径**

* Prompt：repo 文件 → 后续配置中心
* Model：Spec 中声明 → 后续 model registry
* 回滚：Registry 指回旧 version

**常见坑**

* Prompt 直接写在 Agent 代码里
* 线上直接改 Prompt 文件无审计

---

### 🧠 3. Session / State 管理

**目标**

* 多 Agent 并发运行可追溯、可回放、可审计

**最小实现**

* SessionId / RunId 全局唯一
* Session 历史（消息/中间结果）可查询
* RunEvent 持久化（jsonl/DB）

**推荐路径**

* MVP：文件或 SQLite
* 演进：DB + 对象存储
* 回放：`agentctl replay --runId`

**常见坑**

* 只存最终结果 → 无法调试
* Session 和 Run 概念混淆

---

### 🔐 4. 权限与多团队治理

**目标**

* 多业务组并行开发 Agent，不互相踩线

**最小实现**

* Owner=团队
* Agent/Tool 只能由 Owner 修改
* Policy 控制：Agent 能否调用某 Tool

**推荐路径**

* Owner 字段 + 简单 ACL
* PolicySpec 控制 tool.call / model.use

**常见坑**

* 一开始就做复杂 RBAC → 拖慢平台
* 工具权限与 Agent 权限不分

---

### 👁️ 5. Observability（平台视角）

**目标**

* 平台能回答：**哪些 Agent 在跑？是否稳定？花了多少钱？**

**最小实现**

* 指标：成功率、P95 耗时、token/cost、失败原因
* 维度：Agent / Version / Team
* Trace：能从 RunId 看到完整事件

**推荐路径**

* MVP：events.jsonl + 聚合脚本
* 演进：OTLP + Prometheus / Langfuse

**常见坑**

* 只看日志，不看事件
* 成本统计口径不统一

---

### 🧪 6. Eval & 质量门禁（平台化起点）

**目标**

* Agent 行为可回归、可比较、可约束

**最小实现**

* 每个 Agent 有“样例输入集”
* 新版本必须跑样例输入
* 人审或规则校验通过才允许 stage=prod

**推荐路径**

* MVP：手工数据集 + rule-based 校验
* 演进：自动 Eval + 评分

**常见坑**

* 没有回归 → Agent 越改越差
* Eval 过早复杂化

---

## 4️⃣ 组织形态：平台组 + 业务组（RACI）

### 👥 平台组（Platform Team）

**负责（R）**

* Agent OS / 平台架构
* Spec / PAL / Runtime Adapter
* Registry / Policy / Observability
* CI / 门禁 / 安全

**交付物**

* agentctl
* Agent/Tool 模板
* Console
* 平台 SLA

---

### 👥 业务组（Domain Teams）

**负责（R）**

* 业务 Agent（Spec + Prompt + Tool 实现）
* 用例/需求/知识的业务正确性
* Agent 输出质量

**配合（C）**

* 提交 AgentSpec/ToolSpec
* 提供 Eval 数据

---

### 🚦 决策边界（关键）

| 决策         | 平台组  | 业务组 |
| ---------- | ---- | --- |
| Spec 格式    | ✅ 决定 | ❌   |
| Runtime 技术 | ✅ 决定 | ❌   |
| Prompt 内容  | ❌    | ✅   |
| Tool 逻辑    | ❌    | ✅   |
| 上线门禁       | ✅    | ❌   |
| Agent 何时下线 | ✅    | 参与  |

---

## 5️⃣ Agent 生命周期（平台化）

```text
draft
  └─(validate+test)→ active(dev)
        └─(review)→ active(canary)
              └─(eval+metrics)→ active(prod)
                    └─ deprecated
                          └─ disabled
```

* **只有 prod** 才能被默认路由
* deprecated 仍可回放/审计
* disabled 不允许新 Run

---

## 6️⃣ 从 B5 → B6 的实施顺序（很重要）

1. 把 **测试用例生成 Agent** 注册进 Registry
2. 用它验证：版本、stage、路由、观测
3. 引入第二个 Agent（例如“测试计划生成”）
4. 验证多 Agent 并行运行不互相影响
5. 再开放给更多业务组

👉 **顺序反了，平台一定失控**

---

## 7️⃣ 风险与回滚方案（≥3）

1. **风险：业务组绕过平台直接写 agno Agent**

   * 回滚：禁止 agno 依赖 + 提供好用模板

2. **风险：平台组变成“瓶颈审批官”**

   * 回滚：门禁自动化（CI + Spec 校验 + Eval）

3. **风险：Agent 爆炸式增长导致治理崩溃**

   * 回滚：强制 Owner、强制版本、强制下线策略

4. **风险：平台和业务职责不清**

   * 回滚：RACI 固化进 README / 内部规范
