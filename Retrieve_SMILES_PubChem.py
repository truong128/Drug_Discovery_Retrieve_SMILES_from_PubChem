import requests
import csv
import streamlit as st
import io

def read_drug_names_from_file(uploaded_file):
    """Reads drug names from a file-like object, one per line."""
    try:
        # Reset file pointer to beginning
        uploaded_file.seek(0)
        
        # Try different encodings
        encodings = ['utf-8', 'latin-1', 'iso-8859-1']
        
        for encoding in encodings:
            try:
                content = uploaded_file.read().decode(encoding)
                # Split content into lines and filter empty lines
                drug_names = [line.strip() for line in content.splitlines() if line.strip()]
                return drug_names
            except UnicodeDecodeError:
                # Reset file pointer for next attempt
                uploaded_file.seek(0)
                continue
            
        # If no encoding worked, raise an error
        raise ValueError("Could not decode file with any supported encoding")
        
    except Exception as e:
        st.error(f"Error reading file: {str(e)}")
        return []

def get_drug_info(drug_name):
    """Fetches information about a drug from PubChem."""
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
        else:
            st.warning(f"No data found for {drug_name}.")
            return None, None, None

    except requests.HTTPError as http_err:
        st.warning(f"Error retrieving data for {drug_name}: {http_err}")
        return None, None, None
    except Exception as e:
        st.warning(f"Unexpected error for {drug_name}: {e}")
        return None, None, None

def main():
    st.title("Upload TXT file of Drug ở đây")

    uploaded_file = st.file_uploader("Upload a text file with drug names", type=["txt"])

    if uploaded_file is not None:
        drug_names = read_drug_names_from_file(uploaded_file)

        if drug_names:
            drug_data = []
            progress_bar = st.progress(0)
            
            for i, drug in enumerate(drug_names):
                cid, iupac_name, smiles = get_drug_info(drug)
                
                if cid or iupac_name or smiles:
                    drug_data.append([
                        drug, 
                        cid if cid else "CID not found", 
                        iupac_name if iupac_name else "IUPAC not found", 
                        smiles if smiles else "SMILES not found"
                    ])
                
                # Update progress bar
                progress_bar.progress((i + 1) / len(drug_names))

            if drug_data:
                # Create CSV in memory
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(["Drug Name", "Compound CID", "IUPAC Name", "SMILES"])
                writer.writerows(drug_data)
                
                # Convert to bytes for download
                csv_bytes = output.getvalue().encode('utf-8')
                
                st.download_button(
                    label="Download Drug Data_SMILES",
                    data=csv_bytes,
                    file_name="Drug_Data_SMILES.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No data was retrieved for any of the drugs.")

if __name__ == "__main__":
    main()
