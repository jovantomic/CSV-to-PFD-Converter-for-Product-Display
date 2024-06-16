import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib import colors
import requests
from PIL import Image as PILImage
from io import BytesIO
import os

def read_csv(file_path):
    """Read CSV file and return a DataFrame."""
    df = pd.read_csv(os.path.expanduser(file_path))
    # Drop any unnamed index column (commonly 'Unnamed: 0')
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df

def download_image(url):
    """Download image from URL and return a BytesIO object."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        img_data = BytesIO(response.content)
        img = PILImage.open(img_data)
        img_buffer = BytesIO()
        img.save(img_buffer, format="PNG")
        img_buffer.seek(0)
        return img_buffer
    except Exception as e:
        print(f"Error downloading image from {url}: {e}")
        return None

def draw_icon(c, x, y, size, icon_path):
    """Draw an icon at the specified location with a border."""
    icon = PILImage.open(icon_path)
    icon = icon.resize((size, size), PILImage.LANCZOS)
    icon_io = BytesIO()
    icon.save(icon_io, format="PNG")
    icon_io.seek(0)
    icon_reader = ImageReader(icon_io)
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.rect(x - 1, y - 1, size + 2, size + 2, stroke=True, fill=False)
    c.drawImage(icon_reader, x, y, width=size, height=size, mask='auto')

def generate_pdf(df, output_file, title):
    """Generate PDF from DataFrame."""
    c = canvas.Canvas(output_file, pagesize=letter)
    width, height = letter

    # Register and set the TrueType fonts
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))
    c.setFont("DejaVuSans-Bold", 16)

    # Add title
    c.drawCentredString(width / 2.0, height - 40, title)

    c.setFont("DejaVuSans", 10)

    y = height - 80  # Adjust Y position for content
    line_height = 12  # Height for each line of text
    text_spacing = 8  # Spacing between different text blocks

    container_height = 180
    container_spacing = 15  # Reduced spacing between containers

    for index, row in df.iterrows():
        # Draw border for product
        c.setStrokeColor(colors.black)
        c.setLineWidth(1)
        c.rect(20, y - container_height, width - 40, container_height, stroke=True, fill=False)

        # Download and draw the image
        if 'Slika' in df.columns and pd.notna(row['Slika']):
            img = download_image(row['Slika'])
            if img:
                image = ImageReader(img)
                img_width = width * 1/3 - 30  # Set image width to the left third of the container minus margins
                img_height = container_height - 20  # Full height of the container minus margins
                img_x = 20 + (width * 1/3 - img_width) / 2  # Center the image in the left third of the container
                img_y = y - container_height + (container_height - img_height) / 2  # Center the image vertically
                c.drawImage(image, img_x, img_y, width=img_width, height=img_height, preserveAspectRatio=True)

        # Determine the icon based on the 'Grlo' column
        icon_path = None
        if 'Grlo' in df.columns and pd.notna(row['Grlo']):
            if row['Grlo'].strip().lower() == 'e27':
                icon_path = 'e27.png'
            elif row['Grlo'].strip().lower() == 'gu10':
                icon_path = 'gu10.png'

        # Draw product details
        text_x = width * 1/3 + 40
        text_y = y - 30

        if 'Ime' in df.columns and pd.notna(row['Ime']):
            c.setFont("DejaVuSans-Bold", 12)
            c.drawString(text_x, text_y, f"{row['Ime']}")
            text_y -= line_height + text_spacing
            c.setFont("DejaVuSans", 10)

        if 'Cena' in df.columns and pd.notna(row['Cena']):
            c.drawString(text_x, text_y, f"{row['Cena']} RSD")
            text_y -= line_height + text_spacing

        if 'Opis' in df.columns and pd.notna(row['Opis']):
            description = row['Opis']
            while description:
                if len(description) <= 60:
                    c.drawString(text_x, text_y, description)
                    description = ""
                else:
                    for i in range(60, 0, -1):
                        if description[i] == ' ':
                            break
                    c.drawString(text_x, text_y, description[:i])
                    description = description[i+1:]
                text_y -= line_height

        # Draw icon below description
        if icon_path:
            icon_size = int(container_height / 8)
            text_y -= text_spacing
            draw_icon(c, text_x, text_y - icon_size - 2, icon_size, icon_path)
            text_y -= icon_size + text_spacing

        y -= container_height + container_spacing  # Move to the next product position

        # Check if enough space is available for the next item
        if y < container_height + container_spacing:
            c.showPage()  # Start new page if not enough space
            y = height - 80  # Reset Y position for new page
            c.setFont("DejaVuSans-Bold", 16)
            c.drawCentredString(width / 2.0, height - 40, title)
            c.setFont("DejaVuSans", 10)

    c.save()

def main():
    input_csv = 'SpoljnaRasveta2.csv'
    output_pdf = 'Final3.pdf'  # Output PDF file name

    df = read_csv(input_csv)

    # Extract the base name of the CSV file without the extension for the title
    title = os.path.splitext(os.path.basename(input_csv))[0]

    generate_pdf(df, output_pdf, title)
    print(f"PDF file '{output_pdf}' has been generated.")

if __name__ == "__main__":
    main()
