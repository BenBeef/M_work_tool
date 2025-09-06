# Python PDF处理工具示例

这个项目展示了如何使用Python的不同PDF处理库来处理PDF文件。

## 功能特性

- 使用PyPDF2读取PDF文本
- 使用pdfplumber提取PDF文本和表格
- 使用pdf2image将PDF转换为图像
- 使用PDFMiner提取PDF文本

## 环境要求

- Python 3.7+
- 相关依赖包（见requirements.txt）
- Poppler（用于pdf2image功能）

## 安装步骤

1. 克隆项目到本地

2. 创建虚拟环境（推荐）:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   venv\Scripts\activate     # Windows
   ```

3. 安装依赖:
   ```bash
   pip install -r requirements.txt
   ```

4. 安装Poppler（pdf2image必需）:

   Windows:
   - 访问 https://github.com/oschwartz10612/poppler-windows/releases/
   - 下载最新版本的 `Release-xx.xx.x-0.zip`
   - 解压下载的zip文件
   - 将解压后的文件夹复制到 `C:\Program Files\poppler`
   - 将 `C:\Program Files\poppler\bin` 添加到系统环境变量PATH中:
     1. 打开系统属性（右键"此电脑" -> 属性）
     2. 点击"高级系统设置"
     3. 点击"环境变量"
     4. 在"系统变量"中找到"Path"
     5. 点击"编辑"
     6. 点击"新建"
     7. 输入 `C:\Program Files\poppler\bin`
     8. 点击"确定"保存所有更改
   - 重启命令提示符或PowerShell

   Linux:
   ```bash
   sudo apt-get install poppler-utils
   ```

   Mac:
   ```bash
   brew install poppler
   ```

## 使用方法

运行main.py文件：
```bash
python main.py
```

这将使用不同的PDF处理库来读取示例PDF文件，并展示各种处理结果。

## 故障排除

1. pdf2image报错 "PDFInfoNotInstalledError: Unable to get page count. Is poppler installed and in PATH?"
   - 确保已正确安装poppler
   - 确保poppler的bin目录已添加到系统PATH中
   - 重启命令提示符或PowerShell
   - 如果问题仍然存在，尝试重启电脑

2. 如果在Windows中添加PATH后仍然无法运行，可以在代码中直接指定poppler路径：
   ```python
   from pdf2image import convert_from_path
   images = convert_from_path(pdf_path, poppler_path=r"C:\Program Files\poppler\bin")
   ```

## 各库的适用场景

1. PyPDF2：适合基本的PDF操作（读取、合并、分割）
2. pdfplumber：适合提取文本和表格数据
3. pdf2image：适合将PDF转换为图像
4. PDFMiner：适合深入分析PDF结构和布局
