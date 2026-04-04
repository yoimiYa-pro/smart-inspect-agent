# 腾讯云 CentOS + 宝塔面板部署指南

本文适用于将当前项目部署到腾讯云 `CVM / 轻量应用服务器` 的 `CentOS 7.9` 环境，并通过**宝塔面板**完成网站、反向代理和进程守护配置。

当前项目的生产部署方式是：

- `Vue 3 + Vite` 前端先构建为 `frontend/dist`
- `FastAPI` 负责 API，并托管构建后的前端页面
- `Nginx` 通过宝塔面板配置为公网入口，统一反向代理到本机 `8000` 端口
- 如大模型不可用，系统会自动降级到本地 `mock`

---

## 一、部署架构

推荐使用下面这套结构：

```text
公网请求
   ↓
宝塔面板网站（Nginx）
   ↓ 反向代理到 127.0.0.1:8000
FastAPI（uvicorn）
   ├─ /api/* 接口
   └─ /    前端页面（frontend/dist）
```

这意味着：

- **前端不需要单独开 Vite 服务**
- **宝塔只需要做站点管理和反向代理**
- **后端进程建议用宝塔的 Supervisor / 进程守护管理器托管**

---

## 二、部署前准备

### 1）建议服务器配置

- 系统：`CentOS 7.9`
- CPU：`2 核` 及以上
- 内存：`2 GB` 及以上，推荐 `4 GB`
- 磁盘：`20 GB` 及以上

### 2）腾讯云安全组放行

请先在腾讯云控制台放行以下端口：

- `22`：SSH 登录
- `80`：HTTP
- `443`：HTTPS
- `8888` 或你的宝塔面板自定义端口：宝塔后台访问

如果你安装宝塔时改了面板端口，就放行你实际使用的那个端口。

### 3）本项目运行依赖

建议版本：

- Node.js `18+`
- Python `3.10+`
- Nginx `1.20+`

> `CentOS 7` 自带 Python 太旧，不建议直接使用系统 Python。本文仍然建议用 `Miniconda + Python 3.10` 跑后端；宝塔主要负责网站入口、反向代理和进程守护。

---

## 三、安装宝塔面板

先登录服务器：

```bash
ssh root@你的服务器公网IP
```

宝塔面板安装命令请**以宝塔官网当前 CentOS 安装脚本为准**。

安装完成后，你会拿到：

- 面板访问地址
- 面板用户名
- 面板密码

登录宝塔后，建议先完成：

1. 修改面板初始密码
2. 检查面板端口
3. 在安全组中确认已放行面板端口

---

## 四、在宝塔软件商店安装基础软件

进入宝塔面板后，先在“软件商店”安装：

- `Nginx`
- `Supervisor 管理器` 或 `进程守护管理器`
- `终端` 插件（如你的面板未启用）

Node.js 有两种方式：

### 方式 A：用宝塔安装 Node.js

如果你的面板里有 `Node.js 版本管理器`，直接安装 `Node.js 18+` 即可。

### 方式 B：在终端手动安装 Node.js

如果没有 Node 插件，就在宝塔终端或 SSH 中执行：

```bash
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install -y nodejs
node -v
npm -v
```

### Python 3.10 建议安装方式

仍推荐在终端安装 `Miniconda`：

```bash
cd /usr/local/src
sudo curl -LO https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
sudo bash Miniconda3-latest-Linux-x86_64.sh -b -p /opt/miniconda3
sudo /opt/miniconda3/bin/conda init bash
source ~/.bashrc
source /opt/miniconda3/bin/activate
conda create -y -n smart-inspect python=3.10
conda activate smart-inspect
python -V
```

---

## 五、上传项目代码

推荐把项目放到宝塔常用网站目录：

```text
/www/wwwroot/smart-inspect-agent
```

如果你用 Git 拉取：

```bash
mkdir -p /www/wwwroot
cd /www/wwwroot
git clone <你的仓库地址> smart-inspect-agent
cd /www/wwwroot/smart-inspect-agent
```

如果你不用 Git，也可以在宝塔“文件”里上传压缩包后解压到这个目录。

---

## 六、配置环境变量

在项目根目录复制环境变量：

```bash
cd /www/wwwroot/smart-inspect-agent
cp .env.example .env
vi .env
```

推荐至少检查这些变量：

```env
OPENAI_API_KEY=你的密钥
OPENAI_API_BASE=https://你的兼容接口/v1
OPENAI_MODEL=hunyuan-turbos-latest
LLM_TIMEOUT_SECONDS=30
LLM_FALLBACK_TO_MOCK=true
CORS_ORIGINS=http://127.0.0.1:5173,http://localhost:5173,http://127.0.0.1:8000,http://localhost:8000
VITE_API_BASE_URL=
```

当前后端支持的模型值为：

- `hunyuan-pro`
- `hunyuan-standard`
- `hunyuan-large`
- `hunyuan-turbos-latest`

### 如果你想先不接大模型

可以留空：

```env
OPENAI_API_KEY=
OPENAI_MODEL=
```

这样系统会自动走本地 `mock`，页面仍可正常使用。

### 如果你后续绑定正式域名

例如域名是 `contract.example.com`，建议把 `CORS_ORIGINS` 改成：

```env
CORS_ORIGINS=https://contract.example.com,http://contract.example.com
```

如果你还要保留本地调试，再把 `127.0.0.1:5173` 和 `localhost:5173` 一并加上。

---

## 七、安装后端依赖

在宝塔终端或 SSH 中执行：

```bash
source /opt/miniconda3/bin/activate
conda activate smart-inspect
cd /www/wwwroot/smart-inspect-agent/backend
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

说明：

- 后端最终会使用 `backend/.venv/bin/uvicorn`
- `app.config` 会自动读取项目根目录的 `.env`
- 因此只要 `.env` 放在 `/www/wwwroot/smart-inspect-agent/.env` 即可

---

## 八、构建前端

在宝塔终端或 SSH 中执行：

```bash
cd /www/wwwroot/smart-inspect-agent/frontend
npm ci
npm run build
```

构建完成后应生成：

```text
/www/wwwroot/smart-inspect-agent/frontend/dist
```

这个目录会被 FastAPI 自动托管。

---

## 九、先手动启动验证

在正式配置宝塔守护进程前，先手动跑一次：

```bash
source /opt/miniconda3/bin/activate
conda activate smart-inspect
cd /www/wwwroot/smart-inspect-agent/backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

验证：

- 健康检查：`http://服务器公网IP:8000/api/health`
- 页面访问：`http://服务器公网IP:8000`

重点检查 `/api/health` 返回值：

- `status = ok`
- `frontend_ready = true`
- `llm_enabled = true` 表示模型配置已生效

确认正常后，按 `Ctrl + C` 停止这个临时进程。

---

## 十、在宝塔中创建网站

进入宝塔面板：

1. 打开“网站”
2. 点击“添加站点”
3. 域名可以填：
   - 你的正式域名，例如 `contract.example.com`
   - 如果暂时没有域名，也可以先填服务器公网 IP
4. 站点目录建议填写：

```text
/www/wwwroot/smart-inspect-agent/frontend/dist
```

> 这里目录主要是为了让宝塔创建站点；实际访问会通过反向代理交给 FastAPI 处理。

如果宝塔询问是否创建 FTP / 数据库：

- FTP：不需要
- 数据库：不需要
- PHP：不需要

---

## 十一、在宝塔网站中配置反向代理

进入刚刚创建的网站，打开“反向代理”并新增代理，建议如下：

- 代理名称：`smart-inspect-backend`
- 目标 URL：`http://127.0.0.1:8000`
- 发送域名：`$host`

保存后，宝塔会自动生成对应的 Nginx 反向代理配置。

### 推荐效果

配置完成后，应实现：

- 访问 `http://你的域名/` 时，进入前端页面
- 访问 `http://你的域名/api/health` 时，由 FastAPI 返回健康检查

### 如果你想手动检查 Nginx 配置

站点配置里核心逻辑应该接近：

```nginx
location / {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}
```

保存后在宝塔里执行：

- 配置检查
- 重载 Nginx

---

## 十二、在宝塔中配置后端守护进程

推荐使用宝塔的：

- `Supervisor 管理器`
- 或 `进程守护管理器`

新增一个守护进程，建议配置如下：

### 1）基本信息

- 名称：`smart-inspect-backend`
- 启动目录：

```text
/www/wwwroot/smart-inspect-agent/backend
```

### 2）启动命令

```bash
/www/wwwroot/smart-inspect-agent/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 3）运行用户

优先用你当前项目目录有权限的用户。

如果你不准备细拆权限，最省事的做法是：

- 项目由 `root` 部署，就让守护进程也用 `root`
- 项目由 `www` 部署，就统一用 `www`

### 4）启动策略

- 开机自启：开启
- 进程守护：开启
- 异常自动重启：开启

保存后，启动这个守护进程。

### 5）如何确认启动成功

在宝塔面板中，应该能看到：

- 状态为“运行中”
- 端口 `8000` 被 `uvicorn` 占用

也可以在终端里检查：

```bash
curl http://127.0.0.1:8000/api/health
```

---

## 十三、在宝塔中配置 SSL（可选）

如果你已经绑定域名，可以直接在宝塔站点里配置 HTTPS：

1. 打开对应网站
2. 进入“SSL”
3. 申请 Let’s Encrypt 证书，或上传你已有的证书
4. 开启“强制 HTTPS”

配置完成后，建议验证：

- `https://你的域名`
- `https://你的域名/api/health`

---

## 十四、部署完成后的验证清单

至少检查以下几点：

- 宝塔网站状态正常
- 宝塔反向代理已启用
- 宝塔守护进程 `smart-inspect-backend` 正在运行
- `http://公网IP` 或 `https://域名` 能打开首页
- `/api/health` 返回 `status=ok`
- `frontend_ready=true`
- 如果配置了模型，`llm_enabled=true`
- 合同分析、单条追问、合同聊天都可正常返回

如果你想判断当前返回到底是大模型还是本地 mock，可看结果中的：

- `llm_mode=live`：大模型返回
- `llm_mode=mock`：本地降级返回

---

## 十五、更新发布流程

以后更新代码，建议在宝塔终端按下面流程执行：

```bash
cd /www/wwwroot/smart-inspect-agent
git pull

source /opt/miniconda3/bin/activate
conda activate smart-inspect

cd /www/wwwroot/smart-inspect-agent/frontend
npm ci
npm run build

cd /www/wwwroot/smart-inspect-agent/backend
source .venv/bin/activate
pip install -r requirements.txt
```

然后在宝塔里执行两步：

1. 重启 `smart-inspect-backend` 守护进程
2. 重载网站对应的 Nginx 配置

---

## 十六、常见问题

### 1）宝塔面板打不开

优先检查：

- 腾讯云安全组是否放行宝塔端口
- 服务器防火墙是否放行宝塔端口
- 宝塔安装后给你的访问端口是否记错

### 2）首页打不开

优先检查：

- 宝塔站点是否创建成功
- 反向代理是否已开启
- 守护进程 `smart-inspect-backend` 是否运行中
- `frontend/dist/index.html` 是否存在

排查命令：

```bash
ls -lah /www/wwwroot/smart-inspect-agent/frontend/dist
curl http://127.0.0.1:8000/api/health
```

### 3）首页能打开，但接口报错

检查：

- `.env` 是否存在
- `OPENAI_API_BASE` 是否正确
- `OPENAI_MODEL` 是否为支持值
- 守护进程启动目录和命令是否填写正确

### 4）分析结果一直是 mock

常见原因：

- `OPENAI_API_KEY` 未配置
- `OPENAI_MODEL` 未配置
- 模型名不在支持列表中
- 请求超时
- 返回内容不是合法 JSON

### 5）守护进程启动失败

最常见的原因：

- 启动目录写错
- `.venv` 路径写错
- Python 3.10 环境没准备好
- 项目目录权限不匹配

重点检查这条命令是否能手工跑通：

```bash
cd /www/wwwroot/smart-inspect-agent/backend
source .venv/bin/activate
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

### 6）前端构建失败

先确认版本：

```bash
node -v
npm -v
```

建议使用 Node `18+`。必要时可重装依赖：

```bash
cd /www/wwwroot/smart-inspect-agent/frontend
rm -rf node_modules
npm install
npm run build
```

---

## 十七、推荐的最终目录结构

部署完成后，建议目录类似这样：

```text
/www/wwwroot/smart-inspect-agent/
├─ .env
├─ backend/
│  ├─ .venv/
│  ├─ app/
│  └─ requirements.txt
├─ frontend/
│  ├─ dist/
│  ├─ src/
│  └─ package.json
└─ deploy/
```

如果你后面还要接入域名、HTTPS、非 root 用户权限隔离或自动发布，可以继续在这个文档基础上扩展。