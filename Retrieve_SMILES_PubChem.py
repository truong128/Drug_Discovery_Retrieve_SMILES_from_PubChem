import streamlit as st
import requests
import csv
import chardet
import io
from time import sleep

# Configure page
st.set_page_config(
    page_title="TruongNguyen's Drug Information Retriever",
    page_icon="💊",
    layout="wide"
)

# Add custom CSS
st.markdown("""
    <style>
        .stProgress > div > div > div > div {
            background-color: #1c83e1;
        }
        .stDownloadButton {
            width: 100%;
        }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def get_drug_info(drug_name):
    """Fetches information about a drug from PubChem with caching."""
    url = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{drug_name}/JSON"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if 'PC_Compounds' in data and len(data['PC_Compounds']) > 0:
            compound_data = data['PC_Compounds'][0]
            
            smiles, iupac_name, cid = None, None, None
            
            for prop in compound_data['props']:
                if prop['urn']['label'] == 'SMILES':
                    smiles = prop['value'].get('sval', None)
                elif prop['urn']['label'] == 'IUPAC Name':
                    iupac_name = prop['value'].get('sval', None)

            if 'id' in compound_data and 'id' in compound_data['id']:
                cid = compound_data['id']['id'].get('cid')

            return cid, iupac_name, smiles
        return None, None, None

    except Exception as e:
        st.warning(f"Error retrieving data for {drug_name}: {str(e)}")
        return None, None, None

def read_drug_names_from_file(uploaded_file):
    """Reads drug names from a file-like object, one per line."""
    try:
        # Read the file content
        content = uploaded_file.read()
        
        # Detect encoding
        result = chardet.detect(content)
        encoding = result['encoding']
        
        # Decode content
        text = content.decode(encoding or 'utf-8')
        
        # Split into lines and clean
        drug_names = [line.strip() for line in text.splitlines() if line.strip()]
        return drug_names
        
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return []

def main():
    # Title and description
    st.title("💊 TruongNguyen's Drug Information Retriever")
    st.markdown("""
    Upload a text file containing drug names (one per line) to retrieve their:
    - Compound CID
    - IUPAC Name
    - SMILES Structure
    """)

    # File uploader
    uploaded_file = st.file_uploader(
        "Choose a text file containing drug names",
        type=["txt"],
        help="File should contain one drug name per line"
    )

    if uploaded_file is not None:
        # Read drug names
        with st.spinner("Reading file..."):
            drug_names = read_drug_names_from_file(uploaded_file)

        if drug_names:
            st.info(f"Found {len(drug_names)} drug names in the file")
            
            # Process button
            if st.button("Process Drugs"):
                drug_data = []
                progress_text = st.empty()
                progress_bar = st.progress(0)
                
                # Process each drug
                for i, drug in enumerate(drug_names):
                    progress_text.text(f"Processing {drug} ({i+1}/{len(drug_names)})")
                    
                    cid, iupac_name, smiles = get_drug_info(drug)
                    
                    if any([cid, iupac_name, smiles]):
                        drug_data.append([
                            drug, 
                            cid if cid else "Not found", 
                            iupac_name if iupac_name else "Not found", 
                            smiles if smiles else "Not found"
                        ])
                    
                    # Update progress
                    progress_bar.progress((i + 1) / len(drug_names))
                    # Small delay to prevent rate limiting
                    sleep(0.1)

                progress_text.empty()
                
                if drug_data:
                    # Create CSV in memory
                    output = io.StringIO()
                    writer = csv.writer(output)
                    writer.writerow(["Drug Name", "Compound CID", "IUPAC Name", "SMILES"])
                    writer.writerows(drug_data)
                    
                    # Convert to bytes for download
                    csv_bytes = output.getvalue().encode('utf-8')
                    
                    # Show success message and download button
                    st.success(f"Successfully processed {len(drug_data)} drugs!")
                    st.download_button(
                        label="📥 Download Results (CSV)",
                        data=csv_bytes,
                        file_name="Drug_Data_SMILES.csv",
                        mime="text/csv"
                    )
                else:
                    st.error("No data could be retrieved for any of the drugs.")
        else:
            st.error("No drug names found in the uploaded file.")

    # Add footer
    st.markdown("---")
    st.markdown("""
        <div style='text-align: center'>
            <p>Made with ❤️ by Truong Nguyen</p>
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
