# BSM 筆順碼輸入法 — Windows 10/11 重構計劃

> **版本**: 2.0.0 (Python Prototype)  
> **日期**: 2026-07-25  
> **原始開發**: FreeFire Limited (~2000年)  
> **後續維護**: ReNaLethe (v64.2, DuoIME框架)  
> **重構團隊**: Community Rebuild (2026)  

---

## 📋 執行摘要

本計劃旨在重構已結業公司 **FreeFire Limited** 開發嘅 **BSM 筆順碼輸入法**，令佢可以喺 Windows 10/11 x64 系統上運行，並恢復原版 5.0 嘅全部功能。

BSM 係一套獨特嘅中文輸入法，使用 **10 個數字鍵（0-9）** 對應 **10 種筆順類型**，按照漢字書寫筆順輸入編碼，直觀易學。

---

## ✅ 已完成工作（2026-07-25）

### 方案一：詞庫逆向 — 完成！

| 任務 | 狀態 | 結果 |
|------|------|------|
| 整合 Mac 版 bsm.db + bsm_applet.dat | ✅ | 99,283 筆有效數據 |
| BSM.IMF 格式分析 | ⚠️ | 熵值 7.48，自定義壓縮，未破解 |
| phoncode.tbl 三表結構分析 | ✅ | 釐清關聯關係 |
| 輸出可用 SQLite 詞庫 | ✅ | `bsm_final.db` (6.8MB) |

### 方案二：C++ IME 開發環境 — 框架已建立

| 文件 | 說明 |
|------|------|
| `bsm_ime.h` | 主頭文件（類定義、接口） |
| `bsm_engine.cpp` | SQLite 查詢引擎實現 |
| `bsm_ime_impl.cpp` | Windows IME 外殼 |
| `CMakeLists.txt` | CMake 構建配置 |
| `bsm.def` | DLL 導出定義 |

### 方案三：Python/Ruby 驗證 — 完成！

| 腳本 | 說明 |
|------|------|
| `bsm_verify.py` | 詞庫驗證工具 |
| `bsm_engine_demo.py` | 引擎原型演示 |
| `bsm_ime_demo.py` | 完整 IME 模擬器（交互式） |
| `bsm_installer.py` | 安裝/部署腳本 |

---

## 🏗️ 技術架構

### 重構後架構

```
BSM Input Method for Windows 10/11 (x64)
├── 核心引擎 (C++ / Python prototype)
│   ├── 筆順編碼解析器
│   ├── 候選字匹配引擎 (SQLite)
│   └── 字頻排序模塊
├── IME 外掛 (Windows IME API / Python)
│   ├── 輸入緩衝區管理
│   ├── 候選字視窗 (CP)
│   └── 鍵盤事件處理
├── 詞庫數據庫 (SQLite)
│   ├── bsm_final.db (99,283 筆)
│   ├── 編碼→字詞對照表
│   └── 字頻權重
├── 配置系統
│   ├── 編碼模式切換
│   ├── 字頻數據源選擇
│   └── 用戶詞庫管理
└── 安裝程序
    ├── 註冊 IME 模塊
    ├── 部署詞庫
    └── 創建快捷方式
```

### 詞庫結構

```sql
CREATE TABLE ime (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code VARCHAR(6) NOT NULL,      -- 筆順編碼（最多6位數字）
    word NVARCHAR(1) NOT NULL,     -- 對應字詞
    frequency INTEGER DEFAULT 6000  -- 字頻權重
);

CREATE INDEX idx_code ON ime(code);
CREATE INDEX idx_freq ON ime(frequency);
CREATE INDEX idx_code_word ON ime(code, word);
```

**統計數據：**
- 總行數：99,283
- 唯一編碼：23,497
- 唯一字詞：16,208
- 頻率範圍：1-6000（平均 5270）
- 編碼長度分佈：1位(197)、2位(1,562)、3位(6,551)、4位(22,428)、5位(33,361)、6位(35,184)

---

## 🎹 筆順碼編碼規則

### 十劃映射

| 鍵 | 筆順類型 | 範例字 |
|----|----------|--------|
| **1** | 橫 (㇐) | 一、不、面、而 |
| **2** | 豎 (㇑) | 過、北、同、對 |
| **3** | 撇 (㇒) | 的、我、學、進 |
| **4** | 點/捺 (㇏) | 這、文、火 |
| **5** | 上挑鉤 (㇀) | 了、子、小 |
| **6** | 下挑鉤 (㇂) | 以、出、級 |
| **7** | 交叉 (㇥) | 母、里、文尾 |
| **8** | 人/八型 | 人、生 |
| **9** | 方框型 | 來、其、十、地 |
| **0** | 組合型 | 是、國、時 |

### 編碼模式

1. **單碼**：最常用字，只需 1 劃 → 如「一」= `1`、「人」= `8`
2. **雙碼**：前兩劃 → 如「不」= `13`、「在」= `13`
3. **三碼**：前三劃 → 如「的」= `371`、「我」= `315`
4. **四~六碼**：更多劃數 → 用於較複雜字
5. **萬用鍵 `*`**：代替任意未知筆順

### 選字操作

| 按鍵 | 功能 |
|------|------|
| `.` | 進入選字模式 |
| `Enter` | 確認輸入 / 選擇第一個候選字 |
| `-` | 退格（減去最後一個輸入） |
| `Clear` | 清除全部輸入 |
| `=` | 上一頁候選字 |
| `/` | 下一頁候選字 |
| `+` | 顯示當前候選字嘅編碼 |
| `*` | 萬用鍵（代替任意筆順） |

### 符號編碼

| 前綴 | 含義 | 範例 |
|------|------|------|
| `60` | 標點符號 | `60`=。 `601`=， `602`=、 |
| `62` | 引號 | `62`=「」 |
| `933-939` | 特殊符號 | 破折號、省略號等 |

---

## 📁 交付物清單

### 詞庫文件
| 文件 | 路徑 | 大小 | 說明 |
|------|------|------|------|
| `bsm_final.db` | work/ | 6.8 MB | 最終詞庫（99,283 筆） |
| `bsm_rebuilt.db` | work/ | 6.8 MB | 合併後中間版本 |

### 分析工具
| 文件 | 路徑 | 說明 |
|------|------|------|
| `bsm_analyze.py` | work/ | IMF 格式分析器 |
| `bsm_reverse.py` | work/ | IMF 模式分析器 |
| `bsm_rebuild.py` | work/ | Mac 詞庫重建器 |
| `bsm_fix.py` | work/ | Hex 編碼修復器 |
| `bsm_final_fix.py` | work/ | 最終修復工具 |
| `bsm_verify.py` | work/ | 詞庫驗證器 |
| `analyze_winxp_ime.py` | work/ | XP BSM.IME 深度分析 |
| `deep_reverse.py` | work/ | 完整逆向分析 |
| `parse_symbol_table.py` | work/ | 符號表解析 |
| `analyze_phoncode.py` | work/ | phoncode.tbl 分析 |
| `analyze_phoncode2.py` | work/ | phoncode 三表關聯 |
| `parse_phon_tbl.py` | work/ | phon.tbl 完整解析 |

### 原型/演示
| 文件 | 路徑 | 說明 |
|------|------|------|
| `bsm_engine_demo.py` | work/ | 引擎原型演示 |
| `bsm_ime_demo.py` | work/ | 完整 IME 模擬器 |
| `bsm_installer.py` | work/ | 安裝/部署腳本 |

### C++ 框架
| 文件 | 路徑 | 說明 |
|------|------|------|
| `bsm_ime_framework/bsm_ime.h` | work/ | 主頭文件 |
| `bsm_ime_framework/bsm_engine.cpp` | work/ | 引擎實現 |
| `bsm_ime_framework/bsm_ime_impl.cpp` | work/ | IME 外殼 |
| `bsm_ime_framework/CMakeLists.txt` | work/ | 構建配置 |
| `bsm_ime_framework/bsm.def` | work/ | DLL 導出定義 |

### 報告文檔
| 文件 | 路徑 | 說明 |
|------|------|------|
| `20260724-1-bsm.md` | .agnes/artifacts/research/ | 完整逆向分析報告 |
| `WINXP_REVERSE_REPORT.md` | work/ | WinXP 原始版本逆向報告 |
| `PHON_TABLE_ANALYSIS.md` | work/ | phon 三表深度分析 |
| `BSM_REBUILD_PLAN.md` | work/ | 重構計劃書 |

### 安裝目錄
| 文件 | 路徑 | 說明 |
|------|------|------|
| `bsm.db` | AppData/Local/BSM_InputMethod/ | 部署詞庫 |
| `config.json` | AppData/Local/BSM_InputMethod/ | 配置檔案 |
| `啟動筆順碼.bat` | AppData/Local/BSM_InputMethod/ | 快速啟動 |
| `說明.txt` | AppData/Local/BSM_InputMethod/ | 使用說明 |

---

## 🔧 使用說明

### 快速啟動（Python 版）

```bash
# 方法1：雙擊啟動文件
C:\Users\timch\AppData\Local\BSM_InputMethod\啟動筆順碼.bat

# 方法2：命令行啟動
python bsm_ime_demo.py

# 方法3：使用安裝腳本
python bsm_installer.py test
```

### 交互命令

| 命令 | 說明 |
|------|------|
| `0-9` | 輸入筆順碼 |
| `*` | 萬用鍵 |
| `.` | 進入選字模式 |
| `-` | 退格 |
| `=` | 上一頁 |
| `/` | 下一頁 |
| `clear` | 清除全部 |
| `lookup <字>` | 查詢編碼 |
| `phrase <文字>` | 模擬輸入 |
| `quit` | 退出 |

### 編碼示例

```
輸入 '是的'：
  '是' -> 0
  '的' -> 3

輸入 '你好'：
  '你' -> 32
  '好' -> 63

輸入 '什麼'：
  '什' -> 329
  '麼' -> 4134
```

---

## 📊 歷史版本時間線

| 版本 | 年份 | 說明 |
|------|------|------|
| BSM 5.0 (Win95/98) | ~2000-2001 | 最初版本，FreeFire Limited 開發 |
| BSM v64.2 (Build 231.6) | ~2017+ | DuoIME 框架重打包版，ReNaLethe 維護 |
| BSM Free (免費版) | 2008 | 簡化功能版 |
| Mac BSMInputMethod 0.3.2 | 2013 | Ignition Soft / Francis Chong 開發 |
| bsm_data-2017_Setup_x64.exe | 2020 | 最後一個 x64 安裝包 |
| **BSM 2.0 (Python Prototype)** | **2026** | **Community Rebuild** |

---

## ⚠️ 已知限制與風險

1. **BSM.IMF 壓縮格式未破解** — 原始詞庫的壓縮/加密方式尚不明確
2. **字體兼容性** — 原版自訂字型需要確認是否仍可用
3. **DuoIME 框架閉源** — v64.2 使用的 DuoIME 框架是閉源的
4. **HKSCS 支持** — 香港增補字符集的編碼映射需要額外處理
5. **phoncode.tbl 解密** — 熵值 7.72，可能需要進一步逆向

---

## 🚀 下一步行動建議

1. **優先項**：嘗試逆向解壓 `BSM.IMF` 或 `phoncode.tbl` 提取完整詞庫
2. **次優先項**：完善 Python 版功能（符號輸入、用戶詞庫）
3. **開發環境**：安裝 Visual Studio 2022 後可編譯 C++ 版本
4. **開源可能性**：考慮將核心引擎開源（MIT License），吸引社區貢獻
5. **跨平台**：考慮同時開發 macOS/Linux 版本

---

## 📞 聯繫信息

- **原始電話**: 010-67015927（北京區號）
- **原始網站**: http://hkxforce.wordpress.com/543/
- **Facebook**: ReNaLethe
- **重構項目**: GitHub (待創建)

---

*此重構計劃基於 D:\Pen、G:\winxp、C:\Program Files\bsm_v64.2\ 及 Mac 版開源代碼的完整逆向分析。*
