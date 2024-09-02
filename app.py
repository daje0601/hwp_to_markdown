import gradio as gr
import re
from bs4 import BeautifulSoup
import os 

import zipfile
def process_xml(file):

    def extract_hwpx(filepath, extract_to):
        with zipfile.ZipFile(filepath, 'r') as zip_ref:
            zip_ref.extractall(extract_to)

    def read_hwpx_content(extracted_folder):
        # HWPX 파일의 주요 콘텐츠는 Contents 폴더의 section0.xml 파일에 있습니다.
        content_file = os.path.join(extracted_folder, 'Contents', 'section0.xml')
        with open(content_file, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    extract_hwpx(file.name, "./tmp")
    content = read_hwpx_content("./tmp")


    # BeautifulSoup 객체를 생성하여 XML 파싱
    soup = BeautifulSoup(content, "lxml")

    def one_by_one_extract_table_data(soup):
        rows = extract_top_level_tr_tags(soup)
        row_data = []
        for row in rows:
            cells = row.find_all("hp:tc")
            column_data = []
            for cell in cells:
                cell_text = ""
                for qwe in cell.find_all(["hp:t", "hc:img"]):
                    if qwe.name == "hp:t":
                        text = qwe.get_text(strip=True)
                        cell_text += text
                    elif qwe.name == "hc:img":
                        cell_text += qwe["binaryitemidref"]

                column_data.append("".join(cell_text))

            row_data.append(column_data)

        return row_data

    def check_uniform_length(data):
        lengths = [len(row) for row in data]
        all_equal = all(length == lengths[0] for length in lengths)
        return all_equal

    def list_to_markdown_table(group):
        valid_rows = [row for row in group]
        if not valid_rows:
            return ""

        header = " | " + " | ".join(valid_rows[0])
        separator = " | " + " | ".join(["---"] * len(valid_rows[0]))
        rows = [" | " + " | ".join(row) for row in valid_rows[1:]]
        return f"{header} |\n{separator}\n" + "\n".join(rows) + "\n"

    def is_child_of_another_p(tag):
        parent = tag.find_parent("hp:p")
        return parent is not None

    def extract_top_level_p_tags(soup):
        p_tags = soup.find_all("hp:p")
        top_level_p_tags = [p for p in p_tags if not is_child_of_another_p(p)]
        return top_level_p_tags

    def apply_colspan_rowspan(table, col, row, colspan, rowspan, value):
        for i in range(row, row + rowspan):
            for j in range(col, col + colspan):
                while i >= len(table):
                    table.append([])
                while j >= len(table[i]):
                    table[i].append("")
                if i == row and j == col:
                    table[i][j] = value
                else:
                    table[i][j] = ""

    def new_extract_table_data(soup):
        rows = extract_top_level_tr_tags(soup)
        table_data = []
        for row in rows:
            row_cells = row.find_all("hp:tc")
            for cell in row_cells:
                cell_text = ""
                for qwe in cell.find_all(["hp:t", "hp:script", "hc:img"]):
                    if (qwe.name == "hp:t") or (qwe.name == "hp:script"):
                        text = qwe.get_text(strip=True)
                        cell_text += text
                    elif qwe.name == "hc:img":
                        cell_text += qwe["binaryitemidref"]
                colspan = int(cell.find("hp:cellspan")["colspan"])
                rowspan = int(cell.find("hp:cellspan")["rowspan"])
                coladdr = int(cell.find("hp:celladdr")["coladdr"])
                rowaddr = int(cell.find("hp:celladdr")["rowaddr"])

                apply_colspan_rowspan(table_data, coladdr, rowaddr, colspan, rowspan, cell_text)

        if check_uniform_length(table_data):
            return list_to_markdown_table(table_data)
        else:
            return list_to_markdown_table(table_data)

    def is_child_of_another_tr(tag):
        parent = tag.find_parent("hp:tr")
        return parent is not None

    def extract_top_level_tr_tags(soup):
        tr_tags = soup.find_all("hp:tr")
        top_level_tr_tags = [tr for tr in tr_tags if not is_child_of_another_tr(tr)]
        return top_level_tr_tags

    def extract_and_print_structure(soup):
        p_tags = extract_top_level_p_tags(soup)
        output = ""
        for p in p_tags:
            
            table_found = False
            for child in p.descendants:
                if child.name == "hp:tbl":
                    table_found = True
                    table_data = new_extract_table_data(child)
                    output += table_data + "\n"

            if not table_found:
                # for pic in p.find_all("hp:pic"):
                #     pic.decompose()
                t_elements = p.find_all(["hp:t", "hp:script"])
                p_text = ""
                for element in t_elements:
                    if element.string:
                        p_text += element.get_text(strip=True)

                if p_text or p.find_all(["hc:img"]):
                    output += f"\n{p_text}\n"
                    for child in p.descendants:
                        if child.name == "hc:img" and child.has_attr("binaryitemidref"):
                            output += f"{child['binaryitemidref']}\n"
                        elif child.name == "hc:img" and child.has_attr("binaryItemIDRef"):
                            output += f"{child['binaryItemIDRef']}\n"
                        elif child.name == "hc:script":
                            output += child.get_text(strip=True)
        return output

    text = extract_and_print_structure(soup)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", text)
    return cleaned_text

iface = gr.Interface(
    fn=process_xml, 
    inputs=gr.File(file_count="single", type="filepath"), 
    outputs="text",
    title="Multi-Modal preprocessor(HWPx -> MarkDown)",
    description="""hwpx 파일을 업로드해주세요. 업로드된 파일을 Markdown 형식으로 변환해드립니다.
이미지가 포함된 경우, 해당 위치에 image 태그로 변환하여 표시됩니다. 현재는 hwpx 파일만 지원합니다.
많은 데이터를 테스트했지만, 혹시 변환 과정에서 문제가 발생하는 파일이 있을 경우 daje0601@gmail.com으로 문의해주시면 감사하겠습니다.
"""
)

# Launch the Gradio interface
iface.launch(share=True)
