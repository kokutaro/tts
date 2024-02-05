import concurrent.futures
import time
import queue
import threading


def sample_task(name, delay):
    time.sleep(delay)
    return f"Task {name} completed in {delay} seconds"


def worker(task_queue, executor):
    while True:
        try:
            # キューからタスクを取得（ブロック可能）
            name, delay = task_queue.get(block=True, timeout=3)
            future = executor.submit(sample_task, name, delay)
            result = future.result()  # タスクの実行を待つ
            print(result)
            task_queue.task_done()
        except queue.Empty:
            # タイムアウトまたはキューが空の場合はループを続ける
            continue


def main():
    tasks = [("One", 2), ("Two", 3), ("Three", 5)]

    task_queue = queue.Queue()

    # タスクをキューに追加
    for task in tasks:
        task_queue.put(task)

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # ワーカースレッドを起動
        threading.Thread(
            target=worker, args=(task_queue, executor), daemon=True
        ).start()

        # 追加のタスクをキューに入れる
        task_queue.put(("Four", 4))
        task_queue.put(("Five", 1))

        task_queue.join()  # すべてのタスクが完了するのを待つ

    print("All tasks are completed")


# main()を呼び出してプログラムを実行
main()
