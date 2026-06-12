from pypdf import PdfReader
import os

web_dir = r'C:\Users\ALEJOO\Documents\Gym IG Content Landing Page\ai-models\deepl-search\web-sources'
out_dir = r'C:\Users\ALEJOO\Documents\Gym IG Content Landing Page\ai-models\deepl-search\extractions\text_dumps'
os.makedirs(out_dir, exist_ok=True)

pdfs = [
    '1935826.1935921.pdf',
    '2001.00861v1.pdf',
    '2005.13783v2.pdf',
    '2012.03_Wu_Brynjolfsson_The Future of Prediction_299.pdf',
    '2023.findings-acl.474.pdf',
    '23-062_1f58623a-ee21-44b9-a262-276047bc5543.pdf',
    '2306.02043v1.pdf',
    '2401.04319v3.pdf',
    '2408.05676v2.pdf',
    'ajibm_2123854.pdf',
    'applsci-10-08473-v2.pdf',
    'document.pdf',
    'li2020.pdf',
    'pnas.1005962107.pdf',
    'Representing Tasks with a Graph-Based Method for Supporting Users in Complex Search Tasks.pdf',
    'Revealed_Attention.pdf',
    'ssrn-1340267.pdf',
    'suh2021.pdf',
    'sustainability-13-00391-v2.pdf',
]

for fname in pdfs:
    path = os.path.join(web_dir, fname)
    if not os.path.exists(path):
        print(f'MISSING: {fname}')
        continue
    try:
        reader = PdfReader(path)
        pages = [p.extract_text() for p in reader.pages]
        full = '\n\n===PAGE BREAK===\n\n'.join(pages)
        safe_name = fname.replace('.pdf', '.txt')
        outpath = os.path.join(out_dir, safe_name)
        with open(outpath, 'w', encoding='utf-8') as f:
            f.write(full)
        print(f'OK ({len(reader.pages):2d}p): {fname}')
    except Exception as e:
        print(f'ERROR {fname}: {e}')
