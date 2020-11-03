from chatterbot import ChatBot
from chatterbot.trainers import ListTrainer,ChatterBotCorpusTrainer
from flask import Flask, flash, redirect, render_template, request, session, abort, jsonify, redirect, url_for, make_response
import requests
import pandas as pd
from pandas import json_normalize
from pyzomato import Pyzomato
from zomato import Zomato
import json
z = Zomato("21c140569818431922d7b4c833c0849e")
common = z.common
location = z.location
restaurant = z.restaurant

app = Flask(__name__)

bot = ChatBot("Zoma-bot", read_only=False, logic_adapters=[
    {"import_path":"chatterbot.logic.BestMatch",
     "default_response":"Sorry I don't understand you",
        "maximum_similarity_threshold": 0.9
}
])




@app.route("/")
def main():
    return render_template("index.html")



@app.route("/get_city_id")
def get_chatbot_response():
    userText = request.args.get('userMessage')
    url = "https://developers.zomato.com/api/v2.1/cities?q="+userText
    payload = {}
    headers = {
        'user-key': '21c140569818431922d7b4c833c0849e',
        'Cookie': 'fbcity=3; zl=en; fbtrack=a620081bc0fac766172d415987e6057c; AWSALBTG=XaUcBlVSAtoITE/rXos4jCAJvaCXl9kE5hF1Zj59ryM6ZdTQf44mpfocxNGB3meQ6MLQgsrkGkDKhAL7C7ksXI0pwpVHNnxVgPxjOVQK94xSZSf9zZBKhELzDoSGz/R2k22CmKRp66KZ1WtShndmUVjCDlZCxQlpHH5Q1a4fASAHNIUSVIo=; AWSALBTGCORS=XaUcBlVSAtoITE/rXos4jCAJvaCXl9kE5hF1Zj59ryM6ZdTQf44mpfocxNGB3meQ6MLQgsrkGkDKhAL7C7ksXI0pwpVHNnxVgPxjOVQK94xSZSf9zZBKhELzDoSGz/R2k22CmKRp66KZ1WtShndmUVjCDlZCxQlpHH5Q1a4fASAHNIUSVIo='
    }
    response = requests.get(url, headers=headers, data=payload)
    data = response.json()

    list1 = []
    if data['location_suggestions'][0]['name'] == userText:
        list1.append((data['location_suggestions'][0]['name'], data['location_suggestions'][0]['id']))
    message = "the requested city \n"
    for text in list1:
        message += "city_name:" + text[0] + " city_id:" + str(text[1]) + "\n"
    return message

headers = {'user-key': '21c140569818431922d7b4c833c0849e',
               'Accept': 'application/json'}

@app.route("/get_restaurants")
def getLocationDetailsbyName():
        userText = request.args.get('userMessage')

        data = userText
        url = 'https://developers.zomato.com/api/v2.1/locations'
        data = requests.post(url, headers=headers, params=data)
        data = json.loads(data.text)
        print("Came to getLocationDetailsbyName ")
        print()

        if (len(data["location_suggestions"]) > 0):
            entity_type = data["location_suggestions"][0]["entity_type"]
            entity_id = data["location_suggestions"][0]["entity_id"]
            title = data["location_suggestions"][0]["title"]
            city_id = data["location_suggestions"][0]["city_id"]
            country_id = data["location_suggestions"][0]["country_id"]
            details = {"restaurants_available": "yes", "entity_type": entity_type, "entity_id": entity_id,
                       "title": title, "city_id": city_id, "country_id": country_id}
            return str(details)


def getLocationDetailsbyCoordinates(lat, lon):
        print("Came to getLocationDetailsbyCoordinates ")
        data = {'lat': lat, "lon": lon}
        url = 'https://developers.zomato.com/api/v2.1/geocode'
        data = requests.post(url, headers=headers, params=data)
        data = json.loads(data.text)

        if (len(data["location"]) > 0):
            entity_type = data["location"]["entity_type"]
            entity_id = data["location"]["entity_id"]
            title = data["location"]["title"]
            city_id = data["location"]["city_id"]
            country_id = data["location"]["country_id"]
            details = {"restaurants_available": "yes", "entity_type": entity_type, "entity_id": entity_id,
                       "title": title, "city_id": city_id, "country_id": country_id}
            return details
        else:
            return {"restaurants_available": "no"}

def getLocationDetails(entity_id, entity_type):
        data = {'entity_id': entity_id, "entity_type": entity_type}
        url = 'https://developers.zomato.com/api/v2.1/location_details'
        data = requests.post(url, headers=headers, params=data)
        data = json.loads(data.text)
        top_cuisines = data["top_cuisines"]
        cuisines = []

        for cuisine in top_cuisines:
            item = {}
            item["title"] = cuisine
            item["payload"] = cuisine
            cuisines.append(item)

        best_restaurants = []
        if (len(data["best_rated_restaurant"]) < 10):
            restoDataLen = len(data["best_rated_restaurant"])
        else:
            restoDataLen = 10

        for i in range(0, restoDataLen):
            item = {}
            photos = []
            item["id"] = data["best_rated_restaurant"][i]["restaurant"]["id"]
            item["name"] = data["best_rated_restaurant"][i]["restaurant"]["name"]
            item["url"] = data["best_rated_restaurant"][i]["restaurant"]["url"]
            item["timings"] = data["best_rated_restaurant"][i]["restaurant"]["timings"]
            item["votes"] = data["best_rated_restaurant"][i]["restaurant"]["user_rating"]["votes"]
            item["image"] = data["best_rated_restaurant"][i]["restaurant"]["featured_image"]
            item["cuisines"] = data["best_rated_restaurant"][i]["restaurant"]["cuisines"]
            item["ratings"] = data["best_rated_restaurant"][i]["restaurant"]["user_rating"]["aggregate_rating"]
            item["rating_color"] = data["best_rated_restaurant"][i]["restaurant"]["user_rating"]["rating_color"]
            item["price_range"] = data["best_rated_restaurant"][i]["restaurant"]["price_range"]
            item["currency"] = data["best_rated_restaurant"][i]["restaurant"]["currency"]
            item["cost"] = data["best_rated_restaurant"][i]["restaurant"]["average_cost_for_two"]
            item["location"] = data["best_rated_restaurant"][i]["restaurant"]["location"]["locality_verbose"]
            item["user_rating_text"] = data["best_rated_restaurant"][i]["restaurant"]["user_rating"]["rating_text"]

            if "photos" in data["best_rated_restaurant"][i]["restaurant"].keys():
                if (len(data["best_rated_restaurant"][i]["restaurant"]["photos"]) < 5):
                    photos_len = len(data["best_rated_restaurant"][i]["restaurant"]["photos"])
                else:
                    photos_len = 5
                for j in range(0, photos_len):
                    photos.append(data["best_rated_restaurant"][i]["restaurant"]["photos"][j]["photo"]["url"])
                item["photos"] = photos
                best_restaurants.append(item)
            else:
                pass

        details = {"top_cuisines": cuisines, "best_restaurants": best_restaurants}
        return details

def getCuisineId(cuisine_name, city_id):
        data = {'city_id': city_id}
        url = 'https://developers.zomato.com/api/v2.1/cuisines'
        data = requests.post(url, headers=headers, params=data)
        data = json.loads(data.text)
        # print("data: ",data)
        cuisines = data["cuisines"]
        cuisineID = None
        for cuisine in cuisines:
            if (cuisine_name.lower() == cuisine["cuisine"]["cuisine_name"].lower()):
                return cuisine["cuisine"]["cuisine_id"]
        return cuisineID

def searchRestaurants(entity_id, entity_type, cuisine_id, search_query):
        url = 'https://developers.zomato.com/api/v2.1/search'
        data = {"entity_id": entity_id, "entity_type": entity_type,
                "cuisines": cuisine_id, "count": "10", "order": "asc"}
        data = requests.post(url, headers=headers, params=data)
        data = json.loads(data.text)
        restaurants = []
        if (len(data["restaurants"]) < 10):
            restoDataLen = len(data["restaurants"])
        else:
            restoDataLen = 10

        for i in range(0, restoDataLen):
            item = {}
            photos = []
            item["id"] = data["restaurants"][i]["restaurant"]["id"]
            item["name"] = data["restaurants"][i]["restaurant"]["name"]
            item["url"] = data["restaurants"][i]["restaurant"]["url"]
            item["timings"] = data["restaurants"][i]["restaurant"]["timings"]
            item["votes"] = data["restaurants"][i]["restaurant"]["user_rating"]["votes"]
            item["image"] = data["restaurants"][i]["restaurant"]["featured_image"]
            item["cuisines"] = data["restaurants"][i]["restaurant"]["cuisines"]
            item["ratings"] = data["restaurants"][i]["restaurant"]["user_rating"]["aggregate_rating"]
            item["rating_color"] = data["restaurants"][i]["restaurant"]["user_rating"]["rating_color"]
            item["price_range"] = data["restaurants"][i]["restaurant"]["price_range"]
            item["cost"] = data["restaurants"][i]["restaurant"]["average_cost_for_two"]
            item["location"] = data["restaurants"][i]["restaurant"]["location"]["locality_verbose"]
            item["currency"] = data["restaurants"][i]["restaurant"]["currency"]
            item["user_rating_text"] = data["restaurants"][i]["restaurant"]["user_rating"]["rating_text"]

            if "photos" in data["restaurants"][i]["restaurant"].keys():
                if (len(data["restaurants"][i]["restaurant"]["photos"]) < 5):
                    photos_len = len(data["restaurants"][i]["restaurant"]["photos"])
                else:
                    photos_len = 5
                for j in range(0, photos_len):
                    photos.append(data["restaurants"][i]["restaurant"]["photos"][j]["photo"]["url"])
                item["photos"] = photos
                restaurants.append(item)
            else:
                pass

        return restaurants


if __name__ =="__main__":
    app.run(debug=False)