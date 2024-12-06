import pandas as pd

# File paths
input_file = '/home/wajih/Downloads/data/Friday-WorkingHours-Afternoon-DDos.pcap_ISCX.csv'
output_file = 'dataset8.csv'

# Step 1: Normalize the separators in the file
with open(input_file, 'r') as file:
    content = file.read()

# Replace ', ' with ',' to normalize the separators
content = content.replace(', ', ',')

# Save the normalized content to a temporary file
temp_file = 'normalized_temp.csv'
with open(temp_file, 'w') as file:
    file.write(content)

# Step 2: Load the normalized dataset
data = pd.read_csv(temp_file)
print("Columns in the dataset:", data.columns)

# Step 3: Replace all non-BENIGN values in the 'Class' column with 'MALICIOUS'
data['Class'] = data['Class'].apply(lambda x: 'BENIGN' if x == 'BENIGN' else 'MALICIOUS')

# Step 4: Save the modified dataset
data.to_csv(output_file, index=False)
print(f"Modified dataset saved to {output_file}")

# Step 5: Verify the changes
print("Value counts for 'Class':\n", data['Class'].value_counts())