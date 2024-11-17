import pdfplumber
import os
from IPython.display import display, Image
import fitz  # PyMuPDF
import base64
import dotenv

#pdf_file = '/content/wildfire_stats.pdf'
def extract_context(file_path: str) -> dict:

    def extract_text_from_pdf(pdf_path):
        with pdfplumber.open(pdf_path) as pdf:
            text = ''
            for page in pdf.pages:
                text += page.extract_text()  # Extract text from each page
        return text

    def extract_images_from_pdf(pdf_path):
        # Open the PDF file
        pdf_document = fitz.open(pdf_path)
        images_list = []  # List to store image file paths

        # Loop through each page
        for page_num in range(len(pdf_document)):
            page = pdf_document.load_page(page_num)  # Load each page
            image_list = page.get_images(full=True)  # Extract images

            # Loop through all the images on the page
            for img_index, img in enumerate(image_list):
                xref = img[0]  # Image index reference
                base_image = pdf_document.extract_image(xref)  # Extract the image
                image_bytes = base_image["image"]  # Image data
                image_ext = base_image["ext"]  # Image file extension

                # Save the image to a temporary file
                image_filename = f"image_page{page_num + 1}_{img_index + 1}.{image_ext}"
                with open(image_filename, "wb") as image_file:
                    image_file.write(image_bytes)

                images_list.append(image_filename)  # Add file path to the list

                print(f"Extracted: {image_filename}")

        return images_list  # Return the list of images

    def convert_images_to_base64(file_paths):
        base64_images = []
        
        for file_path in file_paths:
            with open(file_path, "rb") as image_file:
                # Read the image file and encode it to base64
                encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                base64_images.append(encoded_string)
        
        return base64_images

    # Convert the images and store them as base64
    base64_images = convert_images_to_base64(image_list)
    base64_images[0]
    pdf_path = "/content/wildfire_stats.pdf"

    text = extract_text_from_pdf(file_path)

    image_list = extract_images_from_pdf(pdf_path)
    base64_images = convert_images_to_base64(image_list)

    data = { "text":text, "base64_images":base64_images}
    return data


 
