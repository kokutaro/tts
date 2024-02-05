from concurrent.futures import Future, ThreadPoolExecutor, as_completed
import time
import queue
import threading

task_a = [2, 5, 5, 3]
task_b = [11, 2, 4, 3]
task_c = [4, 4, 4, 3]


def do_task(delay, seq, done=False):
    time.sleep(delay)
    print(f"Done  Task_{'C' if done else 'B'}: {seq} Delay={delay}")
    if not done:
        do_task(task_c[seq], seq, True)
    return seq


def worker(task_queue: queue.Queue, executor: ThreadPoolExecutor):
    futures: list[Future] = []
    while True:
        try:
            # キューからタスクを取得（ブロック可能）
            i, delay = task_queue.get(block=False, timeout=3)
            futures.append((executor.submit(do_task, delay, i)))
            task_queue.task_done()
        except queue.Empty:
            # タイムアウトまたはキューが空の場合はループを続ける
            continue


def main():
    task_queue = queue.Queue()
    with ThreadPoolExecutor() as executor:
        # ワーカースレッドを起動
        threading.Thread(
            target=worker, args=(task_queue, executor), daemon=True
        ).start()

        for i, task in enumerate(task_a):
            time.sleep(task)
            print(f"Start Task_B: {i} Delay={task_b[i]}")
            task_queue.put((i, task_b[i]))

        task_queue.join()
    print("All tasks are completed")


main()
