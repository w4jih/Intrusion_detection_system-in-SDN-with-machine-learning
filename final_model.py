import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import joblib
import glob
"""
# Load multiple CSV files from a directory
csv_files = glob.glob('/home/wajih/Downloads/ids/*.csv')  # Update with your dataset path

# Load and concatenate all datasets
dataframes = []
for file in csv_files:
    df = pd.read_csv(file)
    df.columns = df.columns.str.strip()  # Clean column names
    dataframes.append(df)
data = pd.concat(dataframes, ignore_index=True)
"""
# Step 1: Load the dataset with ', ' as the delimiter
file_path = '/home/wajih/Downloads/data/modified_dataset.csv'  # Replace with your dataset file
data = pd.read_csv(file_path, delimiter=',')  # Specify delimiter
# Features and Labels
features = ['Flow Duration', 'Total Fwd Packets', 'Flow Bytes/s', 
            'Fwd Packet Length Mean', 'Bwd Packet Length Std']
X = data[features]
y = data['Class']  # Ensure this column exists in all datasets

# Replace infinite and NaN values in features
X = X.replace([float('inf'), float('-inf')], float('nan'))  # Replace infinite values
X = X.fillna(0)  # Replace NaN with 0

# Check for NaN or infinite values in labels
if y.isnull().any():
    print("Warning: Labels contain NaN values. Dropping such rows.")
    valid_indices = y.notnull()
    X = X[valid_indices]
    y = y[valid_indices]

# Preprocessing (Scaling features)
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split data into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# Train a Random Forest Classifier
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate the model
y_pred = model.predict(X_test)
print("Model Accuracy:", accuracy_score(y_test, y_pred))

# Save the model and scaler
joblib.dump(model, 'flow_model.pkl')
joblib.dump(scaler, 'scaler.pkl')

# Predict for unlabeled data
unlabeled_data = pd.read_csv('/home/wajih/Downloads/ids/flow_metrics.csv')

# Preprocess unlabeled data
X_unlabeled = unlabeled_data[features]
X_unlabeled = X_unlabeled.replace([float('inf'), float('-inf')], float('nan')).fillna(0)
X_unlabeled_scaled = scaler.transform(X_unlabeled)

# Predict classes
predictions = model.predict(X_unlabeled_scaled)

# Save predictions
unlabeled_data['Predicted Class'] = predictions
unlabeled_data.to_csv('predicted_dataset.csv', index=False)

print("Predictions saved to 'predicted_dataset.csv'")