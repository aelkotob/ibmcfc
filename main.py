from fastapi import FastAPI
from mangum import Mangum
import json, requests
from shapely.geometry import shape, Point

app = FastAPI()
handler = Mangum(app)


url = "https://us-south.ml.cloud.ibm.com/ml/v1/text/generation?version=2023-05-29"

headers = {
	"Accept": "application/json",
	"Content-Type": "application/json",
	"Authorization": "Bearer {0}}"
}

body = {
	"input": """Given the following indicators and their meaning:
heatValue: 1 means not significant risk and 5 means major risk
dryValue: 1 means not significant risk and 5 means major risk
stormValue: 1 means not significant risk and 5 means major risk
rainValue: 1 means not significant risk and 5 means major risk
floodValue: 1 means not significant risk and 5 means major risk

Evaluate the overall risk and answer with one of the following verdicts:
- Not Significant Risk
- Minor Risk
- Moderate Risk
- High Risk
- Major Risk

Input: heatValue: {0}
dryValue: {1}
stormValue: {2}
rainValue: {3}
floodValue: {4}
Output:""",
	"parameters": {
		"decoding_method": "greedy",
		"max_new_tokens": 1000,
		"repetition_penalty": 1
	},
	"model_id": "ibm/granite-13b-chat-v2",
	"project_id": "eee8c95f-de62-441f-9c43-64e8cda59441",
	"moderations": {
		"hap": {
			"input": {
				"enabled": True,
				"threshold": 0.5,
				"mask": {
					"remove_entity_value": True
				}
			},
			"output": {
				"enabled": True,
				"threshold": 0.5,
				"mask": {
					"remove_entity_value": True
				}
			}
		}
	}
}


rating = {
            1: 'Not Significant Risk',
            2: 'Minor Risk',
            3: 'Moderate Risk',
            4: 'High Risk',
            5: 'Major Risk'
        }

@app.get("/")
async def get_site_info():
    return  {
        'Info': 'Home Safe Home is an IBM CFC project aimed to help people understand the risk in certain areas!'
    }


@app.get("/lat/{lat_val}/long/{long_val}")
async def get_risk_rating(lat_val: float, long_val: float):
    result = {"lat": lat_val, "long": long_val}
    found = False
    with open('climate-change-sample.geojson') as f:
        sample_data = json.load(f)
        point = Point(long_val, lat_val)
        for feature in sample_data['features']:
            polygon = shape(feature['geometry'])
            if polygon.contains(point):
                found = True
                result = result | feature['properties']
                break

    payload = body
    if found:
        payload["input"] = body["input"].format(result['heatValue'],
                             result['dryValue'],
                             result['stormValue'],
                             result['rainValue'],
                             result['floodValue'])

        response = requests.post(
            url,
            headers=headers,
            json=payload
        )
        if response.status_code != 200:
            result['verdict'] = "Unknown Risk"
        else:
            print(response.json())
            result['verdict'] = response.json()
        print(response.json())
    else:
        result['verdict'] = 'Unknown Risk'
    return result