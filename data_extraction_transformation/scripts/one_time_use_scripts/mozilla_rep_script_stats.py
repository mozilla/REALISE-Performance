import json
import argparse
import csv

def load_json(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

def compare_predictions(baseline, predicted, margin):
    results = []
    
    all_keys = set(baseline.keys()).union(predicted.keys())
    
    for signature_id in all_keys:
        baseline_values = baseline.get(signature_id, {}).get("1", [])
        predicted_values = predicted.get(signature_id, {}).get("1", [])
        
        baseline_set = set(baseline_values)
        predicted_set = set(predicted_values)
        
        correct_predictions = len(baseline_set & predicted_set)
        
        nearly_captured = sum(
            any(abs(pred - base) <= margin for base in baseline_values)
            for pred in predicted_values if pred not in baseline_set
        )
        
        false_positives = len(predicted_set - baseline_set)
        false_negatives = len(baseline_set - predicted_set)
        
        results.append([signature_id, correct_predictions, nearly_captured, false_positives, false_negatives])
    
    return results

def save_to_csv(results, output_path):
    headers = ["signature_id", "correct", "nearly_captured", "false_positives", "false_negatives"]
    
    with open(output_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(results)

def main():
    parser = argparse.ArgumentParser(description="Compare JSON prediction results and baseline.")
    parser.add_argument("-b", "--baseline", required=True, help="Path to the baseline JSON file")
    parser.add_argument("-p", "--predicted", required=True, help="Path to the predicted JSON file")
    parser.add_argument("-o", "--output", required=True, help="Path to save the comparison CSV")
    parser.add_argument("-m", "--margin", type=int, default=0, help="Margin for nearly captured predictions")
    
    args = parser.parse_args()
    
    baseline_data = load_json(args.baseline)
    predicted_data = load_json(args.predicted)
    results = compare_predictions(baseline_data, predicted_data, args.margin)
    save_to_csv(results, args.output)
    
if __name__ == "__main__":
    main()
