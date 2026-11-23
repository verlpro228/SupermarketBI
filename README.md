<div align="center">

# 超市库存管理日常业务数据分析及可视化系统

**Supermarket Inventory Management & Analytics System**

从商品建档到批次出入库、临期预警、库存巡检与经营数据可视化的一体化库存管理后台

[![Python](https://img.shields.io/badge/Python-3.12-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![Vue](https://img.shields.io/badge/Vue-3.5-42B883?logo=vuedotjs&logoColor=white)](https://vuejs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178C6?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Element Plus](https://img.shields.io/badge/Element%20Plus-2.9-409EFF)](https://element-plus.org/)
[![License](https://img.shields.io/badge/License-Learning%20Only-lightgrey)](#许可证)

[功能特性](#功能特性) · [技术栈](#技术栈) · [快速开始](#快速开始) · [项目结构](#项目结构) · [API 概览](#api-概览) · [常见问题](#常见问题)

</div>

---

## 简介

本项目是一套前后端分离的超市库存管理后台，围绕门店日常经营的三个核心痛点设计：

| 痛点 | 解决方案 |
| :--- | :--- |
| 临期商品发现不及时，只能靠人工翻货架 | 入库时按保质期自动推算到期日，按「已过期 / 紧急 / 预警」三档实时分档，阈值可配置 |
| 出入库无法追溯，出了问题查不到批次 | 每次入库独立建批次，出库按到期日 FIFO 跨批次扣减，明细记录到批次级 |
| 经营数据靠手工盘点统计 | 看板与趋势图实时聚合，13 张图表覆盖流动、结构、风险、资金四个维度，支持 Excel 导出 |

系统内置管理员与库管员双角色，权限在后端接口层强校验，金额类字段对库管员完全不可见。

---

## 功能特性

### 基础档案

| 模块 | 能力 |
| :--- | :--- |
| 用户管理 | 新增、编辑、启禁用、重置密码；不能禁用自己、不能自降角色、至少保留一个启用的管理员 |
| 商品分类 | 分类增改、逻辑停用；分类下存在启用商品时拒绝停用，避免出现孤儿商品 |
| 商品管理 | 条码唯一校验、按分类筛选、逻辑删除；进价字段仅管理员可见可改 |

### 库存流转

| 模块 | 能力 |
| :--- | :--- |
| 入库登记 | 单商品一单、每次新建批次、到期日由后端按保质期推算、入库金额后端计算 |
| 出库登记 | 销售 / 报损两类，按到期日升序 FIFO 跨批次扣减，库存不足直接拦截 |
| 库存查询 | 汇总库存、低库存标记、批次明细、出入库流水追溯、批次级库存调整（管理员） |

### 临期与巡检

| 模块 | 能力 |
| :--- | :--- |
| 临期清单 | 三档分档、按剩余天数升序、按分类与关键词筛选；已处理批次自动退出清单 |
| 临期处理 | 单条或批量报损（生成报损出库单）、标记促销，全过程写入处理记录 |
| 库存巡检 | 一键扫描低库存与临期问题并保存快照，明细支持逐条标记已处理 / 已忽略 |

### 数据分析

| 模块 | 图表 |
| :--- | :--- |
| 数据看板 | 4 项 KPI + 出入库趋势、分类货值占比、分类出入库对比、临期分档、货值 Top 10、低库存缺口 Top 10 |
| 出入库趋势 | 30 / 90 天，按日或按月聚合，区间汇总与净变化 |
| 入库登记页 | 入库量趋势、供应商供货 Top 8、入库品类占比 |
| 出库登记页 | 出库量趋势、出库类型构成、出库量 Top 8 商品 |

### 数据导出

库存、入库、出库、临期清单、临期处理记录五类数据支持导出 Excel，文件名含时间戳；库管员导出时自动剔除金额列。

---

## 技术栈

| 分类 | 技术 | 版本 |
| :--- | :--- | :--- |
| 后端框架 | FastAPI | 0.115.6 |
| ORM | SQLAlchemy（同步） | 2.0.36 |
| 数据库驱动 | PyMySQL | 1.1.1 |
| 鉴权 | PyJWT + bcrypt | 2.10.1 / 4.2.1 |
| 表格导出 | openpyxl | 3.1.5 |
| 数据库 | MySQL | 8.0 |
| 前端框架 | Vue 3 + TypeScript | 3.5.13 / 5.7.2 |
| 构建工具 | Vite | 6.0.7 |
| UI 组件 | Element Plus | 2.9.1 |
| 图表 | ECharts（按需引入） | 5.5.1 |
| 状态与路由 | Pinia + Vue Router | 2.3.0 / 4.5.0 |

---

## 快速开始

### 环境要求

| 依赖 | 版本 |
| :--- | :--- |
| Python | 3.11 及以上 |
| Node.js | 20 及以上 |
| pnpm | 9 及以上 |
| MySQL | 8.0（默认 3306 端口） |

### 1. 初始化数据库

```bash
cd backend
mysql -u root -p < init_db.sql
```

脚本只创建 `supermarket_bi` 库及其 13 张表，不会影响本机其他数据库。

### 2. 配置连接信息

`backend/.env` 含密码与密钥，**未纳入版本库**，首次运行需从模板复制：

```bash
cd backend

# Windows
copy .env.example .env
# macOS / Linux
cp .env.example .env
```

然后编辑 `backend/.env`，至少修改密码与密钥两项：

```ini
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=你的密码
MYSQL_DB=supermarket_bi
SECRET_KEY=请替换为长随机字符串
```

其余配置项（`ALGORITHM`、`ACCESS_TOKEN_EXPIRE_MINUTES`、`CORS_ORIGINS`）保持默认即可。

### 3. 安装依赖并写入初始数据

```bash
# 后端
cd backend
python -m venv .venv

# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt
python scripts/seed.py
```

`seed.py` 是幂等的，重复执行不会产生脏数据。首次执行会写入：

- 2 个账号、6 个分类、112 个商品
- 115 条入库记录（含多批次与不同临期档位）
- 销售出库、报损出库、临期处理、库存调整各若干
- 一次巡检快照

### 4. 启动服务

```bash
# 终端 1：后端（默认 8000）
cd backend
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000

# 终端 2：前端（默认 5173）
cd frontend
pnpm install
pnpm dev
```

| 地址 | 说明 |
| :--- | :--- |
| http://localhost:5173 | 前端界面 |
| http://localhost:8000/docs | Swagger 接口文档 |
| http://localhost:8000/api/v1/system/health | 健康检查 |

### 5. 登录

| 角色 | 账号 | 密码 | 默认首页 |
| :--- | :--- | :--- | :--- |
| 管理员 | `admin` | `Admin@123` | 数据看板 |
| 库管员 | `keeper` | `Keeper@123` | 库存查询 |

密码以 bcrypt 哈希存储，登录后可在右上角头像菜单中修改。

---

## 项目结构

```
SupermarkeBI/
├── backend/
│   ├── app/
│   │   ├── core/          # 配置、JWT、密码哈希、依赖、统一响应、异常处理
│   │   ├── db/            # ORM 基类、引擎与会话
│   │   ├── models/        # 13 张表的 ORM 模型（每表一个文件）
│   │   ├── schemas/       # 入参出参模型（每模块一个文件）
│   │   ├── crud/          # 单表数据访问（只 flush，不 commit）
│   │   ├── services/      # 业务编排与事务边界（FIFO、库存联动、巡检快照）
│   │   ├── routers/v1/    # HTTP 接口层
│   │   ├── utils/         # 单号生成、Excel 构建、配置读取
│   │   └── main.py        # 应用装配
│   ├── scripts/
│   │   ├── seed.py        # 初始化入口
│   │   └── demo_data.py   # 演示业务数据
│   ├── tests/             # 18 条接口测试
│   ├── init_db.sql
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── api/           # 接口封装（每模块一个文件）
│       ├── components/    # 通用组件（BaseChart 等）
│       ├── constants/     # 枚举、映射、系统名称
│       ├── layouts/       # 主布局
│       ├── router/        # 路由与菜单配置
│       ├── stores/        # Pinia 状态
│       ├── styles/        # 全局样式
│       ├── types/         # 共享类型
│       ├── utils/         # 格式化、下载
│       └── views/         # 页面（私有组件放在各自 components/ 下）
└── README.md
```

**分层约定**：`routers` 只做参数校验与响应封装，`crud` 只做单表查询且不提交事务，`services` 负责事务边界与跨表一致性，`utils` 为无状态纯函数。所有库存计算都在后端完成，前端不参与。

---

## 数据库设计

共 13 张表，按职责分为三组：

| 分组 | 表 | 用途 |
| :--- | :--- | :--- |
| 基础档案 | `sys_user` | 账号、密码哈希、角色、状态 |
| | `category` | 商品分类 |
| | `product` | 商品档案（条码唯一、进价、售价、安全库存、保质期天数） |
| 库存流水 | `inventory_batch` | 批次表，记录生产日期、到期日、初始与剩余数量、批次进价、促销标记 |
| | `inventory` | 商品级汇总数量，承担原子条件扣减 |
| | `inbound_order` | 入库单 |
| | `outbound_order` / `outbound_item` | 出库单与明细（明细带 `batch_id`，跨批次时一单多行） |
| | `stock_adjust_log` | 库存调整留痕 |
| 临期巡检 | `expiry_action_log` | 临期处理记录 |
| | `inspection_record` / `inspection_item` | 巡检头与明细快照 |
| | `sys_config` | 系统配置（临期阈值） |

---

## API 概览

统一前缀 `/api/v1`，统一响应体 `{ code, message, data }`，共 45 个接口。

| 分组 | 接口 |
| :--- | :--- |
| 认证 | `POST /auth/login`、`GET /auth/profile`、`PUT /auth/password` |
| 用户 | `GET/POST /users`、`PUT /users/{id}`、`PUT /users/{id}/status`、`PUT /users/{id}/password` |
| 分类 | `GET/POST /categories`、`GET /categories/options`、`PUT /categories/{id}`、`PUT /categories/{id}/status`、`DELETE /categories/{id}` |
| 商品 | `GET/POST /products`、`GET /products/options`、`PUT /products/{id}`、`PUT /products/{id}/status` |
| 入库 | `POST /inbound`、`GET /inbound` |
| 出库 | `POST /outbound`、`GET /outbound` |
| 库存 | `GET /stock`、`GET /stock/{id}/records`、`GET /stock/{id}/batches`、`POST /stock/adjust` |
| 临期 | `GET /expiry`、`POST /expiry/loss`、`POST /expiry/promo`、`GET /expiry/actions` |
| 巡检 | `POST /inspections/run`、`GET /inspections`、`GET /inspections/{id}`、`PUT /inspections/items/status` |
| 统计 | `GET /stats/dashboard`、`/stats/trend`、`/stats/inbound-analysis`、`/stats/outbound-analysis` |
| 导出 | `GET /export/stock`、`/export/inbound`、`/export/outbound`、`/export/expiry`、`/export/expiry-actions` |

启动后端后访问 http://localhost:8000/docs 查看完整参数说明并在线调试。

---

## 测试

```bash
cd backend
.venv\Scripts\python.exe -m pytest tests -q
```

当前 18 条用例全部通过，覆盖：

- 认证与用户管理（登录、鉴权、越权、生命周期）
- 分类与商品（判重、停用保护、进价可见性）
- 入库与库存调整（批次生成、汇总同步、留痕）
- 出库 FIFO 与负库存拦截
- 临期分档与处理、巡检快照
- 统计接口与 Excel 导出

测试通过直接签发 token 访问接口，不依赖也不修改演示账号密码；用例内创建的临时数据会在结束时清理。

---

## 核心业务规则

<details>
<summary><b>FIFO 扣减</b></summary>

出库按 `expiry_date ASC, id ASC` 选批，先扣到期最早的批次，不足时跨批次继续扣减。事务内先锁商品汇总行、再锁批次行，固定顺序避免死锁。
</details>

<details>
<summary><b>负库存防护</b></summary>

`UPDATE inventory SET total_qty = total_qty - :n WHERE product_id = :pid AND total_qty >= :n`，按影响行数判断，为 0 立即拦截并回滚，不依赖「先查后改」。
</details>

<details>
<summary><b>批次追溯</b></summary>

每次入库新建独立批次，不合并。出库明细记录 `batch_id`，因此「哪个商品、哪一批、何时出库多少」全程可查。
</details>

<details>
<summary><b>临期分档</b></summary>

阈值读取 `sys_config`（默认紧急 7 天、预警 30 天），修改配置立即生效，无需改代码。清单只展示「有剩余、未标记促销、剩余天数 ≤ 预警阈值」的批次。
</details>

<details>
<summary><b>权限隔离</b></summary>

后端写接口统一通过 `Depends` 校验角色，前端菜单仅控制显示。库管员请求商品、库存、看板接口时，服务端直接剔除进价与货值字段，不是前端隐藏。
</details>

<details>
<summary><b>金额计算</b></summary>

入库金额、出库金额、库存货值全部由后端使用 `Decimal` 计算，不接受前端传值。库存货值口径为「当前库存 × 商品当前进价」。
</details>

---

## 常见问题

<details>
<summary><b>克隆下来后能直接启动吗</b></summary>

不能，需要先补齐本地环境，共三步：

1. **配置环境变量**：`backend/.env` 含密码与密钥，未纳入版本库，从 `.env.example` 复制并填写
2. **初始化数据库**：执行 `init_db.sql` 建库建表
3. **写入初始数据**：安装依赖后执行 `scripts/seed.py`，否则没有账号无法登录

另外 `.venv/`、`node_modules/`、`dist/` 均被 `.gitignore` 排除，需重新生成。
</details>

<details>
<summary><b>登录提示「账号或密码错误」</b></summary>

确认已执行过 `python scripts/seed.py`。如果手动改过密码又忘记了，可在数据库中将 `sys_user.password_hash` 重置，或重新执行 seed 前先删除该账号。
</details>

<details>
<summary><b>看板图表没有数据 / 曲线很平</b></summary>

图表基于真实出入库记录聚合。全新初始化的库如果跳过演示数据，需要先做几笔入库、出库，曲线才有形状。
</details>

<details>
<summary><b>端到端流程怎么演示</b></summary>

推荐路径：商品管理中新建商品 → 入库登记两批不同生产日期 → 出库登记（观察 FIFO 是否优先扣临期批次）→ 库存查询看流水 → 临期清单处理 → 库存巡检 → 数据看板 → 导出 Excel。
</details>

<details>
<summary><b>启动报端口占用</b></summary>

后端换端口：`uvicorn app.main:app --reload --port 8001`；前端 Vite 会自动寻找下一个可用端口，或修改 `vite.config.ts` 中的 `server.port`。
</details>

<details>
<summary><b>能否重复执行初始化脚本</b></summary>

可以。账号、分类、商品按唯一键跳过已存在的记录，演示业务数据检测到标记后整体跳过，只为「尚无库存记录的新增商品」补库存。
</details>

---

## 开发约定

| 项 | 约定 |
| :--- | :--- |
| 后端分层 | `routers` → `services` → `crud` → `models`，禁止跨层调用，`crud` 不提交事务 |
| 前端分层 | 页面私有组件放在 `views/<模块>/components/`，跨页面复用才放进 `components/common/` |
| 枚举与文案 | 统一放 `frontend/src/constants/`，不允许在各页面写死角色、状态等字符串 |
| 接口类型 | 前后端共享类型定义在 `frontend/src/types/index.ts` |
| 数据库变更 | 修改表结构需同步更新 `init_db.sql` 与 ORM 模型 |

---

## 许可证

本项目用于学习与课程实践，未经允许不得用于商业用途。

<div align="right"><a href="#超市库存管理日常业务数据分析及可视化系统">回到顶部</a></div>
