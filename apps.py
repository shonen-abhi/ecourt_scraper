import streamlit as st
from datetime import date
from scraper import get_court_complexes, get_judges_for_complex, open_and_fill_then_download

st.set_page_config(page_title="Delhi Courts Cause List", layout="centered")
st.title("Delhi Courts Cause List Downloader")

st.markdown("""
**Flow**
1. Choose Court Complex → then choose Judge (populated from the site).
2. Select Date.
3. Click **Open & Fill**. A Chrome window will open and the form will be auto-filled.
4. Solve the CAPTCHA in the Chrome window and click **Search**.
5. The script will automatically save the results as a PDF in the `downloads/` folder.
""")

with st.spinner("Fetching Court Complex list from site..."):
    try:
        complexes = get_court_complexes()
    except Exception as e:
        st.error("Failed to fetch complex list: " + str(e))
        complexes = []

if not complexes:
    st.warning("Could not fetch court complex list. Try again or use the site directly.")
    st.stop()

complex_map = {name: val for (name, val) in complexes}
complex_names = list(complex_map.keys())

selected_complex = st.selectbox("Court Complex", complex_names)

if st.button("Load Judges for selected complex"):
    with st.spinner("Fetching judges..."):
        try:
            judges = get_judges_for_complex(complex_map[selected_complex])
            if not judges:
                st.warning("No judges found for this complex.")
            else:
                st.session_state['judges'] = judges
        except Exception as e:
            st.error("Failed to fetch judges: " + str(e))

judges = st.session_state.get('judges', None)
if judges:
    judge_display = [t[0] for t in judges]
    judge_map = {t[0]: t[1] for t in judges}
    selected_judge = st.selectbox("Select Judge / Court", judge_display)
else:
    st.info("Click 'Load Judges for selected complex' to populate judges.")
    selected_judge = None
    judge_map = {}

selected_date = st.date_input("Select date", value=date.today())

if st.button("Open site & auto-fill (then solve CAPTCHA)"):
    if not selected_judge:
        st.warning("Please load and select a judge first.")
    else:
        date_str = selected_date.strftime("%m/%d/%Y")
        st.info("Opening browser and auto-filling the form. Solve CAPTCHA and click Search in Chrome.")
        open_and_fill_then_download(date_str, complex_map[selected_complex], judge_map[selected_judge], download_dir="downloads")
        st.success("PDF should now be saved in `downloads/` folder.")
