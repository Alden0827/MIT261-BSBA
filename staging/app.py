import streamlit as st

from streamlit_gallery import apps, components
from streamlit_gallery.utils.page import page_group

def main():
    page = page_group("p")   # Creates a page group named "p"

    with st.sidebar:
        st.title("🔴 Okld's Gallery")   # Sidebar title

        # Section for APPS
        with st.expander("⚡️ APPS", True):
            page.item("Streamlit gallery", apps.gallery, default=True)

        # Section for COMPONENTS
        with st.expander("🌿 COMPONENTS", True):
            page.item("Ace editor", components.ace_editor)
            page.item("Disqus", components.disqus)
            page.item("Elements✨", components.elements)
            page.item("Pandas profiling", components.pandas_profiling)
            page.item("Quill editor", components.quill_editor)
            page.item("React player", components.react_player)

    page.show()  # Displays the selected page

if __name__ == "__main__":
    main()
