from __future__ import print_function
from botocore.vendored import requests
import os
import json
import urllib
import json
import random
import math, random 
import boto3
from botocore.exceptions import ClientError
import smtplib
from boto3.dynamodb.conditions import Key, Attr

from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


num = []
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('Item')
table1 = dynamodb.Table('Purchase')
table2 = dynamodb.Table('Customer')
table3 = dynamodb.Table('Sellers')
table4 = dynamodb.Table('bills')
def otp_in_session(intent,session):
    speech_output = ""
    reprompt_text = ""
    userID = session['user']['userId']
    userID=userID[18:]
    app_id = session['application']['applicationId']
    if ('number' in intent['slots']):
        should_end_session = False
        response1 = table1.get_item(Key={"user_id":userID,"item_list":app_id})
        item1 = response1["Item"]
        if (item1["otp_num"]==intent["slots"]["number"]["value"]):
            table1.update_item(
                    Key={
                        'user_id': userID,
                        'item_list':app_id},
                        UpdateExpression="set otp=:o",
                        ExpressionAttributeValues={
                        ':o':"yes"
                    },
                ReturnValues="UPDATED_NEW")
            speech_output = "verification done, please proceed for billing"
        else:
            speech_output = "Sorry, invalid otp, try again"
    return build_response({}, build_speechlet_response(
                intent['name'], speech_output, reprompt_text, should_end_session))
def customer_in_session(intent, session):
    speech_output = ""
    reprompt_text = ""
    userID = session['user']['userId']
    userID=userID[18:]
    app_id = session['application']['applicationId']
    if ('mobile' in intent['slots']):
        should_end_session = False
        num.append(intent['slots']['mobile']['value'])
        n = ''.join(map(str,num))
        if(len(n)==10):
            should_end_session = False
            response2 = table2.scan (
                        FilterExpression=Key('mobile').eq(n)
                        )
            item2 = response2["Items"]
            cust = item2[0]
            if (cust!=None):
                
                digits = "0123456789"
                OTP = "" 
                b = "no"
                for i in range(4) : 
                    OTP += digits[int(math.floor(random.random() * 10))] 
                table1.update_item(
                    Key={
                        'user_id': userID,
                        'item_list':app_id},
                        UpdateExpression="set email=:r, mobile=:p, customer=:s, otp=:o, otp_num=:n",
                        ExpressionAttributeValues={
                        ':r':cust["email"],
                        ':p':n,
                        ':s':cust["name"],
                        ':o':b,
                        ':n':OTP,
                        #':x':cust["user_id"]
                       #':c':cust["user_id"]
                       # ':n':OTP
                    },
                ReturnValues="UPDATED_NEW")
                build_customer_email(cust["email"],OTP)
                speech_output= "hello, "+cust["name"]+",plese verify otp sent to your email"
                reprompt_text = "request is not valid"
                
            else:
                should_end_session = True
                speech_output = "customer id not valid, try again"
                reprompt_text = "request is not valid"
        
        else:
            reprompt_text = "please make a valid request"
    else:
        should_end_session = True
        speech_output= "please make valid request"
    return build_response({}, build_speechlet_response(
                intent['name'], speech_output, reprompt_text, should_end_session))
def exists(userID,item):
    try:
        item1 = table.get_item(Key={'user_id':userID,'Items':item})
        response = item1["Item"]
    except KeyError:
        response = None
    return response

def purchase_item_in_session(intent,session):
    iitem =[]
    quantity=[]
   
    speech_output = ""
    reprompt_text = ""
    userID = session['user']['userId']
    userID=userID[18:]
    app_id = session['application']['applicationId']
    
    
    if ('quanitity' in intent['slots'] and 'item' in intent['slots']):
        #quantity = []
        should_end_session = True
        item = intent['slots']['item']['value']
        item1 = exists(userID,item)
        #item = response['Item']
        if( item1 is  None):
            speech_output = "Item not available"
        else:
            iitem.append(intent['slots']['item']['value'])
            #iitem.append("fg")
            quantity.append(intent['slots']['quanitity']['value'])
            
            table1.put_item(
                Item={
                    'user_id': userID,
                    'item_list': app_id,
                    'price_list': quantity,
                    'item': iitem
                 }
                )
            speech_output = ' '.join([a +" "+ b for a,b in zip(quantity,iitem)] )+ " is your purchase"
        reprompt_text = "I didn't understand, please make a valid request"
    else:
        should_end_session = True
        reprompt_text = ' '.join([a +" "+ b for a,b in zip(quantity,iitem)] ) + " If you done, confirm the purchase by asking make bil username"
        #quantity.append("8")
    #if (intent_name == "AMAZON.CancelIntent"):
        #should_end_session = True
    #     iitem = []
    #     quantity = []
     #   speech_output = "Thank you, your purchase has cancelled"
    #elif (intent_name == "AMAZON.StopIntent"):
     #    should_end_session = True
        #for i in range(0,len(iitem)):
        #speech_output = ' '.join([a +" "+ b for a,b in zip(quantity,iitem)] )
        #speech_output += " ,for bill ask seller for make bill user name"
    return build_response({}, build_speechlet_response(
            intent['name'], speech_output, reprompt_text, should_end_session))

def bill_in_session(intent,session,intent_request):
    speech_output = ""
    reprompt_text = ""
    userID = session['user']['userId']
    userID=userID[18:]
    app_id = session['application']['applicationId']
    response0 = session["user"]["accessToken"]
    

    # if (r.status_code == 200):
    #     f = r.json()
    # sellers_email = f["email"]
    response1 = table1.get_item(Key={"user_id":userID,"item_list":app_id})
    item1 = response1["Item"]
    purchse_list = item1['item']
    purchase_quantity = item1['price_list']
    price = []
    response1 = table1.get_item(Key={'user_id':userID,'item_list':app_id})
    item1 = response1["Item"]
    should_end_session = True
    total = 0
    host = "https://graph.facebook.com"
    path = "/me"
    params = urllib.urlencode({"access_token": "EAAJ8FGqkUKsBAHGz0OQwRAU1ZBEulKDYAa9oBUdW5T2p2q6CpDO5RyV8R8KPkQA7y0MNhBiy2KShaee23MexMtboLtYfQI4hDP9sLaHUKDZBz33IBo1adoBHsCniegj0I1d8h2r4aO7laiILpglnOcN7WUtlnGBr6ORBOcpAZDZD"})

    url = "{host}{path}?fields=email&{params}".format(host=host, path=path, params=params)

    # open the URL and read the response
    resp = urllib.urlopen(url).read()

    # convert the returned JSON string to a Python datatype 
    me = json.loads(resp)
    if (item1["otp"]=="yes" and purchse_list!= None):
        for i in purchse_list:
            response = table.get_item(Key={'user_id':userID,'Items':i})
            item = response["Item"]
            price.append(item["Price"])
        for i in range(0, len(purchse_list)):
            total += int(int(price[i])*int(purchase_quantity[i]))
        table1.update_item(
                    Key={
                        'user_id': userID,
                        'item_list':app_id},
                        UpdateExpression="set otp=:o",
                        ExpressionAttributeValues={
                        ':o':"no",
                       # ':n':OTP
                    },
                ReturnValues="UPDATED_NEW")
        response3 = table3.scan (
                        FilterExpression=Key('alexa_id').eq(userID)
                        )
        item3 = response3["Items"]
        #sell = item3[0]
        response4 = table4.put_item(
                                Item={
                                    'id':userID,
                                    'timestamp':intent_request["timestamp"],
                                    #'cust_email':item1["email"],
                                    'total':total
                                }
                                )
        build_email(purchse_list,purchase_quantity,price,"foodteech","678903459","hjk","ajit27.iitkgp@gmail.com","kaleajit27@gmail.com")
        speech_output = "Invoice has been sent to your mail"
    else:
        speech_output = "please do customer verification"
    return build_response({}, build_speechlet_response(
            intent['name'], speech_output, reprompt_text, should_end_session))
    
    

#print(purchase_item_in_session)
def add_item(item, price,userID):
    response = table.put_item(
           Item={
                'user_id': userID,
                'Items': item,
                'Price': price
            }
        ) 
    return None
def add_item_in_session(intent, session):
    speech_output = ""
    reprompt_text = ""
    userID = session['user']['userId']
    userID=userID[18:]


    if ('item' in intent['slots'] and 'price' in intent['slots']):
        try:
            item = intent['slots']['item']['value']
            price = intent['slots']['price']['value']
            should_end_session = True
            error = add_item(item,price,userID)
            speech_output = "item added"
        except KeyError:
            should_end_session = False
            speech_output = "That didn't work"
        
    else:
        reprompt_text = "Sorry, I didn't understand"
        should_end_session = False

    return build_response({}, build_speechlet_response(
        intent['name'], speech_output, reprompt_text, should_end_session))
    #TODO: change sort key
def change_price(item,price,userID):
    response = table.get_item(Key={'user_id':userID,'Items':item})
    item = response['Item']
    item['Price'] = price
    table.put_item(Item = item)
         
        
    return None
    
def change_price_in_session(intent, session):
    speech_output = ""
    reprompt_text = ""
    userID = session['user']['userId']
    userID=userID[18:]
    if ('item' in intent['slots'] and 'price' in intent['slots']):
        item = intent['slots']['item']['value']
        price = intent['slots']['price']['value']
        should_end_session = True
        error = change_price(item,price,userID)
        if error is not None:
            speech_output = "That didn't work. " + error
        else:
            speech_output = "price of "+item+" changed to "+price
    else:
        reprompt_text = "Sorry, I didn't understand. Please try again."
        should_end_session = False

    card_title = intent['name']
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
def email_in_session(intent,session):
    speech_output = ""
    reprompt_text = ""
    should_end_session = True
    build_email(data)
    speech_output = "email sent"
    card_title = intent['name']
    return build_response({}, build_speechlet_response(
        card_title, speech_output, reprompt_text, should_end_session))
    
         
def build_speechlet_response(title, output, reprompt_text, should_end_session):
    return {
        'outputSpeech': {
            'type': 'PlainText',
            'text': output
        },
        'card': {
            'type': 'Simple',
            'title': title,
            'content': output
        },
        'reprompt': {
            'outputSpeech': {
                'type': 'PlainText',
                'text': reprompt_text
            }
        },
        'shouldEndSession': should_end_session
    }

def build_response(session_attributes, speechlet_response):
    return {
        'version': '1.0',
        'sessionAttributes': session_attributes,
        'response': speechlet_response
    }
def get_welcome_response(session,event):
    """ If we wanted to initialize the session to have some attributes we could
    add those here
    """
    speech_output = ""
    reprompt_text = ""
    try:
        response = event["session"]["user"]["accessToken"]
    except KeyError:
        response = None
    
    if (response is None):
        speech_output = "please, link your account"
        session_attributes = {}

        card_title = "Link Account"
        should_end_session = True
    else:
        session_attributes = {}
        card_title = "Welcome"
        userID = session['user']['userId']
        userID=userID[18:]
        app_id = session['application']['applicationId']
        
        table1.update_item(
                    Key={
                        'user_id': userID,
                        'item_list':app_id},
                        UpdateExpression="set otp=:o",
                        ExpressionAttributeValues={
                        ':o':"no",
                       # ':n':OTP
                    },
                ReturnValues="UPDATED_NEW")
    
        should_end_session = False
        speech_output= "Hello, welcome to shop assistant. You can say add item, purchase item, make bills."
        reprompt_text = "I didn't get that. Can you repeat what please."

    # If the user either does not reply to the welcome message or says something
    # that is not understood, they will be prompted again with this text.
    #a = get_alexa_email(deviceId)
        
    #return a
    return build_response({},build_speechlet_response(
card_title, speech_output, reprompt_text, should_end_session))

def on_launch(launch_request, session, event):
    """ Called when the user launches the skill without specifying what they
    want
    """

    
    return get_welcome_response(session,event)

def on_session_started(session_started_request, session):
    """ Called when the session starts """

    print("on_session_started requestId=" + session_started_request['requestId']
+ ", sessionId=" + session['sessionId'])

def on_session_ended(session_ended_request, session):
    """ Called when the user ends the session.
    Is not called when the skill returns should_end_session=true
    """
    print("on_session_ended requestId=" + session_ended_request['requestId'] +
", sessionId=" + session['sessionId'])
def handle_session_end_request(session):
    card_title = "Session Ended"
    speech_output = "Thanks"
    # Setting this to true ends the session and exits the skill.
    should_end_session = True
    return build_response({}, build_speechlet_response(
        card_title, speech_output, None, should_end_session))
        
def on_intent(intent_request, session):
    """ Called when the user specifies an intent for this skill """

    print("on_intent requestId=" + intent_request['requestId'] +
          ", sessionId=" + session['sessionId'])
    
    intent = intent_request['intent']
    intent_name = intent_request['intent']['name']

    # Dispatch to your skill's intent handlers
    if intent_name == "add_item":
        return add_item_in_session(intent, session)
    if intent_name == "change_price":
        return change_price_in_session(intent, session)
    if intent_name == "email":
        return email_in_session(intent,session)
    if intent_name == "OTP":
        return otp_in_session(intent,session)
    
    if intent_name == "purchase":
        return purchase_item_in_session(intent,session)
    if intent_name == "bill":
        return bill_in_session(intent,session,intent_request)
    if intent_name == "customer":
        return customer_in_session(intent,session)
    elif intent_name == "AMAZON.HelpIntent":
        return get_welcome_response(session)
    elif intent_name == "AMAZON.CancelIntent" or intent_name == "AMAZON.StopIntent":
        return handle_session_end_request(session)
    else:
        raise ValueError("Invalid intent")


def lambda_handler(event, context):
    """ Route the incoming request based on type (LaunchRequest, IntentRequest,
    etc.) The JSON body of the request is provided in the event parameter.
    """
    print("event.session.application.applicationId=" +
          event['session']['application']['applicationId'])
    #deviceId = context.System.device.deviceId
    """
    Uncomment this if statement and populate with your skill's application ID to
    prevent someone else from configuring a skill that sends requests to this
    function.
    """
    # if (event['session']['application']['applicationId'] !=
    #         "amzn1.echo-sdk-ams.app.[unique-value-here]"):
    #     raise ValueError("Invalid Application ID")

    if (event['session']['new']):
        on_session_started({'requestId': event['request']['requestId']},
                           event['session'])

    if (event['request']['type'] == "LaunchRequest"):
        return on_launch(event['request'], event['session'], event)
    elif (event['request']['type'] == "IntentRequest"):
        return on_intent(event['request'], event['session'])
    elif event['request']['type'] == "SessionEndedRequest":
        return on_session_ended(event['request'], event['session'])



gmail_user = "kaleajit27@gmail.com"
gmail_appPassword = "Ajit@1997"

msg = MIMEMultipart('alternative')
sent_from = [gmail_user]
msg['Subject'] = 'Invoice'
msg1 = MIMEMultipart('alternative')
msg1['Subject'] = 'Your verification code'
#excel-file=data

# Invoice is Constructor. Builds template rows for html
class Invoice:    
    
    def __init__(self, item_list, quantity, price):
        self.item_list = item_list
        self.quantity = quantity
        self.price = price
        self.total = 0
        
        self.template_array = []
#        print(self.notes[0], self.invoice_num, self.to)
        
#        sum amounts for total
        for i in range(0, len(self.item_list)):
            self.total += int(int(self.price[i])*int(self.quantity[i]))
            
            template = """
                <tr class="left">
                    <td style="padding: 10px; text-align: left;">"""+ self.item_list[i] +"""</td>
                    <td style="padding: 10px;">""" + self.quantity[i] + """</td>
                    <td style="text-align: right; padding: 10px;">"""+ self.price[i] +"""</td>
                    </tr>
                """        
            self.template_array.append(template)
        self.total = str(self.total)

        
        
def send_email(to, msg, new_template):
        
    
           
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(gmail_user, gmail_appPassword)
        server.sendmail(sent_from, to, msg.as_string())
        
        print("Email Sent To: ", new_template.name)
        print("@: ", to)            
        print("TOTAL: ", new_template.total, "---------------------------")            
        server.quit()
        
        if(data[0] == 'None'):
            print('END OF LIST')
        else:            
            build_email(name, item_list, quantity, price)
    except Exception as e:
        print(e)
        print('Email Failed')
        print("@: ", to)
def send_customer_email(to, msg):
        
    
           
    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(gmail_user, gmail_appPassword)
        server.sendmail(sent_from, to, msg1.as_string())
        
                   
        server.quit()
        
        if(data[0] == 'None'):
            print('END OF LIST')
        else:            
            build_customer_email(email,OTP)
    except Exception as e:
        print(e)
        print('Email Failed')
        print("@: ", to)

#print(data)
def build_customer_email(email,OTP):
    to = [email]
    html ="""\
    <!DOCTYPE html>
    <html>
        <body>
            <p style="text-align: center"> Hello from shop assistant, """+ OTP +""" is your OTP.</p> 
            </body>
    </html>
    """
    part1 = MIMEText(html, 'html')
    
    
    msg1.attach(part1)
    send_customer_email(to, msg)

def build_email(item_list, quantity, price,shop,mobile,address,email_cust,email_shop):
    
#    print(data[5])
    new_template = Invoice(item_list, quantity, price)
    
    to = [email_cust,email_shop]
    #This must be a list i.e. ['someaddress@gmail.com']



        #use IN-LINE Styling    
    html = """\
    <!DOCTYPE html>
    <html>
        <body>
            <p style="text-align: center"> Hello,This is from,"""+shop+"""</p> 
              
            <p style="text-align: center">Here are your outstanding invoices</p>
            <hr style="width: 500px;">
            <table style="margin-left: auto; margin-right: auto">
                <tr>
                    <th>INVOICE TOTAL:</th>
                    <th style="padding-left: 100px">Rs"""+ new_template.total +"""</th>
                </tr>
            </table>
            <hr class="width">
            
            <table style="margin-left: auto; margin-right: auto">
                <tr class="left padded">
                    <th style="text-align: left;"> Items </th>
                    <th> Quantity </th>
                    <th style="text-align: right;"> Price </th>
                </tr>
                """ + ''.join(new_template.template_array) + """
            </table>
            
            <hr style="width: 500px;">
                <table style="margin-left: auto; margin-right: auto; padding: 10px;">
                    <tr>
                        <th> Thank You! </th>
                    </tr>
                    <tr>
                        <th> """+shop+""" </th>
                        <th> """+mobile+"""</th>
                        <th> """+address+"""</th>
                    </tr>
                </table>
            <hr style="width: 500px;">
            
        </body>
    </html>
    """
    
    part2 = MIMEText(html, 'html')
    
    
    msg.attach(part2)
      
    send_email(to, msg, new_template)  

                               


