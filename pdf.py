import datetime
from datetime import datetime
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

def draw_multiline_text(c, text, x, y, line_height=12):
    """Draw multi-line text on the canvas."""
    for line in text.split('\n'):
        c.drawString(x, y, line)
        y -= line_height
    return y

def read_csv(file_path):
    """Read CSV file and return a DataFrame."""
    df = pd.read_csv(os.path.expanduser(file_path))
    # Drop any unnamed index column (commonly 'Unnamed: 0')
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    return df

def draw_icon_with_text(c, x, y, size, icon_path, text):
    """Draw an icon with text below it."""
    icon = PILImage.open(icon_path)
    icon = icon.resize((size, size), PILImage.LANCZOS)
    icon_io = BytesIO()
    icon.save(icon_io, format="PNG")
    icon_io.seek(0)
    icon_reader = ImageReader(icon_io)
    c.drawImage(icon_reader, x, y, width=size, height=size, mask='auto')
    c.setFont("DejaVuSans", 8)
    c.drawCentredString(x + size / 2, y - 10, text)

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

def draw_icon_with_text(c, x, y, size, icon_path, text):
    """Draw an icon with text below it and a border around the icon."""
    icon = PILImage.open(icon_path)
    icon = icon.resize((size, size), PILImage.LANCZOS)
    icon_io = BytesIO()
    icon.save(icon_io, format="PNG")
    icon_io.seek(0)
    icon_reader = ImageReader(icon_io)
    
    # Draw border
    c.setStrokeColor(colors.black)
    c.setLineWidth(1)
    c.rect(x - 1, y - 1, size + 2, size + 2, stroke=True, fill=False)
    
    # Draw image
    c.drawImage(icon_reader, x, y, width=size, height=size, mask='auto')
    
    # Draw text
    c.setFont("DejaVuSans", 8)
    text_lines = text.split('\n')
    for i, line in enumerate(text_lines):
        c.drawCentredString(x + size / 2, y - 10 - (i * 10), line)


def generate_pdf(df, output_file, title):
    c = canvas.Canvas(output_file, pagesize=letter)
    width, height = letter

    # Register and set the TrueType fonts
    pdfmetrics.registerFont(TTFont('DejaVuSans', 'DejaVuSans.ttf'))
    pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', 'DejaVuSans-Bold.ttf'))
    
    # Add title on the first page
    c.setFont("DejaVuSans-Bold", 18)
    c.drawCentredString(width / 2.0, height - 30, title)

    # Add subtitle on the first page
    c.setFont("DejaVuSans-Bold", 16)
    c.drawCentredString(width / 2.0, height - 50, "Leuci Centar")

    # Add contact information on the left
    c.setFont("DejaVuSans", 10)
    contact_text = "+38163 212 212\nleucibeograd@gmail.com"
    draw_multiline_text(c, contact_text, 30, height - 20, line_height=12)

    # Add information text on the right
    info_text = "Za cene i količinu pozovite \nili pošaljite upit putem mejla"
    info_y = draw_multiline_text(c, info_text, width - 150, height - 20, line_height=12)

    # Add creation date at the bottom of information text
    creation_date = f"Datum kreiranja: {datetime.now().strftime('%Y-%m-%d')}"
    c.drawString(width - 150, info_y - 12, creation_date)

    c.setFont("DejaVuSans", 12)


    y = height - 60  # Adjust Y position for content, accounting for the subtitle
    line_height = 12  # Height for each line of text
    text_spacing = 8  # Spacing between different text blocks

    container_height = 150

    colors_cycle = [colors.HexColor("#E0F7FA"), colors.white]  # Light blue and white
    color_index = 0

    for index, row in df.iterrows():
        # Set the background color
        c.setFillColor(colors_cycle[color_index])
        c.rect(0, y - container_height, width, container_height, stroke=False, fill=True)
        color_index = (color_index + 1) % 2

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

        # Draw product details
        text_x = width * 1/3 + 40
        text_y = y - 30

        if 'Ime' in df.columns and pd.notna(row['Ime']):
            c.setFont("DejaVuSans-Bold", 12)
            c.setFillColor(colors.black)  # Set text color to black
            c.drawString(text_x, text_y, f"{row['Ime']}")
            text_y -= line_height + text_spacing
            c.setFont("DejaVuSans", 10)

        if 'Opis' in df.columns and pd.notna(row['Opis']):
            description = row['Opis']
            while description:
                if len(description) <= 70:
                    c.drawString(text_x, text_y, description)
                    description = ""
                else:
                    for i in range(70, 0, -1):
                        if description[i] == ' ':
                            break
                    c.drawString(text_x, text_y, description[:i])
                    description = description[i+1:]
                text_y -= line_height

        # Define icons and their descriptions
        icons = [
            ('Rok Isporuke', 'delivery.png'),
            ('Grlo', {'e27': 'e27.png', 'gu10': 'gu10.png', 'g9': 'g9.png', 'e14': 'e14.png'}),
            ('CCT', 'cct.jpg'),
            ('Dim', 'dim.jpg'),
            ('Remote', 'remote.jpg'),
            ('IP', 'IP.png')
        ]

        # Draw icons side by side at the bottom of the container
        icon_size = int(container_height / 8)
        icon_x = text_x
        icon_y = y - container_height + 45  # Align icons at the bottom of the containerubicu se  zadasadselenui kvadratic danas nisam kucao

        for column, icon in icons:
            if column in df.columns and pd.notna(row[column]):
                if row[column].strip().lower() == 'ne':
                    continue

                icon_path = icon if isinstance(icon, str) else icon.get(row[column].strip().lower(), None)
                text = row[column] if row[column].strip().lower() != 'da' else column

                # Special handling for Rok Isporuke to split text into two lines
                if column == 'Rok Isporuke':
                    text = f"do\n{row[column]}"

                if icon_path:
                    draw_icon_with_text(c, icon_x, icon_y - icon_size - 2, icon_size, icon_path, text)
                    icon_x += icon_size + 10  # Adjust space between icons

        y -= container_height  # Move to the next product position

        # Check if enough space is available for the next item
        if y < container_height:
            c.showPage()  # Start new page if not enough space
            y = height - 20  # Reset Y position for new page, but do not add title or subtitle
            c.setFont("DejaVuSans", 10)

    c.save()



def main():
    input_csv = 'SpoljnaRasveta.csv'
    output_pdf = 'Final7.pdf'  # Output PDF file name

    df = read_csv(input_csv)

    # Extract the base name of the CSV file without the extension for the title
    title = os.path.splitext(os.path.basename(input_csv))[0]

    generate_pdf(df, output_pdf, title)
    print(f"PDF file '{output_pdf}' has been generated.")

if __name__ == "__main__":
    main()