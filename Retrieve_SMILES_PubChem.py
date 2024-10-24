import requests
import csv
import streamlit as st

def read_drug_names_from_file(uploaded_file):
    """Reads drug names from a file-like object, one per line."""
    return [line.decode('utf-8').strip() for line in uploaded_file.readlines() if line.strip()]

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
            print(f"No data found for {drug_name}.")
            return None, None, None

    except requests.HTTPError as http_err:
        print(f"Error retrieving data for {drug_name}: {http_err}")
        return None, None, None
    except Exception as e:
        print(f"Unexpected error for {drug_name}: {e}")
        return None, None, None

def main():
    st.title("Upload file txt chứa tên Drug của bạn lên đây nhé!!!")

    
    uploaded_file = st.file_uploader("Upload a text file with drug names", type=["txt"])

    if uploaded_file is not None:
        
        drug_names = read_drug_names_from_file(uploaded_file)

        
        drug_data = []

        
        for drug in drug_names:
            cid, iupac_name, smiles = get_drug_info(drug)
            
            
            if cid or iupac_name or smiles:
                drug_data.append([
                    drug, 
                    cid if cid else "CID not found", 
                    iupac_name if iupac_name else "IUPAC not found", 
                    smiles if smiles else "SMILES not found"
                ])

        
        output_file = "Drug_Data_SMILES.csv"
        with open(output_file, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file)
            
            writer.writerow(["Drug Name", "Compound CID", "IUPAC Name", "SMILES"])
            
            writer.writerows(drug_data)

        
        with open(output_file, "rb") as f:
            st.download_button("Download Drug Data_SMILES", f, file_name=output_file)

if __name__ == "__main__":
    main()
