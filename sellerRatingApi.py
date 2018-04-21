from flask import Flask, request,jsonify
from flask_restful import Resource, Api
import pandas as pd
from pymongo import *
import bson	
import csv
from sklearn.externals import joblib
from bson.objectid import ObjectId
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
		transctionId = request.json
		print(transctionId['id'])
		tId = transctionId['id']
		transctionDetail = db.transctions.find_one({"_id":ObjectId(str(tId))})
		#transctionDetail = db.transctions.find()
		print(transctionDetail)
		userData = db.users.find_one({"email":transctionDetail['user']})
		#print(data['seller_id'])
		print(userData)
		category = transctionDetail['category']
		#seller_id = transctionDetail['sellerId']
		#print(category, seller_id)
		#seller data retrival
		sellerId = transctionDetail['sellerId']
		sellerData = db.sellers.find_one({"id":transctionDetail['sellerId']})
		print(sellerData)
		# total number of rating for each tangible category
		tr_automobiles = sellerData['category_count']['automobiles']
		tr_daily_needs= sellerData['category_count']['daily_needs']
		tr_electronics = sellerData['category_count']['electronics']
		tr_clothes = sellerData['category_count']['clothes']
		tr_ticket = sellerData['category_count']['tickets']
		tr_education = sellerData['category_count']['education']
		tr_entertainment = sellerData['category_count']['entertainment']

		r_automobiles = sellerData['category_score']['automobiles']
		r_daily_needs= sellerData['category_score']['daily_needs']
		r_electronics = sellerData['category_score']['electronics']
		r_clothes = sellerData['category_score']['clothes']
		r_ticket = sellerData['category_score']['tickets']
		r_education = sellerData['category_score']['education']
		r_entertainment = sellerData['category_score']['entertainment']
		#print(data)


		# For intangible items
		if(category == 'tickets' or category =='education' or category=='entertainment'):
			
			User_given_rating = transctionDetail["userGivenRating"]
			Willingness = transctionDetail["willingness"]
			Genuineness = transctionDetail["genuineness"]
			SysRate = ratingInangible(2,User_given_rating, Willingness, Genuineness)
			Overall = float(SysRate)/4
			print('\n','===================================================================')
			print("\tSystem Calculated seller Rating:",Overall)
			print('===================================================================','\n')

			if(category =='tickets'):
				BuyerScore = userData['category_count']['tickets']
				BuyerScore = BuyerScore/100
				total = tr_ticket
				sellerRating = (r_ticket * total+ Overall * BuyerScore)/(total+1)
				newSellerData = {
					"category_count":{
						"clothes":tr_clothes,
						"automobiles":tr_automobiles,
						"daily_needs":tr_daily_needs,
						"electronics":tr_electronics,

						"tickets":tr_ticket+1,
						"education":tr_education,
						"entertainment":tr_entertainment
					},
					"category_score":{
						"clothes":r_clothes,
						"automobiles":r_automobiles,
						"daily_needs":r_daily_needs,
						"electronics":r_electronics,

						"tickets":sellerRating,
						"education":r_education,
						"entertainment":r_entertainment
					}
				}
			


			elif(category =='entertainment'):
				BuyerScore = userData['category_count']['entertainment']
				BuyerScore = BuyerScore/100
				total = tr_entertainment
				sellerRating = (r_entertainment * total+ Overall * BuyerScore)/(total+ 1)
				newSellerData = {
					"category_count":{
						"clothes":tr_clothes,
						"automobiles":tr_automobiles,
						"daily_needs":tr_daily_needs,
						"electronics":tr_electronics,

						"tickets":tr_ticket,
						"education":tr_education,
						"entertainment":tr_entertainment+1
					},
					"category_score":{
						"clothes":r_clothes,
						"automobiles":r_automobiles,
						"daily_needs":r_daily_needs,
						"electronics":r_electronics,

						"tickets":r_ticket,
						"education":sellerRating,
						"entertainment":r_entertainment
					}
				}

			elif(category =='education'):
				BuyerScore = userData['category_count']['education']
				BuyerScore = BuyerScore/100
				total = tr_education
				sellerRating = (r_education * total+ Overall * BuyerScore)/(total+ 1)
				newSellerData = {
					"category_count":{
						"clothes":tr_clothes,
						"automobiles":tr_automobiles,
						"daily_needs":tr_daily_needs,
						"electronics":tr_electronics,

						"tickets":tr_ticket,
						"education":tr_education+1,
						"entertainment":tr_entertainment
					},
					"category_score":{
						"clothes":r_clothes,
						"automobiles":r_automobiles,
						"daily_needs":r_daily_needs,
						"electronics":r_electronics,

						"tickets":r_ticket,
						"education":sellerRating,
						"entertainment":r_entertainment
					}
				}

			if(userData['category_score']['education']>70 and userData['category_score']['entertainment']>70 and userData['category_score']['ticket']>70):
				fields=[transctionDetail['User_given_rating'], transctionDetail['Genuineness'],transctionDetail['Willingness'],transctionDetail['User_given_rating']*4]
				with open(r'datasetIntangible.csv', 'a') as file:
				    writer = csv.writer(file)
				    writer.writerow(fields)
				    print("#### New Row is appeneded in Intangible dataset####")
			db.sellers.update({'id':transctionDetail['sellerId']},{'$set':newSellerData},False)
			print('\n','===================================================================')
			print("Seller Updated data: ",newSellerData)
			print('===================================================================','\n')
			return(jsonify(newSellerData))


		#For tangible items
		elif(category == 'automobiles' or category=='daily_needs' or category=='electronics' or category=='clothes'):
			

 
			#print("\n",sellerData,"\n")

			# Rating
			User_given_rating = transctionDetail['userGivenRating']
			Delivery_on_time = transctionDetail['deliveryOntime']
			Originality_of_Product =transctionDetail['originality']
			Willingness = transctionDetail['willingness']

			SysRate = ratingTangible(1,User_given_rating, Delivery_on_time, Originality_of_Product, Willingness)
			
			Overall = float(SysRate)/4
			print('\n','===================================================================')
			print("\tSystem Calculated seller Rating:",Overall)
			print('===================================================================','\n')
			if(category =='automobiles'):
				BuyerScore = userData['category_score']['automobiles']
				BuyerScore = BuyerScore/100
				total = tr_automobiles
				sellerRating = (r_automobiles * total+ Overall * BuyerScore)/(total+ 1)
				newSellerData = {
					"category_count":{
						"clothes":tr_clothes,
						"automobiles":tr_automobiles+1,
						"daily_needs":tr_daily_needs,
						"electronics":tr_electronics,

						"tickets":tr_ticket,
						"education":tr_education,
						"entertainment":tr_entertainment
					},
					"category_score":{
						"clothes":r_clothes,
						"automobiles":sellerRating,
						"daily_needs":r_daily_needs,
						"electronics":r_electronics,

						"tickets":r_ticket,
						"education":r_education,
						"entertainment":r_entertainment
					}
				}

			elif(category=='daily_needs'):
				BuyerScore = userData['category_score']['daily_needs']
				BuyerScore = BuyerScore/100
				total = tr_daily_needs
				sellerRating = (r_daily_needs * total+ Overall * BuyerScore)/(total+ 1)
				newSellerData = {
					"category_count":{
						"clothes":tr_clothes,
						"automobiles":tr_automobiles,
						"daily_needs":tr_daily_needs+1,
						"electronics":tr_electronics,

						"tickets":tr_ticket,
						"education":tr_education,
						"entertainment":tr_entertainment
					},
					"category_score":{
						"clothes":r_clothes,
						"automobiles":r_automobiles,
						"daily_needs":sellerRating,
						"electronics":r_electronics,

						"tickets":r_ticket,
						"education":r_education,
						"entertainment":r_entertainment
					}
				}

			elif(category=='electronics'):
				BuyerScore = userData['category_score']['electronics']
				BuyerScore = BuyerScore/100
				total = tr_electronics
				sellerRating = (r_electronics * total+ Overall * BuyerScore)/(total+ 1)
				newSellerData = {
					"category_count":{
						"clothes":tr_clothes,
						"automobiles":tr_automobiles,
						"daily_needs":tr_daily_needs,
						"electronics":tr_electronics+1,

						"tickets":tr_ticket,
						"education":tr_education,
						"entertainment":tr_entertainment
					},
					"category_score":{
						"clothes":r_clothes,
						"automobiles":r_automobiles,
						"daily_needs":r_daily_needs,
						"electronics":sellerRating,

						"tickets":r_ticket,
						"education":r_education,
						"entertainment":r_entertainment
					}
				}


			elif(category=='clothes'):
				BuyerScore = userData['category_score']['clothes']
				BuyerScore = BuyerScore/100
				total = tr_clothes
				sellerRating = (r_clothes * total+ Overall * BuyerScore)/(total+ 1)
				newSellerData = {
					"category_count":{
						"clothes":tr_clothes+1,
						"automobiles":tr_automobiles,
						"daily_needs":tr_daily_needs,
						"electronics":tr_electronics,

						"tickets":tr_ticket,
						"education":tr_education,
						"entertainment":tr_entertainment
					},
					"category_score":{
						"clothes":sellerRating,
						"automobiles":r_automobiles,
						"daily_needs":r_daily_needs,
						"electronics":r_electronics,

						"tickets":r_ticket,
						"education":r_education,
						"entertainment":r_entertainment
					}
				}

			if(userData['category_score']['daily_needs']>70 and userData['category_score']['automobiles']>70 and userData['category_score']['electronics']>70 and userData['category_score']['clothes']>70):
				fields=[transctionDetail['userGivenRating'], transctionDetail['daliveryOntime'],transctionDetail['originality'],transctionDetail['willingness'],transctionDetail['userGivenRating']*4]
				with open(r'datasetTangible.csv', 'a') as f:
				    writer = csv.writer(f)
				    writer.writerow(fields)
				    print("#### New Row is appeneded in Tangible dataset ####")
			db.sellers.update({'id':transctionDetail['sellerId']},{'$set':newSellerData},False)
			print('\n','===================================================================')
			print("Seller Updated data: ",newSellerData)
			print('===================================================================','\n')
			return(jsonify(newSellerData))

		#return(jsonify(newSellerData)) 

api.add_resource(Seller_NewRating,'/NewRating')


if __name__ == "__main__":
	app.run(debug=True)