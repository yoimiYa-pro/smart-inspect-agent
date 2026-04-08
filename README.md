# 智能合同审查助手

基于 `Vue 3 + Vite` 与 `FastAPI` 的本地优先合同审查项目。

它不是简单做“风险命中”，而是围绕 **角色视角、风险优先级、签约建议、法律依据、相似案例、合同对话** 做完整输出，适合比赛展示、课程答辩、产品原型演示与本地部署。

## 智能体能力对照（答辩材料）

本系统实现为 **编排式混合智能体**：后端固定规划审查子步骤，在关键步骤调用 **腾讯混元（OpenAI 兼容 API）** 完成语言增强与对话；并在 Prompt 构造前执行 **确定性工具**（金额/期限片段抽取、条款序号列表）将结果注入模型上下文，体现「行动」闭环。

| 赛道要素 | 在本项目中的体现 |
| --- | --- |
| **感知** | 条款切分、合同类型与规则命中、角色视角输入；对话轮次理解用户追问 |
| **规划** | 固定流水线：切分 → 规则识别 → Prompt 组装 → LLM 增强 → 结构化合并（前端加载时展示流水线示意） |
| **行动** | 调用混元 API；后端 `deterministic_tool_outputs`（启发式抽取 + 条款序号）注入 enhance 阶段 |
| **记忆** | 合同级多轮 `messages` 上下文；分析结果对象作为后续对话的只读依据 |

## 项目亮点

- 支持从 **甲方 / 乙方** 视角审查合同
- 强制执行 AI 工作流：**条款切分 → 规则识别 → Prompt 构造 → LLM 生成 → 结构化输出**
- 输出 **AI 一句话结论、总体风险等级、风险评分、签约建议、是否建议咨询律师**
- 风险结果分层展示：**🚨 高风险 TOP3 / 🟡 中风险 / 🟢 低风险**
- 每条风险均包含：
  - `reason` 法律视角说明
  - `plain_explanation` 通俗解释
  - `suggestion` 修改建议
  - `role_impact` 角色影响
  - `legal_basis` 法律依据
  - `case_reference` 相似案例提示
- 新增合同级对话接口：`chat_with_contract()` / `POST /api/chat`
- 真实模型失败、未配置、返回异常 JSON 时，自动回退到本地 `mock`，保证系统不崩溃

## 使用场景

- 采购 / 服务 / 技术开发合同的快速预审
- 招投标、外包、软件交付前的风险预警
- 甲方法务、乙方销售、项目经理的签约前自查
- 课堂作业、比赛项目、合同 AI 产品 demo

## AI 工作流

后端审查流程固定为：

1. **条款切分**
   - 自动按“第X条 / 1. / 一、”等结构切分
   - 若原文不规范，则回退到段落 / 句子切分

2. **规则识别**
   - 识别付款、责任、解除、保密与数据、知识产权、争议解决等核心风险
   - 对缺失条款、单方优势条款、责任失衡条款进行结构化命中

3. **Prompt 构造**
   - 将条款切分结果、规则命中结果、风险草稿、角色视角和整体结论打包为 Prompt

4. **LLM 生成**
   - 只要求模型返回 JSON
   - 模型负责补充专业表达、通俗解释、法律依据与相似案例

5. **结构化输出**
   - 后端统一整理为稳定字段供前端渲染与对话继续使用

## 功能说明

### 1. 合同分析

输入合同全文后，系统会输出：

- 合同类型识别
- 合同切分条款列表
- 风险卡片清单
- 风险优先级排序
- TOP3 最危险条款
- 角色视角判断
- 风险评分 `risk_score`
- 总体风险等级 `overall_risk_level`
- 签约建议 `signing_advice`
- 律师建议 `lawyer_suggestion`
- 顶部一句话结论 `one_line_conclusion`

首页与审查页底部输入条提供 **「示例合同…」** 下拉框，可一键填入三份示范节选（房屋租赁、商品买卖、技术服务），体例参考 [全国合同示范文本库](http://htsfwb.samr.gov.cn/)，便于演示；正式缔约请以官方最新文本为准。

### 2. 每条风险的结构化字段

每个风险项至少包含：

- `title`
- `severity`
- `priority_rank`
- `reason`
- `plain_explanation`
- `suggestion`
- `role_impact`
- `legal_basis`
- `case_reference`
- `followup_hint`

### 3. 合同对话能力

前端支持对当前合同继续提问，例如：

- 这份合同安全吗？
- 哪些条款最危险？
- 我应该注意什么？
- 如果我是乙方，最应该先改哪3条？

回答会结合：

- 当前分析结论
- TOP3 风险
- 用户角色视角
- 已有聊天上下文

### 4. 模型异常兜底

以下情况都会自动 fallback：

- 未配置 `OPENAI_API_KEY`
- 未配置 `OPENAI_MODEL`
- 请求超时
- 返回内容不是合法 JSON
- 兼容接口不可用

fallback 模式下仍然可以：

- 完成合同审查
- 生成结构化风险
- 给出签约建议
- 使用合同对话功能

## 项目结构

```text
smatr-inspect-agent/
├─ backend/
│  ├─ app/
│  │  ├─ main.py                 # FastAPI 入口与 API 路由
│  │  ├─ config.py               # 环境变量与运行配置
│  │  ├─ schemas.py              # 统一数据模型
│  │  └─ services/
│  │     ├─ analyzer.py          # 条款切分、规则识别、总结与对话编排
│  │     ├─ contract_tools.py    # 确定性工具输出（金额/期限片段、条款序号），注入 LLM 上下文
│  │     ├─ llm_client.py        # OpenAI 兼容接口调用，强制 JSON 输出
│  │     └─ mock_fallback.py     # 本地 fallback 与聊天兜底
│  └─ requirements.txt
├─ frontend/
│  ├─ src/
│  │  ├─ App.vue                 # 主界面组装
│  │  ├─ components/             # 分区展示组件、审查流水线进度、锚点导航等
│  │  ├─ api.js                  # 前端 API 封装
│  │  ├─ main.js
│  │  └─ styles.css              # 页面视觉与响应式布局
│  ├─ index.html
│  ├─ package.json
│  └─ vite.config.js
├─ deploy/
├─ .env.example
├─ README.md
└─ DEPLOY.md
```

## 本地运行

### 环境要求

- Python `3.10+`
- Node.js `18+`

### 1）配置环境变量

在项目根目录复制：

```powershell
Copy-Item .env.example .env
```

如果暂时不接入模型，可以直接留空 `OPENAI_API_KEY` 和 `OPENAI_MODEL`，系统会自动启用 mock。

### 2）启动后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

健康检查：

```text
http://127.0.0.1:8000/api/health
```

### 3）启动前端

新开一个终端：

```powershell
cd frontend
npm install
npm run dev
```

浏览器访问：

```text
http://127.0.0.1:5173
```

默认使用 `Vite proxy` 将 `/api` 转发到 `http://127.0.0.1:8000`。

### 4）构建前端并由后端托管

```powershell
cd frontend
npm install
npm run build
```

构建完成后，只启动 FastAPI 也可直接访问：

```text
http://127.0.0.1:8000
```

## API 说明

### `POST /api/review`

请求体：

```json
{
  "text": "合同全文...",
  "role": "乙方",
  "enhance_with_llm": true
}
```

### `POST /api/chat`

请求体核心字段：

```json
{
  "contract_text": "合同全文...",
  "role": "乙方",
  "question": "这份合同安全吗？",
  "messages": [],
  "analysis": { "...": "review 结果对象" },
  "enhance_with_llm": true
}
```

### `POST /api/followup`

保留单风险追问接口，适合对某一条具体风险进行追问。

## 腾讯混元与 OpenAI 兼容 API 配置

本项目通过 **OpenAI 协议兼容** 客户端调用大模型（见 `backend/app/services/llm_client.py`），便于对接 **腾讯混元** 或其他兼容网关。

在 `.env` 中配置（示例为混元，密钥与 Base URL 以控制台为准）：

```env
OPENAI_API_KEY=你的_API_Key
OPENAI_API_BASE=https://api.hunyuan.cloud.tencent.com/v1
OPENAI_MODEL=hunyuan-turbos-latest
```

说明：

- `OPENAI_MODEL` 须与混元控制台可用的模型 ID 一致（如 `hunyuan-turbos-latest` 等）。
- 未配置密钥或请求失败时，系统自动 **mock 兜底**，仍可完整演示审查与对话流程。

若使用官方 **OpenAI**，可改为：

```env
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o-mini
```

## 得理法规与案例检索（可选）

配置后，在 **启用 LLM 增强** 的审查流程中会对优先风险并行调用：

- **法规**：`queryListLaw`，结果写入 `law_references`，参与 `legal_basis` 增强；前端可点击 **查看全文**（经后端代理 `lawInfo`，密钥不暴露给浏览器）。
- **案例**：`queryListCase`（请求体 `condition.keywordArr` 与开放平台一致），结果写入 `case_references`，参与 `case_reference` 增强；前端展示检索到的标题及法院、案号等元数据（首版不提供案例全文代理）。

在 `.env` 中可配置（示例值请替换为控制台真实凭证）：

```env
DELILEGAL_APPID=
DELILEGAL_SECRET=
# 可选
# DELILEGAL_API_BASE=https://openapi.delilegal.com
# DELILEGAL_TIMEOUT_SECONDS=20
# DELILEGAL_MAX_RISKS=8
# DELILEGAL_FETCH_DETAIL_IN_REVIEW=false
# DELILEGAL_EXCERPT_MAX_CHARS=1500
```

未配置时行为与原先一致；`/api/health` 中 `delilegal_enabled` 表示是否已配置。

## 展示建议

比赛展示时建议按以下顺序演示：

1. 贴入一份明显偏向单方的合同
2. 切换 `甲方 / 乙方` 视角对比结果
3. 展示顶部一句话结论、总体风险、风险评分
4. 展示 TOP3 风险与法律依据
5. 点击某条风险的“提问这条”进入合同对话
6. 关闭模型配置，展示 mock fallback 依然可用

## 部署

仓库已提供 CentOS 7.9 部署相关文件：

- `DEPLOY.md`
- `deploy/centos7/nginx-smart-inspect.conf`
- `deploy/centos7/smart-inspect-backend.service`
