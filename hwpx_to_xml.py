
import zipfile
import os

def extract_hwpx(filepath, extract_to):
    with zipfile.ZipFile(filepath, 'r') as zip_ref:
        zip_ref.extractall(extract_to)

def read_hwpx_content(extracted_folder):
    # HWPX 파일의 주요 콘텐츠는 Contents 폴더의 section0.xml 파일에 있습니다.
    content_file = os.path.join(extracted_folder, 'Contents', 'section0.xml')
    with open(content_file, 'r', encoding='utf-8') as file:
        content = file.read()
    return content

# HWPX 파일 경로와 추출 폴더 지정
hwpx_file = f'./data/{file_name}.hwpx'
extracted_folder = f"./data/{file_name}"

# HWPX 파일 추출
extract_hwpx(hwpx_file, extracted_folder)

# 추출된 XML 콘텐츠 읽기
content = read_hwpx_content(extracted_folder)
 
