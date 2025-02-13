import re
import pandas as pd

# Function to extract caption from latex table
def extract_caption(latex_table_content):
    caption_pattern = re.compile(r'\\caption{(.*?)}', re.DOTALL)
    caption_match = caption_pattern.search(latex_table_content)
    if caption_match:
        return caption_match.group(1).strip()
    return "No caption found"

# Function to convert LaTeX table content to DataFrame
def latex_table_to_dataframe(latex_table_content):
    table_data = []
    rows = latex_table_content.split("\\\\")
    
    for row in rows:
        row = row.strip()
        if row:
            # Keep LaTeX formatting but split at '&' for each column
            cleaned_row = re.sub(r'\\[a-zA-Z]+\{[^}]*\}', '', row)  # Removing LaTeX commands
            table_data.append(cleaned_row.split('&'))
    
    # Convert to DataFrame for easier statistical analysis
    df = pd.DataFrame(table_data)
    return df

# Function to calculate statistics (mean, median, min, max)
def calculate_statistics(df):
    # Convert all columns to numeric values (ignoring non-numeric columns)
    df_numeric = df.apply(pd.to_numeric, errors='coerce')

    # Calculate statistics
    mean_row = df_numeric.mean()
    median_row = df_numeric.median()
    min_row = df_numeric.min()
    max_row = df_numeric.max()

    return mean_row, median_row, min_row, max_row

# Function to add the statistics row to the LaTeX table
def add_statistics_to_latex_table(latex_table_content, mean_row, median_row, min_row, max_row):
    table_rows = latex_table_content.split("\\\\")
    
    # Create a formatted statistics row
    stats_row = "Mean & " + " & ".join([f"{value:.3f}" for value in mean_row]) + " \\\\"
    table_rows.append(stats_row)
    
    stats_row = "Median & " + " & ".join([f"{value:.3f}" for value in median_row]) + " \\\\"
    table_rows.append(stats_row)
    
    stats_row = "Min & " + " & ".join([f"{value:.3f}" for value in min_row]) + " \\\\"
    table_rows.append(stats_row)
    
    stats_row = "Max & " + " & ".join([f"{value:.3f}" for value in max_row]) + " \\\\"
    table_rows.append(stats_row)
    
    latex_table_with_stats = "\\\\\n".join(table_rows)
    
    # Add the caption and return the updated table
    caption = extract_caption(latex_table_content)
    updated_latex_table = latex_table_with_stats + "\n\\caption{" + caption + "}"
    
    return updated_latex_table

# Function to process a list of LaTeX tables and add statistics rows
def process_multiple_latex_tables(latex_tables):
    updated_tables = []
    
    for latex_table in latex_tables:
        # Convert LaTeX table content to DataFrame
        df = latex_table_to_dataframe(latex_table)
        
        # Calculate statistics (mean, median, min, max)
        mean_row, median_row, min_row, max_row = calculate_statistics(df)
        
        # Add the statistics row to the original LaTeX table
        updated_latex_table = add_statistics_to_latex_table(latex_table, mean_row, median_row, min_row, max_row)
        
        updated_tables.append(updated_latex_table)
    
    return updated_tables




latex_input_list = [
    """
    \begin{table*}[t!]
    \centering
    \resizebox{\textwidth}{!}{%
    \begin{tabular}{|l|c|c|c||c|c|c|c|c||c|c|c|}
    \hline
    Method & \multicolumn{3}{c||}{Default} & \multicolumn{5}{c||}{Best} & \multicolumn{3}{c|}{Oracle} \\
    \cline{2-13}
    & F1 & Precision & Recall & F1 & Precision & Recall & Precision (F1 max) & Recall (F1 max) & F1 & Precision & Recall \\
    \hline
    BinSeg & 0.524 & 0.481 & 0.693 & 0.653 & 1.000 & 1.000 & 0.961 & 0.562 & 0.764 & 1.000 & 1.000 \\
    BOCPD & 0.256 & 0.177 & 0.791 & 0.591 & 0.621 & 0.918 & 0.592 & 0.681 & 0.710 & 0.789 & 0.946 \\
    CPNP & 0.284 & 0.187 & 0.785 & 0.292 & 0.193 & 0.999 & 0.193 & 0.793 & 0.305 & 0.203 & 0.999 \\
    KCPA & 0.516 & 0.497 & 0.676 & 0.516 & 0.497 & 0.795 & 0.497 & 0.676 & 0.557 & 0.516 & 0.801 \\
    MongoDB & 0.428 & 0.339 & 0.746 & 0.432 & 0.343 & 0.769 & 0.343 & 0.744 & 0.464 & 0.374 & 0.773 \\
    PELT & 0.451 & 0.382 & 0.722 & 0.451 & 0.382 & 1.000 & 0.382 & 0.722 & 0.525 & 0.458 & 1.000 \\
    RFPOP & 0.248 & 0.158 & 0.817 & 0.248 & 0.158 & 0.866 & 0.158 & 0.817 & 0.256 & 0.164 & 0.866 \\
    pelt & 0.451 & 0.382 & 0.722 & 0.451 & 0.382 & 1.000 & 0.382 & 0.722 & 0.525 & 0.458 & 1.000 \\
    WBS & 0.170 & 0.107 & 0.804 & 0.305 & 0.215 & 1.000 & 0.215 & 0.775 & 0.346 & 0.247 & 1.000 \\
    zero & 0.648 & 1.000 & 0.545 & 0.648 & 1.000 & 0.545 & 1.000 & 0.545 & 0.648 & 1.000 & 0.545 \\
    \hline
    \end{tabular}%%
    }
    \caption{Performance Metrics for Methods over 195 average-aggregated datasets}
    \end{table*}
    """
]







# latex_input_list = [
#     """
#     \begin{table*}[t!]
#     \centering
#     \resizebox{\textwidth}{!}{%
#     \begin{tabular}{|l|c|c|c||c|c|c|c|c||c|c|c|}
#     \hline
#     Method & \multicolumn{3}{c||}{Default} & \multicolumn{5}{c||}{Best} & \multicolumn{3}{c|}{Oracle} \\
#     \cline{2-13}
#     & F1 & Precision & Recall & F1 & Precision & Recall & Precision (F1 max) & Recall (F1 max) & F1 & Precision & Recall \\
#     \hline
#     BinSeg & 0.524 & 0.481 & 0.693 & 0.653 & 1.000 & 1.000 & 0.961 & 0.562 & 0.764 & 1.000 & 1.000 \\
#     BOCPD & 0.256 & 0.177 & 0.791 & 0.591 & 0.621 & 0.918 & 0.592 & 0.681 & 0.710 & 0.789 & 0.946 \\
#     CPNP & 0.284 & 0.187 & 0.785 & 0.292 & 0.193 & 0.999 & 0.193 & 0.793 & 0.305 & 0.203 & 0.999 \\
#     KCPA & 0.516 & 0.497 & 0.676 & 0.516 & 0.497 & 0.795 & 0.497 & 0.676 & 0.557 & 0.516 & 0.801 \\
#     MongoDB & 0.428 & 0.339 & 0.746 & 0.432 & 0.343 & 0.769 & 0.343 & 0.744 & 0.464 & 0.374 & 0.773 \\
#     PELT & 0.451 & 0.382 & 0.722 & 0.451 & 0.382 & 1.000 & 0.382 & 0.722 & 0.525 & 0.458 & 1.000 \\
#     RFPOP & 0.248 & 0.158 & 0.817 & 0.248 & 0.158 & 0.866 & 0.158 & 0.817 & 0.256 & 0.164 & 0.866 \\
#     pelt & 0.451 & 0.382 & 0.722 & 0.451 & 0.382 & 1.000 & 0.382 & 0.722 & 0.525 & 0.458 & 1.000 \\
#     WBS & 0.170 & 0.107 & 0.804 & 0.305 & 0.215 & 1.000 & 0.215 & 0.775 & 0.346 & 0.247 & 1.000 \\
#     zero & 0.648 & 1.000 & 0.545 & 0.648 & 1.000 & 0.545 & 1.000 & 0.545 & 0.648 & 1.000 & 0.545 \\
#     \hline
#     \end{tabular}%%
#     }
#     \caption{Performance Metrics for Methods over 195 average-aggregated datasets}
#     \end{table*}
#     """
#     ,
#     """
#     \begin{table*}[t!]
#     \centering
#     \resizebox{\textwidth}{!}{%
#     \begin{tabular}{|l|c|c|c||c|c|c|c|c||c|c|c|}
#     \hline
#     Method & \multicolumn{3}{c||}{Default} & \multicolumn{5}{c||}{Best} & \multicolumn{3}{c|}{Oracle} \\
#     \cline{2-13}
#     & F1 & Precision & Recall & F1 & Precision & Recall & Precision (F1 max) & Recall (F1 max) & F1 & Precision & Recall \\
#     \hline
#     Mozilla \& BinSeg & 0.746 & 0.951 & 0.679 & 0.802 & 1.000 & 0.958 & 0.895 & 0.792 & 0.929 & 1.000 & 0.958 \\
#     Mozilla \& BOCPD & 0.772 & 0.867 & 0.771 & 0.797 & 0.981 & 0.889 & 0.935 & 0.754 & 0.906 & 0.996 & 0.909 \\
#     Mozilla \& CPNP & 0.768 & 0.860 & 0.769 & 0.787 & 0.880 & 0.957 & 0.764 & 0.884 & 0.895 & 0.908 & 0.957 \\
#     Mozilla \& KCPA & 0.725 & 0.939 & 0.664 & 0.767 & 0.942 & 0.774 & 0.875 & 0.765 & 0.820 & 0.965 & 0.782 \\
#     Mozilla \& MongoDB & 0.761 & 0.916 & 0.726 & 0.769 & 0.923 & 0.747 & 0.904 & 0.742 & 0.787 & 0.929 & 0.751 \\
#     Mozilla \& PELT & 0.769 & 0.943 & 0.709 & 0.784 & 0.943 & 0.958 & 0.880 & 0.781 & 0.927 & 0.972 & 0.958 \\
#     Mozilla \& RFPOP & 0.772 & 0.850 & 0.793 & 0.778 & 0.850 & 0.841 & 0.840 & 0.809 & 0.808 & 0.864 & 0.841 \\
#     Mozilla \& WBS & 0.782 & 0.866 & 0.786 & 0.784 & 0.896 & 0.958 & 0.869 & 0.789 & 0.881 & 0.908 & 0.958 \\
#     Mozilla \& Zero & 0.648 & 1.000 & 0.545 & 0.648 & 1.000 & 0.545 & 1.000 & 0.545 & 0.648 & 1.000 & 0.545 \\
#     \hline
#     \end{tabular}%%
#     }
#     \caption{Performance Metrics for Methods over 195 average-aggregated datasets merged with Mozilla method results}
#     \end{table*}
#     """
#     ,
#     """
#     \begin{table*}[t!]
#     \centering
#     \resizebox{\textwidth}{!}{%
#     \begin{tabular}{|l|c|c|c||c|c|c|c|c||c|c|c|}
#     \hline
#     Method & \multicolumn{3}{c||}{Default} & \multicolumn{5}{c||}{Best} & \multicolumn{3}{c|}{Oracle} \\
#     \cline{2-13}
#     & F1 & Precision & Recall & F1 & Precision & Recall & Precision (F1 max) & Recall (F1 max) & F1 & Precision & Recall \\
#     \hline
#     Mozilla \& BinSeg \& BOCPD & 0.771 & 0.863 & 0.772 & 0.804 & 0.981 & 0.958 & 0.892 & 0.797 & 0.933 & 0.996 & 0.958 \\
#     Mozilla \& BinSeg \& KCPA & 0.745 & 0.926 & 0.694 & 0.793 & 0.942 & 0.958 & 0.880 & 0.792 & 0.910 & 0.966 & 0.958 \\
#     Mozilla \& BinSeg \& MongoDB & 0.771 & 0.916 & 0.736 & 0.804 & 0.923 & 0.958 & 0.892 & 0.795 & 0.903 & 0.934 & 0.958 \\
#     Mozilla \& Bineg \& PELT & 0.767 & 0.932 & 0.714 & 0.802 & 0.943 & 0.958 & 0.895 & 0.792 & 0.929 & 0.972 & 0.958 \\
#     Mozilla \& KCPA & 0.725 & 0.939 & 0.664 & 0.767 & 0.942 & 0.774 & 0.875 & 0.765 & 0.820 & 0.965 & 0.782 \\
#     MozillA \& KCPA \& BOCPD & 0.770 & 0.863 & 0.771 & 0.788 & 0.934 & 0.894 & 0.866 & 0.793 & 0.892 & 0.966 & 0.913 \\
#     Mozilla \& MongoDB \& BOCPD & 0.775 & 0.857 & 0.781 & 0.800 & 0.920 & 0.892 & 0.906 & 0.779 & 0.885 & 0.933 & 0.913 \\
#     Mozilla \& MongoDB \& KCPA & 0.768 & 0.897 & 0.746 & 0.776 & 0.904 & 0.781 & 0.895 & 0.756 & 0.807 & 0.914 & 0.789 \\
#     Mozilla \& MongoDB \& PELT & 0.779 & 0.910 & 0.749 & 0.790 & 0.911 & 0.958 & 0.887 & 0.780 & 0.905 & 0.929 & 0.958 \\
#     Mozilla \& PELT BOCPD & 0.771 & 0.865 & 0.771 & 0.795 & 0.941 & 0.958 & 0.923 & 0.759 & 0.930 & 0.972 & 0.958 \\
#     Mozilla \& PELT \& KCPA & 0.757 & 0.920 & 0.712 & 0.783 & 0.923 & 0.958 & 0.876 & 0.784 & 0.910 & 0.945 & 0.958 \\
#     \hline
#     \end{tabular}%%
#     }
#     \caption{Performance Metrics for Methods over 195 average-aggregated datasets merged with Mozilla method results (two CPDs/testing all combinations)}
#     \end{table*}
#     """
#     ,
#     """
#     \begin{table*}[t!]
#     \centering
#     \resizebox{\textwidth}{!}{%
#     \begin{tabular}{|l|c|c|c||c|c|c|c|c||c|c|c|}
#     \hline
#     Method & \multicolumn{3}{c||}{Default} & \multicolumn{5}{c||}{Best} & \multicolumn{3}{c|}{Oracle} \\
#     \cline{2-13}
#     & F1 & Precision & Recall & F1 & Precision & Recall & Precision (F1 max) & Recall (F1 max) & F1 & Precision & Recall \\
#     \hline
#     Mozilla \& BinSeg \& BOCPD \& KCPA & 0.770 & 0.860 & 0.772 & 0.737 & 0.926 & 0.687 & 0.926 & 0.687 & 0.737 & 0.926 & 0.687 \\
#     Mozilla \& BinSeg \& BOCPD \& MongoDB & 0.775 & 0.857 & 0.781 & 0.780 & 0.910 & 0.748 & 0.910 & 0.748 & 0.780 & 0.910 & 0.748 \\
#     Mozilla \& BinSeg \& BOCPD \& PELT & 0.771 & 0.863 & 0.772 & 0.768 & 0.936 & 0.714 & 0.936 & 0.714 & 0.768 & 0.936 & 0.714 \\
#     Mozilla \& BinSeg \& KCPA \& MongoDB & 0.769 & 0.897 & 0.747 & 0.765 & 0.896 & 0.742 & 0.896 & 0.742 & 0.765 & 0.896 & 0.742 \\
#     Mozilla \& BinSeg \& KCPA \& PELT & 0.756 & 0.913 & 0.716 & 0.755 & 0.918 & 0.712 & 0.918 & 0.712 & 0.755 & 0.918 & 0.712 \\
#     Mozilla \& BinSeg \& MongoDB \& PELT & 0.781 & 0.910 & 0.750 & 0.774 & 0.904 & 0.744 & 0.904 & 0.744 & 0.774 & 0.904 & 0.744 \\
#     Mozilla \& BOCPD \& MongoDB \& PELT & 0.775 & 0.857 & 0.781 & 0.777 & 0.902 & 0.749 & 0.902 & 0.749 & 0.777 & 0.902 & 0.749 \\
#     Mozilla \& KCPA \& BinSeg \& BOCPD & 0.770 & 0.860 & 0.772 & 0.737 & 0.926 & 0.687 & 0.926 & 0.687 & 0.737 & 0.926 & 0.687 \\
#     Mozilla \& KCPA \& BOCPD \& MongoDB & 0.773 & 0.854 & 0.781 & 0.768 & 0.892 & 0.748 & 0.892 & 0.748 & 0.768 & 0.892 & 0.748 \\
#     Mozilla \& KCPA \& BOCPD \& PELT & 0.770 & 0.863 & 0.771 & 0.755 & 0.914 & 0.716 & 0.914 & 0.716 & 0.755 & 0.914 & 0.716 \\
#     Mozilla \& KCPA \& MongoDB \& PELT & 0.770 & 0.895 & 0.750 & 0.767 & 0.891 & 0.746 & 0.891 & 0.746 & 0.767 & 0.891 & 0.746 \\
#     \hline
#     \end{tabular}%%
#     }
#     \caption{Performance Metrics for Methods over 195 average-aggregated datasets merged with Mozilla method results (three CPD methods/testing only Best combinations)}
#     \end{table*}
#     """
#     ,
#     """
#     \begin{table*}[t!]
#     \centering
#     \resizebox{\textwidth}{!}{%
#     \begin{tabular}{|l|c|c|c||c|c|c|c|c||c|c|c|}
#     \hline
#     Method & \multicolumn{3}{c||}{Default} & \multicolumn{5}{c||}{Best} & \multicolumn{3}{c|}{Oracle} \\
#     \cline{2-13}
#     & F1 & Precision & Recall & F1 & Precision & Recall & Precision (F1 max) & Recall (F1 max) & F1 & Precision & Recall \\
#     \hline
#     mozilla \& Binseg \& BOCPD \& KCPA \& Mongodb & 0.773 & 0.854 & 0.781 & 0.768 & 0.892 & 0.748 & 0.892 & 0.748 & 0.768 & 0.892 & 0.748 \\
#     mozilla \& BinSeg \& BOCPD \& KCPA \& PELT & 0.770 & 0.860 & 0.772 & 0.755 & 0.914 & 0.716 & 0.914 & 0.716 & 0.755 & 0.914 & 0.716 \\
#     mozilla \& BinSeg \& BOCPD \& MongoDB \& PELT & 0.775 & 0.857 & 0.781 & 0.777 & 0.902 & 0.749 & 0.902 & 0.749 & 0.777 & 0.902 & 0.749 \\
#     mozilla \& KCPA \& MongoDB \& PELT \& BinSeg & 0.770 & 0.895 & 0.750 & 0.767 & 0.891 & 0.746 & 0.891 & 0.746 & 0.767 & 0.891 & 0.746 \\
#     mozilla \& KCPA \& MongoDB \& PELT \& BOCPD & 0.773 & 0.854 & 0.781 & 0.769 & 0.890 & 0.749 & 0.890 & 0.749 & 0.769 & 0.890 & 0.749 \\
#     mozilla \& PELT \& BinSeg \& BOCPD \& KCPA \& MongoDB & 0.773 & 0.854 & 0.781 & 0.769 & 0.890 & 0.749 & 0.890 & 0.749 & 0.769 & 0.890 & 0.749 \\
#     \hline
#     \end{tabular}%%
#     }
#     \caption{Performance Metrics for Methods over 195 average-aggregated datasets merged with Mozilla method results (four or five CPD methods/testing only Best combinations)}
#     \end{table*}
#     """
# ]

# Process the list of latex tables and add the statistics rows
updated_latex_tables = process_multiple_latex_tables(latex_input_list)

# Print the updated LaTeX tables with statistics rows
for updated_table in updated_latex_tables:
    print("###################")
    print(updated_table)
