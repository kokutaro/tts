# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import service_pb2 as service__pb2


class APIServiceStub(object):
    """サービスの定義
    """

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.CallAPI = channel.unary_stream(
                '/example.APIService/CallAPI',
                request_serializer=service__pb2.APIRequest.SerializeToString,
                response_deserializer=service__pb2.APIResponse.FromString,
                )


class APIServiceServicer(object):
    """サービスの定義
    """

    def CallAPI(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_APIServiceServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'CallAPI': grpc.unary_stream_rpc_method_handler(
                    servicer.CallAPI,
                    request_deserializer=service__pb2.APIRequest.FromString,
                    response_serializer=service__pb2.APIResponse.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'example.APIService', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class APIService(object):
    """サービスの定義
    """

    @staticmethod
    def CallAPI(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_stream(request, target, '/example.APIService/CallAPI',
            service__pb2.APIRequest.SerializeToString,
            service__pb2.APIResponse.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)