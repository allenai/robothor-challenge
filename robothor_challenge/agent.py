from abc import ABC, abstractmethod


class Agent(ABC):

    def __init__(self, episode):
        self.episode = episode

    @abstractmethod
    def on_event(self, event):
        pass
