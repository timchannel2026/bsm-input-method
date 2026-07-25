# BSM 筆順碼輸入法 — Windows 10/11 重構計劃

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Version: 2.0.1](https://img.shields.io/badge/version-2.0.1-brightgreen.svg)]()

BSM (筆順碼) 係一套獨特嘅中文輸入法，使用 **10 個數字鍵（0-9）** 對應 **10 種筆順類型**。

> **原始開發**: FreeFire Limited (~2000年)  
> **重構**: Community Rebuild (2026)  

---

## 🚀 快速開始

### 方法 1：便攜版（推薦）

直接複製 `portable/` 資料夾去任何電腦，雙擊 `BSM_筆順碼.exe` 即用！

### 方法 2：安裝版

運行 `BSM_筆順碼_v2.0.1_Setup.exe` 按照嚮導安裝。

### 方法 3：Python 運行

```bash
python bsm_gui_app.py
```

---

## ✨ 功能特點

- ✅ 十劃映射輸入（0-9）
- ✅ 可編輯已輸入文字區（6行高度）
- ✅ 打完字自動清空編碼區
- ✅ 候選字選擇（數字鍵或滑鼠點擊）
- ✅ 多頁翻頁（/ =）
- ✅ 萬用鍵 *
- ✅ 符號輸入
- ✅ 用戶自訂詞庫
- ✅ 編碼查詢對話框

---

## 🎹 編碼規則

| 鍵 | 筆順 | 範例 |
|----|------|------|
| 1 | 橫(㇐) | 一、不 |
| 2 | 豎(㇑) | 過、北 |
| 3 | 撇(㇒) | 的、我 |
| 4 | 點捺(㇏) | 這、文 |
| 5 | 上挑鉤(㇀) | 了、子 |
| 6 | 下挑鉤(㇂) | 以、出 |
| 7 | 交叉(㇥) | 母、里 |
| 8 | 人八型 | 人、生 |
| 9 | 方框型 | 來、其 |
| 0 | 組合型 | 是、國 |

---

## 📦 下載

| 文件 | 大小 | 說明 |
|------|------|------|
| `BSM_筆順碼_v2.0.1.exe` | 13.3 MB | 獨立可執行文件 |
| `portable.zip` | 20.3 MB | 便攜版（含詞庫） |
| `bsm_final.db` | 6.8 MB | SQLite 詞庫 |

---

## 🛠️ 技術架構

```
BSM Input Method
├── bsm_gui_app_v2.py    # Python GUI 應用
├── bsm_final.db         # 詞庫 (99,283 筆)
├── portable/            # 便攜版
└── bsm_ime_framework/   # C++ TIP IME 框架
```

---

## 📊 詞庫統計

- 總行數: 99,283
- 唯一編碼: 23,497
- 唯一字詞: 16,208

---

## 🗺️ 開發路線圖

- [x] 詞庫重建 (99,283 筆)
- [x] Python GUI 應用 v2.0.1
- [x] 獨立 .exe 打包
- [ ] 破解 BSM.IMF 壓縮格式
- [ ] 解碼 phoncode.tbl
- [ ] C++ TIP IME 版本
- [ ] GitHub 開源發布

---

## 📞 聯繫

- 原始電話: 010-67015927
- 維護: ReNaLethe (v64.2)

---

*BSM 筆順碼輸入法 — 讓中文輸入更直觀、更高效*
