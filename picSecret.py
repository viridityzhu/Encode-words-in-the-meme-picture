#!/usr/bin/python
# -*- coding: UTF-8 -*-
import tkinter as tk      # 导入 Tkinter 库
from tkinter import filedialog
from tkinter.filedialog import askdirectory
import tkinter.messagebox as messagebox
import tkinter.ttk as ttk
from tkinter import scrolledtext
from tkinter import Menu
import random
from PIL import Image
import os
import sys
# 这句话就是密钥本身
# TODO：
# 1. 帮助 ok
# 2. 解密密码 ok
# 3. 图片格式自动转换 ok


def get__dir__():
    if getattr(sys, 'frozen', False):
        # frozen
        dir_ = os.path.dirname(sys.executable)
    else:
        # unfrozen
        dir_ = os.path.dirname(os.path.realpath(__file__))

    return dir_


saveDir = get__dir__()


# 字符串加密
def encrypt(key, s):
    # key和s都是字符串
    key = bytearray(str(key).encode("utf-8"))
    b = bytearray(str(s).encode("utf-8"))
    n = len(b)  # 求出 b 的字节数
    c = bytearray(n * 2)
    j = 0
    lenKey = len(key)
    for i in range(0, n):
        b1 = b[i] ^ key[(i * 5) % lenKey]
        b2 = b1 ^ key[(i + 3) % lenKey]  # b1 = b2^ key
        c1 = b2 % 16
        c2 = b2 // 16  # b2 = c2*16 + c1
        c1 = c1 + 65
        c2 = c2 + 65  # c1,c2都是0~15之间的数,加上65就变成了A-P 的字符的编码
        c[j] = c1
        c[j + 1] = c2
        j = j + 2
    return c.decode("utf-8")


# 字符串解密
def decrypt(key, s):
    key = bytearray(str(key).encode("utf-8"))
    c = bytearray(str(s).encode("utf-8"))
    n = len(c)  # 计算 b 的字节数
    lenKey = len(key)
    if n % 2 != 0:
        return ""
    n = n // 2
    b = bytearray(n)
    j = 0
    for i in range(0, n):
        c1 = c[j]
        c2 = c[j + 1]
        j = j + 2
        c1 = c1 - 65
        c2 = c2 - 65
        b2 = c2 * 16 + c1
        b1 = b2 ^ key[(i + 3) % lenKey]
        b[i] = b1 ^ key[(i * 5) % lenKey]
    try:
        return b.decode("utf-8")
    except:
        return "密钥错误"


# 待隐写图片初始化
def makeImageEven(image):
    # 得到类表[(r,g,b,t),(r,g,b,t)...]
    pixels = list(image.getdata())
    # 将每个像素的最低有效位初始化为0
    evenPixels = [(r >> 1 << 1, g >> 1 << 1, b >> 1 << 1, t >> 1 << 1)
                  for [r, g, b, t] in pixels]
    # 创建原图副本
    evenImage = Image.new(image.mode, image.size)
    # 把擦除的像素放入副本
    evenImage.putdata(evenPixels)
    # 返回初始化的隐写图片
    return evenImage


def constLenBin(int):
    # 去掉bin()返回的二进制字符串的'0b'
    # 在左边补足'0'直到字符串长度为8
    binary = "0" * (8 - (len(bin(int)) - 2)) + bin(int).replace('0b', '')
    return binary


# 隐写数据
def encodeDataInImage(image, data):
    # 获得最低有效位为0的图片副本
    evenImage = makeImageEven(image)
    # 将被隐藏的字符串转换成二进制字符串
    binary = ''.join(map(constLenBin, bytearray(data, 'utf-8')))

    # 数据信息溢出图片空间，则抛异常
    # 每个像素rgba有四个分量，即四个最低有效位
    if len(binary) > len(image.getdata()) * 4:
        raise Exception("Error: Can't encode more than " +
                        len(evenImage.getdata()) * 4 + " bits in this image. ")
    # 将字符二进制位数写入遍历像素的最低有效位
    encodedPixels = [(r + int(binary[index * 4 + 0]), g + int(binary[index * 4 + 1]), b + int(binary[index * 4 + 2]), t + int(binary[index * 4 + 3]))
                     if index * 4 < len(binary) else (r, g, b, t) for index, (r, g, b, t) in enumerate(list(evenImage.getdata()))]
    # 创建新图存放编码后的像素
    encodedImage = Image.new(evenImage.mode, evenImage.size)
    # 添加数据
    encodedImage.putdata(encodedPixels)
    return encodedImage


# 解码接受图片对象参数
def decodeImage(image):
    # 获取像素列表
    pixels = list(image.getdata())
    # 提取图片中所有最低有效位中的数据
    binary = ''.join([str(int(r >> 1 << 1 != r)) + str(int(g >> 1 << 1 != g)) + str(
        int(b >> 1 << 1 != b)) + str(int(t >> 1 << 1 != t)) for (r, g, b, t) in pixels])
    # 找到数据截止处的索引
    # 中文字符utf-8两个字节，16个二进制位
    locationDoubleNull = binary.find('0000000000000000')
    # 不足位补零
    endIndex = locationDoubleNull + \
        (8 - (locationDoubleNull % 8)
         ) if locationDoubleNull % 8 != 0 else locationDoubleNull
    data = binaryToString(binary[0:endIndex])
    return data


# 位字节->字符
# 将提取出来的二进制字符转换为隐藏的文本
def binaryToString(binary):
    index = 0
    string = []
    # 提取码点真正的字符数据
    # 区分字节标志与字符数据

    def rec(x, i): return x[2:8] + \
        (rec(x[8:], i - 1) if i > 1 else '') if x else ''
    # 获取字符数据

    def fun(x, i): return x[i + 1:8] + rec(x[8:], i - 1)
    while index + 1 < len(binary):
        # 分析字节序列
        # 字符的字节数据中，第一个字节开头 1 的数目便是字符所占的字节数
        chartype = binary[index:].index('0')
        length = chartype * 8 if chartype else 8
        # chr()将unicode码点转为对应字符
        string.append(chr(int(fun(binary[index:index + length], chartype), 2)))
        index += length
    return ''.join(string)


def encode():
    # 随机从图库挑一张图片
    if isCustomize.get() == 0:
        r = random.randint(1, 4)
        filename = get__dir__() + '/' + str(r) + '.png'
    # 自选图片
    else:
        filename = filedialog.askopenfilename(filetypes=[("Png", ".png"),
                                                         ("Jpg", ".jpg"),
                                                         ("Jpeg", ".jpeg"),
                                                         ("BMP", ".bmp")])
    image = Image.open(filename)
    if image.mode != 'RGBA':
        # 图片格式转化
        image = image.convert("RGBA")
    data = entryText.get('1.0', 'end')
    # 加密文字
    key = encodeKey.get()
    if key != '':
        data = encrypt(key, data)
    encodeDataInImage(image, data).save(
        saveDir + '/' + 'encodeImage.png')
    messagebox.showinfo(title="加密成功！", message="已生成图片文件“encodeImage.png”")


def decode():
    filename = filedialog.askopenfilename(filetypes=[("Pictures", ".png")])
    text = decodeImage(Image.open(filename))
    key = decodeKey.get()
    if key != '':
        text = decrypt(key, text)
    labelDecode.delete('1.0', 'end')
    labelDecode.insert('1.0', text)


def helpWindow():
    helpWin = tk.Toplevel(root)
    helpWin.title('使用说明')
    helpLabel = ttk.Label(helpWin, text="""
        本工具可将文本进行加密，并藏匿于图片的编码中，不改变图片的肉眼效果。
        - 加密
        1. 「自选图片」：自由上传被加密图片；否则从图库中随机挑选一张
        2. 「密钥」：使用密钥加密文本；留空则不加密
        3. 单击「加密」按钮，生成加密图片“encodeImage.png”，默认保存在本程序所在文件夹中。
        （可在设置中修改默认图片保存位置）

        - 解密
        1. 「密钥」：填写加密密钥；若未加密，留空即可
        2. 单击「上传图片」按钮，选择图片进行解密。
        """)
    helpLabel.pack()


def dirSet():
    setDirWin = tk.Toplevel(root)
    setDirWin.title('图片默认存储位置')
    dirFrame = ttk.Frame(setDirWin)
    dirLabel = ttk.Label(dirFrame, text='路径：')

    dirText = tk.Entry(dirFrame, textvariable=path)
    path.set(saveDir)
    dirText['state'] = 'readonly'
    dirBtn = ttk.Button(setDirWin, text='选择', command=dirChange)

    dirFrame.pack(padx=5, pady=5)
    dirLabel.pack(side=tk.LEFT)
    dirText.pack(side=tk.RIGHT, ipadx=150)
    dirBtn.pack(pady=5)


def dirChange():
    global saveDir
    saveDir = askdirectory()
    path.set(saveDir)


# ------------------主窗口----------------------
root = ttk.setup_master()
root.title('图片传密')
path = tk.StringVar()
# -------tab-------
tabControl = ttk.Notebook(root)

tabEncode = ttk.Frame(tabControl)
tabControl.add(tabEncode, text='加密')
tabDecode = ttk.Frame(tabControl)
tabControl.add(tabDecode, text='解密')
# -------tab-------


# 创建菜单栏
menuBar = Menu(root)
root.config(menu=menuBar)

# 添加菜单项：设置
setMenu = Menu(menuBar, tearoff=0)
setMenu.add_command(label="更改默认存储位置", command=dirSet)
setMenu.add_separator()
setMenu.add_command(label="退出", command=tk._exit)
menuBar.add_cascade(label="设置", menu=setMenu)

# 添加菜单项：帮助
helpMenu = Menu(menuBar, tearoff=0)
helpMenu.add_command(label="使用说明", command=helpWindow)
menuBar.add_cascade(label="帮助", menu=helpMenu)
# ------------------主窗口----------------------


# -------------------组件-----------------------
# 按钮
btnEncode = ttk.Button(tabEncode, text='加密', command=encode)
btnDecode = ttk.Button(tabDecode, text='上传图片', command=decode)

# 密文输入框
text = '输入密文'
entryText = scrolledtext.ScrolledText(
    tabEncode, width=40, height=5, font=('Arial', 14))
entryText.insert(tk.END, '输入密文')

# 解密框
labelExplain = ttk.Label(tabDecode, text='密文如下：')
labelDecode = scrolledtext.ScrolledText(
    tabDecode, width=40, height=5, font=('Arial', 14))
labelDecode.insert(tk.END, '...')

# 自选图片复选按钮
isCustomize = tk.IntVar()
isCustomize.set(0)
checkCustomize = ttk.Checkbutton(
    tabEncode, text='自选图片', variable=isCustomize, onvalue=1, offvalue=0)

# Encode密钥
frameKeyE = ttk.Frame(tabEncode)
labelKeyE = ttk.Label(frameKeyE, text='密钥：')
encodeKey = ttk.Entry(frameKeyE)
# Decode密钥
frameKey = ttk.Frame(tabDecode)
labelKey = ttk.Label(frameKey, text='密钥：')
decodeKey = ttk.Entry(frameKey)

# -------------------组件-----------------------


# -------------------放置-----------------------
tabControl.pack(expand=1, fill="both", padx=10)

entryText.pack(expand=1, fill="both",)
checkCustomize.pack(pady=5, after=entryText, anchor=tk.W)


frameKeyE.pack(pady=2)
labelKeyE.pack(side=tk.LEFT)
encodeKey.pack(side=tk.RIGHT)
btnEncode.pack()

frameKey.pack(pady=10)
labelKey.pack(side=tk.LEFT)
decodeKey.pack(side=tk.RIGHT)

btnDecode.pack()
labelExplain.pack(anchor=tk.W)
labelDecode.pack()
# -------------------放置-----------------------


# 进入消息循环
entryText.focus()
root.mainloop()
