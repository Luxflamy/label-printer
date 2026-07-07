# TSPL2 常用命令速查（TTP-344M）

> 完整手册见 TSC 官方 TSPL/TSPL2 Programming Manual

## 走纸/传感器校准

| 命令 | 示例 | 说明 |
|------|------|------|
| SET GAP AUTO | `SET GAP AUTO` | 自动调节间隙传感器灵敏度 |
| GAPDETECT | `GAPDETECT 240,16` | 间隙纸：学习标签长+间隙（dots） |
| AUTODETECT | `AUTODETECT 240,16` | 自动判断介质（固件 V6.86+，不设 GAP） |
| BLINEDETECT | `BLINEDETECT 1200,16` | 黑标纸：学习标签长+黑标 |
| HOME | `HOME` | 走纸到标签起始位置 |
| FORMFEED | `FORMFEED` | 走到下一张标签起始（需先 SIZE） |

## 标签设置

| 命令 | 示例 | 说明 |
|------|------|------|
| SIZE | `SIZE 40 mm,30 mm` | 标签宽×高 |
| GAP | `GAP 2 mm,0 mm` | 间隙高度, 偏移 |
| GAP | `GAP 0,0` | 连续纸（无间隙） |
| BLINE | `BLINE 3 mm,0 mm` | 黑标纸 |
| DIRECTION | `DIRECTION 1` | 0=正常, 1=旋转 180° |
| REFERENCE | `REFERENCE 0,0` | 坐标原点偏移 |
| CLS | `CLS` | 清空图像缓冲区 |
| PRINT | `PRINT 1` | 打印 n 张 |

## 文字

```
TEXT x,y,"font",rotation,x_mul,y_mul,"content"
```

| 参数 | 说明 |
|------|------|
| x, y | 左上角坐标（dots） |
| font | 内置字体编号 "1"~"8" 或 TTF 名 |
| rotation | 0/90/180/270 |
| x_mul, y_mul | 放大倍数 1~10 |

示例：
```
TEXT 20,20,"3",0,1,1,"Hello"
```

## 一维条码

```
BARCODE x,y,"type",height,human_readable,rotation,narrow,wide,"data"
```

常用 type：`128`, `39`, `EAN13`, `EAN8`, `UPCA`

示例：
```
BARCODE 20,80,"128",80,1,0,2,4,"1234567890"
```

## 二维码

```
QRCODE x,y,ECC_level,cell_width,mode,rotation,"data"
```

示例：
```
QRCODE 20,150,H,4,A,0,"https://example.com"
```

## 位图（中文推荐）

```
BITMAP x,y,width_bytes,height,mode,data
```

中文标签通常先用 Pillow 生成单色 BMP，再转 TSPL BITMAP 命令（阶段 5 实现）。

## 行尾与编码

- 每条命令以 `\r\n` 结尾
- 纯英文/数字可用 UTF-8
- 含特殊符号时注意打印机固件编码限制

## 203 dpi 换算

```
1 mm ≈ 8 dots
1 inch = 203 dots
```

40mm 宽标签 → 320 dots
