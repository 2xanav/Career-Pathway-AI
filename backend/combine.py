import json
import os

def combine_json_files():
    # Automatically find the exact folder where this script is saved
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    finance_path = os.path.join(script_dir, 'curriculum_data.json')
    cse_path = os.path.join(script_dir, 'cse_curriculum_data.json')
    
    # Read the Finance data
    with open(finance_path, 'r', encoding='utf-8') as f:
        finance_data = json.load(f)
        
    # Read the CSE data
    with open(cse_path, 'r', encoding='utf-8') as f:
        cse_data = json.load(f)
        
    # Combine them into one master dictionary, keeping majors separate
    combined_data = {
        "majors": {
            "Finance": finance_data,
            "CSE": cse_data
        }
    }
    
    # Save the combined data to a new file
    output_path = os.path.join(script_dir, 'combined_curriculum.json')
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(combined_data, f, indent=4)
        
    print(f"🎉 Successfully combined both majors into: {output_path}")

if __name__ == "__main__":
    combine_json_files()