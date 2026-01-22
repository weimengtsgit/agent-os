## 1️⃣ 本轮产出摘要（B0）

1. 明确了 **Agent 底座 / Agent OS 的目标边界**：不是做业务 Agent，而是做“可规模化的 Agent 平台能力”
2. 将 agno **初始定位为 Agent Runtime + 部分 Control Plane 能力提供者**，而不是完整平台
3. 确认必须引入 **平台抽象层（PAL, Platform Abstraction Layer）**，避免未来被 agno 锁死
4. 确定平台建设必须 **Spec-first**（先定义 Agent / Tool / Run / Trace / Policy 契约）
5. 明确 MVP 阶段的成功标准：**1 个 Agent 跑通 + 可复制 + 可观测**
6. 把“不确定性”显式转成了 **可验证假设与 TODO**
7. 为下一轮（B1）铺好了 **Backlog 化输入结构**

---

## 2️⃣ 可执行 TODO 清单（P0 / P1 / P2）

### P0（必须立刻做，不做无法开工）

1. 明确定义 **Agent 底座的非目标清单**（避免平台无限膨胀）
2. 选定 **第一个样板 Agent 类型**（对话 / 流程 / 分析 / 自动化）
3. 决定 **是否强制 Spec-first（Agent Spec / Tool Spec）**
4. 设计 **Platform Abstraction Layer（PAL）初版接口范围**
5. 确认 **agno 仅作为 Runtime，而非唯一真理层**
6. 确定 **最小可观测性要求**（trace / log / token / cost 至少到什么粒度）

### P1（MVP 阶段必须补齐）

7. 定义 **Agent Registry 的最小字段集**（name / owner / version / capability）
8. 明确 **Session / Run / State 的存储策略假设**
9. 选定 **agent-ui 的使用方式**（直接用 / fork / 仅参考）
10. 确定 **Tool 调用的安全与权限边界**
11. 明确 **人审（Human-in-the-loop）在 MVP 是否必须**
12. 明确 **配置是“代码即配置”还是“平台动态配置”**

### P2（后续演进，但现在要预留）

13. Agent / Prompt / Tool 的版本管理策略
14. Eval 与质量门禁是否纳入平台职责
15. 多团队并行开发 Agent 的治理模型
16. agno 升级或替换的迁移策略预案

---

## 3️⃣ 关键接口 / 契约草案（B0 级，先定方向）

> ⚠️ 注意：这里不是最终版，而是 **“先把边界钉死”** 的草案

### 3.1 Agent Spec（平台级，而非 agno 内部对象）

```yaml
apiVersion: agent.platform/v1
kind: Agent
metadata:
  name: test-case-generator
  owner: qa-platform
  version: v0.1.0
spec:
  type: workflow | conversational | batch
  description: Generate test cases from requirements
  model:
    provider: openai
    name: gpt-4.1
  promptRef: prompts/test_case_v1
  tools:
    - jira_reader
    - testcase_writer
  policies:
    maxTokens: 8000
    allowTools:
      - jira_reader
  observability:
    trace: enabled
    costTracking: enabled
```

---

### 3.2 Run / Session 事件契约（与 Runtime 解耦）

```json
{
  "runId": "run-123",
  "agent": "test-case-generator",
  "sessionId": "session-456",
  "eventType": "tool_call",
  "timestamp": "2026-01-21T10:00:00Z",
  "payload": {
    "tool": "jira_reader",
    "input": { "issueKey": "PROJ-123" }
  }
}
```

> 这个契约 **不允许直接依赖 agno 内部对象结构**

---

## 4️⃣ 目录结构 / 模块划分建议（最小可开工）

### 推荐：**多 repo，但先从 2 个开始**

```text
agent-os/
├── control-plane/          # 平台核心（PAL + Spec + Registry）
│   ├── agent_control_plane/
│   │   ├── specs/
│   │   │   ├── agent.yaml
│   │   │   ├── tool.yaml
│   │   │   └── run-event.json
│   │   ├── pal/
│   │   │   ├── llm.py
│   │   │   ├── runtime.py
│   │   │   └── memory.py
│   │   └── registry/
│   │ 
├── agent-runtime/     # Runtime 适配层
│   ├── agno/
│   │   ├── agent_runtime_agno/
│   │   │   ├── adapters/
│   │   │   │   ├── agent_adapter.py
│   │   │   │   ├── tool_adapter.py
│   │   │   └── bootstrap.py
│   │   └── pyproject.toml
├── agents/                 # 业务 Agent（样板与示例）
│   └── test-case-generator/
│
└── console/                # 控制面（agent-ui / 自研）
```

---

## 5️⃣ 里程碑与验收标准（量化）

### M0（1 周内）

* [ ] 能用 Spec 定义一个 Agent
* [ ] Spec 可被解析并启动 Runtime

### M1（2~3 周）

* [ ] 第一个 Agent 可端到端跑通
* [ ] 每次 Run 有 traceId
* [ ] Tool 调用可被审计

### M2（4~6 周）

* [ ] 第二个 Agent 复用平台能力
* [ ] Agent 可配置（prompt 或 model）
* [ ] 失败 Run 可回放

---

## 6️⃣ 风险与回滚方案

### 风险 1：过早深度绑定 agno 内部模型

* **信号**：Agent Spec 直接映射到 agno 类
* **回滚**：强制通过 PAL + Adapter 层调用 agno

### 风险 2：平台一开始就想“全做”

* **信号**：Backlog 超过 30 个 P0
* **回滚**：冻结治理/评测类需求，只保留 Runtime + Trace

### 风险 3：agent-ui 不适配企业需求

* **信号**：大量 fork / hack
* **回滚**：仅保留其数据模型与交互范式，自研最小 Console
