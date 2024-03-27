from src.common import *
from pathlib import Path
import os, shutil
import numpy as np
from src.masstable import parseFLASHDeconvOutput


def initializeWorkspace(input_types, parsed_df_types):
    for dirname in input_types:
        dirpath = Path(st.session_state["workspace"], dirname)
        if not os.path.isdir(dirpath):
            os.mkdir(dirpath)

        if dirname not in st.session_state:
            st.session_state[dirname] = []

    # sync session state and default-workspace
    for input_type in input_types:
        st.session_state[input_type] = os.listdir(Path(st.session_state["workspace"], input_type))

    # initializing session state for storing data
    for df_type in parsed_df_types:
        if df_type not in st.session_state:
            st.session_state[df_type] = {}

#@st.cache_data
def getUploadedFileDF(deconv_files, anno_files, tag_files, db_files):
    # leave only names
    deconv_files = [Path(f).name for f in deconv_files]
    anno_files = [Path(f).name for f in anno_files]
    tag_files = [Path(f).name for f in tag_files]
    db_files = [Path(f).name for f in db_files]

    # getting experiment name from annotated file (tsv files can be multiple per experiment)
    experiment_names = [f[0: f.rfind('_')] for f in anno_files]

    df = pd.DataFrame({'Experiment Name': experiment_names,
                       'Deconvolved Files': deconv_files,
                       'Annotated Files': anno_files,
                       'Tag Files' : tag_files,
                       'DB Files' : db_files})
    return df

def showUploadedFilesTable():
    deconv_files = sorted(st.session_state["deconv_dfs"].keys())
    anno_files = sorted(st.session_state["anno_dfs"].keys())
    tag_files = sorted(st.session_state["tag_dfs"].keys())
    db_files = sorted(st.session_state["protein_dfs"].keys())

    # error message if files not exist
    if len(deconv_files) == 0 and len(anno_files) == 0:
        #st.info('No mzML added yet!', icon="ℹ️")
        return
    elif len(deconv_files) == 0:
        st.error("FLASHDeconv deconvolved mzML file is not added yet!")
    elif len(anno_files) == 0:
        st.error("FLASHDeconv annotated mzML file is not added yet!")
    elif len(tag_files) == 0:
        st.error("FLASHDeconv annotated tag file is not added yet!")
    elif len(db_files) == 0:
        st.error("Protein database file is not added yet!")
    elif np.any(np.array([len(deconv_files), len(anno_files)]) != len(tag_files)) :
        st.error("The same number of deconvolved and annotated files should be uploaded!")
    else:
        st.session_state["experiment-df"] = getUploadedFileDF(deconv_files, anno_files, tag_files, db_files)
        #st.markdown('**Uploaded experiments**')
        #st.dataframe(st.session_state["experiment-df"])

def handleInputFiles(uploaded_files):
    for file in uploaded_files:
        file = Path(file)
        if not (file.name.endswith("mzML") or file.name.endswith("tsv") or file.name.endswith("fasta")):
            continue

        session_name = ''
        if file.name.endswith('_deconv.mzML'):
            session_name = 'deconv-mzMLs'
        elif file.name.endswith('_annotated.mzML'):
            session_name = 'anno-mzMLs'
        elif file.name.endswith('_tagged.tsv'):
            session_name = 'tags-tsv'
        elif file.name.endswith('_db.fasta'):
            session_name = 'db-fasta'
        elif file.name.endswith('_protein.tsv'):
            session_name = 'proteins-tsv'

        if file.name not in st.session_state[session_name]:
            with open(
                    Path(st.session_state["workspace"], session_name, file.name), "wb"
            ) as f:
                f.write(file.getbuffer())
            st.session_state[session_name].append(file.name)

def parseUploadedFiles(reparse=False):
    # get newly uploaded files
    deconv_files = st.session_state['deconv-mzMLs']
    anno_files = st.session_state['anno-mzMLs']
    tag_files = st.session_state['tags-tsv']
    # db_files = st.session_state['db-fasta']
    protein_files = st.session_state['proteins-tsv']
    # anno_files = Path(st.session_state['anno-mzMLs']).iterdir()
    new_deconv_files = [f for f in deconv_files if f not in st.session_state['deconv_dfs'] or reparse]
    new_anno_files = [f for f in anno_files if f not in st.session_state['anno_dfs'] or reparse]
    new_tag_files = [f for f in tag_files if f not in st.session_state['tag_dfs'] or reparse]
    new_protein_files = [f for f in protein_files if f not in st.session_state['protein_dfs'] or reparse]
    # new_db_files = [f for f in db_files if f not in st.session_state['protein_db']]

    # if newly uploaded files are not as needed
    if len(new_deconv_files)==0 and len(new_anno_files)==0 and len(new_tag_files)==0 and len(new_protein_files)==0: # if no newly uploaded files, move on
        return
    elif np.any(np.array([len(new_deconv_files), len(new_anno_files), len(new_protein_files)]) != len(new_tag_files)): # if newly uploaded files doesn't match, write message
        st.error('Added files are not in pair, so not parsed. \n Here are added ones, but not parsed ones:')
        # not_parsed = [f.name for f in new_deconv_files] + [f.name for f in new_anno_files]
        not_parsed = new_deconv_files + new_anno_files + new_tag_files + new_protein_files
        for i in not_parsed:
            st.markdown("- " + i)
        return

    # parse newly uploaded files
    new_deconv_files = sorted(new_deconv_files)
    new_anno_files = sorted(new_anno_files)
    new_tag_files = sorted(new_tag_files)
    # new_db_files = sorted(new_db_files)
    new_protein_files = sorted(new_protein_files)
    parsingWithProgressBar(new_deconv_files, new_anno_files, new_tag_files, new_protein_files)

def parsingWithProgressBar(infiles_deconv, infiles_anno, infiles_tag, infiles_protein):
    successes = []
    with st.session_state['progress_bar_space']:
        for anno_f, deconv_f, tag_f, protein_f in zip(infiles_anno, infiles_deconv, infiles_tag, infiles_protein):
            if not anno_f.endswith('.mzML'):
                continue
            exp_name = anno_f[0: anno_f.rfind('_')]

            with st.spinner('Parsing the experiment %s...'%exp_name):
                spec_df, anno_df, tolerance, massoffset, chargemass, tag_df, protein_df = parseFLASHDeconvOutput(
                    Path(st.session_state["workspace"], "anno-mzMLs", anno_f),
                    Path(st.session_state["workspace"], "deconv-mzMLs", deconv_f),
                    Path(st.session_state["workspace"], "tags-tsv", tag_f),
                    Path(st.session_state["workspace"], "proteins-tsv", protein_f)
                    # Path(st.session_state["workspace"], "db-fasta", db_f)
                )
                st.session_state['anno_dfs'][anno_f] = anno_df
                st.session_state['deconv_dfs'][deconv_f] = spec_df
                st.session_state['tag_dfs'][tag_f] = tag_df
                # st.session_state['protein_db'][db_f] = db
                st.session_state['protein_dfs'][protein_f] = protein_df
            successes.append(st.success('Done parsing the experiment %s!'%exp_name))
        for success in successes:
            success.empty()

def content():
    page_setup()

    # make directory to store deconv and anno mzML files & initialize data storage
    input_types = ["deconv-mzMLs", "anno-mzMLs", "tags-tsv", "proteins-tsv"]
    parsed_df_types = ["deconv_dfs", "anno_dfs", "tag_dfs", "protein_dfs"]
    initializeWorkspace(input_types, parsed_df_types)

    c1, c2, c3 = st.columns([0.6, 0.2, 0.2])
    # c1, c2, c3 = st.columns(3)
    c1.title("File Upload")

    # Load Example Data
    v_space(1, c2)
    if c2.button("Load Example Data"):
        # loading and copying example files into default workspace
        for filetype, session_name in zip(['*annotated.mzML', '*deconv.mzML', '*tagged.tsv', '*protein.tsv'],
                                          ['anno-mzMLs', 'deconv-mzMLs', 'tags-tsv', 'proteins-tsv']):
            for file in Path("example-data").glob(filetype):
                if file.name not in st.session_state[session_name]:
                    shutil.copy(file, Path(st.session_state["workspace"], session_name, file.name))
                    st.session_state[session_name].append(file.name)
        # parsing the example files is done in parseUploadedFiles later

    # Delete all uploaded files
    v_space(1, c3)
    if c3.button("Delete uploaded Data"):
        for file_option, df_option in zip(input_types, parsed_df_types):
            if file_option in st.session_state:
                reset_directory(Path(st.session_state["workspace"], file_option))
                st.session_state[file_option] = []
            if  df_option in st.session_state:
                st.session_state[df_option] = {}


    # Display info how to upload files
    st.info(
        """
    **💡 How to upload files**

    1. Browse files on your computer or drag and drops files
    2. Click the **Add the uploaded mzML files** button to use them in the workflows

    Select data for analysis from the uploaded files shown below.
    
    **💡 Make sure that the same number of deconvolved and annotated mzML files are uploaded!**
    """
    )

    # Online accept only one file per upload, local is unrestricted
    accept_multiple = True
    if st.session_state.location == "online":
        accept_multiple = False

    # Upload files via upload widget
    st.subheader("**Upload FLASHDeconv output files (\*_annotated.mzML & \*_deconv.mzML)**")

    with st.form('input_mzml', clear_on_submit=True):
        uploaded_file = st.file_uploader(
            "FLASHDeconv output mzML files", accept_multiple_files=accept_multiple
        )
        _, c2, _ = st.columns(3)
        # User needs to click button to upload selected files
        submitted = c2.form_submit_button("Add the uploaded mzML files")
        if submitted:
            # Need to have a list of uploaded files to copy to the mzML dir,
            # in case of online only a single item is return, so we put it in the list
            if st.session_state.location == "online":
                uploaded_file = [uploaded_file]
            # Copy uploaded mzML files to deconv-mzML-files directory
            if uploaded_file:
                # opening file dialog and closing without choosing a file results in None upload
                handleInputFiles(uploaded_file)
                st.success("Successfully added uploaded files!")
            else:
                st.warning("Upload some files before adding them.")

    st.session_state['progress_bar_space'] = st.container()

    # parse files if newly uploaded
    parseUploadedFiles()

    # for error message or list of uploaded files
    showUploadedFilesTable()

    # TODO: figure out what to do with here
    # # Local file upload option: via directory path
    # if st.session_state.location == "local":
    #     st.markdown("**OR specify the path to a folder containing your mzML files**")
    #     c1, c2 = st.columns([0.8, 0.2])
    #     upload_dir = c1.text_input("path to folder with mzML files")
    #     upload_dir = r"{}".format(upload_dir)
    #     c2.markdown("##")
    #     if c2.button("Upload"):
    #         uploaded_mzML = Path("example-data", "mzML").glob("*.mzML")
    #         with st.spinner("Uploading files..."):
    #             for file in Path(upload_dir).glob("*.mzML"):
    #                 if file.name not in st.session_state["mzML-files"].iterdir():
    #                     shutil.copy(file, st.session_state["mzML-files"])
    #             st.success("Successfully added uploaded files!")


if __name__ == "__main__":
    # try:
    content()
# except:
#     st.error(ERRORS["general"])
