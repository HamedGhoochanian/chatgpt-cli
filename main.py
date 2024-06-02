import datetime
import json
import os.path
import time
from enum import Enum
from typing import List
import click
import openai
from rich.console import Console

with open('OPENAI_API_KEY', 'r') as key_file:
    openai.api_key = key_file.readline()


class ChatMessage:
    role: str
    content: str

    def __init__(self, role: str, content: str):
        self.content = content
        self.role = role

    def dict(self):
        return {
            "content": self.content,
            "role": self.role,
        }


class Roles(Enum):
    USER = 'user'
    ASSISTANT = 'assistant'
    SYSTEM = 'system'


class Conversation:
    messages: List[ChatMessage]
    history_path: str

    def _load_history_from_file(self):
        with open(self.history_path, 'r') as f:
            json_data = json.loads(f.read())
        self.messages = [ChatMessage(**l) for l in json_data]

    def __init__(self, history_path: str = None):
        if history_path:
            if not os.path.exists(history_path):
                raise Exception()
            self.history_path = history_path
            self._load_history_from_file()
        else:
            self.history_path = f'{int(datetime.datetime.now().timestamp())}.json'
            self.messages = []

    def ask_question(self, prompt: str, sleep_duration: float = 0.8) -> ChatMessage:
        if sleep_duration:
            time.sleep(sleep_duration)
        new_message = ChatMessage(Roles.USER.value, prompt)
        api_response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[m.dict() for m in self.messages] + [new_message.dict()],
        )
        response_message = ChatMessage(**api_response.choices[0].message)
        self.messages.extend([new_message, response_message])
        self._save_conversation_to_file()
        return response_message

    def _save_conversation_to_file(self):
        with open(self.history_path, 'w') as file:
            json_str = json.dumps([m.dict() for m in self.messages], indent=2)
            file.write(json_str)


def print_old_messages(console: Console, messages: List[ChatMessage]) -> None:
    for m in messages:
        if m.role == Roles.USER.value:
            console.print('Question: ', m.content, '\n', style='red')
        elif m.role == Roles.ASSISTANT.value:
            console.print('Answer: ', m.content, '\n', style='green')


@click.command()
@click.option('--history', help="history file path")
@click.option('--question_file')
def main(history: str, question_file: str) -> None:
    console = Console()
    conversation = Conversation(history)
    if conversation.messages:
        print_old_messages(console, conversation.messages)
    if question_file:
        with open(question_file, 'r') as f:
            prompt = f.read()
        response = conversation.ask_question(prompt)
        console.print(response.content, '\n', style='green')

    while True:
        prompt = click.prompt('Ask your question')
        response = conversation.ask_question(prompt)
        console.print(response.content, '\n', style='green')


if __name__ == '__main__':
    main()
