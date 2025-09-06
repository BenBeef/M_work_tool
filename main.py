
# https://doi.org/10.17882/49388
from tkinter import N
import fitz  # PyMuPDF
import re
import pandas as pd
import numpy as np
from typing import *
from datetime import datetime
import traceback
import os
from config import Config

from sqlalchemy import false, true 

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
    return pre_content + doi


class RefContext:

    def __init__(self, page:int, content:str) -> None:
        self.page = page
        self.content = content
    
    def __str__(self) -> str:
        s = f'page:{self.page}, context:{self.content}'
        return s
    
    def to_json(self):
        return {'page':self.page, 'content':self.content}
    
    __repr__ = __str__

class Citation:

    def __init__(self, article_id:str, dataset_id:str, row_id=-1, true_type='Missing', pred_type="Missing") -> None:
        self.row_id = row_id
        self.article_id = article_id
        self.dataset_id = dataset_id
        self.true_type = true_type
        self.pred_type = pred_type
        self.page_num = -1  # 出现在文献的位置
        self.content = '' # 引用内容
        self.tag = None  # 出现在文章中的标签
        self.ref_contexts = [] # 文中的上线文
    
    def __str__(self) -> str:
        s = f'article_id:{self.article_id}, dataset_id:{self.dataset_id}, IN page:{self.page_num}, tag:{self.tag}'
        return s
    __repr__ = __str__

    def extrace_feature(self):
        """
        """
        pass
    
    @classmethod
    def to_excel(cls, cts:List["Citation"], file_path):
        """将Citation列表保存为Excel文件
        Args:
            cts: Citation对象列表
            file_path: 保存的Excel文件路径
        """
        columns = ['row_id', 'article_id', 'dataset_id', 'type', 'pred_type', 'content', 'tag', 'ref_contexts']
        
        # 构建数据列表
        data = []
        for ct in cts:
            row = {
                'row_id': ct.row_id,
                'article_id': ct.article_id,
                'dataset_id': ct.dataset_id,
                'type': ct.true_type,
                'pred_type': ct.pred_type,
                'content': ct.content,
                'tag': ct.tag,
                'ref_contexts': [ctx.to_json() for ctx in ct.ref_contexts] if ct.ref_contexts else []
            }
            data.append(row)
            
        # 转换为DataFrame并保存
        df = pd.DataFrame(data, columns=columns)
        df.to_excel(file_path, index=False)


class CitationExtractor:

    def __init__(self, article_id:str, pdf_dir) -> None:
        self.article_id = article_id
        self.pdf_path = os.path.join(pdf_dir, f'{self.article_id}.pdf')
        self.doc = fitz.open(self.pdf_path)
    
    def close(self):
        self.doc.close()
    
    def find_citations(self, page, ct:Citation):
        """查找页面中的引用"""
        
        # 定义可能的DOI引用格式
        target_doi = ct.dataset_id.strip()

        # 获取页面块，用于分析文本结构
        blocks = page.get_text("blocks")
        page_num = page.number + 1  # 页码从0开始，转换为从1开始

        contents = [block[4] for block in blocks]
        content = ''.join(contents)

        origin_cont = content
        if target_doi.startswith('https://doi.org'):
            # https://doi.org/10.5061/dryad.v2t58
            target_doi = re.sub(r'\.v[0-9]+$', '', target_doi)
            doi_number = target_doi.split('doi.org/')[-1].strip().lower()
            # http://dx.doi.org/10.5061/dryad.p3fg9
            origin_cont = origin_cont.replace('http://dx.doi', 'https://doi')
            key_words = ['https', 'DOI', 'doi']
            finded = False
            for key_word in key_words:
                if target_doi in origin_cont:
                    break
                if doi_number in origin_cont:
                    target_doi = doi_number
                    break
                content = origin_cont
                while content:
                    start = content.find(key_word)
                    if start == -1:
                        break
                    word = ''
                    origin_word = ''
                    for ch in content[start:]:
                        origin_word += ch
                        ch = ch.strip()
                        word += ch.lower()
                        if word in {target_doi, doi_number}:
                            origin_cont = origin_cont.replace(origin_word, word)
                            target_doi = word
                            finded = True
                            break
                        elif word != target_doi[:len(word)] and word != doi_number[:len(word)]:
                            content = content[start+len(key_word):]
                            break
                    if finded:
                        break
                if finded:
                    break
        content = origin_cont
        if content.find(target_doi) == -1:
            return
        citation_cont = cut_doi_citation(content, target_doi)
        if not citation_cont:
            return 
        ct.page_num = page_num
        ct.content = citation_cont
        ct.tag = extract_ref_tag(citation_cont)
        return True

    def cut_contexts(self, ct:Citation):
        """
        """
        tag = ct.tag
        if not tag:
            return 
        
        ref_contexts = []
        for page in self.doc:
            blocks = page.get_text("blocks")
            page_num = page.number + 1  # 页码从0开始，转换为从1开始
            for block in blocks:
                block_text = block[4].strip()  # block[4]包含文本内容
                block_text = re.sub(r'\s+', ' ', block_text)  # 将连续的空白字符替换为单个空格
                idx = block_text.find(tag)
                if idx == -1:
                    continue
                ref_context = RefContext(page=page_num, content=block_text[max(0, idx-256):idx+128])
                ref_contexts.append(ref_context)
        ct.ref_contexts = ref_contexts
    
    def extract_citation(self, ct:Citation):
        """处理PDF文件并查找所有引用"""
        try:
            for page in self.doc:
                if self.find_citations(page, ct):
                    self.cut_contexts(ct)
                    break
        except Exception as e:
            traceback.print_exc()
            print(f"处理PDF时出错: {str(e)}")
    
    @classmethod
    def pipeline(cls, csv_path:str, pdf_dir, to_excel=False):
        df = pd.read_csv(csv_path)
        if 'row_id' not in df.columns:
            df['row_id'] = np.arange(1, len(df)+1)
        
        # 取出数据
        citations:List[Citation] = []
        for _, row in df.iterrows():
            citation = Citation(
                article_id=row['article_id'],
                dataset_id=row['dataset_id'],
                row_id=row['row_id'],
                true_type=row.get('type', 'Missing')  # 使用get方法，如果没有type列则默认为Missing
            )
            citations.append(citation)
        
        for i, citation in enumerate(citations, start=1):
            extractor = cls(citation.article_id, pdf_dir)
            extractor.extract_citation(citation)
            extractor.close()
            citation.extrace_feature()
            if i % 50 == 0:
                print(f'finished {i}/{len(citations)}')
        
        if to_excel:
            file_path = f'citation_results_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
            Citation.to_excel(citations, file_path)
        
        return citations


if __name__ == "__main__":
    pdf_dir = Config.TRAIN_PDF_DIR
    csv_path = Config.TRAIN_LABLES
    CitationExtractor.pipeline(csv_path=csv_path, pdf_dir=pdf_dir, to_excel=True)
    # 10.1002_ecs2.1280	https://doi.org/10.5061/dryad.p3fg9	Primary
    # citation = Citation(article_id="10.1021_jacs.2c06519", dataset_id="https://doi.org/10.25377/sussex.21184705.v1")
    # extractor = CitationExtractor(citation.article_id, pdf_dir)
    # extractor.extract_citation(citation)
    # print(citation.ref_contexts)
    # print(citation.content)

