import pandas as pd
import numpy as np
import pandas as pd
import random
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.neural_network import MLPRegressor
from sklearn.model_selection import train_test_split, cross_val_score, LeaveOneOut
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_squared_error, r2_score

original_df = pd.read_csv(r'C:\Users\Austin\Downloads\Capstone\Model Data\Merge2\FinalD\Ams_tot3.csv')
Rot = pd.read_csv(r'C:\Users\Austin\Downloads\Capstone\Model Data\Merge2\FinalD\Rot_tot3.csv')

def select_random_rows(df, n):
    selected_rows = pd.DataFrame(columns=df.columns)
    num_rows = len(df)
    for i in range(0, num_rows, n):
        random_row_index = random.randint(i, min(i+n-1, num_rows-1))
        selected_rows = selected_rows.append(df.iloc[random_row_index])
    return selected_rows

# Example usage
# Assuming you have an existing DataFrame named 'original_df'
# You can replace 'original_df' with your actual DataFrame

train_df = select_random_rows(original_df, 12)
validation_df = select_random_rows(Rot, 10)


X_train = train_df.drop('NO2', axis=1)  # Update 'target_variable_column' with the actual column name
X_train = X_train.drop('Datetime', axis=1)
X_train = X_train.drop('Traffic', axis=1)
#X_train = X_train.drop('T_alt', axis=1)
#X_train = X_train.drop('Hour', axis=1)
#X_train = X_train.drop('Road', axis=1)

y_train = train_df['NO2']

# Separate the features (X) and the target variable (y) for validation data
X_val = validation_df.drop('NO2', axis=1)
X_val = X_val.drop('Datetime', axis=1)# Update 'target_variable_column' with the actual column name
X_val = X_val.drop('Traffic', axis=1)
#X_val = X_val.drop('T_alt', axis=1)
#X_val = X_val.drop('Hour', axis=1)
#X_val = X_val.drop('Road', axis=1)
y_val = validation_df['NO2']

# Scale the features to improve the training process
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)

# Create an MLPRegressor object with desired parameters
mlp = MLPRegressor(hidden_layer_sizes=(5,3), activation='relu', solver='adam', alpha=0.001,
                   max_iter=10000, random_state=42)

# Train the model using the training data
mlp.fit(X_train_scaled, y_train)

# Make predictions on the validation set
y_pred = mlp.predict(X_val_scaled)

# Evaluate the model on the validation set
mse = mean_squared_error(y_val, y_pred)
r2 = r2_score(y_val, y_pred)
print(f"Mean Squared Error: {mse}")
print(f"R^2 Score: {r2}")

plt.scatter(y_val, y_pred, color='black')
plt.plot([min(y_val), max(y_val)], [min(y_val), max(y_val)], 'b--', lw=2)  # Plot the ideal line (y = x)
plt.xlabel('Actual Labels')
plt.ylabel('Predicted Values')
plt.title('Rotterdam -> Den Haag')
plt.show()
