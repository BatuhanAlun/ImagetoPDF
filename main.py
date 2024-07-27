from PIL import Image
from reportlab.pdfgen import canvas
from io import BytesIO
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import fitz  # PyMuPDF

def merge_images_to_pdf(image_paths, output_pdf_path):
    pdf_buffer = BytesIO()
    pdf = canvas.Canvas(pdf_buffer)

    for image_path in image_paths:
        try:
            img = Image.open(image_path)
            width, height = img.size
            pdf.setPageSize((width, height))
            pdf.showPage()
            pdf.drawInlineImage(img, 0, 0, width, height)
        except (OSError, IOError) as e:
            print(f"Error processing {image_path}: {e}")
            continue  

    pdf.save()

    with open(output_pdf_path, 'wb') as output_pdf:
        pdf_buffer.seek(0)
        output_pdf.write(pdf_buffer.read())

def download_manga_image(url, save_path):
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        with open(save_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    file.write(chunk)
    except requests.exceptions.RequestException as e:
        print(f"Error downloading {url}: {e}")
        raise  

def get_manga_image_urls(imagesite_url, chapter_start, chapter_end):
    image_urls = []
    
    for chapter_number in range(chapter_start, chapter_end + 1):
        chapter_url = f"{imagesite_url}/chapter-{chapter_number}"
        response = requests.get(chapter_url)
        response.raise_for_status() 

        soup = BeautifulSoup(response.content, 'html.parser')
        img_tags = soup.find_all('img', {'data-src': True})
        
        for img in img_tags:
            image_urls.append(urljoin(chapter_url, img['data-src']))

    return image_urls

def compress_pdf(input_pdf_path, output_pdf_path):
    pdf_document = fitz.open(input_pdf_path)
    pdf_document.save(output_pdf_path, garbage=4, deflate=True)
    pdf_document.close()

def delete_images(image_paths):
    for image_path in image_paths:
        try:
            os.remove(image_path)
            print(f"Deleted: {image_path}")
        except OSError as e:
            print(f"Error deleting {image_path}: {e}")

def create_pdf(imagesite_url, output_directory, output_pdf_path, chapter_start, chapter_end):
    os.makedirs(output_directory, exist_ok=True)

    image_urls = get_manga_image_urls(imagesite_url, chapter_start, chapter_end)

    for i, url in enumerate(image_urls, start=1):
        image_path = os.path.join(output_directory, f"page_{i}.jpg")
        try:
            download_manga_image(url, image_path)
        except Exception as e:
            print(f"Error processing {url}: {e}")
            continue  

    
    existing_image_paths = [os.path.join(output_directory, f"page_{i}.jpg") for i in range(1, len(image_urls) + 1) if os.path.exists(os.path.join(output_directory, f"page_{i}.jpg"))]

    merge_images_to_pdf(existing_image_paths, output_pdf_path)

    # Compress the PDF
    compress_pdf(output_pdf_path, output_pdf_path.replace(".pdf", "_compressed.pdf"))

    # Delete the image files
    delete_images(existing_image_paths)

if __name__ == "__main__":
    imagesite_url = "https://ww7.mangakakalot.tv/chapter/manga-bn978870"
    output_directory = "C:\\images"
    output_pdf_path = "C:\\images\\merged_manga.pdf"

    chapter_start = 1
    chapter_end = 2

    create_pdf(imagesite_url, output_directory, output_pdf_path, chapter_start, chapter_end)
