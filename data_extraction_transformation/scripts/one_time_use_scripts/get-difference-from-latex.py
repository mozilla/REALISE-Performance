import pandas as pd
from io import StringIO

# Define the tables as multi-line strings
default_table = """
amoc & 0.057 & 0.586 & 0.030 & 0.065 & 1.000 & 0.035 & 0.647 & 0.035 & 0.068 & 1.000 & 0.036 \\
binseg & 0.105 & 0.422 & 0.061 & 0.164 & 1.000 & 0.895 & 0.170 & 0.171 & 0.208 & 1.000 & 0.921 \\
bocpd & 0.166 & 0.215 & 0.168 & 0.176 & 0.905 & 0.594 & 0.198 & 0.184 & 0.220 & 0.521 & 0.548 \\
cpnp & 0.181 & 0.222 & 0.165 & 0.188 & 0.229 & 0.984 & 0.228 & 0.171 & 0.204 & 0.244 & 0.987 \\
kcpa & 0.066 & 0.443 & 0.036 & 0.142 & 0.523 & 0.094 & 0.317 & 0.094 & 0.152 & 0.579 & 0.097 \\
mongodb & 0.158 & 0.330 & 0.111 & 0.166 & 0.338 & 0.121 & 0.295 & 0.121 & 0.176 & 0.366 & 0.125 \\
pelt & 0.127 & 0.247 & 0.095 & 0.159 & 0.306 & 1.000 & 0.155 & 0.177 & 0.203 & 0.346 & 1.000 \\
rfpop & 0.169 & 0.171 & 0.181 & 0.169 & 0.171 & 0.356 & 0.171 & 0.181 & 0.176 & 0.173 & 0.356 \\
segneigh & 0.078 & 0.350 & 0.045 & 0.156 & 1.000 & 0.891 & 0.227 & 0.145 & 0.201 & 1.000 & 0.931 \\
wbs & 0.149 & 0.141 & 0.170 & 0.167 & 0.238 & 0.999 & 0.229 & 0.141 & 0.194 & 0.285 & 0.999 \\
zero & 0.052 & 1.000 & 0.027 & 0.052 & 1.000 & 0.027 & 1.000 & 0.027 & 0.052 & 1.000 & 0.027 \\
"""

normalized_table = """
amoc & 0.148 & 0.638 & 0.085 & 0.161 & 1.000 & 0.093 & 0.612 & 0.093 & 0.174 & 1.000 & 0.097 \\
binseg & 0.235 & 0.480 & 0.168 & 0.284 & 1.000 & 1.000 & 0.309 & 0.308 & 0.373 & 1.000 & 1.000 \\
bocpd & 0.284 & 0.238 & 0.461 & 0.307 & 0.900 & 0.858 & 0.268 & 0.433 & 0.382 & 0.528 & 0.842 \\
cpnp & 0.320 & 0.247 & 0.483 & 0.328 & 0.254 & 0.993 & 0.254 & 0.488 & 0.345 & 0.266 & 0.996 \\
kcpa & 0.179 & 0.471 & 0.112 & 0.315 & 0.529 & 0.293 & 0.350 & 0.293 & 0.352 & 0.571 & 0.305 \\
mongodb & 0.327 & 0.367 & 0.342 & 0.328 & 0.376 & 0.366 & 0.334 & 0.361 & 0.363 & 0.427 & 0.378 \\
pelt & 0.241 & 0.260 & 0.269 & 0.269 & 0.315 & 1.000 & 0.242 & 0.398 & 0.344 & 0.349 & 1.000 \\
rfpop & 0.296 & 0.210 & 0.535 & 0.296 & 0.210 & 0.697 & 0.210 & 0.535 & 0.297 & 0.211 & 0.701 \\
segneigh & 0.196 & 0.364 & 0.138 & 0.269 & 1.000 & 1.000 & 0.242 & 0.398 & 0.354 & 1.000 & 1.000 \\
wbs & 0.223 & 0.146 & 0.494 & 0.306 & 0.248 & 0.999 & 0.248 & 0.421 & 0.340 & 0.282 & 0.999 \\
zero & 0.142 & 1.000 & 0.077 & 0.142 & 1.000 & 0.077 & 1.000 & 0.077 & 0.142 & 1.000 & 0.077 \\
"""

# Convert the multi-line string into a format pandas can read
def parse_table(table_str):
    # Replace & with spaces to use as separator
    table_str = table_str.replace("&", " ")
    # Use StringIO to treat string as file for pandas
    data = pd.read_csv(StringIO(table_str), delim_whitespace=True, header=None)
    return data

# Parse tables
default_df = parse_table(default_table)
normalized_df = parse_table(normalized_table)

# Set the first column as the index (method names)
default_df.set_index(0, inplace=True)
normalized_df.set_index(0, inplace=True)

# Display the data
print("Default Table:")
print(default_df)
print("\nNormalized Table:")
print(normalized_df)
