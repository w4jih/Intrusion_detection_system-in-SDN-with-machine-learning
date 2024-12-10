import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
import joblib

# Step 1: Load the labeled dataset
file_path = '/home/wajih/Downloads/data/modified_dataset.csv'  # Update with your dataset path
data = pd.read_csv(file_path)

# Step 2: Define Features and Labels
features = ['Flow Duration', 'Total Fwd Packets', 'Flow Bytes/s', 
            'Fwd Packet Length Mean', 'Bwd Packet Length Std']
X = data[features]
y = data['Class']  # Ensure the 'Class' column exists in the dataset

# Replace infinite and NaN values in features
X = X.replace([float('inf'), float('-inf')], float('nan')).fillna(0)

# Check for NaN in labels and clean data
if y.isnull().any():
    print("Warning: Labels contain NaN values. Dropping such rows.")
    valid_indices = y.notnull()
    X = X[valid_indices]
    y = y[valid_indices]

# Step 3: Preprocess the Features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Step 4: Split the data
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# Step 5: Train the Model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate the Model
y_pred = model.predict(X_test)
print("Model Accuracy:", accuracy_score(y_test, y_pred))

# Step 6: Save the Model, Scaler, and Training Data
joblib.dump(model, 'flow_model.pkl')
joblib.dump(scaler, 'scaler.pkl')


