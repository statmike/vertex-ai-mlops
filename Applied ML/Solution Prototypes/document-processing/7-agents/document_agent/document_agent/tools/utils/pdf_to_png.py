import fitz #pymupdf

def pdf_to_png(file_type, file_bytes):

    if file_type == 'application/pdf':
        doc = fitz.open(filetype ="pdf", stream = file_bytes)
        page = doc.load_page(0)
        pix = page.get_pixmap(dpi=300)
        file_bytes = pix.tobytes(output = 'png')                
        file_type = 'image/png'       

    return (file_type, file_bytes)