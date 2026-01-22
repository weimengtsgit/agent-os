## 1️⃣ 本轮产出摘要（B4）

1. 推荐 **mono-repo 起步**（一个仓库内分包），以“明天能开工 + 统一契约/CI”为优先；后续再拆 repo
2. 给出可直接落地的 **目录结构到 3 层**，覆盖 core/specs/registry/pal/sdk + agno runtime adapter + console + 示例 agents
3. 提供 **Agent 模板 / Tool 模板 / Workflow 模板（可选）**：包含示例 YAML（符合 B3 的 schema）
4. 给出 **配置管理策略**：Spec/Prompt/ModelRef 的存放方式、加载规则、灰度/回滚最小实现
5. 给出 **CI 最小流水线**：schema validate + unit tests + contract tests + dependency guard（禁止业务直接依赖 agno）
6. 给出“明天开工”的 **第一周里程碑**与验收口径

---

## 2️⃣ 可执行 TODO 清单（P0/P1/P2，≥12）

### P0（明天开工必须做）

1. 初始化 mono-repo 目录结构（见下文树）并跑通最小 `python -m` 包导入
2. 把 B3 的 5 个 schema 落盘到 `control-plane/specs/schemas/`
3. 实现 `agentctl validate`：对 `agents/**.yaml` 做 JSON Schema 校验
4. 实现 `agentctl run-local`：读取 `agent.yaml` → 选择 runtime(selector=agno) → 启动适配器
5. 加入 CI：对所有 PR 执行 `agentctl validate`
6. 加入 CI：dependency guard，阻止 `agents/` 或 `control-plane/sdk` 引入 agno 包
7. 建立 sample agent（最少 1 个）+ sample tool（最少 1 个），跑通 end-to-end（即便 tool 是 mock）

### P1（1~2 周内补齐）

8. 实现 `agentctl register`：把 Agent/Tool/Policy 写入 Registry（先 SQLite）
9. 实现 contract test 框架：固定输入 → 输出 RunEvent 序列断言
10. 实现 `agentctl replay`：从 events.jsonl 回放 run（MVP 级）
11. Console（最小）：Run 列表 + Run 事件流查看（先读文件或 SQLite）
12. Tool 模板支持超时/重试配置（从 tool spec 生效）

### P2（预留但现在定规矩）

13. Spec 的版本化资源：promptRef/modelRef 约定命名规则并写进 README
14. 灰度机制：支持 `labels.stage=canary` + `registry` 路由（后续）
15. 工作流模板：先占位，后续再接 agno workflow/teams 能力
16. 安全：预留 secrets 接口（不把密钥写入 spec）

---

## 3️⃣ 关键接口 / 契约草案（工程脚手架相关）

### 3.1 `agentctl` CLI 命令契约（伪代码）

```text
agentctl validate  [--path agents/]                 # schema 校验
agentctl run-local --agent agents/sample-agent/agent.yaml --input input.json
agentctl register  --path agents/                   # 注册到 registry
agentctl list      [--kind Agent|Tool|Policy]       # 查询 registry
agentctl show      --kind Agent --name xxx --version v0.1.0
agentctl replay    --events runs/run-123/events.jsonl
```

### 3.2 Spec 加载契约（SDK 内部接口，伪代码）

```python
load_agent_spec(path) -> AgentSpec
load_tool_spec(path) -> ToolSpec
validate_spec(obj, schema_name) -> None
resolve_prompt(promptRef) -> str  # 先支持 file path，后续支持 prompt://
```

---

## 4️⃣ 目录结构 / 模块划分建议（mono-repo 推荐）

```text
agent-os/                         # mono-repo
├── pyproject.toml
├── README.md
├── .github/
│   └── workflows/
│       └── ci.yml
├── control-plane/
│   ├── agent_control_plane/
│   │   ├── specs/
│   │   │   ├── schemas/
│   │   │   │   ├── agent.schema.json
│   │   │   │   ├── tool.schema.json
│   │   │   │   ├── run-event.schema.json
│   │   │   │   ├── trace-span.schema.json
│   │   │   │   └── policy.schema.json
│   │   │   ├── validator.py
│   │   │   └── README.md
│   │   ├── pal/
│   │   │   ├── types.py
│   │   │   ├── runtime.py
│   │   │   ├── tools.py
│   │   │   ├── llm.py
│   │   │   ├── memory.py
│   │   │   ├── observability.py
│   │   │   └── policy.py
│   │   ├── registry/
│   │   │   ├── store_sqlite.py
│   │   │   ├── service.py
│   │   │   └── models.py
│   │   └── sdk/
│   │       ├── loader.py
│   │       ├── runtime_router.py
│   │       ├── tool_executor.py
│   │       └── cli/
│   │           ├── __init__.py
│   │           ├── validate.py
│   │           ├── run_local.py
│   │           ├── register.py
│   │           └── replay.py
├── agent-runtime/
│   ├── agno/
│   │   ├── adapters/
│   │   │   ├── agno_runtime.py
│   │   │   ├── agno_tool_bridge.py
│   │   │   └── agno_event_bridge.py
│   │   ├── tests/
│   │   │   ├── contract/
│   │   │   └── fixtures/
│   └── README.md
├── console/
│   └── minimal/
│       ├── server.py                 # MVP: runs list + event viewer
│       └── ui/                       # 可后续换 agent-ui
├── agents/
│   ├── sample-agent/
│   │   ├── agent.yaml
│   │   ├── prompts/
│   │   │   └── prompt.txt
│   │   ├── tools/
│   │   │   └── echo.tool.yaml
│   │   └── inputs/
│   │       └── input.json
│   └── README.md
└── runs/
    └── .gitkeep                      # 本地 run 产物（events.jsonl等）
```

**为什么 mono-repo 起步更好**

* schema、PAL、adapter、样板 agent **必须同步演进**，拆 repo 会把 CI/契约一致性搞复杂
* 等到平台稳定再拆（例如 `control-plane` 独立 repo）成本更低

---

## 5️⃣ 模板（明天就能复制）

### 5.1 Agent 模板：`agents/<agent-name>/agent.yaml`

```yaml
apiVersion: agent.platform/v1
kind: Agent
metadata:
  name: sample-agent
  version: v0.1.0
  owner: platform-team
  labels:
    stage: dev
  description: "Sample agent that calls echo tool"
spec:
  type: conversational
  runtime:
    selector: agno
    params: {}
  modelRef:
    provider: openai
    name: gpt-4.1
    params:
      temperature: 0.2
  promptRef: prompts/prompt.txt
  tools:
    - echo
  policiesRef: []
  limits:
    maxTokens: 4000
    maxToolCalls: 5
    timeoutMs: 120000
  observability:
    trace: true
    costTracking: true
    eventLevel: standard
```

### 5.2 Tool 模板：`agents/<agent-name>/tools/echo.tool.yaml`

```yaml
apiVersion: agent.platform/v1
kind: Tool
metadata:
  name: echo
  version: v0.1.0
  owner: platform-team
  description: "Echo tool for MVP"
spec:
  inputsSchema:
    type: object
    properties:
      text:
        type: string
    required: [text]
  outputsSchema:
    type: object
    properties:
      text:
        type: string
    required: [text]
  timeoutMs: 1000
  retry: 0
  idempotent: true
  sideEffects: false
  auth:
    type: none
    scopes: []
  permissions: []
  rateLimit:
    rps: 0
    burst: 0
```

### 5.3 Prompt 模板：`agents/<agent-name>/prompts/prompt.txt`

```text
You are a helpful agent.
If user asks to echo, call tool "echo" with {"text": "<content>"}.
Return the tool result to user.
```

### 5.4 输入样例：`agents/<agent-name>/inputs/input.json`

```json
{ "text": "echo: hello platform" }
```

---

## 6️⃣ 配置管理策略（Prompt/Model/Spec/灰度）

### MVP 规则（简单但不乱）

* **Spec（Agent/Tool/Policy）**：只放在 repo（`agents/**`），由 CI 校验
* **Prompt**：先文件引用（`promptRef: prompts/prompt.txt`），后续再上 prompt:// 资源服务
* **Model**：先写在 spec（provider/name/params），后续引入 `modelRef` 注册表
* **灰度/回滚（最小实现）**：

  * 用 `metadata.labels.stage=dev/canary/prod` 表示阶段
  * registry 只允许 `prod` 被默认路由
  * 回滚 = registry 指回旧 version（不改代码）

---

## 7️⃣ CI 最小流水线（Schema + 测试 + 防锁死）

### 7.1 CI 阶段（建议顺序）

1. **Lint/Format**（python）
2. **Schema Validate**：`agentctl validate --path agents/`
3. **Unit Tests**：`pytest control-plane`
4. **Contract Tests**：`pytest agent-runtime-agno/tests/contract`
5. **Dependency Guard**：扫描 `agents/` 与 `control-plane/sdk` 禁止 `agno` import

### 7.2 Dependency Guard（规则）

* **允许**：`agent-runtime-agno/**` import agno
* **禁止**：`control-plane/**`、`agents/**` 出现 `import agno` 或依赖 agno 包

> MVP 先用 grep/简单脚本即可，后续再用更专业的依赖分析。

---

## 8️⃣ 里程碑与验收标准（明天开工版）

### Day 1

* [ ] mono-repo 初始化完成
* [ ] schema 落盘 + `agentctl validate` 能跑
* [ ] sample-agent spec 校验通过

### Day 2–3

* [ ] `agentctl run-local` 能跑通 sample-agent
* [ ] 产出 `runs/<runId>/events.jsonl`，至少包含 run_start / run_end

### Week 1（验收）

* [ ] tool_call/tool_result 事件可见（echo tool）
* [ ] dependency guard 生效（PR 引入 agno 会失败）
* [ ] contract test 有至少 1 条（固定输入输出）

---

## 9️⃣ 风险与回滚方案（≥3）

1. **风险：mono-repo 变大后管理困难**

   * 回滚：稳定后拆出 `control-plane` 为独立 repo；schema 作为独立 package 发布

2. **风险：agent-ui 引入成本过高**

   * 回滚：先用 `console/minimal`（读 events.jsonl/SQLite），agent-ui 放到 Phase 2 再评估

3. **风险：spec/模板不够顺手导致业务绕路**

   * 回滚：把 `agentctl init agent/tool` 加入脚手架（下一阶段增强 DevX）

4. **风险：事件流/回放做得太晚导致不可调试**

   * 回滚：MVP 强制 events.jsonl 落盘，先解决“可见性”
