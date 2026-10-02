"""Regenerate fictional demo resumes with only PyMuPDF and Pillow."""
import io
import json
import fitz
from PIL import Image, ImageEnhance
from config import BASE_DIR

TEXT = '''ANANYA RAO
AI & Data Science Student
ananya@example.com | Mysuru, India

Education
B.E. Artificial Intelligence & Data Science, 2024-2028
Fictional Institute of Technology

Skills
Python, SQL, Pandas, Excel, Power BI, Git
Data Visualization and Communication

Projects
Student Performance Dashboard
Cleaned attendance data with Python and Pandas.
Used SQL joins to summarize student records.
Created Excel reports and Power BI charts for Data Visualization.
Tracked project changes with Git.

Experience
College data club volunteer
Explained dashboard findings through Communication with peers.

This is a fictional resume created for project demonstration.
'''
ADDITION = '''\nAdditional Project\n+Machine Learning Classification Study\n+Used NumPy and Scikit-learn for a Machine Learning experiment.\n+Applied Statistics to compare precision and recall on held-out data.\n+'''


def make_pdf(text, path):
    with fitz.open() as doc:
        page = doc.new_page(width=595, height=842)
        page.draw_rect(fitz.Rect(0, 0, 595, 112), color=None, fill=(.07, .15, .23))
        lines = text.splitlines()
        page.insert_text((42, 47), lines[0], fontsize=22, fontname='hebo', color=(1, 1, 1))
        page.insert_text((42, 69), lines[1], fontsize=12, color=(.7, .87, .85))
        page.insert_text((42, 90), lines[2], fontsize=10, color=(.8, .87, .93))
        y = 148
        for line in lines[3:]:
            if not line:
                y += 12; continue
            heading = line in {'Education', 'Skills', 'Projects', 'Experience', 'Additional Project'}
            page.insert_text((42, y), line, fontsize=12 if heading else 10,
                             fontname='hebo' if heading else 'helv', color=(.05, .45, .42) if heading else (.12, .2, .28))
            y += 21 if heading else 17
        doc.save(path)


def main():
    out = BASE_DIR / 'samples'; out.mkdir(exist_ok=True)
    make_pdf(TEXT, out / 'sample_resume.pdf')
    make_pdf(TEXT + ADDITION, out / 'sample_resume_v2.pdf')
    (out / 'sample_resume.txt').write_text(TEXT, encoding='utf-8')
    (out / 'sample_job_description.txt').write_text('Data Analyst intern: Python, SQL, Pandas, Excel and Statistics. Create dashboards with Power BI and communicate findings through Communication.', encoding='utf-8')
    with fitz.open(out / 'sample_resume.pdf') as doc:
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
        image = Image.frombytes('RGB', (pix.width, pix.height), pix.samples)
        image.save(out / 'sample_resume.png')
        photo = image.rotate(2.2, resample=Image.Resampling.BICUBIC, expand=True, fillcolor=(222, 224, 218))
        photo = ImageEnhance.Contrast(photo).enhance(.88)
        photo = ImageEnhance.Brightness(photo).enhance(.96)
        photo.save(out / 'sample_phone_photo.jpg', quality=89)
        stream = io.BytesIO(); image.save(stream, format='PNG')
    with fitz.open() as scanned:
        page = scanned.new_page(width=595, height=842)
        page.insert_image(page.rect, stream=stream.getvalue())
        scanned.save(out / 'sample_scanned_resume.pdf')
    expected = ['Python','SQL','Pandas','Excel','Power BI','Git','Data Visualization','Communication']
    annotations = {f: expected for f in ['sample_resume.pdf','sample_resume.png','sample_phone_photo.jpg','sample_scanned_resume.pdf']}
    annotations['sample_resume_v2.pdf'] = expected + ['NumPy','Scikit-learn','Machine Learning','Statistics']
    (BASE_DIR / 'data/sample_annotations.json').write_text(json.dumps(annotations, indent=2), encoding='utf-8')
    print('Created fictional PDF, PNG, photo, scanned PDF, v2 PDF and annotations.')


if __name__ == '__main__':
    main()

