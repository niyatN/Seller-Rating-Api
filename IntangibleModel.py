import pandas as pd
from sklearn.externals import joblib


df = pd.read_csv('datasetIntangible.csv')
df.head(9)
from sklearn.ensemble import RandomForestClassifier
X = df[['User_given_rating','Genuineness','Willingness']].values
y = df['Seller_rating'].values
rfc = RandomForestClassifier(n_estimators=100)
rfc.fit(X, y)

joblib.dump(rfc, 'IntangibleModel.pkl') 
