import grpc
from concurrent import futures
from openai import OpenAI
from tts import text_to_speech
import service_pb2
import service_pb2_grpc
from queue import Queue
import queue
import dotenv

dotenv.load_dotenv()

client = OpenAI()

MODEL = "gpt-3.5-turbo-1106"


class ClosableQueue(Queue):
    SENTINEL = object()

    def __init__(self, max_size=0):
        super().__init__(max_size)
        self.closed = False
        self.close_request = False

    def close(self):
        self.put(self.SENTINEL)
        self.close_request = True

    def __iter__(self):
        while True:
            item = self.get()
            try:
                if item is self.SENTINEL:
                    self.closed = True
                    return
                yield item
            finally:
                self.task_done()


def contains_special_characters(input_string):
    special_characters = ["。", "\n"]

    for char in input_string:
        if char in special_characters:
            return True

    return False


class APIService(service_pb2_grpc.APIServiceServicer):
    def CallAPI(self, request, context):
        response_queue = ClosableQueue()
        message_queue = ClosableQueue()
        executor = futures.ThreadPoolExecutor(max_workers=5)

        def create_audio(text, seq):
            is_final = message_queue.close_request
            result = text_to_speech(text, seq=seq)
            response_queue.put(str(result))
            if is_final:
                response_queue.close()
            print(result)

        def run_task():
            seq = 0
            message_chunk = ""
            stream = client.chat.completions.create(
                messages=[{"role": "user", "content": request.data}],
                model=MODEL,
                stream=True,
            )
            for chunk in stream:
                delta = chunk.choices[0].delta.content
                if delta is None:
                    continue
                message_queue.put(delta)
                message_chunk += delta
                if contains_special_characters(delta):
                    print(message_chunk)
                    executor.submit(create_audio, message_chunk, seq)
                    message_chunk = ""
                    seq += 1

            if len(message_chunk) > 0:
                print(message_chunk)
                executor.submit(create_audio, message_chunk, seq)

            message_queue.close()

        executor.submit(run_task)

        while True:
            try:
                if not message_queue.empty():
                    message = message_queue.get(timeout=10)
                    if message is not message_queue.SENTINEL:
                        yield service_pb2.APIResponse(result=message)
                    else:
                        message_queue.closed = True

                if not response_queue.empty():
                    response_data = response_queue.get(timeout=10)
                    if response_data is not response_queue.SENTINEL:
                        yield service_pb2.APIResponse(
                            result=response_data, is_audio=True
                        )
                    else:
                        response_queue.closed = True

                if response_queue.closed and message_queue.closed:
                    break

            except queue.Empty:
                continue

        print("Done")


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    service_pb2_grpc.add_APIServiceServicer_to_server(APIService(), server)
    server.add_insecure_port("[::]:50051")
    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    try:
        serve()
    except KeyboardInterrupt:
        exit()
