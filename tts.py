import dotenv
import io
import pygame
import glob
import queue
import threading
from pydub import AudioSegment
from pydub.playback import play
from concurrent.futures import Future, ThreadPoolExecutor
from openai import OpenAI
from pathlib import Path
from uuid import uuid4

dotenv.load_dotenv()

client = OpenAI()

MODEL = "gpt-3.5-turbo-1106"


def contains_special_characters(input_string):
    special_characters = ["。", "\n"]

    for char in input_string:
        if char in special_characters:
            return True

    return False


def worker(task_queue: queue.Queue, executor: ThreadPoolExecutor):
    while True:
        try:
            # キューからタスクを取得（ブロック可能）
            name = task_queue.get(block=True, timeout=3)
            future = executor.submit(play_audio, name)
            future.result()  # タスクの実行を待つ
            task_queue.task_done()
        except queue.Empty:
            # タイムアウトまたはキューが空の場合はループを続ける
            continue


def generate(propmt: str) -> str:
    message = ""
    message_chunk = ""

    tasks: list[Future[str]] = []
    task_queue = queue.Queue()
    message_queue = queue.Queue()

    def get_message():
        message = ""
        seq = 1
        stream = client.chat.completions.create(
            messages=[{"role": "user", "content": propmt}], model=MODEL, stream=True
        )

        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta is None:
                continue
            message_chunk += delta
            if contains_special_characters(delta):
                print(message_chunk)
                message_queue.put(message_chunk)
                message += message_chunk
                seq += 1
                message_chunk = ""
        if len(message_chunk) > 0:
            print(message_chunk)
            message_queue.put(message_chunk)
            message += message_chunk

    executor = ThreadPoolExecutor()
    executor.submit(get_message)

    while True:
        try:
            res = message_queue.get(timeout=10)
            print(res)
        except queue.Empty:
            break

    # with ThreadPoolExecutor() as executor:
    #     threading.Thread(
    #         target=worker, args=(task_queue, executor), daemon=True
    #     ).start()
    #     for chunk in stream:
    #         delta = chunk.choices[0].delta.content
    #         if delta is None:
    #             continue
    #         message_chunk += delta
    #         if contains_special_characters(delta):
    #             print(message_chunk)
    #             message += message_chunk
    #             tasks.append(executor.submit(text_to_speech, message_chunk, seq=seq))
    #             seq += 1
    #             message_chunk = ""
    #     if len(message_chunk) > 0:
    #         tasks.append(executor.submit(text_to_speech, message_chunk, seq=seq))

    #     for task in tasks:
    #         try:
    #             result = task.result()
    #             print(result)
    #             task_queue.put(task.result())
    #         except Exception as exc:
    #             print(f"Task generated an exception: {exc}")
    #     task_queue.join()

    return message + message_chunk


def text_to_speech(text, model="tts-1", voice="alloy", seq=0):
    try:
        audio_dir = Path.cwd() / "audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        speech_file_path = audio_dir / f"audio_{seq:03d}_{voice}_{model}_{uuid4()}.mp3"

        response = client.audio.speech.create(model=model, voice=voice, input=text)
        if speech_file_path.exists():
            speech_file_path.unlink()

        response.write_to_file(speech_file_path)

        return speech_file_path
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def play_audio(file_path, speed=1):
    sound = AudioSegment.from_file(file_path)
    sound_with_altered_speed = sound._spawn(
        sound.raw_data, overrides={"frame_rate": int(sound.frame_rate * speed)}
    ).set_frame_rate(sound.frame_rate)

    byte_io = io.BytesIO()
    sound_with_altered_speed.export(byte_io, format="wav")
    byte_io.seek(0)

    pygame.mixer.init()
    pygame.mixer.music.load(byte_io)
    pygame.mixer.music.play()

    while pygame.mixer.music.get_busy():
        pygame.time.Clock().tick(500)


def main():
    response = generate(
        """以下の文章を英語に翻訳してください。
1. エラーハンドリングが難しい: async void メソッドは非同期的な処理を行うため、エラーハンドリングが難しくなります。
例外が発生した場合、どこでキャッチすべきか不明確になります。
2. テストが難しい: async void メソッドはテストが難しくなります。
非同期的な処理の完了を待つ方法がないため、テストを書く際に問題が発生します。
3. タスクの完了を追跡できない: async void メソッドでは非同期的な処理の完了を追跡することができません。
そのため、タスクの進行状況を追うことができなくなります。
4. 例外がスレッドをクラッシュさせる可能性がある: async void メソッドは例外がスレッドをクラッシュさせる可能性があるため、安全ではありません。
そのため、代わりにasync Task メソッドを使用することをお勧めします。
async Task メソッドを使用すると、非同期的な処理を行う際にエラーハンドリングやタスクの進行状況を追跡することができ、より安全で柔軟なコードを書くことができます。"""
    )
    # file_path = text_to_speech(response)
    # for file in glob.glob("audio/*.mp3"):
    #     play_audio(file, 1)


if __name__ == "__main__":
    main()
