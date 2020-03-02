"""
This is a management command, that listens for inbound messages.
This module is responsible for storing inbound status messages and data messages.

This module implements B41.
Design is documented in B36-B38.
Uses the B39 JSON schema, which implements the protocol v1.0.
"""

from datetime import datetime
from django.core.management.base import BaseCommand
from django.utils import timezone
from demo_module.messagehandler.client import MqttClient
from demo_module.messagehandler import protocol
from demo_module.models import Status, Result, Test, Inbound_teststand_package, Test_stand_data, Test_stand_parameters

# class Command(BaseCommand):
#     help = 'Displays current time'
#
#     def handle(self, *args, **kwargs):
#         time = timezone.now().strftime('%X')
#         self.stdout.write("It's now %s" % time)
#
#         # define the on_message call-back
#         def on_message_callback(client, userdata, message):
#
#             #Create a new message object
#             m = protocol.Message()
#
#             # Convert the incoming JSON message to Python vars
#             msg = message.payload.decode("utf-8")
#             obj = protocol.ProtocolSchema.read_jsonstr(msg)
#
#             # Do some validation here
#             # Evaluate if the Python object conforms to the protocol
#             schema_validation_result = protocol.ProtocolSchema.validating(obj, m.protocol_schema)
#
#             # Consider implementing a break if the validation fails.
#
#             # Insert into struct-like variables in the m-object.
#             m.unpack(**obj)
#
#             # Store any received statuscodes
#             # 6xx -> Power Codes
#             # 1xx-5xx -> Status Codes
#             if m.msgType == "status":
#                 # Get object in the db
#                 s = Status.objects.all()[0]
#
#                 if int(m.statusCode) >= 600:
#                     s.latest_power_code = m.statusCode
#                 else:
#                     s.latest_status_code = m.statusCode
#
#                 # Update the object
#                 s.save()
#
#             if m.msgType == "data":
#                 # Create and store a new result in the db
#                 r = Result()
#
#                 # Needs to be decided:
#                 # - How to transport the nodelete tag through a roundtrip?
#                 # - How to transport the requested_by tag through a roundtrip?
#                 # - Is it the right choice to store the embedded file as binary? Do we need it?
#
#                 # Set relevant values from message
#                 r.command_list = m.commandList
#                 r.parameter_obj = m.parameterObj
#                 r.data_obj = m.dataObj
#                 r.embedded_file_format = m.embeddedFileFormat
#                 r.embedded_file = bytearray(m.embeddedFile, "utf8")
#
#                 # Create the object in the db
#                 r.save()
#
#         # Pass the callback to the client
#         subscriber = MqttClient("MessageHandler", on_message_callback)
#
#         # Only subscribe to relevant inbound messages
#         subscriber.subscribe("demo_module/inbound")
#
#         print("Starting listening loop")
#         subscriber.loop()


# for database structure
class Command(BaseCommand):
    help = 'Displays current time'

    def handle(self, *args, **kwargs):
        time = timezone.now().strftime('%X')
        self.stdout.write("It's now %s" % time)

        # define the on_message call-back
        def on_message_callback(client, userdata, message):

            #Create a new message object
            m = protocol.Message()

            # Convert the incoming JSON message to Python vars
            msg = message.payload.decode("utf-8")
            obj = protocol.ProtocolSchema.read_jsonstr(msg)

            # Do some validation here
            # Evaluate if the Python object conforms to the protocol
            schema_validation_result = protocol.ProtocolSchema.validating(obj, m.protocol_schema)

            # If validation fails it will give a boolean fail in the database, and skip the unpacking process
            if schema_validation_result == True:

                # Insert into struct-like variables in the m-object.
                m.unpack(**obj)
                package = obj

                # Store any received statuscodes
                # 6xx -> Power Codes
                # 1xx-5xx -> Status Codes
                if m.msgType == "status":
                    # Get object in the db
                    s = Status.objects.all()[0]

                    if int(m.statusCode) >= 600:
                        s.latest_power_code = m.statusCode
                    else:
                        s.latest_status_code = m.statusCode

                    # Update the object
                    s.save()

                # For inbound data
                if m.msgType == "data":

                    # Needs to be decided:
                    # - How to transport the nodelete tag through a roundtrip?
                        # Have an idea --jan--

                    # - How to transport the requested_by tag through a roundtrip?
                        # ???? ask what's meant with  the question ????

                    #   [solved]
                    # - Is it the right choice to store the embedded file as binary? Do we need it?
                        # Binary is obsolete

                    # Create and store a JSON package in the db
                    ITP = Inbound_teststand_package()

                    # TimeStamp for primary_key
                    Timestamp = datetime.now()
                    ITP.Timestamp = Timestamp.strftime("%x-%I:%M:%S")

                    # Store values from inbound validated JSON
                    ITP.Sent_by = package["sentBy"]
                    ITP.command_list = package["commandList"]
                    ITP.Validation_failed = 0
                    ITP.save()

                    # Parameter's table
                    for p_name, p_val in package["parameterObj"].items():
                        print(p_name, p_val)
                        TSP = Test_stand_parameters()
                        TSP.Parameter_name = p_name
                        TSP.Parameter_value = p_val
                        TSP.Inbound_teststand_package = ITP
                        TSP.save()

                    # Data table
                    for data_name, data_points in package["dataObj"].items():
                        print(data_name, data_points)
                        TSD = Test_stand_data()
                        TSD.Data_name = data_name
                        TSD.Data_points = data_points
                        TSD.Inbound_teststand_package = ITP
                        TSD.save()

            else:
                package = obj

                # Create and store a JSON package in the db
                ITP = Inbound_teststand_package()

                # TimeStamp for primary_key
                Timestamp = datetime.now()

                if "sentBy" in package:
                    ITP.Sent_by = package["sentBy"]
                else:
                    ITP.Sent_by = "Failed validation"

                ITP.Timestamp = Timestamp.strftime("%x-%I:%M:%S")
                ITP.Validation_failed = 1

                ITP.save()

        # Pass the callback to the client
        subscriber = MqttClient("MessageHandler", on_message_callback)

        # Only subscribe to relevant inbound messages
        subscriber.subscribe("demo_module/inbound")

        print("Starting listening loop")
        subscriber.loop()