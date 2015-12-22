from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
import helperfunctions


def textresponse(messageProtocolEntity):

    messagebody = messageProtocolEntity.getBody()
    if messagebody.startswith("#"):
        response = helperfunctions.parsecapabilities(messagebody)
    else:
        response = helperfunctions.APIresponse(messagebody)
        #response = helperfunctions.chitchatresponse(messagebody)

    if response != "" and response != "<no results>" and len(response) < 250:
        safe_response = response.encode('ascii','ignore')
        messageProtocolEntity.setBody(safe_response)
    elif len(messagebody.split(' ')) == 1:
        messageProtocolEntity.setBody(":)")
    else:
        messageProtocolEntity.setBody("Can I answer every question? Nobody likes a know-it-all!!!")

    return messageProtocolEntity




