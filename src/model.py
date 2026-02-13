from sklearn.linear_model import LinearRegression, Ridge
from sklearn.ensemble import RandomForestRegressor

def get_model():
    # Experiment 1: Linear Regression
    # return LinearRegression()

    # Experiment 2: Ridge Regression
    # return Ridge(alpha=1.0)

    # Example 3: Random Forest
    # return RandomForestRegressor(
    #     n_estimators=50,
    #     max_depth=10,
    #     random_state=42
    # )

    # Example 4: Random Forest
    return RandomForestRegressor(
        n_estimators=100,
        max_depth=15,
        random_state=42
    )

