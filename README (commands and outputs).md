# DSA5205 Project 2: code package (Group 3)

This package contains the code for the Group 3 report for DSA5205 Project 2 (`Group_3_Report.pdf`). It downloads daily prices for Apple, Microsoft, NVIDIA, Tesla, and SPY from Yahoo Finance, cleans them, and builds open-to-open return labels and seven price and volume features. `modelling_validation.ipynb` then forecasts each stock's next open-to-open return with a LASSO and three baselines (ridge regression, AR(3) and the historical mean), re-estimated on rolling windows.

| File | Contents |
|---|---|
| `download_data.py` | Downloads the daily prices, volume, dividends, and splits of the five assets from Yahoo Finance into `data/` |
| `prepare_data.py` | Cleans the downloaded prices and builds the open-to-open return labels |
| `build_features.py` | Builds the seven features and the table used for modelling |
| `modelling_validation.ipynb` | Rolling estimation, model validation, forecast accuracy evaluation, forecast export, and trading evaluation |
| `strategy.py` | Converts LASSO return forecasts into long-only portfolio weights |
| `backtest.py` | Runs open-to-open backtests with transaction costs |
| `evaluation.py` | Selects trading parameters and evaluates validation/test performance |
| `requirements.txt` | Pinned Python packages used in the scripts and notebook. |
| `data/` | CSV files downloaded by running download_data.py |
| `data/prepared/` | Outputs of prepare_data.py |
| `results/` | Trading parameter selection, performance tables, portfolio weights, daily returns, cumulative wealth plots, $R^2$-by-year plot |

The package was tested on Windows 11 with Conda 26.5.3 and Python 3.12, by running the commands below in a new environment that contained only the packages in `requirements.txt`. The notebook was also run in Visual Studio Code 1.144.0.

Run all commands from the folder that contains this `README.md`. The commands are the same on macOS and Linux, but they were tested only on Windows.

## 1. Install Miniconda or Anaconda

> Skip this step if conda is already installed on your machine.

Download the installer from the [Anaconda download page](https://www.anaconda.com/download/success?reg=skipped-miniconda), then follow the installation steps.

## 2. Create a new Conda environment

Open Anaconda Prompt (Windows) or a terminal (macOS and Linux) and go to the folder that contains this `README.md`. Then run:

```bash
conda create --name dsa5205_group3 python=3.12 --yes
conda activate dsa5205_group3
python -m pip install -r requirements.txt
```

## 3. Download the data

To download data of the four stocks, run:

```bash
python download_data.py
```

> Yahoo revises historical prices, so a new download can produce results that differ from the report.

## 4. Prepare the data

To clean the downloaded data and build the features, run:

```bash
python prepare_data.py
python build_features.py
```

## 5. Run the notebook

Open `modelling_validation.ipynb` in Visual Studio Code with the Jupyter and Python extensions (both by Microsoft) installed, select the `dsa5205_group3` environment as the kernel, and click **Run All**.

All model settings are in the `CONFIG` dictionary in the first code cell. No step is random (the cross-validation folds follow time order, and every estimator is deterministic), so no random seed is needed. All paths are relative to this folder.

After the modelling and forecast accuracy evaluation, the notebook
exports the selected LASSO forecasts to:

`data/prepared/forecasts.csv`

The notebook then runs `evaluation.py` to perform trading parameter
selection and out-of-sample backtesting.

The trading evaluation can also be rerun independently without
retraining the models:

```bash
python evaluation.py
```

The trading parameters are selected using the 2012–2017 validation
period and kept fixed for the 2018–2025 test period.

## 6. Expected outputs

**Data scripts**

| Script | Output file | Rows |
|---|---|---:|
| `prepare_data.py` | `data/prepared/clean_prices.csv` | 18,860 |
| `prepare_data.py` | `data/prepared/stock_targets.csv` | 15,080 |
| `build_features.py` | `data/prepared/model_data.csv` | 15,000 |
| `build_features.py` | `data/prepared/train.csv`, `validation.csv`, `test.csv` | 7,960, 3,020, 4,004 |

<br>

**Modelling and validation notebook**

| Output | Contents |
|---|---|
| Validation table (displayed) | $R^2$ against zero and against the historical mean for every model, window length $L$, and refit interval $R$ (24 rows) over the validation period. |
| `CHOSEN` cell | Each model's $L$ and $R$, set from the validation table |
| Test table (displayed) | $R^2$ of each model at its chosen setting over the test period. |
| $R^2$-by-year table (displayed) | Test-period $R^2$ against zero by calendar year |
| `results/test_r2_by_year.png` | Bar chart of the $R^2$-by-year table |

<br>

**Trading and evaluation scripts**

| Output | Contents |
|---|---|
| `data/prepared/forecasts.csv` | Selected LASSO forecasts used for trading |
| `results/validation_grid.csv` | Validation results for 12 trading parameter combinations |
| `results/performance.csv` | Annualized return, volatility, Sharpe ratio, maximum drawdown, and cumulative return |
| `results/validation_daily.csv` | Validation-period daily backtest results |
| `results/test_daily.csv` | Test-period daily backtest results |
| `results/validation_weights.csv` | Validation-period portfolio weights |
| `results/test_weights.csv` | Test-period portfolio weights |
| `results/validation_cumulative.png` | Validation cumulative wealth comparison with SPY |
| `results/test_cumulative.png` | Test cumulative wealth comparison with SPY |