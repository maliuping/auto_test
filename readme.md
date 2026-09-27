# auto_test 自动化测试框架说明文档

# 1 auto_test overview

基于 **pytest + ADB + 驱动检查 + dmesg 监控 + Pipeline 执行** 的自动化测试框架，用于验证：

* **DPU / VO / MIPI / DSI / Panel**
* 显示链路格式（RGB / YUV）
* PPI packet monitor 数据
* CRC / EDPI / Polarity 状态
* 驱动加载/卸载行为（linlon-dp / mipi_tx / panel）
* 屏幕刷新、场景切换、Underrun 错误检测
* 单 Pipeline 多 case 复用（避免重复烧 case）

框架可支持功能、场景、格式、压力等多种类型自动化测试。

## 1.1 环境组成
```
┌─────────────────┐                     ┌─────────────────┐
│                 │       ssh           │                 │
│   Local PC      ├────────────────────►│  Server         │
│  (Pytest host)  │◄────────────────────┤  (case gen      │
│                 │                     │   & cmodel run) │
└───────┬─────────┘                     └─────────────────┘
      ▲ │
      │ │ usb
      │ │
      │ │
      │ ▼
┌─────┴───────────┐
│                 │
│                 │
│   DUT           │
│                 │
└───────┬─────────┘
        │
        │dsi
        │
        │
┌───────▼─────────┐
│                 │
│                 │
│     Panel       │
│                 │
└─────────────────┘
```
### Local PC
---

运行 pytest / auto_test 框架。调度测试流程，并协调 Server 与 DUT。

负责：
- ADB 控制 DUT
- Pull dmesg / dump
- 执行解析与结果比对
- 生成 HTML 报告

### Server
---
负责 case 相关的 heavy 任务：
- 生成 test case（gen_case.py）
- 保存 case 配置、模板、输入文件
- 生成 cmodel 输入数据（gen_cmodel_config.py）
- 执行 cmodel（run_cmodel.py）
- Local PC 与 Server 通过 SSH / SCP 通信
- Server 不与 DUT 直接连接

### DUT
---
- 加载 linlon-dp / dsi / panel 等驱动
- 执行测试 case：
    - linlondp_cv_unit -c xxx.xml -d dump -R
    - im_vo_unit -m 1 -w 1080 -h 1920 -f 4
- 输出画面到 Panel
- Local PC 通过 ADB 控制 DUT


# 2 目录结构

```
auto_test/
│
├── helpers/
│   ├── case_runner.py           # 测试核心封装（pipeline 执行、dmesg 收集、视频/图片采集）
│   ├── adb_utils.py             # ADB 封装
│   ├── fun_utils.py             # 驱动加载、卸载、系统工具函数, 正则解析（CRC、PPI monitor、Underrun 等）
│
├── tests/
│   ├── dpu/
│   ├── vo_subsys/
│
├── conftest.py                  # 全局 fixture / mark 注册
├── pytest.ini                   # markers、log 配置
└── README.md                    # 本文件
```

---

# 3 测试框架核心能力

## 3.1 @require_driver

自动确保某些测试必须依赖驱动，例如：

```python
@pytest.mark.require_driver("linlon_dp")
def test_xxx():
    ...
```

pytest 会在 test 执行前自动执行：

```
modprobe linlon-dp
检查驱动是否正常加载
失败则直接 skip
```

---

## 3.2 CaseRunner：Pipeline 执行引擎

核心函数：

```python
result = case_runner.run_pipeline("mode1.xx")
```

运行逻辑：

1. 上传 case 到设备
2. 清理 dmesg
3. 运行 pipeline 可执行
4. 等待 case 完成
5. 收集 dmesg + log
6. 提取 PPI/CRC/Underrun 等信息
7. 返回 PASS / FAIL

---

## 3.3 单 pipeline，多 case 复用

避免重复运行mode消耗时间。

```python
@pytest.fixture(scope="session")
def single_mode_pipeline_result(case_runner):
    return case_runner.run_pipeline("mode1.27")
```

多个 case 复用结果：

```python
def test_xxx(single_mode_pipeline_result):
    assert single_mode_pipeline_result == "PASS"
```

---

## 3.4 dmesg 监控解析（PPI / CRC / Underrun）

### Underrun 统计

```python
errs = parse_underrun(log_text)
assert errs == 0
```

---

### PPI Packet Monitor 解析

```python
entries = parse_packet_monitor(log)
ok, e = find_entry(entries, dt=0x3E, wc=1080*3, cnt=0)
```

---

### VO Unit / CRC / Polarity 解析

正则自动提取：

```
[vo_unit] PPI_CRC:0x12345678
[vo_unit] FLIP: frame=100 ts=12345
[vo_unit] VBLANK: frame=101 ts=12346
```

---

## 3.5 DSI Bus Format 自动化设置（Fixture）

```python
@pytest.fixture
def set_dsi_bus_format_setup_teardown():
    def _set(fmt):
        unload_driver("linlon-dp")
        reload_dsi_subsys(fmt)
    yield _set
    restore_default_bus_format()
```

使用：

```python
def test_mipi_rgb101010(set_dsi_bus_format_setup_teardown):
    set_dsi_bus_format_setup_teardown("rgb101010")
```

---

## 3.6 视频/图像采集
TODO


## 3.7 持续压测支持

循环跑所有 case：

```bash
python stress.py
```

其中每轮生成：

```
report_001.html
report_002.html
...
```

---

# 4 安装依赖

## 4.1 Python 依赖

```
pip install -r requirements.txt
```

## 4.2 ADB

```
adb devices
```

## 4.3 配置环境信息
参照1.1 环境组成图，需要配置DUT的串口信息; server的登陆信息；Server上case path等。
在Local PC auto_test下 新建 ".env" 文件， 配置如下信息。
```
SERIAL_PORT=COM5
SERIAL_BAUD=921600
REPO_DIR=/mnt/user_home/loganma/workspace/argos_v3
HOST=loganma@10.198.24.11
PORT=39912
KEY="D:\loganma\ssh-miyao\loganMa.ppk"
```


# 5 运行测试

## 只跑 DPU 相关 case：

```bash
python -m pytest -s -v --capture=sys --html=report.html -m "dpu"
```

## 运行 VO Subsy case：

```bash
python -m pytest -s -v --capture=sys --html=report.html -m "subsys"
```

# 6 平台抽象第一阶段

平台抽象代码位于：

```text
framework/core/          typed operation、artifact 和错误模型
framework/platform_db/   target 加载、schema 校验和寄存器解析
framework/compiler/      operation plan 到 Shell 的编译
hal/                     面向能力的硬件 HAL
platforms/               SoC、Board、Runtime、Lab 和 Target profile
unit_tests/              不连接 Server/DUT 的本地测试
```

当前提供两个未确认正式产品映射的 target：

```text
legacy_160    DPU base 0x16000000
candidate_170 DPU base 0x17000000
```

在硬件 owner 确认平台归属前，不要将它们重命名为正式 SoC 名称。

运行本地单元测试：

```bash
cd auto_test
python -m pytest -q unit_tests
```

新平台 fixture 通过以下方式选择 target：

```bash
python -m pytest --target=legacy_160 ...
```

也可以设置：

```text
AUTO_TEST_TARGET=legacy_160
```

现有未使用 `resolved_target`、`shell_compiler` 或 `dpu_hal` fixture 的历史用例不受影响。
