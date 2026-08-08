import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
import streamlit as st
from utils.ui import inject_css
from utils.analysis import PREMIUM
from utils.stock_page import render_stock_page

st.set_page_config(page_title="Saham Premium", page_icon="📈", layout="wide")
inject_css()
render_stock_page(PREMIUM, "Saham Premium", "📈")
