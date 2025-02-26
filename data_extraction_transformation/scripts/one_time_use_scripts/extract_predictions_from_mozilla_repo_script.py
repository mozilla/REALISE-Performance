import json
import os
import argparse

def accumulate_cplocations(folder_path):
    # Initialize an empty dictionary to store the accumulated data
    accumulated_data = {}

    # Loop over all JSON files in the folder
    for filename in os.listdir(folder_path):
        if filename.endswith('.json'):
            # Construct the full path of the JSON file
            file_path = os.path.join(folder_path, filename)
            
            # Open and load the JSON data
            with open(file_path, 'r') as f:
                data = json.load(f)
                
                # Extract the dataset identifier
                dataset_id = data.get("dataset")
                
                # Ensure there's a valid 'dataset' and 'best_mozilla_rep' field in the file
                if dataset_id and 'results' in data and 'best_mozilla_rep' in data['results']:
                    # Initialize the dictionary entry if it doesn't exist
                    if dataset_id not in accumulated_data:
                        accumulated_data[dataset_id] = {}
                    
                    # Extract cplocations for the "best_mozilla_rep"
                    best_mozilla_rep = data['results']['best_mozilla_rep']
                    cplocations = []
                    
                    # Loop through the best_mozilla_rep items to collect cplocations
                    for rep in best_mozilla_rep:
                        cplocations.extend(rep.get("cplocations", []))
                    
                    # Store the cplocations in the accumulated_data dictionary under the appropriate dataset
                    # Assuming we want to store them under "1" (from your example)
                    accumulated_data[dataset_id]["1"] = cplocations
    
    # Return the accumulated data
    return accumulated_data

def save_to_json(data, output_path):
    with open(output_path, 'w') as f:
        json.dump(data, f, indent=4)

def main():
    # Set up argparse to handle command-line arguments
    parser = argparse.ArgumentParser(description="Accumulate cplocations from JSON files.")
    parser.add_argument('-f', '--folder_path', help="Path to the folder containing JSON files")
    parser.add_argument('-o' ,'--output_path', help="Path to the output JSON file")
    
    # Parse the arguments
    args = parser.parse_args()

    # Accumulate the cplocations data
    accumulated_data = accumulate_cplocations(args.folder_path)

    # Save the output to a JSON file
    save_to_json(accumulated_data, args.output_path)

    # Optionally, print the accumulated data
    print(f"Accumulated data saved to {args.output_path}")
    print(json.dumps(accumulated_data, indent=4))

if __name__ == "__main__":
    main()
