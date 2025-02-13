import numpy as np
import re

# Example usage
input_dict = {
    "Performance Metrics for Methods over 195 average-aggregated datasets": """
BinSeg & 0.524 & 0.481 & 0.693 & 0.653 & 1.000 & 1.000 & 0.961 & 0.562 & 0.764 & 1.000 & 1.000 \\
BOCPD & 0.256 & 0.177 & 0.791 & 0.591 & 0.621 & 0.918 & 0.592 & 0.681 & 0.710 & 0.789 & 0.946 \\
CPNP & 0.284 & 0.187 & 0.785 & 0.292 & 0.193 & 0.999 & 0.193 & 0.793 & 0.305 & 0.203 & 0.999 \\
KCPA & 0.516 & 0.497 & 0.676 & 0.516 & 0.497 & 0.795 & 0.497 & 0.676 & 0.557 & 0.516 & 0.801 \\
MongoDB & 0.428 & 0.339 & 0.746 & 0.432 & 0.343 & 0.769 & 0.343 & 0.744 & 0.464 & 0.374 & 0.773 \\
PELT & 0.451 & 0.382 & 0.722 & 0.451 & 0.382 & 1.000 & 0.382 & 0.722 & 0.525 & 0.458 & 1.000 \\
RFPOP & 0.248 & 0.158 & 0.817 & 0.248 & 0.158 & 0.866 & 0.158 & 0.817 & 0.256 & 0.164 & 0.866 \\
WBS & 0.170 & 0.107 & 0.804 & 0.305 & 0.215 & 1.000 & 0.215 & 0.775 & 0.346 & 0.247 & 1.000 \\
zero & 0.648 & 1.000 & 0.545 & 0.648 & 1.000 & 0.545 & 1.000 & 0.545 & 0.648 & 1.000 & 0.545 \\
""",
    
    "Performance Metrics for Methods over 195 average-aggregated datasets merged with Mozilla method results": """
Mozilla \\& BinSeg & 0.746 & 0.951 & 0.679 & 0.802 & 1.000 & 0.958 & 0.895 & 0.792 & 0.929 & 1.000 & 0.958 \\
Mozilla \\& BOCPD & 0.772 & 0.867 & 0.771 & 0.797 & 0.981 & 0.889 & 0.935 & 0.754 & 0.906 & 0.996 & 0.909 \\
Mozilla \\& CPNP & 0.768 & 0.860 & 0.769 & 0.787 & 0.880 & 0.957 & 0.764 & 0.884 & 0.895 & 0.908 & 0.957 \\
Mozilla \\& KCPA & 0.725 & 0.939 & 0.664 & 0.767 & 0.942 & 0.774 & 0.875 & 0.765 & 0.820 & 0.965 & 0.782 \\
Mozilla \\& MongoDB & 0.761 & 0.916 & 0.726 & 0.769 & 0.923 & 0.747 & 0.904 & 0.742 & 0.787 & 0.929 & 0.751 \\
Mozilla \\& PELT & 0.769 & 0.943 & 0.709 & 0.784 & 0.943 & 0.958 & 0.880 & 0.781 & 0.927 & 0.972 & 0.958 \\
Mozilla \\& RFPOP & 0.772 & 0.850 & 0.793 & 0.778 & 0.850 & 0.841 & 0.840 & 0.809 & 0.808 & 0.864 & 0.841 \\
Mozilla \\& WBS & 0.782 & 0.866 & 0.786 & 0.784 & 0.896 & 0.958 & 0.869 & 0.789 & 0.881 & 0.908 & 0.958 \\
""",

"Performance Metrics for Methods over 195 average-aggregated datasets merged with Mozilla method results (one CPD/testing only Best combination)": """
Mozilla \\& BinSeg & 0.746 & 0.951 & 0.679 & 0.659 & 1.000 & 0.560 & 1.000 & 0.560 & 0.659 & 1.000 & 0.560 \\
Mozilla \\& BOCPD & 0.772 & 0.867 & 0.771 & 0.748 & 0.962 & 0.672 & 0.962 & 0.672 & 0.748 & 0.962 & 0.672 \\
Mozilla \\& CPNP & 0.768 & 0.860 & 0.769 & 0.779 & 0.877 & 0.773 & 0.877 & 0.773 & 0.779 & 0.877 & 0.773 \\
Mozilla \\& KCPA & 0.725 & 0.939 & 0.664 & 0.723 & 0.937 & 0.664 & 0.937 & 0.664 & 0.723 & 0.937 & 0.664 \\
Mozilla \\& MongoDB & 0.761 & 0.916 & 0.726 & 0.759 & 0.913 & 0.724 & 0.913 & 0.724 & 0.759 & 0.913 & 0.724 \\
Mozilla \\& PELT & 0.769 & 0.943 & 0.709 & 0.769 & 0.943 & 0.709 & 0.943 & 0.709 & 0.769 & 0.943 & 0.709 \\
Mozilla \\& RFPOP & 0.772 & 0.850 & 0.793 & 0.772 & 0.850 & 0.793 & 0.850 & 0.793 & 0.772 & 0.850 & 0.793 \\
Mozilla \\& WBS & 0.782 & 0.866 & 0.786 & 0.774 & 0.895 & 0.757 & 0.895 & 0.757 & 0.774 & 0.895 & 0.757 \\
""",

"Performance Metrics for Methods over 195 average-aggregated datasets merged with Mozilla method results (two CPDs/testing all combinations)": """
Mozilla \\& BinSeg \\& BOCPD & 0.771 & 0.863 & 0.772 & 0.804 & 0.981 & 0.958 & 0.892 & 0.797 & 0.933 & 0.996 & 0.958 \\
Mozilla \\& BinSeg \\& KCPA & 0.745 & 0.926 & 0.694 & 0.793 & 0.942 & 0.958 & 0.880 & 0.792 & 0.910 & 0.966 & 0.958 \\
Mozilla \\& BinSeg \\& MongoDB & 0.771 & 0.916 & 0.736 & 0.804 & 0.923 & 0.958 & 0.892 & 0.795 & 0.903 & 0.934 & 0.958 \\
Mozilla \\& Bineg \\& PELT & 0.767 & 0.932 & 0.714 & 0.802 & 0.943 & 0.958 & 0.895 & 0.792 & 0.929 & 0.972 & 0.958 \\
Mozilla \\& KCPA & 0.725 & 0.939 & 0.664 & 0.767 & 0.942 & 0.774 & 0.875 & 0.765 & 0.820 & 0.965 & 0.782 \\
MozillA \\& KCPA \\& BOCPD & 0.770 & 0.863 & 0.771 & 0.788 & 0.934 & 0.894 & 0.866 & 0.793 & 0.892 & 0.966 & 0.913 \\
Mozilla \\& MongoDB \\& BOCPD & 0.775 & 0.857 & 0.781 & 0.800 & 0.920 & 0.892 & 0.906 & 0.779 & 0.885 & 0.933 & 0.913 \\
Mozilla \\& MongoDB \\& KCPA & 0.768 & 0.897 & 0.746 & 0.776 & 0.904 & 0.781 & 0.895 & 0.756 & 0.807 & 0.914 & 0.789 \\
Mozilla \\& MongoDB \\& PELT & 0.779 & 0.910 & 0.749 & 0.790 & 0.911 & 0.958 & 0.887 & 0.780 & 0.905 & 0.929 & 0.958 \\
Mozilla \\& PELT BOCPD & 0.771 & 0.865 & 0.771 & 0.795 & 0.941 & 0.958 & 0.923 & 0.759 & 0.930 & 0.972 & 0.958 \\
Mozilla \\& PELT \\& KCPA & 0.757 & 0.920 & 0.712 & 0.783 & 0.923 & 0.958 & 0.876 & 0.784 & 0.910 & 0.945 & 0.958 \\
""",

"Performance Metrics for Methods over 195 average-aggregated datasets merged with Mozilla method results (two CPDs/testing only Best combinations)": """
Mozilla \\& BinSeg \\& BOCPD & 0.771 & 0.863 & 0.772 & 0.750 & 0.962 & 0.673 & 0.962 & 0.673 & 0.750 & 0.962 & 0.673 \\
Mozilla \\& BinSeg \\& KCPA & 0.745 & 0.926 & 0.694 & 0.723 & 0.937 & 0.664 & 0.937 & 0.664 & 0.723 & 0.937 & 0.664 \\
Mozilla \\& BinSeg \\& MongoDB & 0.771 & 0.916 & 0.736 & 0.759 & 0.913 & 0.724 & 0.913 & 0.724 & 0.759 & 0.913 & 0.724 \\
Mozilla \\& BinSeg \\& PELT & 0.767 & 0.932 & 0.714 & 0.769 & 0.943 & 0.709 & 0.943 & 0.709 & 0.769 & 0.943 & 0.709 \\
Mozilla \\& BOCPD \\& KCPA & 0.770 & 0.863 & 0.771 & 0.737 & 0.926 & 0.687 & 0.926 & 0.687 & 0.737 & 0.926 & 0.687 \\
Mozilla \\& BOCPD \\& MongoDB & 0.775 & 0.857 & 0.781 & 0.780 & 0.910 & 0.748 & 0.910 & 0.748 & 0.780 & 0.910 & 0.748 \\
Mozilla \\& BOCPD \\& PELT & 0.771 & 0.865 & 0.771 & 0.768 & 0.936 & 0.714 & 0.936 & 0.714 & 0.768 & 0.936 & 0.714 \\
Mozilla \\& KCPA \\& MongoDB & 0.768 & 0.897 & 0.746 & 0.765 & 0.896 & 0.742 & 0.896 & 0.742 & 0.765 & 0.896 & 0.742 \\
Mozilla \\& KCPA \\& PELT & 0.757 & 0.920 & 0.712 & 0.755 & 0.918 & 0.712 & 0.918 & 0.712 & 0.755 & 0.918 & 0.712 \\
Mozilla \\& MongoDB \\& PELT & 0.779 & 0.910 & 0.749 & 0.774 & 0.904 & 0.744 & 0.904 & 0.744 & 0.774 & 0.904 & 0.744 \\
""",

"Performance Metrics for Methods over 195 average-aggregated datasets merged with Mozilla method results (three CPD methods/testing only Best combinations)": """
Mozilla \\& BinSeg \\& BOCPD \\& KCPA & 0.770 & 0.860 & 0.772 & 0.737 & 0.926 & 0.687 & 0.926 & 0.687 & 0.737 & 0.926 & 0.687 \\
Mozilla \\& BinSeg \\& BOCPD \\& MongoDB & 0.775 & 0.857 & 0.781 & 0.780 & 0.910 & 0.748 & 0.910 & 0.748 & 0.780 & 0.910 & 0.748 \\
Mozilla \\& BinSeg \\& BOCPD \\& PELT & 0.771 & 0.863 & 0.772 & 0.768 & 0.936 & 0.714 & 0.936 & 0.714 & 0.768 & 0.936 & 0.714 \\
Mozilla \\& BinSeg \\& KCPA \\& MongoDB & 0.769 & 0.897 & 0.747 & 0.765 & 0.896 & 0.742 & 0.896 & 0.742 & 0.765 & 0.896 & 0.742 \\
Mozilla \\& BinSeg \\& KCPA \\& PELT & 0.756 & 0.913 & 0.716 & 0.755 & 0.918 & 0.712 & 0.918 & 0.712 & 0.755 & 0.918 & 0.712 \\
Mozilla \\& BinSeg \\& MongoDB \\& PELT & 0.781 & 0.910 & 0.750 & 0.774 & 0.904 & 0.744 & 0.904 & 0.744 & 0.774 & 0.904 & 0.744 \\
Mozilla \\& BOCPD \\& MongoDB \\& PELT & 0.775 & 0.857 & 0.781 & 0.777 & 0.902 & 0.749 & 0.902 & 0.749 & 0.777 & 0.902 & 0.749 \\
Mozilla \\& KCPA \\& BinSeg \\& BOCPD & 0.770 & 0.860 & 0.772 & 0.737 & 0.926 & 0.687 & 0.926 & 0.687 & 0.737 & 0.926 & 0.687 \\
Mozilla \\& KCPA \\& BOCPD \\& MongoDB & 0.773 & 0.854 & 0.781 & 0.768 & 0.892 & 0.748 & 0.892 & 0.748 & 0.768 & 0.892 & 0.748 \\
Mozilla \\& KCPA \\& BOCPD \\& PELT & 0.770 & 0.863 & 0.771 & 0.755 & 0.914 & 0.716 & 0.914 & 0.716 & 0.755 & 0.914 & 0.716 \\
Mozilla \\& KCPA \\& MongoDB \\& PELT & 0.770 & 0.895 & 0.750 & 0.767 & 0.891 & 0.746 & 0.891 & 0.746 & 0.767 & 0.891 & 0.746 \\
""",

"Performance Metrics for Methods over 195 average-aggregated datasets merged with Mozilla method results (four CPD methods/testing only Best combinations)": """
Mozilla \\& Binseg \\& BOCPD \\& KCPA \\& Mongodb & 0.773 & 0.854 & 0.781 & 0.768 & 0.892 & 0.748 & 0.892 & 0.748 & 0.768 & 0.892 & 0.748 \\
Mozilla \\& BinSeg \\& BOCPD \\& KCPA \\& PELT & 0.770 & 0.860 & 0.772 & 0.755 & 0.914 & 0.716 & 0.914 & 0.716 & 0.755 & 0.914 & 0.716 \\
Mozilla \\& BinSeg \\& BOCPD \\& MongoDB \\& PELT & 0.775 & 0.857 & 0.781 & 0.777 & 0.902 & 0.749 & 0.902 & 0.749 & 0.777 & 0.902 & 0.749 \\
Mozilla \\& KCPA \\& MongoDB \\& PELT \\& BinSeg & 0.770 & 0.895 & 0.750 & 0.767 & 0.891 & 0.746 & 0.891 & 0.746 & 0.767 & 0.891 & 0.746 \\
Mozilla \\& KCPA \\& MongoDB \\& PELT \\& BOCPD & 0.773 & 0.854 & 0.781 & 0.769 & 0.890 & 0.749 & 0.890 & 0.749 & 0.769 & 0.890 & 0.749 \\
"""
}

import pandas as pd
import re


def parse_latex_table(latex_string, expected_numeric_cols=11):
    """Convert a LaTeX table string into a DataFrame while ensuring 12 columns (1 text + 11 numeric)."""
    
    # Step 1: Preprocess rows, remove LaTeX line breaks, and split the table into rows
    rows = [re.sub(r"\\\\", "", row).strip() for row in latex_string.split("\n") if row.strip()]

    # Step 2: Handle escaped ampersands (\\&) correctly by replacing them with a placeholder
    rows = [row.replace(r"\\&", "[AMP]") for row in rows]  # Temporarily replace \\& with [AMP]
    
    # Step 3: Split the row by " & " but preserve the [AMP] in the text column
    data = [row.split(" & ") for row in rows]

    # Step 4: Restore the ampersand in the first column after splitting
    data = [[cell.replace("[AMP]", "&") for cell in row] for row in data]
    
    # Step 5: Ensure every row has exactly 12 columns (1 text + 11 numeric)
    for i, row in enumerate(data):
        if len(row) < expected_numeric_cols + 1:  # If row has fewer columns, pad it
            missing_cols = (expected_numeric_cols + 1) - len(row)
            data[i].extend(["N/A"] * missing_cols)  # Fill missing columns with N/A
        elif len(row) > expected_numeric_cols + 1:  # If row has too many columns, keep only the first 12
            data[i] = row[:expected_numeric_cols + 1]  # Keep only 12 columns (1 text + 11 numeric)

    # Step 6: Convert to DataFrame
    df = pd.DataFrame(data)
    df.iloc[:, -1] = df.iloc[:, -1].str.replace(r'\\', '', regex=True)  # Remove backslashes
    df.iloc[:, -1] = df.iloc[:, -1].str.strip()

    # Step 7: Convert numeric columns (2nd to last) to numeric values
    for col in df.columns.tolist()[1:]:  # Exclude the first column (text)
        df[col] = pd.to_numeric(df[col], errors="coerce")  # Coerce invalid numeric entries to NaN
    # print(df)
    return df

def compute_summary_stats(df, expected_numeric_cols=11):
    """Compute mean, median, min, and max for exactly 11 numeric columns."""
    
    numeric_df = df.iloc[:, 1:].apply(pd.to_numeric, errors="coerce")  # Ensure numeric conversion
    # print(df.iloc[:, 1:])
    
    # Ensure correct number of numeric columns
    if numeric_df.shape[1] != expected_numeric_cols:
        raise ValueError(f"Expected {expected_numeric_cols} numeric columns, found {numeric_df.shape[1]}.")

    summary = pd.DataFrame({
        "Statistic": ["\\textbf{Mean}", "\\textbf{Median}", "\\textbf{Min}", "\\textbf{Max}"],
    })

    for col in numeric_df.columns:
        summary[col] = [
            numeric_df[col].mean(),
            numeric_df[col].median(),
            numeric_df[col].min(),
            numeric_df[col].max()
        ]

    # Convert to LaTeX row format
    latex_rows = [
        " & ".join([stat] + [f"{val:.3f}" if pd.notna(val) else "N/A" for val in row]) + r" \\"
        for stat, row in zip(summary["Statistic"], summary.iloc[:, 1:].values)
    ]

    return latex_rows

def process_latex_tables(latex_dict):
    """Process a list of LaTeX table strings and return summary statistics in LaTeX format."""
    all_summaries = dict()
    
    for key, latex_str in latex_dict.items():
        df = parse_latex_table(latex_str)
        summary_rows = compute_summary_stats(df)
        all_summaries[key] = summary_rows
    
    return all_summaries

# Process and get summary LaTeX rows
summary_latex_rows = process_latex_tables(input_dict)

# Print summary in LaTeX format
for key, summary in summary_latex_rows.items():
    print(f"{key}:")
    for row in summary:
        print(row)
    print("\n")
