# Imports
from flask import Flask, render_template, request, jsonify
import nltk
import datetime
from nltk.stem.lancaster import LancasterStemmer
import numpy as np
import tflearn
import tensorflow as tf
import random
import json
import pickle
import requests

headers = {'user-key': '21c140569818431922d7b4c833c0849e',
               'Accept': 'application/json'}
stemmer = LancasterStemmer()
seat_count = 50

with open("intents.json") as file:
    data = json.load(file)
with open("data.pickle", "rb") as f:
    words, labels, training, output = pickle.load(f)


# Function to process input
def bag_of_words(s, words):
    bag = [0 for _ in range(len(words))]

    s_words = nltk.word_tokenize(s)
    s_words = [stemmer.stem(word.lower()) for word in s_words]

    for se in s_words:
        for i, w in enumerate(words):
            if w == se:
                bag[i] = 1

    return np.array(bag)


tf.reset_default_graph()

net = tflearn.input_data(shape=[None, len(training[0])])
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, 8)
net = tflearn.fully_connected(net, len(output[0]), activation="softmax")
net = tflearn.regression(net)

# Loading existing model from disk
model = tflearn.DNN(net)
model.load("model.tflearn")

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index1.html')


@app.route('/get')
def get_bot_response(entity_id, entity_type, cuisine_id, search_query):
    global seat_count
    message = request.args.get('msg')
    if message:
        message = message.lower()
        results = model.predict([bag_of_words(message, words)])[0]
        result_index = np.argmax(results)
        tag = labels[result_index]
        if results[result_index] > 0.5:
            if tag == "mumbai":
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
                response = str(restaurants)
                #seat_count -= 1
                #response = "Your table has been booked successfully. Remaining tables: " + str(seat_count)


            elif tag == "available_tables":
                response = "There are " + str(seat_count) + " tables available at the moment."

            elif tag == "menu":
                day = datetime.datetime.now()
                day = day.strftime("%A")
                if day == "Monday":
                    response = "Chef recommends: Steamed Tofu with Schezwan Peppercorn, Eggplant with Hot Garlic Sauce, Chicken & Chives, Schezwan Style, Diced Chicken with Dry Red Chilli, Schezwan Pepper"

                elif day == "Tuesday":
                    response = "Chef recommends: Asparagus Fresh Shitake & King Oyster Mushroom, Stir Fried Chilli Lotus Stem, Crispy Fried Chicken with Dry Red Pepper, Osmanthus Honey, Hunan Style Chicken"

                elif day == "Wednesday":
                    response = "Chef recommends: Baby Pokchoi Fresh Shitake Shimeji Straw & Button Mushroom, Mock Meat in Hot Sweet Bean Sauce, Diced Chicken with Bell Peppers & Onions in Hot Garlic Sauce, Chicken in Chilli Black Bean & Soy Sauce"

                elif day == "Thursday":
                    response = "Chef recommends: Eggplant & Tofu with Chilli Oyster Sauce, Corn, Asparagus Shitake & Snow Peas in Hot Bean Sauce, Diced Chicken Plum Honey Chilli Sauce, Clay Pot Chicken with Dried Bean Curd Sheet"

                elif day == "Friday":
                    response = "Chef recommends: Kailan in Ginger Wine Sauce, Tofu with Fresh Shitake & Shimeji, Supreme Soy Sauce, Diced Chicken in Black Pepper Sauce, Sliced Chicken in Spicy Mala Sauce"

                elif day == "Saturday":
                    response = "Chef recommends: Kung Pao Potato, Okra in Hot Bean Sauce, Chicken in Chilli Black Bean & Soy Sauce, Hunan Style Chicken"

                elif day == "Sunday":
                    response = "Chef recommends: Stir Fried Bean Sprouts & Tofu with Chives, Vegetable Thou Sou, Diced Chicken Plum Honey Chilli Sauce, Diced Chicken in Black Pepper Sauce"
            else:
                for tg in data['intents']:
                    if tg['tag'] == tag:
                        responses = tg['responses']
                response = random.choice(responses)
        else:
            response = "I didn't quite get that, please try again."
        return str(response)
    return "Missing Data!"


if __name__ == "__main__":
    app.run()