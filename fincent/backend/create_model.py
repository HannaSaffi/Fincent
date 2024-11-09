# create_model.py
import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

# Generate or load some example data for the model
# Here, let's use some random data as an example
data = {
    "day": list(range(1, 101)),
    "price": [100 + i * 0.5 + (i % 5) for i in range(1, 101)]  # Just a simple increasing trend
}
df = pd.DataFrame(data)

# Prepare data for model training
X = df[['day']]  # Days
y = df['price']   # Prices

# Train a simple linear regression model
model = LinearRegression()
model.fit(X, y)

# Save the model to a .pkl file using joblib
joblib.dump(model, 'stock_price_model.pkl')
