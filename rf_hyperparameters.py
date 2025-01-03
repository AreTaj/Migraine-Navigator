""" Hyperparameter tuning using GridSearchCV """

from rf_model import X_train_reg, y_train_reg, reg
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV

# Define the parameter grid
param_grid = {
    'n_estimators': [100, 200, 300],
    'max_depth': [None, 10, 20, 30],
    'min_samples_split': [2, 5, 10],
    'min_samples_leaf': [1, 2, 4],
    'bootstrap': [True, False]
}

# Initialize GridSearchCV
grid_search = GridSearchCV(estimator=reg, param_grid=param_grid, cv=3, n_jobs=-1, verbose=2)
# Fit the model
grid_search.fit(X_train_reg, y_train_reg)
# Get the best parameters
best_params = grid_search.best_params_
print(f"Best parameters: {best_params}")

""" 
Best parameters: {
    'bootstrap': True,
    'max_depth': 30, 
    'min_samples_leaf': 1, 
    'min_samples_split': 2, 
    'n_estimators': 200
    }
"""