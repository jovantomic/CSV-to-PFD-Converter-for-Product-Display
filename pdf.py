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
    
    # Add title on the first page
    c.setFont("DejaVuSans-Bold", 18)
    c.drawCentredString(width / 2.0, height - 30, title)

    # Add subtitle on the first page
    c.setFont("DejaVuSans-Bold", 16)
    c.drawCentredString(width / 2.0, height - 50, "Leuci Centar")

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

        # Determine the icons based on the 'Rok Isporuke' and 'Grlo' columns
        delivery_icon_path = 'delivery.png'  # Set your delivery icon path here
        delivery_icon_description = ''
        if 'Rok Isporuke' in df.columns and pd.notna(row['Rok Isporuke']):
            delivery_icon_description = row['Rok Isporuke']

        socket_icon_path = None
        socket_icon_description = ''
        if 'Grlo' in df.columns and pd.notna(row['Grlo']):
            socket_icon_description = row['Grlo']
            if row['Grlo'].strip().lower() == 'e27':
                socket_icon_path = 'e27.png'
            elif row['Grlo'].strip().lower() == 'gu10':
                socket_icon_path = 'gu10.png'
            elif row['Grlo'].strip().lower() == 'g9':
                socket_icon_path = 'g9.png'
            elif row['Grlo'].strip().lower() == 'e14':
                socket_icon_path = 'e14.png'

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

        # Draw icons side by side below description
        if delivery_icon_path or socket_icon_path:
            icon_size = int(container_height / 8)
            text_y -= text_spacing
            icon_x = text_x

            # Draw delivery icon and text
            if delivery_icon_path:
                draw_icon(c, icon_x, text_y - icon_size - 2, icon_size, delivery_icon_path)
                c.setFont("DejaVuSans", 8)
                c.drawString(icon_x-8, text_y - icon_size - 14, delivery_icon_description)
                icon_x += icon_size + 20  # Adjust space between icons

            # Draw socket icon and text
            if socket_icon_path:
                draw_icon(c, icon_x, text_y - icon_size - 2, icon_size, socket_icon_path)
                c.setFont("DejaVuSans", 8)
                c.drawString(icon_x, text_y - icon_size - 14, socket_icon_description.upper())

            text_y -= icon_size + text_spacing + 20  # Adjust for the next row

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