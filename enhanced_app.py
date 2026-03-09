import easyocr
import numpy as np
import PIL
from PIL import Image, ImageDraw
import cv2
import os
import re
import pandas as pd
from nlp_module import extract_entities
import openpyxl
from datetime import datetime
import streamlit as st

st.set_page_config(layout='wide')

st.title(':blue[Business Card Data Extraction]')

tab1, tab2 = st.tabs(["Data Extraction zone", "Data modification zone"])

with tab1:
    st.subheader(':red[Data Extraction]')

    import_image = st.file_uploader('**Select a business card (Image file)**', type=['png','jpg',"jpeg"], accept_multiple_files=False)

    st.markdown('''File extension support: **PNG, JPG, TIFF**, File size limit: **2 Mb**, Image dimension limit: **1500 pixel**, Language : **English**.''')

    if import_image is not None:
        try:
            reader = easyocr.Reader(['en'], gpu=False)
        except:
            st.info("Error: easyocr module is not installed. Please install it.")

        try:
            if isinstance(import_image, str):
                image = Image.open(import_image)
            elif isinstance(import_image, Image.Image):
                image = import_image
            else:
                image = Image.open(import_image)

            image_array = np.array(image)
            text_read = reader.readtext(image_array)

            result = []
            for text in text_read:
                result.append(text[1])

        except:
            st.info("Error: Failed to process the image. Please try again with a different image.")

        col1, col2 = st.columns(2)

        with col1:
            def draw_boxes(image, text_read, color='yellow', width=2):
                image_with_boxes = image.copy()
                draw = ImageDraw.Draw(image_with_boxes)
                for bound in text_read:
                    p0, p1, p2, p3 = bound[0]
                    draw.line([*p0, *p1, *p2, *p3, *p0], fill=color, width=width)
                return image_with_boxes

            result_image = draw_boxes(image, text_read)

            st.image(result_image, caption='Captured text')

        with col2:
            def get_data_enhanced(ocr_result):
                text = '\n'.join(ocr_result)
                extracted_data = extract_entities(text)
                return {
                    "Company_name": [extracted_data["Company Name"]],
                    "Card_holder": [extracted_data["Card Holder"]],
                    "Designation": [extracted_data["Designation"]],
                    "Mobile_number": [extracted_data["Mobile Number"]],
                    "Email": [extracted_data["Email"]],
                    "Website": [extracted_data["Website"]],
                    "Area": [extracted_data["Area"]],
                    "City": [extracted_data["City"]],
                    "State": [extracted_data["State"]],
                    "Pin_code": [extracted_data["Pincode"]]
                }

            data = get_data_enhanced(result)

            data_df = pd.DataFrame(data)

            st.session_state["last_extracted_row"] = data_df.iloc[0].to_dict()

            st.dataframe(data_df.T)

        class SessionState:
            def __init__(self, **kwargs):
                self.__dict__.update(kwargs)

        session_state = SessionState(data_uploaded=False)

        st.write('Click :red[**Upload to Excel**] button to upload data')
        Upload = st.button('**Upload to Excel**', key='upload_button')

        if Upload:
            session_state.data_uploaded = True

        if session_state.data_uploaded:
            excel_file = "business_card_database.xlsx"

            try:
                if os.path.exists(excel_file):
                    existing_df = pd.read_excel(excel_file)
                    updated_df = pd.concat([existing_df, data_df], ignore_index=True)
                else:
                    updated_df = data_df

                updated_df["Date_Added"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                updated_df["Status"] = "Active"

                updated_df.to_excel(excel_file, index=False)

                st.success('✅ Data Successfully Uploaded to Excel!')
                st.info(f'📁 Saved to: {excel_file}')

            except Exception as e:
                st.error(f'❌ Error saving to Excel: {str(e)}')

            session_state.data_uploaded = False

    else:
        st.info('Click Browse file button and upload an image')

with tab2:

    col1, col2 = st.columns(2)

    with col1:
        st.subheader(':red[Edit option]')

        excel_file = "business_card_database.xlsx"

        st.subheader(':red[Current scanned card]')
        last = st.session_state.get("last_extracted_row")
        if last:
            with st.form(key="current_scan_form"):
                cur_Company_name = st.text_input("Company name", str(last.get("Company_name", "")))
                cur_Card_holder = st.text_input("Cardholder", str(last.get("Card_holder", "")))
                cur_Designation = st.text_input("Designation", str(last.get("Designation", "")))
                cur_Mobile_number = st.text_input("Mobile number", str(last.get("Mobile_number", "")))
                cur_Email = st.text_input("Email", str(last.get("Email", "")))
                cur_Website = st.text_input("Website", str(last.get("Website", "")))
                cur_Area = st.text_input("Area", str(last.get("Area", "")))
                cur_City = st.text_input("City", str(last.get("City", "")))
                cur_State = st.text_input("State", str(last.get("State", "")))
                cur_Pin_code = st.text_input("Pincode", str(last.get("Pin_code", "")))
                cur_check = st.form_submit_button("Check / Preview Current")

            if cur_check:
                pending = {
                    "Company_name": cur_Company_name,
                    "Card_holder": cur_Card_holder,
                    "Designation": cur_Designation,
                    "Mobile_number": cur_Mobile_number,
                    "Email": cur_Email,
                    "Website": cur_Website,
                    "Area": cur_Area,
                    "City": cur_City,
                    "State": cur_State,
                    "Pin_code": cur_Pin_code,
                }

                errors = []
                if pending["Email"].strip() and not re.search(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", pending["Email"], re.IGNORECASE):
                    errors.append("Invalid Email format")
                if pending["Website"].strip() and not (re.search(r"(?i)\bhttps?://", pending["Website"]) or re.search(r"(?i)\bwww\.", pending["Website"]) or re.search(r"(?i)\b[a-z0-9][a-z0-9.-]+\.[a-z]{2,}\b", pending["Website"])):
                    errors.append("Invalid Website format")
                if pending["Mobile_number"].strip():
                    digits = re.sub(r"\D", "", pending["Mobile_number"])
                    if len(digits) < 10:
                        errors.append("Mobile number looks too short")
                if pending["Pin_code"].strip() and not re.fullmatch(r"\d{6}", pending["Pin_code"].strip()):
                    errors.append("Pincode must be 6 digits")

                st.session_state["pending_current"] = pending
                st.session_state["pending_current_errors"] = errors

            pending = st.session_state.get("pending_current")
            if pending:
                st.subheader(":red[Preview current scan]")
                preview_df = pd.DataFrame([{"Field": k, "New": str(v)} for k, v in pending.items()])
                st.dataframe(preview_df)

                errors = st.session_state.get("pending_current_errors", [])
                if errors:
                    st.error("❌ Fix these before saving: " + ", ".join(errors))
                else:
                    save_current = st.button("Save Current to Excel", key="save_current")
                    if save_current:
                        new_df = pd.DataFrame([pending])
                        if os.path.exists(excel_file):
                            existing_df = pd.read_excel(excel_file)
                            updated_df = pd.concat([existing_df, new_df], ignore_index=True)
                        else:
                            updated_df = new_df
                        updated_df["Date_Added"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        updated_df["Status"] = "Active"
                        updated_df.to_excel(excel_file, index=False)
                        st.success("✅ Current scanned card saved to Excel.")
                        st.session_state.pop("pending_current", None)
                        st.session_state.pop("pending_current_errors", None)
        else:
            st.info("Scan a card in 'Data Extraction zone' first. Then you can edit & save it here.")

    with col2:
        st.subheader(':red[Delete option]')

        try:
            if os.path.exists(excel_file):
                df = pd.read_excel(excel_file)

                names = df["Card_holder"].dropna().unique().tolist()

                if names:
                    delete_name = st.selectbox("**Select a Cardholder name to Delete details**", names, key='delete_name')

                    session_state = SessionState(data_delet=False)

                    st.write('Click :red[**Delete**] button to Delete selected Cardholder details')
                    delet = st.button('**Delete**', key='delet')

                    if delet:
                        session_state.data_delet = True

                    if session_state.data_delet:
                        df = df[df["Card_holder"] != delete_name]

                        df.to_excel(excel_file, index=False)

                        st.success("✅ Successfully deleted from Excel.")
                        session_state.data_delet = False
                else:
                    st.info('No data available to delete')

        except Exception as e:
            st.info(f'No data stored in Excel file: {str(e)}')