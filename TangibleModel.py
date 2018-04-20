import pandas as pd
from sklearn.externals import joblib

df = pd.read_csv('datasetTangible.csv')
from sklearn.ensemble import RandomForestClassifier
X = df[['User_given_rating','Delivery_on_time','Originality_of_Product','Willingness']].values
y = df['Seller_rating'].values
rfc = RandomForestClassifier(n_estimators=100)
rfc.fit(X, y)

joblib.dump(rfc, 'TangibleModel.pkl') 
