import argparse
import json
import time
import numpy as np
import socket
import hashlib
import ruptures as rpt
 
def kcpa(data, L, cost):
    algo = rpt.KernelCPD(kernel="linear", min_size=3, cost=cost).fit(data)
    breakpoints = algo.predict(n_bkps=L)
    
    return breakpoints


    algo = rpt.KernelCPD(kernel="linear").fit(data)
    return algo.predict(n_bkps=L)

# Function to handle e.divisive Change Point Analysis
def e_divisive(data, alpha, minsize, siglvl, runs):
    algo = rpt.Edivisive(alpha=alpha, min_size=minsize, significance_level=siglvl).fit(data)
    return algo.predict(n_bkps=runs)

# Function to load dataset from a JSON file
def load_dataset(filepath):
    with open(filepath, 'r') as f:
        return json.load(f)

# Function to get the MD5 hash of a file
def get_md5(filepath):
    with open(filepath, 'rb') as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()

# Argument parsing function
def parse_args():
    parser = argparse.ArgumentParser(description="Run KCPA or e.divisive algorithms on a time series dataset.")
    parser.add_argument('-i', '--input', required=True, help="Path to the input JSON dataset file.")
    parser.add_argument('-o', '--output', help="Path to the output JSON file.")
    parser.add_argument('-a', '--algorithm', choices=['e.divisive', 'kcpa'], required=True, help="Algorithm to run.")
    parser.add_argument('--alpha', type=float, help="Alpha parameter for e.divisive.", default=1.0)
    parser.add_argument('--minsize', type=int, help="Minimum segment size.", default=2)
    parser.add_argument('-R', '--runs', type=int, help="Number of runs for the algorithm.", default=20)
    parser.add_argument('--siglvl', type=float, help="Significance level for e.divisive.", default=0.05)
    parser.add_argument('-C', '--cost', type=float, help="Cost parameter for KCPA.", default=1.0)
    parser.add_argument('-L', '--maxcp', help="Maximum number of change points for KCPA (or set to 'max').", default='max')
    
    return parser.parse_args()

# Main function to execute the selected algorithm
def main():
    args = parse_args()
    
    # Load dataset
    data = load_dataset(args.input)
    time_series = np.array(data["series"][0]["raw"]).reshape(-1, 1)  # Convert to numpy array
    dataset_md5 = get_md5(args.input)
    
    # Set `maxcp` to a reasonable value if it's 'max'
    if args.maxcp == 'max':
        args.maxcp = min(len(time_series) // 2, 100)  # Limit L to at most 100 or half the length of the series
    
    start_time = time.time()
    try:
        # Run the appropriate algorithm
        if args.algorithm == 'e.divisive':
            result = e_divisive(time_series, alpha=args.alpha, runs=args.runs, minsize=args.minsize, siglvl=args.siglvl)
        elif args.algorithm == 'kcpa':
            result = kcpa(time_series, L=args.maxcp, cost=args.cost)
        
        runtime = time.time() - start_time
        
        # If result is None or empty, raise an error to handle it as a failure
        if not result:
            raise ValueError("No valid change points detected.")
        
        # Construct success output
        output_data = {
            "error": None,
            "command": f"python3.9 /TCPDBench/execs/python/kcpa_ecp.py -i {args.input} -a {args.algorithm} --alpha {args.alpha} --minsize {args.minsize} --runs {args.runs} --siglvl {args.siglvl}",
            "script": "/TCPDBench/execs/python/kcpa_ecp.py",
            "script_md5": get_md5('/TCPDBench/execs/python/kcpa_ecp.py'),
            "hostname": socket.gethostname(),
            "dataset": args.input.split('/')[-1].split('.')[0],
            "dataset_md5": dataset_md5,
            "status": "SUCCESS",
            "parameters": {
                "alpha": args.alpha,
                "minsize": args.minsize,
                "max_cp": args.maxcp,
                "method": args.algorithm,
                "runs": args.runs,
                "siglvl": args.siglvl
            },
            "arguments": vars(args),
            "result": {
                "cplocations": list(map(int, result)),
                "runtime": runtime
            }
        }

    except Exception as e:
        # Handle any errors and produce a failure output
        runtime = time.time() - start_time
        output_data = {
            "error": str(e),
            "command": f"python3.9 /TCPDBench/execs/python/kcpa_ecp.py -i {args.input} -a {args.algorithm} --alpha {args.alpha} --minsize {args.minsize} --runs {args.runs} --siglvl {args.siglvl}",
            "script": "/TCPDBench/execs/python/kcpa_ecp.py",
            "script_md5": get_md5('/TCPDBench/execs/python/kcpa_ecp.py'),
            "hostname": socket.gethostname(),
            "dataset": args.input.split('/')[-1].split('.')[0],
            "dataset_md5": dataset_md5,
            "status": "FAIL",
            "parameters": {
                "alpha": args.alpha,
                "minsize": args.minsize,
                "max_cp": args.maxcp,
                "method": args.algorithm,
                "runs": args.runs,
                "siglvl": args.siglvl
            },
            "arguments": vars(args),
            "result": {
                "cplocations": None,
                "runtime": None
            }
        }
    
    # Write output to file or print to console
    if args.output:
        with open(args.output, 'w') as outfile:
            json.dump(output_data, outfile, indent=4)
    else:
        print(json.dumps(output_data, indent=4))

if __name__ == "__main__":
    main()
