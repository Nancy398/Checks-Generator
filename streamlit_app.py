import streamlit as st
from io import BytesIO
# import pypandoc
# import num2words  # 用于将数字转换为英文大写
from datetime import datetime
import os
from PyPDF2 import PdfReader, PdfWriter

import io
from datetime import date
from decimal import Decimal, InvalidOperation
import streamlit as st
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

COMPANY = 'LAKE VIEW DEVELOPMENT LLC'
ADDRESS = ['3250 Wilshire Blvd, STE 1502', 'Los Angeles, CA 90010']
BANK = 'COMMERCIAL BANK OF CALIFORNIA'

ONES = ('','One','Two','Three','Four','Five','Six','Seven','Eight','Nine','Ten','Eleven','Twelve','Thirteen','Fourteen','Fifteen','Sixteen','Seventeen','Eighteen','Nineteen')
TENS = ('','','Twenty','Thirty','Forty','Fifty','Sixty','Seventy','Eighty','Ninety')
def under_thousand(n):
    parts=[]
    if n>=100:
        parts.append(ONES[n//100]+' Hundred'); n%=100
    if n>=20:
        parts.append(TENS[n//10]); n%=10
    if n: parts.append(ONES[n])
    return ' '.join(parts)
def money_words(amount):
    value=Decimal(str(amount)).quantize(Decimal('0.01'))
    whole=int(value); cents=int((value-whole)*100)
    if whole>999999999: raise ValueError('Amount too large')
    if whole==0: words='Zero'
    else:
        chunks=[]
        for divisor,name in ((1000000,'Million'),(1000,'Thousand'),(1,'')):
            chunk=whole//divisor; whole%=divisor
            if chunk: chunks.append(under_thousand(chunk)+(' '+name if name else ''))
        words=' '.join(chunks)
    return f'{words} and {cents:02d}/100 Dollars'

def make_pdf(check_no, issued, payee, amount, memo):
    buf=io.BytesIO()
    c=canvas.Canvas(buf,pagesize=letter)
    c.setTitle('Lakeview Check Print Layout')
    # Fixed positions in points on US Letter, from bottom left.
    c.setFont('Helvetica-Bold',11); c.drawString(90,744,COMPANY)
    c.setFont('Helvetica',8)
    for i,line in enumerate(ADDRESS): c.drawString(111,727-i*12,line)
    c.setFont('Helvetica-Bold',9); c.drawString(390,744,BANK)
    c.setFont('Helvetica',11); c.drawRightString(745,744,str(check_no))
    c.drawRightString(710,700,issued.strftime('%m/%d/%Y'))
    c.setFont('Helvetica',7); c.drawString(16,669,'PAY TO THE'); c.drawString(16,660,'ORDER OF')
    c.setFont('Helvetica',11); c.drawString(90,663,payee[:72])
    c.line(90,658,570,658)
    c.setFont('Helvetica-Bold',11); c.drawRightString(744,663,f'$ {amount:,.2f}')
    words=money_words(amount)
    c.setFont('Helvetica',9)
    if c.stringWidth(words,'Helvetica',9)>650:
        raise ValueError('Amount in words is too long for one line; adjust the template')
    c.drawString(16,631,words)
    c.line(16,625,742,625)
    c.setFont('Helvetica',8); c.drawString(16,584,'MEMO')
    c.setFont('Helvetica',9); c.drawString(55,584,memo[:70]); c.line(55,580,345,580)
    c.line(439,579,751,579)
    c.setFont('Helvetica',7); c.drawCentredString(600,567,'AUTHORIZED SIGNATURE')
    c.setFont('Helvetica',7); c.drawRightString(750,610,'VOID 90 DAYS AFTER ISSUE')
    # MICR intentionally omitted: use bank-approved preprinted check stock.
    c.setFont('Helvetica-Oblique',7); c.drawString(16,524,'PRINT ON BANK-APPROVED PREPRINTED CHECK STOCK; MICR NOT INCLUDED')
    c.line(16,490,750,490)
    c.setFont('Helvetica-Bold',10); c.drawString(16,464,'PAYMENT RECORD')
    for y,label,val in [(443,'CHECK NUMBER',str(check_no)),(425,'DATE',issued.strftime('%m/%d/%Y')),(407,'PAYEE',payee),(389,'AMOUNT',f'${amount:,.2f}'),(371,'MEMO',memo)]:
        c.setFont('Helvetica-Bold',9); c.drawString(16,y,label+':')
        c.setFont('Helvetica',9); c.drawString(125,y,str(val)[:100])
    c.save(); buf.seek(0)
    return buf.getvalue()

st.set_page_config(page_title='Lakeview Check Generator',layout='centered')
st.title('Lakeview Check Generator')
st.caption('Printable PDF layout based on your sample. Bank MICR information is not generated.')
with st.form('check'):
    a,b=st.columns(2)
    with a:
        check_no=st.text_input('Check number',value='2001')
        issued=st.date_input('Date',value=date.today())
    with b:
        amount_text=st.text_input('Amount (USD)',value='2500.00')
    payee=st.text_input('Payee',value='')
    memo=st.text_input('Memo',value='')
    submitted=st.form_submit_button('Generate printable PDF')
if submitted:
    try:
        amount=Decimal(amount_text.replace(',','').replace('$','')).quantize(Decimal('0.01'))
        if amount<=0: raise ValueError('Amount must be greater than zero')
        if not payee.strip(): raise ValueError('Payee is required')
        if not check_no.strip(): raise ValueError('Check number is required')
        pdf=make_pdf(check_no.strip(),issued,payee.strip(),amount,memo.strip())
        st.success('PDF generated')
        st.write('Amount in words:',money_words(amount))
        st.download_button('Download / Print PDF',pdf,file_name=f'Lakeview_Check_{check_no}.pdf',mime='application/pdf')
        st.info('Print at 100% / Actual size on US Letter. Check stock alignment and bank requirements before use.')
    except (ValueError,InvalidOperation) as e:
        st.error(str(e))


st.set_page_config(
    page_title="Check Generator", page_icon="🧾", layout="wide"
)


def number_to_words_usd(amount):
    """把数字金额转换为支票的标准大写英文"""
    try:
        dollars = int(amount)
        cents = int(round((amount - dollars) * 100))
        words = num2words(dollars, lang="en").title()
        return f"{words} and {cents:02d}/100 Dollars"
    except Exception:
        return ""


def fill_pdf_placeholders(pdf_bytes, replacements):
    """查找 PDF 中的 {{ key }} 占位符并替换为实际数据"""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    for page in doc:
        for key, val in replacements.items():
            str_val = str(val) if val is not None else ""

            # 兼容带有不同空格数量的占位符模式
            patterns = [
                f"{{{{ {key} }}}}",
                f"{{{{{key}}}}}",
                f"{{{{  {key}  }}}}",
                f"{{{{   {key}   }}}}",
            ]

            for pattern in patterns:
                rects = page.search_for(pattern)
                for rect in rects:
                    # 擦除原来的 {{ xxx }} 占位符文字
                    page.add_redact_annot(rect, fill=(1, 1, 1))
                    page.apply_redactions()

                    # 写入新数据（调整 baseline 基线对齐）
                    point = fitz.Point(rect.x0, rect.y1 - 2)
                    page.insert_text(
                        point, str_val, fontsize=10, color=(0, 0, 0)
                    )

    output_stream = io.BytesIO()
    doc.save(output_stream)
    doc.close()
    return output_stream.getvalue()


def display_pdf_preview(pdf_bytes):
    """在 Streamlit 页面中嵌入 PDF 实时预览"""
    base64_pdf = base64.b64encode(pdf_bytes).decode("utf-8")
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="100%" height="750" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)


# ----------------- Streamlit 界面排版 -----------------

st.title("🧾 Checks Generator")

# 1. 加载默认模板文件
DEFAULT_TEMPLATE_PATH = "check_run.pdf"
pdf_bytes = None

col1, col2 = st.columns([1, 1.2])

with col1:
    st.subheader("1. Import Info")

    # 判断本地是否存在 check_run.pdf
    if os.path.exists(DEFAULT_TEMPLATE_PATH):
        st.success(f"✅ 已成功读取后台模板：`{DEFAULT_TEMPLATE_PATH}`")
        with open(DEFAULT_TEMPLATE_PATH, "rb") as f:
            pdf_bytes = f.read()
    else:
        st.warning(
            f"⚠️ 未在同级目录下找到 `{DEFAULT_TEMPLATE_PATH}`，请手动上传："
        )
        uploaded_file = st.file_uploader(
            "上传 PDF 模板", type=["pdf"], key="check_uploader"
        )
        if uploaded_file:
            pdf_bytes = uploaded_file.read()

    st.markdown("---")

    # 变量输入框
    input_date = st.date_input("日期 (date)", value=date.today())
    date_str = input_date.strftime("%m/%d/%Y")

    name = st.text_input("收款人 (name)", value="John Doe")

    col_amt1, col_amt2 = st.columns([1, 1])
    with col_amt1:
        amount_num = st.number_input(
            "金额 $ (amount)",
            min_value=0.0,
            value=1250.50,
            step=0.01,
            format="%.2f",
        )
        amount_str = f"${amount_num:,.2f}"

    # 自动算出大写英文，也可手动微调
    auto_words = number_to_words_usd(amount_num)
    amount_words = st.text_input(
        "金额大写 (amount_words)", value=auto_words
    )

    col_chk1, col_chk2 = st.columns([1, 1])
    with col_chk1:
        check_number = st.text_input("支票编号 (number)", value="1001")
    with col_chk2:
        account = st.text_input("账号 (account)", value="ACC-883921")

    memo = st.text_area("备忘/用途 (memo)", value="Invoice Payment")

    # 建立对应你 PDF 里的变量映射字典
    replacements = {
        "date": date_str,
        "name": name,
        "amount": amount_str,
        "amount_words": amount_words,
        "memo": memo,
        "number": check_number,
        "account": account,
    }

with col2:
    st.subheader("2. 实时生成与预览")

    if pdf_bytes is not None:
        try:
            # 替换占位符并生成新的 PDF
            filled_pdf = fill_pdf_placeholders(pdf_bytes, replacements)

            st.download_button(
                label="📥 点击下载生成好的支票 PDF",
                data=filled_pdf,
                file_name=f"Check_{check_number}_{date_str.replace('/', '-')}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True,
            )

            st.markdown("---")
            display_pdf_preview(filled_pdf)

        except Exception as e:
            st.error(f"处理 PDF 时出错: {str(e)}")
    else:
        st.info("💡 请确保 `check_run.pdf` 放在项目根目录下。")
