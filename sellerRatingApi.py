from flask import Flask, request,jsonify
from flask_restful import Resource, Api
import pandas as pd
from pymongo import *
import bson	
import csv
from sklearn.externals import joblib
import pickle
app = Flask(__name__)
api = Api(app)



# Connection with MonogoDB
client = MongoClient(port= 27017)
db = client.PayPal
	


# Random Forest Classifire to find Seller Rating
def ratingTangible(category,userGivenRating,Delivery,Originality,Willingness):
	if(category==1):
		rfc = joblib.load('TangibleModel.pkl')
		return rfc.predict([[userGivenRating,Delivery,Originality,Willingness]])[0]
def ratingInangible(category,userGivenRating,genuineness,Willingness):
	if(category==2):
		rfc = joblib.load('IntangibleModel.pkl')
		return rfc.predict([[userGivenRating,genuineness,Willingness]])[0]

class Seller_NewRating(Resource):
	def post(self):
		# Geting UserScore And SellerId
		data = request.json
		print(data['seller_id'])
		
		if not all([data.get('category'), data.get('seller_id'), data.get('User_given_rating')]):
			error = {'Error': 'Missing Fields category or seller id or userGivenRating'}
			return jsonify(error)
	
		category = data['category']
		seller_id = data['seller_id']
		print(category, seller_id)
		#seller data retrival
		sellerData = db.SellerRating.find_one({"seller_id":seller_id})
		#print(sellerData)
		# total number of rating for each tangible category
		tr_automobiles = sellerData['tr_automobiles']
		tr_daily_needs= sellerData['tr_daily_needs']
		tr_electronics = sellerData['tr_electronics']
		tr_clothes = sellerData['tr_clothes']
		tr_ticket = sellerData['tr_ticket']
		tr_education = sellerData['tr_education']
		tr_entertainment = sellerData['tr_entertainment']

		r_automobiles = sellerData['r_automobiles']
		r_daily_needs= sellerData['r_daily_needs']
		r_electronics = sellerData['r_electronics']
		r_clothes = sellerData['r_clothes']
		r_ticket = sellerData['r_ticket']
		r_education = sellerData['r_education']
		r_entertainment = sellerData['r_entertainment']
		print(data)


		# For intangible items
		if(category == 'ticket' or category =='education' or category=='entertainment'):
			if not all([data.get("Willingness"),data.get("Genuineness")]):
				error = {'Error': 'Missing fields in intangible category'}
				return jsonify(error)
			if(data['ticket_bs']==-1 or data['education_bs']==-1 or data['entertainment_bs']==-1):
				error = {'Error': 'Missing buyer score'}
				return jsonify(error)

			User_given_rating = data["User_given_rating"]
			Willingness = data["Willingness"]
			Genuineness = data["Genuineness"]

			SysRate = ratingInangible(2,User_given_rating, Willingness, Genuineness)
			Overall = float(SysRate)/4
			print('\n','===================================================================')
			print("\tSystem Calculated seller Rating:",Overall)
			print('===================================================================','\n')

			if(category =='ticket'):
				BuyerScore = data['ticket_bs']
				total = tr_ticket
				sellerRating = (sellerData['r_ticket'] * total+ Overall)/(total+1)
				newSellerData = {
					"seller_id":seller_id,
					"tr_clothes":tr_clothes,
					"tr_automobiles":tr_automobiles,
					"tr_daily_needs":tr_daily_needs,
					"tr_electronics":tr_electronics,

					"tr_ticket":tr_ticket+1,
					"tr_education":tr_education,
					"tr_entertainment":tr_entertainment,

					"r_automobiles":r_automobiles,
					"r_electronics":r_electronics,
					"r_clothes":r_clothes,
					"r_daily_needs":r_daily_needs,

					"r_ticket":sellerRating,
					"r_education":r_education,
					"r_entertainment":r_entertainment


				}

			elif(category =='entertainment'):
				BuyerScore = data['entertainment_bs']
				total = tr_ticket
				sellerRating = (sellerData['r_entertainment'] * total+ Overall)/(total+1)
				newSellerData = {
					"seller_id":seller_id,
					"tr_clothes":tr_clothes,
					"tr_automobiles":tr_automobiles,
					"tr_daily_needs":tr_daily_needs,
					"tr_electronics":tr_electronics,

					"tr_ticket":tr_ticket,
					"tr_education":tr_education,
					"tr_entertainment":tr_entertainment+1,

					"r_automobiles":r_automobiles,
					"r_electronics":r_electronics,
					"r_clothes":r_clothes,
					"r_daily_needs":r_daily_needs,

					"r_ticket":r_ticket,
					"r_education":r_education,
					"r_entertainment":sellerRating


				}
			elif(category =='education'):
				BuyerScore = data['education_bs']
				total = tr_ticket
				sellerRating = (sellerData['r_education'] * total+ Overall)/(total+1)
				newSellerData = {
					"seller_id":seller_id,
					"tr_clothes":tr_clothes,
					"tr_automobiles":tr_automobiles,
					"tr_daily_needs":tr_daily_needs,
					"tr_electronics":tr_electronics,

					"tr_ticket":tr_ticket,
					"tr_education":tr_education+1,
					"tr_entertainment":tr_entertainment,

					"r_automobiles":r_automobiles,
					"r_electronics":r_electronics,
					"r_clothes":r_clothes,
					"r_daily_needs":r_daily_needs,

					"r_ticket":r_ticket,
					"r_education":sellerRating,
					"r_entertainment":r_entertainment


				}
			if(data['education_bs']>70 and data['ticket_bs']>70 and data['entertainment_bs']>70):
				fields=[data['User_given_rating'], data['Genuineness'],data['Willingness'],data['User_given_rating']*4]
				with open(r'datasetIntangible.csv', 'a') as file:
				    writer = csv.writer(file)
				    writer.writerow(fields)
				    print("#### New Row is appeneded in Intangible dataset####")

			


			db.SellerRating.update({'seller_id':seller_id},{'$set':newSellerData},False)
			print('\n','===================================================================')
			print("Seller Updated data: ",newSellerData)
			print('===================================================================','\n')
			#return(jsonify(newSellerData))


		#For tangible items
		elif(category == 'automobiles' or category=='daily_needs' or category=='electronics' or category=='clothes'):
			if not all([ data.get('Delivery_on_time'),data.get("Willingness"), data.get('Originality_of_Product')]):
				error = {'Error':'Missing Fields in tangible category'}
				return jsonify(error)
			if(data['automobiles_bs']==-1 or data['daily_needs_bs']==-1 or data['electronics_bs']==-1 or data['clothes_bs']==-1):
				error = {'Error': 'Missing buyer score'}
				return jsonify(error)

 
			print("\n",sellerData,"\n")

			# Rating
			User_given_rating = data['User_given_rating']
			Delivery_on_time = data['Delivery_on_time']
			Originality_of_Product =data['Originality_of_Product']
			Willingness = data['Willingness']

			SysRate = ratingTangible(1,User_given_rating, Delivery_on_time, Originality_of_Product, Willingness)
			
			Overall = float(SysRate)/4
			print('\n','===================================================================')
			print("\tSystem Calculated seller Rating:",Overall)
			print('===================================================================','\n')
			if(category =='automobiles'):
				BuyerScore = data['automobiles_bs']
				total = tr_automobiles
				sellerRating = (sellerData['r_automobiles'] * total+ Overall)/(total+1)
				newSellerData = {
					"seller_id":seller_id,
					"tr_clothes":tr_clothes,
					"tr_automobiles":tr_automobiles+1,
					"tr_daily_needs":tr_daily_needs,
					"tr_electronics":tr_electronics,

					"tr_ticket":tr_ticket,
					"tr_education":tr_education,
					"tr_entertainment":tr_entertainment,

					"r_automobiles":sellerRating,
					"r_electronics":r_electronics,
					"r_clothes":r_clothes,
					"r_daily_needs":r_daily_needs,

					"r_ticket":r_ticket,
					"r_education":r_education,
					"r_entertainment":r_entertainment


				}



			elif(category=='daily_needs'):
				BuyerScore = data['daily_needs_bs']
				total = tr_daily_needs
				sellerRating = (sellerData['r_daily_needs'] *total + Overall)/(total+1)

				newSellerData ={
					"seller_id":seller_id,
					"tr_clothes":tr_clothes,
					"tr_automobiles":tr_automobiles,
					"tr_daily_needs":tr_daily_needs+1,
					"tr_electronics":tr_electronics,

					"tr_ticket":tr_ticket,
					"tr_education":tr_education,
					"tr_entertainment":tr_entertainment,

					"r_automobiles":r_automobiles,
					"r_electronics":r_electronics,
					"r_clothes":r_clothes,
					"r_daily_needs":sellerRating,

					"r_ticket":r_ticket,
					"r_education":r_education,
					"r_entertainment":r_entertainment


				}

			elif(category=='electronics'):
				BuyerScore = data['electronics_bs']
				total = tr_electronics
				sellerRating = (sellerData['r_electronics']* total+Overall)/(total+1)
				newSellerData ={
					"seller_id":seller_id,
					"tr_clothes":tr_clothes,
					"tr_automobiles":tr_automobiles,
					"tr_daily_needs":tr_daily_needs,
					"tr_electronics":tr_electronics+1,

					"tr_ticket":tr_ticket,
					"tr_education":tr_education,
					"tr_entertainment":tr_entertainment,

					"r_automobiles":r_automobiles,
					"r_electronics":sellerRating,
					"r_clothes":r_clothes,
					"r_daily_needs":r_daily_needs,

					"r_ticket":r_ticket,
					"r_education":r_education,
					"r_entertainment":r_entertainment


				}

			elif(category=='clothes'):
				BuyerScore = data['clothes_bs']
				total = tr_clothes
				sellerRating = (sellerData['r_clothes'] * total+Overall)/(total+1)
				newSellerData ={
				
					"seller_id":seller_id,
					"tr_clothes":tr_clothes+1,
					"tr_automobiles":tr_automobiles,
					"tr_daily_needs":tr_daily_needs,
					"tr_electronics":tr_electronics,

					"tr_ticket":tr_ticket,
					"tr_education":tr_education,
					"tr_entertainment":tr_entertainment,

					"r_automobiles":r_automobiles,
					"r_electronics":r_electronics,
					"r_clothes":sellerRating,
					"r_daily_needs":r_daily_needs,

					"r_ticket":r_ticket,
					"r_education":r_education,
					"r_entertainment":r_entertainment
					
				}

			if(data['daily_needs_bs']>70 and data['clothes_bs']>70 and data['automobiles_bs']>70 and data['electronics_bs']>70):
				fields=[data['User_given_rating'], data['Delivery_on_time'],data['Originality_of_Product'],data['Willingness'],data['User_given_rating']*4]
				with open(r'datasetTangible.csv', 'a') as f:
				    writer = csv.writer(f)
				    writer.writerow(fields)
				    print("#### New Row is appeneded in Tangible dataset ####")
			db.SellerRating.update({'seller_id':seller_id},{'$set':newSellerData},False)
			print('\n','===================================================================')
			print("Seller Updated data: ",newSellerData)
			print('===================================================================','\n')
			#return(jsonify(newSellerData))

		return(jsonify(newSellerData)) 

api.add_resource(Seller_NewRating,'/NewRating')


if __name__ == "__main__":
	app.run(debug=True)