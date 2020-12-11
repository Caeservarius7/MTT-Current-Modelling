#include "secrets.h"
#include <WiFiClientSecure.h>
#include <MQTTClient.h>
#include <ArduinoJson.h>
#include "WiFi.h"
#include "time.h"
#include "EmonLib.h"
#include <driver/adc.h>
#include <Arduino.h>

// The MQTT topics that this device should publish/subscribe
#define AWS_IOT_PUBLISH_TOPIC   "esp32/pub"
#define AWS_IOT_SUBSCRIBE_TOPIC "esp32/sub"

//Calibration for the sensor
#define Current_cal 111.1

//Initialise Sensor
EnergyMonitor emon1;
EnergyMonitor emon2;
EnergyMonitor emon3;

//Setup for Time
time_t now;
char strftime_buf[64];
const char* ntpServer = "pool.ntp.org";const long  gmtOffset_sec = 0;const int   daylightOffset_sec = 3600;

//Wifi
WiFiClientSecure net = WiFiClientSecure();
MQTTClient client = MQTTClient(256);

//AWS connnection
void connectAWS()
{
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);

  Serial.println("Connecting to Wi-Fi");

  while (WiFi.status() != WL_CONNECTED){
    delay(500);
    Serial.print(".");
  }

  // Configure WiFiClientSecure to use the AWS IoT device credentials
  net.setCACert(AWS_CERT_CA);
  net.setCertificate(AWS_CERT_CRT);
  net.setPrivateKey(AWS_CERT_PRIVATE);

  // Connect to the MQTT broker on the AWS endpoint
  client.begin(AWS_IOT_ENDPOINT, 8883, net);

  // Create a message handler
  client.onMessage(messageHandler);

  Serial.print("Connecting to AWS IOT");

  while (!client.connect(THINGNAME)) {
    Serial.print(".");
    delay(100);
  }

  if(!client.connected()){
    Serial.println("AWS IoT Timeout!");
    return;
  }

  // Subscribe to a topic
  client.subscribe(AWS_IOT_SUBSCRIBE_TOPIC);

  Serial.println("AWS IoT Connected!");
}


//Main publishing code
void publishMessage()
{
  StaticJsonDocument<200> doc;
  struct tm timeinfo;
  getLocalTime(&timeinfo);
  char datetime[64];
  strftime(datetime, 64, "%Y:%m:%d:%H:%M:%S", &timeinfo);
  double currentDraw1 = emon1.calcIrms(1480);
  double currentDraw2 = emon2.calcIrms(1480);
  double currentDraw3 = emon3.calcIrms(1480);

  doc["time"] = datetime;
  doc["Uncalibrated current 1"] = currentDraw1;
  doc["Uncalibrated current 2"] = currentDraw2;
  doc["Uncalibrated current 3"] = currentDraw3; 
     
  //JSON setup  

  char jsonBuffer[512];
  serializeJson(doc, jsonBuffer); // print to client
  serializeJson(doc, Serial); // print to Serial
  Serial.println();
  client.publish(AWS_IOT_PUBLISH_TOPIC, jsonBuffer);
}

void messageHandler(String &topic, String &payload) {
  Serial.println("incoming: " + topic + " - " + payload);
}

//Calculating current from the relevant GPIO ports
void setup() {
  Serial.begin(9600);
  connectAWS();
  configTime(gmtOffset_sec, daylightOffset_sec, ntpServer);
  emon1.current(35, Current_cal);
  emon2.current(36, Current_cal);
  emon3.current(39, Current_cal);
}

//Takes a value every second
void loop() {
  publishMessage();
  client.loop();
  delay(1000);
}
