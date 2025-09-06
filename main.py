
# https://doi.org/10.17882/49388
from tkinter import N
import fitz  # PyMuPDF
import re

def extract_ref_tag(citation_cont:str):
    """
    """
    # 1- 以姓名开头
    auth_pat = '^([A-Z][a-z]+),\s+[A-Z]\.'  # 匹配单个作者姓名，例如: "Barbieux, M."
    year_pat = '\(([1-2][09][0-9][0-9])\)'
    auths = re.findall(auth_pat, citation_cont)
    years = re.findall(year_pat, citation_cont)
    if auths and years:
        # Barbieux, M., Organelli, E., Claustre, H., Schmechtig, C., Poteau, A., Boss, E., . . . Xing, X. (2017).
        # (Barbieux et al., 2017).
        auth = auths[0]
        tag = f'({auth} et al., {years[0]})'
        return tag
    
    # 2- 以[数字]格式开头
    ref_num_pat = '^\[(\d+)\]'  # 匹配类似[12]这样的引用标记
    ref_nums = re.findall(ref_num_pat, citation_cont)
    if ref_nums:
        return f'[{ref_nums[0]}]'
    return None


def longest_match(text:str, doi:str):
    """
    """
    idx = 0 
    while idx < len(doi):
        if text.find(doi[idx:]) > -1:
            return doi[idx:]
        idx += 1
    return None


def cut_doi_citation(text:str, doi:str):
    """ 这里假设doi是做了最长匹配了
    """
    doi = longest_match(text, doi)
    if not doi:
        return None
    start = text.find(doi)
    pre_content = text[:start][-256:]
    pat = '(?:\n|^)[A-Z].*?\([1-2][09][0-9][0-9]\).*?$'
    groups = re.findall(pat, pre_content, re.DOTALL)
    if groups:
        return (groups[0] + doi).strip()
    return None


def find_citations(page, target_doi):
    """查找页面中的引用"""
    
    # 定义可能的DOI引用格式
    doi_patterns = [
        rf"https?://doi\.org/{target_doi.split('doi.org/')[-1]}",  # 完整URL
        rf"DOI:\s*{target_doi.split('doi.org/')[-1]}",  # DOI: 格式
        rf"doi:\s*{target_doi.split('doi.org/')[-1]}",  # doi: 格式
        rf"{target_doi.split('doi.org/')[-1]}"  # 纯DOI号
    ]
    
    citations = []
    
    # 获取页面块，用于分析文本结构
    blocks = page.get_text("blocks")
    page_num = page.number + 1  # 页码从0开始，转换为从1开始


    exist_pos = set()
    
    for block in blocks:
        block_text = block[4]  # block[4]包含文本内容
        block_bbox = block[:4]  # 文本块的边界框坐标
        
        # 检查所有可能的引用格式
        for pattern in doi_patterns:
            matches = re.finditer(pattern, block_text, re.IGNORECASE)
            for match in matches:
                pos = f'{block_bbox[0]}__{block_bbox[1]}__{block_bbox[2]}__{block_bbox[3]}'
                if pos in exist_pos:
                    continue
                citation_cont = cut_doi_citation(block_text.strip(), target_doi)
                if not citation_cont:
                    continue
                exist_pos.add(pos)
                citation_info = {
                    "page": page_num,
                    "text": block_text.strip(),
                    "position": f"坐标: ({block_bbox[0]:.2f}, {block_bbox[1]:.2f}, {block_bbox[2]:.2f}, {block_bbox[3]:.2f})",
                    "match": match.group(),
                    "context": citation_cont,
                    "tag":extract_ref_tag(citation_cont)
                }
                citations.append(citation_info)
    
    return citations

def process_pdf(pdf_path, target_doi):
    """处理PDF文件并查找所有引用"""
    try:
        doc = fitz.open(pdf_path)
        all_citations = []
        
        for page in doc:
            citations = find_citations(page, target_doi)
            if citations:
                all_citations.extend(citations)
        
        doc.close()
        return all_citations
    
    except Exception as e:
        print(f"处理PDF时出错: {str(e)}")
        raise

def print_citations(citations):
    """格式化打印引用信息"""
    if not citations:
        print("未找到引用")
        return
    
    print(f"\n找到 {len(citations)} 处引用：\n")
    for i, citation in enumerate(citations, 1):
        print(f"引用 {i}:")
        print(f"页码: {citation['page']}")
        print(f"位置: {citation['position']}")
        print(f"匹配: {citation['match']}")
        print(f"引用上下文: {citation['context']}")
        print(f"引用标签: {citation['tag']}")
        print("-" * 80)


if __name__ == "__main__":
    pdf_path = "10.1002_2017jc013030.pdf"
    target_doi = "https://doi.org/10.17882/49388"
    
    try:
        citations = process_pdf(pdf_path, target_doi)
        print_citations(citations)
    except Exception as e:
        print(f"错误: {str(e)}")

