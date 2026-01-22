任务：补齐平台工程化能力。

【Console（最小）】
- /runs：列出 runs
- /runs/<id>：展示 events.jsonl + artifacts
- 若存在 human_review_request，提供 approve / reject

【Contract Tests】
- 固定输入跑 sample-agent
- 断言：
  - 事件顺序
  - 必要字段存在

【Guard】
- CI 中禁止：
  - control-plane / agents import agno

【交付】
- Console 代码
- pytest contract tests
- CI workflow 示例
