import streamlit as st
import google.generativeai as genai

# Titulli i faqes sate
st.title("Aplikacioni im me Gemini AI 🚀")

# Marrja e API Key në mënyrë të sigurt
api_key = st.sidebar.text_input("Vendos API Key këtu:", type="password")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-pro')

    user_input = st.text_input("Pyet diçka:")

    if user_input:
        response = model.generate_content(user_input)
        st.write("Përgjigja e AI:")
        st.info(response.text)
else:
    st.warning("Ju lutem vendosni API Key në anën e majtë për të filluar.")
