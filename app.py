"""
Main page for the OpenMS Template App.

This module sets up and displays the Streamlit app for the OpenMS Template App.
It includes:
- Setting the app title.
- Displaying a description.
- Providing a download button for the Windows version of the app.

Usage:
Run this script to launch the OpenMS Template App.

Note:
- If run in local mode, the CAPTCHA control is not applied.
- If not in local mode, CAPTCHA control is applied to verify the user.

Returns:
    None
"""

import sys

import streamlit as st

from src.captcha_ import captcha_control
from src.common import page_setup, save_params

from st_pages import Page, show_pages

params = page_setup(page="main")



def flashdeconvPages():
    show_pages([
        Page("app.py", "FLASHViewer", "🏠"),
        Page("pages/FLASHDeconvWorkflow.py", "Workflow", "⚙️"),
        Page("pages/FLASHDeconvDownload.py", "Download", "⬇️"),
        #Page("pages/FileUpload.py", "File Upload", "📁"),
        #Page("pages/SequenceInput.py", "Sequence Input", "🧵"),
        #Page("pages/LayoutManager.py", "Layout Manager", "⚙️"),
        #Page("pages/FLASHDeconvViewer.py", "Viewer", "👀"),
    ])

def flashtagPages():
    show_pages([
        Page("app.py", "FLASHViewer", "🏠"),
        Page("pages/FLASHTaggerWorkflow.py", "Workflow", "⚙️"),
        Page("pages/FLASHTaggerViewer.py", "Viewer", "👀"),
    ])

def flashquantPages():
    show_pages([
        Page("pages/FLASHViewer.py", "FLASHViewer", "🏠"),
        Page("pages/FileUpload_FLASHQuant.py", "File Upload", "📁"),
        Page("pages/FLASHQuantViewer.py", "Viewer", "👀"),
    ])


page_names_to_funcs = {
    "FLASHTagger": flashtagPages,
    "FLASHDeconv": flashdeconvPages,
    "FLASHQuant": flashquantPages,
}


def onToolChange():
    if 'changed_tool_name' in st.session_state:
        st.session_state['tool_index'] = 0 if st.session_state.changed_tool_name == 'FLASHDeconv' else 1



def main():
    """
    Display main page content.
    """

    # sidebar to toggle between tools
    if 'tool_index' not in st.session_state:
        page_names_to_funcs['FLASHDeconv']()
        st.session_state['tool_index'] = 0

    # main content
    st.markdown('#### FLASHViewer visualizes outputs from FLASH\* tools.')

    st.info("""
        **💡 How to run FLASHViewer**
        1. Go to the **⚙️ Workflow** page through the sidebar and run your analysis.
        2. Click the **👀 Viewer** page on the sidebar to view the results in detail.
            
            **\***For FLASHDeconv only download of results is supported.
        """)

    # when entered into other page, key is resetting (emptied) - thus set the value with index
    # st.selectbox("Choose a tool", ['FLASHTagViewer', 'FLASHDeconv', 'FLASHQuant'], index=st.session_state.tool_index,
    st.selectbox("Choose a tool", ['FLASHDeconv', 'FLASHTagger'], index=st.session_state.tool_index,
                 on_change=onToolChange(), key='changed_tool_name')
    page_names_to_funcs[st.session_state.changed_tool_name]()
    
    save_params(params)

# Check if the script is run in local mode (e.g., "streamlit run app.py local")
if "local" in sys.argv:
    # In local mode, run the main function without applying captcha
    main()

# If not in local mode, assume it's hosted/online mode
else:

    show_pages([
        Page("app.py", "FLASHViewer", "🏠"),
    ])

    # WORK LIKE MULTIPAGE APP
    if "controllo" not in st.session_state or st.session_state["controllo"] is False:
        # Apply captcha control to verify the user
        captcha_control()

    else:
        # Run the main function
        main()