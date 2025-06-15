from rapidfuzz import fuzz
import streamlit as st
import pandas as pd
from utils.preprocessing import (
    get_file_hash,
    save_to_cache,
    read_metadata,
    write_metadata,
    load_and_cache_data,
    load_cached_dataframe_if_any,
    clear_cache,
    clean_data,
    normalize_col_name,
    drop_unwanted_columns,
    preview_columns_to_drop,
    DROP_COLUMNS,
    prepare_time_series,
    aggregate_time_series,
    fill_missing_values,
    create_datetime_features,
    create_datetime_features_df,
    create_lag_features,
    create_rolling_features,
    preprocess_for_lstm_multivariate,
    create_lstm_univariate_dataset,
    create_lstm_multivariate_dataset
)

def show_similar_pairs(df, col_name, threshold=70):
    if col_name not in df.columns:
        st.warning(f"Kolom '{col_name}' tidak ditemukan di data.")
        return

    st.subheader(f"Frekuensi {col_name.capitalize()}")
    counts = df[col_name].value_counts().reset_index()
    counts.columns = [col_name.capitalize(), 'Jumlah']
    st.dataframe(counts.head(10), use_container_width=True)

    st.subheader(f"Pasangan {col_name.capitalize()} dengan kemiripan ≥ {threshold}%")
    unique_vals = df[col_name].dropna().unique()
    similar_pairs = []

    for i in range(len(unique_vals)):
        for j in range(i + 1, len(unique_vals)):
            score = fuzz.token_sort_ratio(unique_vals[i], unique_vals[j])
            if score >= threshold:
                similar_pairs.append((unique_vals[i], unique_vals[j], score))

    if similar_pairs:
        df_similar = pd.DataFrame(similar_pairs, columns=[f'{col_name.capitalize()} 1', f'{col_name.capitalize()} 2', 'Similarity'])
        st.dataframe(df_similar)
    else:
        st.info(f"Tidak ditemukan pasangan '{col_name}' dengan kemiripan ≥ {threshold}%.")
