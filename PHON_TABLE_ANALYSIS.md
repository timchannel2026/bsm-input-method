# BSM phon.tbl / phonptr.tbl / phoncode.tbl 深度分析報告

## 文件概覽

| 文件 | 大小 | 類型 |
|------|------|------|
| `phon.tbl` | 4,071 bytes | 筆順碼映射表（結構化數據） |
| `phonptr.tbl` | 2,714 bytes | 指針表（1357個2-byte LE偏移） |
| `phoncode.tbl` | 43,242 bytes | 編碼索引表（高熵二進位） |

---

## phon.tbl 結構解析

### 文件格式
```
[FF FF FF] [header?]
[data_byte][group_id][0x00][data_byte][group_id]...
```

- 前3 bytes: `FF FF FF`（可能是文件頭或結束標記）
- 之後為交替的 `[數據字節][組ID]` 對，中間以 `0x00` 分隔
- 共提取 **1992 條記錄**，分為 **72 個組**

### 組ID分佈
| 組ID範圍 | 數量 | 含義推測 |
|----------|------|---------|
| 0x01-0x09 | 9 組 | 基本筆順碼（0-8） |
| 0x0C-0x55 | 30+ 組 | 組合編碼（雙碼、三碼等） |
| 0x60-0x6A | 11 組 | 符號/特殊鍵映射 |
| 0x70-0x89 | 8 組 | 擴展功能 |
| 0xA6-0xAA | 5 組 | 用戶詞庫 |
| 0xE6-0xFF | 5 組 | 系統配置 |

### 關鍵發現
- 組 ID 0x06 (6) → 61 字符，包含 ASCII 和 BIG5 高字節
- 組 ID 0x08 (8) → 142 字符，最大組別
- 數據字節包含：ASCII (`f`, `g`, `h`, `i`, `p`, `v`, `w`, `x`, `y`) 和 BIG5 高字節 (`0xA6`, `0xE6` 等)

---

## phonptr.tbl 指針表

### 格式
- 1357 個 2-byte 小端偏移量
- 指向 phoncode.tbl 中的位置
- 所有指針值 < 21,621（在 phoncode.tbl 範圍內）

### 示例
```
ptr[  7] -> offset    19 -> '淐'
ptr[ 16] -> offset   195 -> '齲'
ptr[ 19] -> offset   198 -> '蕧'
ptr[ 30] -> offset   332 -> '宇'
ptr[ 37] -> offset   376 -> '呂'
...
```

成功提取 **146 個 Big5 字符**。

---

## phoncode.tbl 索引表

### 格式
- 43,242 bytes，Shannon 熵值 7.72（接近隨機）
- 可能係壓縮或加密的編碼查找表
- 使用 phonptr.tbl 的指針進行訪問

### 最常見的 2-byte 模式
```
0x8155: 7 次
0x9091: 7 次
0x5785: 7 次
0x9951: 7 次
```

---

## 三表關聯關係

```
phon.tbl          phonptr.tbl        phoncode.tbl
┌──────────┐     ┌──────────────┐    ┌──────────────┐
│ 組ID映射 │────▶│ 指針數組     │───▶│ 編碼索引表   │
│ (1992條) │     │ (1357個偏移) │    │ (43,242 bytes)│
└──────────┘     └──────────────┘    └──────────────┘
     │                  │                    │
     ▼                  ▼                    ▼
  筆順碼分類      定位到具體位置    存儲實際編碼數據
```

### 工作流程推測
1. 用戶輸入筆順碼（如 `321`）
2. phon.tbl 將碼值映射到對應組
3. phonptr.tbl 提供該組在 phoncode.tbl 中的起始偏移
4. phoncode.tbl 存儲實際的編碼→字符對照

---

## 與 Mac 版 bsm.db 對比

Mac 版結構更簡單：
```sql
CREATE TABLE ime (
    id INTEGER PRIMARY KEY,
    code VARCHAR(6),      -- 筆順編碼
    word CHAR(1),         -- 對應字
    frequency INTEGER     -- 字頻
);
```

XP 版則使用三表結構，可能為了：
- 節省空間（壓縮存儲）
- 支持更多編碼模式
- 便於動態加載

---

## 結論

1. **BSM.IMF 壓縮格式仍未破解** — 但 phoncode.tbl 可能係其一部分
2. **三表結構複雜** — 需要進一步逆向才能完全理解
3. **phon.tbl 提供組映射** — 是解碼的關鍵
4. **phonptr.tbl + phoncode.tbl** — 組成完整的編碼查找表

建議下一步：
- 嘗試用 phon.tbl 的組ID作為索引去 phoncode.tbl 查找
- 對比 phoncode.tbl 中不同區域的數據模式
- 嘗試將 phoncode.tbl 與 bsm.db 的編碼進行匹配
