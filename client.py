import grpc
import service_pb2
import service_pb2_grpc
import queue
import threading
from concurrent.futures import ThreadPoolExecutor
from tts import play_audio


def worker(task_queue, executor):
    while True:
        try:
            # キューからタスクを取得（ブロック可能）
            name = task_queue.get(block=True, timeout=3)
            future = executor.submit(play_audio, name)
            result = future.result()  # タスクの実行を待つ
            print(result)
            task_queue.task_done()
        except queue.Empty:
            # タイムアウトまたはキューが空の場合はループを続ける
            continue


def run():
    audio_queue = queue.Queue()
    executor = ThreadPoolExecutor()
    threading.Thread(target=worker, args=(audio_queue, executor), daemon=True).start()
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = service_pb2_grpc.APIServiceStub(channel)
        response = stub.CallAPI(
            service_pb2.APIRequest(
                data="async voidメソッドを避けるべき理由を教えてください"
            )
        )
        for res in response:
            if res.is_audio:
                audio_queue.put(res.result)
                print("API Response:", res.result)

    audio_queue.join()


try:
    run()
except KeyboardInterrupt:
    exit()
