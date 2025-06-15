from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

def calculate_forecast_accuracy(actual, predicted):
    actual, predicted = np.array(actual), np.array(predicted)
    mae = mean_absolute_error(actual, predicted)
    mse = mean_squared_error(actual, predicted)
    rmse = np.sqrt(mse)
    
    # MAPE: hindari pembagian dengan nol
    nonzero_mask = actual != 0
    if np.any(nonzero_mask):
        mape = np.mean(np.abs((actual[nonzero_mask] - predicted[nonzero_mask]) / actual[nonzero_mask])) * 100
    else:
        mape = np.nan  # jika semua actual = 0
    
    # SMAPE: symmetric MAPE, juga hindari nol pada denominator
    denominator = (np.abs(actual) + np.abs(predicted)) / 2
    nonzero_denom_mask = denominator != 0
    if np.any(nonzero_denom_mask):
        smape = np.mean(np.abs(actual[nonzero_denom_mask] - predicted[nonzero_denom_mask]) / denominator[nonzero_denom_mask]) * 100
    else:
        smape = np.nan
    
    return {"MAE": mae, "RMSE": rmse, "MAPE": mape, "SMAPE": smape}
