# -*- coding: utf-8 -*-
"""Tanh_IoHT.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1olrxJVm6u5OAgbDGcQSISIx4myuMtDEE
"""

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import SimpleRNN, Dense
import pandas as pd
import numpy as np
from sklearn.preprocessing import MinMaxScaler

#Load training and test files
train_data = pd.read_csv("/content/540-ws-training_processed.csv")
test_data = pd.read_csv("/content/540-ws-testing_processed.csv")
gen_data = pd.read_csv("/content/544-ws-testing_processed.csv")


# Show data preview
print("Training data :")
print(train_data.head())
print("\ntest data :")
print(test_data.head())
print("\nGeneralization data :")
print(gen_data.head())

train_data= train_data[['5minute_intervals_timestamp','cbg']]
test_data= test_data[['5minute_intervals_timestamp','cbg']]
gen_data= gen_data[['5minute_intervals_timestamp','cbg']]
print("Training data :")
print(train_data.head())
print("\nTest Data :")
print(test_data.head())
print("\nGeneralization data :")
print(gen_data.head())

print(train_data.isnull().sum())
print(test_data.isnull().sum())
print(gen_data.isnull().sum())

train_data = train_data.dropna()
test_data = test_data.dropna()
gen_data = gen_data.dropna()

scaler = MinMaxScaler()

# Normalize glucose levels in both sets
train_data["cbg"] = scaler.fit_transform(train_data[["cbg"]])
test_data["cbg"] = scaler.transform(test_data[["cbg"]])
gen_data["cbg"] = scaler.transform(gen_data[["cbg"]])

def create_sequences(data, sequence_length):
    X, y = [], []
    for i in range(len(data) - sequence_length):
        X.append(data[i:i + sequence_length])
        y.append(data[i + sequence_length])
    return np.array(X), np.array(y)

sequence_length = 10

# Create the sequences for training
X_train, y_train = create_sequences(train_data["cbg"].values, sequence_length)

# Create the sequences for the test
X_test, y_test = create_sequences(test_data["cbg"].values, sequence_length)

# Create the sequences for generalization
X_gen, y_gen = create_sequences(gen_data["cbg"].values, sequence_length)

# Reshape the data
X_train = X_train.reshape((X_train.shape[0], X_train.shape[1], 1))
X_test = X_test.reshape((X_test.shape[0], X_test.shape[1], 1))
X_gen = X_gen.reshape((X_gen.shape[0], X_gen.shape[1], 1))

print(f"Shape of training data : {X_train.shape}")
print(f"Shape of test data {X_test.shape}")
print(f"Shape of generalization data : {X_gen.shape}")

print("train data   :")
print(train_data.head())
print("\nTest data :")
print(test_data.head())
print("\n generalisation data :")
print(gen_data.head())

model = Sequential([
    SimpleRNN(5, activation='tanh', input_shape=(X_train.shape[1], X_train.shape[2])),
    Dense(1)  # A single output: prediction of the glucose level
])

# Compile the model
model.compile(optimizer='adam', loss='mse', metrics=['mae'])

# Print a summary of the model
model.summary()

history = model.fit(
    X_train, y_train,
    validation_data=(X_test, y_test),
    epochs=20,
    batch_size=32,
    verbose=1
)

loss, mae = model.evaluate(X_test, y_test)
print(f"Mean Absolute Error on test data: {mae}")

loss1, mae1 = model.evaluate(X_gen, y_gen)
print(f"Mean Absolute Error on data generalisation : {mae1}")

import matplotlib.pyplot as plt
import numpy as np

# Plot the loss curves during training
plt.figure(figsize=(10, 5))
plt.plot(history.history['loss'], label='Training Loss')
plt.plot(history.history['val_loss'], label='Validation Loss')
plt.title('Loss Curve')
plt.xlabel('Epochs')
plt.ylabel('MSE (Mean Squared Error)')
plt.legend()
plt.show()

# Plot the MAE (Mean Absolute Error) curves during training
plt.figure(figsize=(10, 5))
plt.plot(history.history['mae'], label='Training MAE')
plt.plot(history.history['val_mae'], label='Validation MAE')
plt.title('Mean Absolute Error Curve')
plt.xlabel('Epochs')
plt.ylabel('MAE')
plt.legend()
plt.show()

# Compare the actual and predicted values on the test data with adjusted scale
y_test_pred = model.predict(X_test)

plt.figure(figsize=(10, 5))
plt.plot(y_test, label='Actual Values - Test')
plt.plot(y_test_pred, label='Predicted Values - Test')
plt.ylim(min(y_test) * 0.95, max(y_test) * 1.05)  # Adjust the Y-scale to zoom in
plt.title('Comparison of Actual and Predicted Values (Test)')
plt.xlabel('Examples')
plt.ylabel('Glucose Level')
plt.legend()
plt.show()

# Compare the actual and predicted values on the generalization data with adjusted scale
y_gen_pred = model.predict(X_gen)

plt.figure(figsize=(10, 5))
plt.plot(y_gen, label='Actual Values - Generalization')
plt.plot(y_gen_pred, label='Predicted Values - Generalization')
plt.ylim(min(y_gen) * 0.95, max(y_gen) * 1.05)  # Adjust the Y-scale to zoom in
plt.title('Comparison of Actual and Predicted Values (Generalization)')
plt.xlabel('Examples')
plt.ylabel('Glucose Level')
plt.legend()
plt.show()

# Save model weights
model.save_weights('/content/rnn_weights.weights.h5')
print("Saved model weights.")

from sklearn.metrics import mean_absolute_error, mean_squared_error
import numpy as np

def evaluate_future_predictions(model, X_test, y_test, steps=6, num_samples=40):
    """
    Tests the model on a subset of num_samples sequences and predicts blood glucose levels over 30 minutes.

    :param model: The trained RNN model.
    :param X_test: Test sequences (shape: nb_samples, sequence_length, 1).
    :param y_test: True test values corresponding to the sequences.
    :param steps: Number of prediction steps (6 * 5 min = 30 min).
    :param num_samples: Number of samples to test (default: 20).
    :return: List of predictions and evaluation metrics.
    """
    # Randomly select 20 indices from X_test
    indices = np.random.choice(len(X_test), num_samples, replace=False)

    all_predictions = []
    true_values = []  # Stores true values at 30 min

    for i in indices:
        current_sequence = X_test[i].reshape(1, sequence_length, 1)  # Reshape for model input
        future_predictions = []  # Stores the next 6 predictions

        for _ in range(steps):
            next_glucose = model.predict(current_sequence, verbose=0)[0, 0]  # Single prediction
            future_predictions.append(next_glucose)

            # Update the input sequence
            current_sequence = np.roll(current_sequence, -1, axis=1)  # Shift to the left
            current_sequence[0, -1, 0] = next_glucose  # Add the new value

        all_predictions.append(future_predictions[-1])  # Last prediction = 30 min
        true_values.append(y_test[i + steps - 1])  # True value after 30 min

    # Convert to numpy arrays
    all_predictions = np.array(all_predictions)
    true_values = np.array(true_values)

    # Compute evaluation metrics
    mae = mean_absolute_error(true_values, all_predictions)
    mse = mean_squared_error(true_values, all_predictions)

    return all_predictions, true_values, mae, mse

# Run evaluation on 20 test sequences
predictions_30min, true_30min, mae, mse = evaluate_future_predictions(model, X_test, y_test)

# Display results
print(f"Mean Absolute Error (MAE) after 30 minutes: {mae:.4f}")
print(f"Mean Squared Error (MSE) after 30 minutes: {mse:.4f}")

# Example of displaying 5 predictions compared to true values
for i in range(5):
    print(f"True value after 30 min: {true_30min[i]:.2f} | Prediction: {predictions_30min[i]:.2f}")

import matplotlib.pyplot as plt

def plot_predictions(true_values, predicted_values):
    """
    Displays a graph comparing the true values and the model's predictions after 30 minutes.

    :param true_values: True glucose values after 30 minutes.
    :param predicted_values: Model predictions after 30 minutes.
    """
    plt.figure(figsize=(8, 5))

    # Plot true values and predictions
    plt.plot(true_values, label="True Values", marker='o', linestyle='dashed')
    plt.plot(predicted_values, label="Model Prediction", marker='x', linestyle='dashed')

    # Add labels and a title
    plt.xlabel("Test sequence (samples)")
    plt.ylabel("Glucose after 30 min (mg/dL)")
    plt.title("Comparison of True Values vs Predictions After 30 Minutes")
    plt.legend()
    plt.grid(True)

    # Show the plot
    plt.show()

# Display results
plot_predictions(true_30min, predictions_30min)

import tensorflow as tf

# Rebuild the model with the same architecture
sequence_length = 5  # Sequence length used
model = tf.keras.Sequential([
    tf.keras.layers.SimpleRNN(5, activation='tanh', input_shape=(sequence_length, 1)),
    tf.keras.layers.Dense(1)
])

# Load the saved weights
model.load_weights("/content/rnn_weights.weights.h5")

rnn_kernel, rnn_recurrent_kernel, rnn_bias = model.layers[0].get_weights()
dense_weights, dense_bias = model.layers[1].get_weights()

# Display weight details
print("=== RNN Layer Weights ===")
print(f"RNN Kernel (Input Weights) - Shape: {rnn_kernel.shape}\n{rnn_kernel}")
print(f"RNN Recurrent Kernel (Recurrent Weights) - Shape: {rnn_recurrent_kernel.shape}\n{rnn_recurrent_kernel}")
print(f"RNN Bias - Shape: {rnn_bias.shape}\n{rnn_bias}")

print("\n=== Dense Layer Weights ===")
print(f"Dense Weights (Output Weights) - Shape: {dense_weights.shape}\n{dense_weights}")
print(f"Dense Bias - Shape: {dense_bias.shape}\n{dense_bias}")

import tenseal as ts
import numpy as np
import tensorflow as tf

# Function to approximate tanh(x) with a degree-3 polynomial
def tanh_approximation_homomorphic(encrypted_x):
    """
    Homomorphic approximation of tanh(x): tanh(x) ≈ 0.7616x - 0.0591x^3
    """
    factor1 = 0.7616 / 2**4  # Scale reduction for the constant
    factor2 = -0.0591 / 2**4  # Scale reduction for the constant
    term1 = encrypted_x.mul(factor1)  # 0.7616 * x
    encrypted_x2 = encrypted_x.mul(encrypted_x)  # x^2
    encrypted_x3 = encrypted_x2.mul(encrypted_x)  # x^3
    term2 = encrypted_x3.mul(factor2)  # -0.0591 * x^3

    result = term1.add(term2)  # Approximation of tanh(x)
    return result

# Add bootstrapping if needed
def bootstrap_if_needed(ciphertext):
    """
    Applies bootstrapping to reduce noise if needed.
    """
    if hasattr(ciphertext, "bootstrap"):
        print("Bootstrapping applied to reduce noise.")
        return ciphertext.bootstrap()
    return ciphertext  # If bootstrapping is not available, return the original ciphertext

def create_context():
    poly_mod_degree = 32768  # Increased polynomial size for more capacity
    coeff_mod_bit_sizes = [60, 50, 50, 50, 60]  # Adjusted modulus chain
    context = ts.context(ts.SCHEME_TYPE.CKKS, poly_mod_degree, coeff_mod_bit_sizes)
    context.global_scale = 2**6  # Higher initial scale
    context.generate_galois_keys()
    return context

# Load model parameters
def load_model_parameters():
    """
    Loads the RNN model parameters from saved files.
    """
    sequence_length = 5
    model = tf.keras.Sequential([
        tf.keras.layers.SimpleRNN(5, activation='tanh', input_shape=(sequence_length, 1)),
        tf.keras.layers.Dense(1)
    ])
    model.load_weights("/content/rnn_weights.weights.h5")
    rnn_kernel, rnn_recurrent_kernel, rnn_bias = model.layers[0].get_weights()
    dense_weights, dense_bias = model.layers[1].get_weights()
    return rnn_kernel, rnn_recurrent_kernel, rnn_bias, dense_weights, dense_bias

# Normalize a sequence
def normalize_sequence(sequence):
    """
    Normalizes a sequence based on its min and max values.
    """
    sequence = np.array(sequence, dtype=np.float32)
    min_val = sequence.min()
    max_val = sequence.max()
    normalized_sequence = (sequence - min_val) / (max_val - min_val)
    return normalized_sequence, min_val, max_val

# Homomorphic inference on a sequence
def inference_homomorphic(context, rnn_kernel, rnn_recurrent_kernel, rnn_bias, dense_weights, dense_bias, sequence):
    """
    Performs homomorphic inference on an input sequence.
    """
    h_t = ts.ckks_vector(context, np.zeros(5))  # Initialize hidden state
    for t in range(5):
        x_t = ts.ckks_vector(context, [sequence[t]])  # Load input at time t

        # Homomorphic computation: z_t = W_h * x_t + U_h * h_t + b_h
        z_t = x_t.matmul(rnn_kernel)  # W_h * x_t
        z_t = z_t.add(h_t.matmul(rnn_recurrent_kernel))  # + U_h * h_t
        z_t = z_t.add(rnn_bias)  # + b_h

        # Reduce noise via bootstrapping if needed
        z_t = bootstrap_if_needed(z_t)

        # Approximate tanh(z_t) to obtain h_t
        h_t = tanh_approximation_homomorphic(z_t)

        # Reduce noise after each iteration
        h_t = bootstrap_if_needed(h_t)

    # Compute final output: y = Dense(h_t)
    y_t = h_t.matmul(dense_weights).add(dense_bias)

    # Final bootstrapping
    y_t = bootstrap_if_needed(y_t)

    return y_t

# Main program
def main():
    # Create encryption context
    context = create_context()

    # Load model parameters
    rnn_kernel, rnn_recurrent_kernel, rnn_bias, dense_weights, dense_bias = load_model_parameters()

    # Initialize input sequence
    raw_sequence = [254, 250, 249, 247, 242]

    # Normalize the sequence
    normalized_sequence, min_val, max_val = normalize_sequence(raw_sequence)
    print("Normalized sequence:", normalized_sequence)

    # Perform homomorphic inference
    encrypted_output = inference_homomorphic(
        context, rnn_kernel, rnn_recurrent_kernel, rnn_bias, dense_weights, dense_bias, normalized_sequence
    )

    # Decrypt to verify results
    decrypted_output = encrypted_output.decrypt()

    # Denormalize the output
    denormalized_output = np.array(decrypted_output) * (max_val - min_val) + min_val
    print("Denormalized result:", denormalized_output)

if __name__ == "__main__":
    main()