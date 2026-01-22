## 1️⃣ 本轮产出摘要（B5）

1. 选定 MVP 样板：**测试用例生成 Agent（Test Case Generator）**，原因是“价值直观、工具链清晰、人审天然、可复制到其它 Agent”
2. 给出端到端闭环：**输入（需求）→检索（Jira/文档）→生成（LLM）→校验（规则/覆盖）→人审→落库/回写→观测/审计**
3. 定义 MVP 的最小控制台能力（6+）：Agent 列表、Run 列表、事件流、输入/输出、人工审核、成本/耗时
4. 明确关键非功能清单：**超时、取消、重试、幂等、审计、成本统计、降级**
5. 提供 Week1~Week6 交付计划 + 每周验收标准 + Demo 脚本
6. 输出本次需要新增的最小契约字段/事件类型（在不破坏 B3 schema 的前提下）

---

## 2️⃣ 可执行 TODO 清单（P0/P1/P2，≥12）

### P0（MVP 必须做）

1. 创建样板 Agent：`agents/test-case-generator/`（spec + prompt + inputs）
2. 实现最小 Tool 套件（先 mock 后对接）：`requirements_reader`、`testcase_writer`、`testcase_repo`
3. 在 ToolExecutor 中落地：**超时 + 重试 + 事件**（tool_call/tool_result）
4. 在 Runtime Adapter 中落地：**run_start/run_end/run_error/run_cancel** 事件齐全
5. 输出结果标准化：生成的测试用例必须是结构化 JSON（便于回写/审计）
6. 增加人审流程：human_review_request/human_review_result（至少支持 approve/reject）
7. events.jsonl 落盘 + 运行目录规范（runs/<runId>/）
8. 最小 Console：能选中一次 Run 查看事件流与最终产物

### P1（强烈建议在 MVP 内完成）

9. 对接真实需求来源（Jira/需求系统）至少一种（read-only 即可）
10. 增加“规则校验”步骤（必选字段、覆盖维度、重复用例检测）作为 run_step 或 tool
11. 增加幂等键：同一需求版本重复运行可复用结果或生成新版本
12. 成本/耗时统计：每次 Run 汇总 token/cost/duration 到 run_end payload
13. 回写通道：把用例写入测试管理系统/仓库（先写本地 JSON/Markdown）

### P2（先预留，后续做）

14. 多模型路由：便宜模型草稿 + 贵模型精修
15. 自动 Eval：用历史需求/用例回归评测
16. 覆盖度指标：功能点覆盖、场景覆盖、边界覆盖可视化

---

## 3️⃣ 关键接口/契约草案（MVP 补充点）

> 不改 B3 schema，只规定 payload 约定（平台可校验/可观测）。

### 3.1 测试用例输出结构（LLM 产物标准）

```json
{
  "requirementId": "PROJ-123",
  "requirementVersion": "v12",
  "testCases": [
    {
      "id": "TC-001",
      "title": "登录成功-正确用户名密码",
      "type": "functional",
      "priority": "P1",
      "preconditions": ["用户已注册", "网络正常"],
      "steps": [
        { "action": "打开登录页", "expected": "展示登录表单" },
        { "action": "输入正确用户名密码并提交", "expected": "进入首页并展示用户信息" }
      ],
      "tags": ["login", "happy-path"],
      "coverage": { "feature": "auth.login", "risk": "medium" }
    }
  ],
  "notes": "生成依据：需求描述+验收标准",
  "quality": { "missingInfo": [], "assumptions": ["用户名密码规则按现网"] }
}
```

### 3.2 人审事件 payload 约定（RunEvent.payload）

**human_review_request**

```json
{
  "stage": "testcase_review",
  "artifactPath": "runs/run-123/artifacts/testcases.json",
  "summary": { "count": 23, "highPriority": 5 },
  "reviewHints": ["检查边界场景", "检查异常路径"]
}
```

**human_review_result**

```json
{
  "stage": "testcase_review",
  "decision": "approve",
  "comments": "补充了密码错误次数限制场景",
  "patch": {
    "type": "json-merge",
    "content": { "testCases": [/* optionally patched */] }
  }
}
```

---

## 4️⃣ MVP 最小控制台能力（≥6）

你可以用 `console/minimal` 很快实现，先不追求 agent-ui。

1. **Agent 列表**：从 registry 读 AgentSpec（name/version/owner/stage）
2. **Run 列表**：按时间列出 runs（runId/agent/status/duration/cost）
3. **Run 详情**：展示 events.jsonl（过滤 eventType、按 tool 分组）
4. **Artifacts 视图**：展示生成的 `testcases.json`（支持下载/复制）
5. **人审面板**：Approve/Reject + 评论（写入 human_review_result 事件）
6. **成本/耗时面板**：token/cost/duration 汇总（来自 run_end payload）

> MVP 的 UI 只要能“看见一次运行发生了什么”，就已经值回票价。

---

## 5️⃣ 关键非功能清单（MVP 必须具备）

1. **超时**

   * tool 级 timeoutMs（来自 ToolSpec）
   * run 级 timeoutMs（来自 AgentSpec.limits）

2. **取消**

   * `agentctl cancel --runId` 或 Console 按钮
   * cancel 后必须发 `run_cancel` 事件并停止 tool 调用

3. **重试**

   * tool retry（来自 ToolSpec.retry）
   * 每次重试 tool_call payload 带 attempt

4. **幂等**

   * 幂等键：`requirementId + requirementVersion + agentVersion`
   * 同键重复运行：生成新 run，但 artifact 可复用或产生新 revision

5. **审计**

   * 需求读取、工具调用、人审决定必须有事件记录

6. **成本统计**

   * run_end payload 汇总：promptTokens/completionTokens/totalTokens/cost

7. **降级策略**

   * 如果 Jira 读不到：允许用户手工粘贴需求文本
   * 如果 LLM 失败：保留上下文与失败原因（run_error）

---

## 6️⃣ Week1~Week6 计划（每周交付 + 验收）

### Week 1：闭环骨架跑通（mock 工具）

* 交付：AgentSpec + prompt + run-local
* 工具：echo / requirements_reader(mock) / testcase_repo(local file)
* 验收：

  * 能跑一次 run，落 events.jsonl
  * 有 run_start/run_end/tool_call/tool_result

### Week 2：结构化产物 + 人审闭环

* 交付：testcases.json 结构化输出 + human_review_request/result
* 验收：

  * Console 能 approve/reject
  * 审批决定写入事件流

### Week 3：接入真实需求源（Jira read-only）

* 交付：jira_reader tool（或 requirements_reader 对接 Jira）
* 验收：

  * 输入 requirementId 能拉取需求文本+验收标准
  * 可在事件中看到读取结果摘要（不要写敏感全文）

### Week 4：质量校验（规则/覆盖）

* 交付：testcase_validator tool（检查必填、重复、覆盖维度）
* 验收：

  * validator 输出质量报告
  * 人审界面展示质量报告

### Week 5：回写/落库（最小）

* 交付：testcase_writer（写 Markdown/JSON 到 repo 或测试系统）
* 验收：

  * run_end 指向 artifactPath
  * 可追溯：从需求 → 用例文件路径

### Week 6：稳定性与可观测完善

* 交付：取消/重试/超时完整 + cost/duration 汇总
* 验收：

  * 故意超时/取消能正确终止并记录
  * run_end 有成本与耗时汇总

---

## 7️⃣ Demo 脚本（对外演示 5–8 分钟）

1. 打开 Console：展示 Agent 列表（test-case-generator）
2. 输入需求：填 `PROJ-123` 或粘贴需求文本 → 点击 Run
3. 展示运行中事件：run_start → tool_call(jira_reader) → tool_result
4. 展示生成步骤：run_step（生成中）→ artifact 产出 `testcases.json`
5. 触发人审：human_review_request → 在 UI 里 approve 并补充评论
6. 展示回写：tool_call(testcase_writer) → tool_result → run_end
7. 展示成本：token/cost/duration 汇总
8. 总结：**同样方式可以复用到“测试计划生成、缺陷分析、发布评估”等 Agent**

---

## 8️⃣ 风险与回滚方案（≥3）

1. **风险：Jira 接入周期拖慢 MVP**

   * 回滚：Week1~2 用 mock + 手工粘贴输入，Week3 再接 Jira

2. **风险：生成结果不结构化导致无法回写/审计**

   * 回滚：强制模型输出 JSON（并用 validator 校验），不通过则重试/人审修复

3. **风险：人审流程过重影响演示**

   * 回滚：MVP 只保留一个人审点（生成后），其余全部自动

4. **风险：工具链权限/密钥管理复杂**

   * 回滚：MVP 工具只读 + 使用本地 env secrets；不把密钥写 spec
