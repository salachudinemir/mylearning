import streamlit as st
import pandas as pd
from utils.evaluation import calculate_forecast_accuracy
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
from visualization.tables import (
    top_rootcause_table,
    sla_violation_table,
    top_subcause_table,
    top_rootcause_subcause_table,
    top_mccluster_table,
    display_table_forecast
)
from visualization.plots import (
    plot_incident_per_circle,
    plot_restore_duration,
    plot_incident_per_region,
    plot_incident_per_severity,
    plot_sla_violation_pie,
    plot_by_circle,
    plot_by_alarmname,
    plot_by_subcause,
    plot_mccluster_repetitive,
    plot_siteid_repetitive,
    plot_forecast,
)
from utils.forecast import (
    get_model_key_from_params,
    get_model_key_from_series,
    get_model_key,
    train_arima,
    load_arima_model,
    forecast_arima,
    train_auto_arima,
    load_auto_arima_model,
    forecast_auto_arima,
    train_prophet,
    load_prophet_model,
    save_or_load_prophet_model,
    forecast_prophet,
    train_lstm_univariate,
    load_lstm_univariate_model,
    save_or_load_lstm_univariate_model,
    forecast_lstm_univariate,
    train_lstm_multivariate,
    load_lstm_multivariate_model,
    save_or_load_lstm_multivariate_model,
    forecast_lstm_multivariate
)

def render_tab7(df_filtered, createmode_filter, circle_filter, severity_filter, start_date, end_date):
    st.header("Forecasting dengan Filter & Cache Model ARIMA")
    if df_filtered is None or df_filtered.empty:
        st.warning("Data kosong setelah filter. Silakan atur filter sidebar.")
        return

    ts = prepare_time_series(df_filtered, date_col='createtime', count_col='orderid', freq='D')
    ts_agg = aggregate_time_series(ts, freq_days=7)

    split_point = int(len(ts_agg) * 0.8)
    train_ts = ts_agg.iloc[:split_point]
    test_ts = ts_agg.iloc[split_point:]
    forecast_steps = max(len(test_ts), 8)
    last_date = train_ts.index[-1]

    model_type = st.radio(
        "Pilih model algoritma forecasting",
        ["Manual ARIMA", "Auto ARIMA", "Prophet", "LSTM Univariate", "LSTM Multivariate"]
    )

    st.subheader(f"📈 Forecast Gangguan dengan {model_type}")

    interactive_mode = st.checkbox("🔍 Gunakan plot interaktif (Plotly)", value=True)

    filter_params = {
        "createmode": tuple(sorted(createmode_filter)) if 'createmode_filter' in locals() else (),
        "circle": tuple(sorted(circle_filter)) if 'circle_filter' in locals() else (),
        "severity": tuple(sorted(severity_filter)) if 'severity_filter' in locals() else (),
        "date_range": (str(start_date), str(end_date)) if start_date and end_date else (None, None),
        "model_type": model_type,
    }

    train_df = train_ts.to_frame(name='target')
    train_df = create_datetime_features_df(train_df)
    train_df = create_lag_features(train_df, lags=[1, 2])
    train_df = create_rolling_features(train_df, windows=[3, 7])
    train_df = train_df.dropna()

    if model_type == "Manual ARIMA":
        p = st.number_input("p (AR order)", min_value=0, max_value=10, value=1)
        d = st.number_input("d (Differencing order)", min_value=0, max_value=2, value=1)
        q = st.number_input("q (MA order)", min_value=0, max_value=10, value=1)
        arima_order = (p, d, q)
        filter_params["order"] = arima_order
    else:
        arima_order = None

    if st.button("Run Forecast"):
        st.info("Training model & melakukan forecast...")

        model_key = get_model_key(
            model_type=model_type,
            ts_data=train_ts,
            params=filter_params,
            order=arima_order if model_type == "Manual ARIMA" else None
        )

        forecast = None

        if model_type == "Manual ARIMA":
            st.subheader("🔍 Sampel Data Training (Manual ARIMA)")
            st.dataframe(train_df.tail(10))

            model = train_arima(train_ts, order=arima_order, model_key=model_key)
            forecast_values = forecast_arima(model, steps=forecast_steps)
            forecast_index = pd.date_range(start=last_date + pd.Timedelta(days=7), periods=forecast_steps, freq='7D')
            forecast = pd.Series(forecast_values, index=forecast_index)

            st.subheader("📈 Hasil Forecast Preview (Manual ARIMA)")
            st.dataframe(forecast.to_frame(name='predicted').head(10))

        elif model_type == "Auto ARIMA":
            st.subheader("🔍 Sampel Data Training (Auto ARIMA)")
            st.dataframe(train_df.tail(10))
        
            model = train_auto_arima(train_ts, model_key=model_key)
            forecast_values = forecast_auto_arima(model, steps=forecast_steps)
            forecast_index = pd.date_range(start=last_date + pd.Timedelta(days=7), periods=forecast_steps, freq='7D')
            forecast = pd.Series(forecast_values, index=forecast_index)
            
            st.subheader("📈 Hasil Forecast Preview (Auto ARIMA)")
            st.dataframe(forecast.to_frame(name='predicted').head(10))

        elif model_type == "Prophet":

            st.subheader("🔍 Sampel Data Training (Prophet)")
            st.dataframe(train_df.tail(10))

            model = save_or_load_prophet_model(train_ts, model_key=model_key)
            forecast = forecast_prophet(model, steps=forecast_steps, last_date=last_date)

            st.subheader("📈 Hasil Forecast Preview (Prophet)")
            st.dataframe(forecast.to_frame(name='predicted').head(10))

        elif model_type == "LSTM Univariate":
            st.subheader("🔍 Sampel Data Training (LSTM Univariate)")
            st.dataframe(train_df.tail(10))

            model, scaler = save_or_load_lstm_univariate_model(train_ts, model_key=model_key, window_size=7)
            forecast = forecast_lstm_univariate(model, scaler, train_ts, steps=forecast_steps, window_size=7, freq='7D')

            st.subheader("📈 Hasil Forecast Preview (LSTM Univariate)")
            st.dataframe(forecast.to_frame(name='predicted').head(10))

        elif model_type == "LSTM Multivariate":
            train_df_mv = train_ts.to_frame(name='target')
            train_df_mv = create_datetime_features_df(train_df_mv)
            train_df_mv = create_lag_features(train_df_mv, lags=[1, 2])
            train_df_mv = create_rolling_features(train_df_mv, windows=[3, 7], target_col='target')
            train_df_mv = train_df_mv.dropna()

            st.subheader("🔍 Sampel Data Training (LSTM Multivariate)")
            st.dataframe(train_df_mv.tail(10))

            model_key_mv = get_model_key(model_type=model_type, ts_data=train_df_mv, params=filter_params)
            model_mv, scaler_mv = save_or_load_lstm_multivariate_model(train_df_mv, target_column='target', model_key=model_key_mv)
            forecast = forecast_lstm_multivariate(model_mv, scaler_mv, train_df_mv, target_column='target', steps=forecast_steps, freq='7D')

        else:
            st.warning("Model type tidak dikenali atau belum tersedia.")

        if forecast is not None:
            combined_ts = pd.concat([train_ts, test_ts])
            fig = plot_forecast(combined_ts, forecast, interactive=interactive_mode, start_date=start_date, end_date=end_date)
            if interactive_mode:
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.pyplot(fig)

            st.markdown(f"### 📋 Tabel Forecast {model_type}")
            df_forecast_table = display_table_forecast(test_ts, forecast)
            st.dataframe(df_forecast_table, use_container_width=True)

            st.markdown(f"### 📊 Evaluasi Akurasi Forecast {model_type}")
            # Samakan panjang prediksi dan data aktual
            forecast = forecast[:len(test_ts)]
            accuracy = calculate_forecast_accuracy(test_ts, forecast)
            st.write(f"- MAE: {accuracy['MAE']:.2f}")
            st.write(f"- RMSE: {accuracy['RMSE']:.2f}")
            st.write(f"- MAPE: {accuracy['MAPE']:.2f}%")
            st.write(f"- SMAPE: {accuracy['SMAPE']:.2f}%")
        else:
            st.warning("Forecast belum tersedia untuk tipe model ini.")
    else:
        st.write("Tekan tombol 'Run Forecast' untuk mulai training dan forecasting.")
