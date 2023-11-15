import base64
import streamlit as st

from PIL import Image, ImageDraw, ImageOps


# Function to create rounded icons
def create_rounded_icon(path, size=(60, 60)):
    img = Image.open(path).resize(size)
    mask = Image.new('L', img.size, 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.ellipse((0, 0) + img.size, fill=255)
    img_rounded = ImageOps.fit(img, mask.size, centering=(0.5, 0.5))
    img_rounded.putalpha(mask)
    return img_rounded


# Load and process logos
USER_LOGO = create_rounded_icon('./img/user_logo_dark.jpg')
ASSISTANT_LOGO = create_rounded_icon('./img/ai_logo_2.jpg')


# Function to set the logo in the sidebar
def set_logo(logo_path):
    logo = Image.open(logo_path)
    st.sidebar.image(logo, use_column_width=True)


# Function to set the background image
def set_background_image(image_path):
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-image: url("data:image/jpg;base64,{image_path}");
            background-size: cover;
            background-repeat: no-repeat;
            background-attachment: fixed;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


def set_dark_background():
    st.markdown(
        f"""
        <style>
        .stApp {{
            background-color: #222222;
        }}
        </style>
        """,
        unsafe_allow_html=True
    )


# Encode the image to base64 string
def get_image_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded = base64.b64encode(image_file.read()).decode()
    return encoded
